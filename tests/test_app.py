"""Tests for the FastAPI web application."""
import os
import sys
import json
import pytest
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock, mock_open, PropertyMock
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app
from app import (
    StateLoadingStats, 
    log_state_stats, 
    load_state_mapping, 
    save_state_mapping,
    get_latest_state
)

# Import HivemindState from src.hivemind.state
sys.path.append(os.path.join(project_root, "src"))
from hivemind.state import HivemindState

# Create a fixture for temporary directory
@pytest.fixture(scope="session")
def temp_states_dir():
    """Create a temporary directory for test state files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Clean up after tests
    shutil.rmtree(temp_dir)

@pytest.fixture(autouse=True)
def patch_states_dir(temp_states_dir):
    """Patch the STATES_DIR constant in app.py to use the temporary directory."""
    with patch("app.STATES_DIR", temp_states_dir):
        yield

@pytest.mark.unit
class TestStateLoadingStats:
    """Test the StateLoadingStats class."""
    
    def test_init(self) -> None:
        """Test initialization of StateLoadingStats."""
        stats = StateLoadingStats()
        assert stats.state_cid is None
        assert stats.state_load_time == 0
        assert stats.options_load_time == 0
        assert stats.opinions_load_time == 0
        assert stats.calculation_time == 0
        assert stats.total_time == 0
        assert stats.num_questions == 0
        assert stats.num_options == 0
        assert stats.num_opinions == 0
        
    def test_to_dict(self) -> None:
        """Test the to_dict method."""
        stats = StateLoadingStats()
        stats.state_cid = "test_cid"
        stats.state_load_time = 1.0
        stats.options_load_time = 2.0
        stats.opinions_load_time = 3.0
        stats.calculation_time = 4.0
        stats.total_time = 10.0
        stats.num_questions = 5
        stats.num_options = 6
        stats.num_opinions = 7
        
        stats_dict = stats.to_dict()
        assert stats_dict["state_cid"] == "test_cid"
        assert stats_dict["state_load_time"] == 1.0
        assert stats_dict["options_load_time"] == 2.0
        assert stats_dict["opinions_load_time"] == 3.0
        assert stats_dict["calculation_time"] == 4.0
        assert stats_dict["total_time"] == 10.0
        assert stats_dict["num_questions"] == 5
        assert stats_dict["num_options"] == 6
        assert stats_dict["num_opinions"] == 7


@pytest.mark.unit
class TestLoggingFunctions:
    """Test logging related functions."""
    
    @patch("app.logger")
    def test_log_state_stats(self, mock_logger) -> None:
        """Test logging state statistics."""
        # Create test stats
        stats = StateLoadingStats()
        stats.state_cid = "test_cid"
        stats.state_load_time = 1.0
        stats.options_load_time = 2.0
        stats.opinions_load_time = 3.0
        stats.calculation_time = 4.0
        stats.total_time = 10.0
        stats.num_questions = 5
        stats.num_options = 6
        stats.num_opinions = 7
        
        # Call the function
        log_state_stats(stats)
        
        # Verify logger was called with expected messages
        assert mock_logger.info.call_count == 11
        mock_logger.info.assert_any_call("State Loading Statistics:")
        mock_logger.info.assert_any_call(f"  State CID: test_cid")
        mock_logger.info.assert_any_call(f"  State Load Time: 1.0s")
        mock_logger.info.assert_any_call(f"  Options Load Time: 2.0s")
        mock_logger.info.assert_any_call(f"  Opinions Load Time: 3.0s")
        mock_logger.info.assert_any_call(f"  Calculation Time: 4.0s")
        mock_logger.info.assert_any_call(f"  Total Time: 10.0s")
        mock_logger.info.assert_any_call(f"  Number of Questions: 5")
        mock_logger.info.assert_any_call(f"  Number of Options: 6")
        mock_logger.info.assert_any_call(f"  Number of Opinions: 7")

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.writer")
    def test_log_stats_to_csv(self, mock_csv_writer, mock_file) -> None:
        """Test logging state statistics to CSV file."""
        # Create test stats
        stats = StateLoadingStats()
        stats.state_cid = "test_cid"
        stats.state_load_time = 1.0
        stats.options_load_time = 2.0
        stats.opinions_load_time = 3.0
        stats.calculation_time = 4.0
        stats.total_time = 10.0
        stats.num_questions = 5
        stats.num_options = 6
        stats.num_opinions = 7
        stats.timestamp = "2023-01-01T12:00:00"
        
        # Mock csv.writer
        mock_writer = MagicMock()
        mock_csv_writer.return_value = mock_writer
        
        # Call the function
        from app import log_stats_to_csv
        log_stats_to_csv(stats)
        
        # Verify file was opened correctly
        mock_file.assert_called_once_with('logs/state_loading_stats.csv', 'a', newline='')
        
        # Verify writer was called with expected row
        mock_writer.writerow.assert_called_once_with([
            "2023-01-01T12:00:00",
            "test_cid",
            1.0,
            2.0,
            3.0,
            4.0,
            10.0,
            5,
            6,
            7
        ])
    
    @patch("builtins.open")
    @patch("app.logger")
    def test_log_stats_to_csv_exception(self, mock_logger, mock_open_func) -> None:
        """Test logging state statistics to CSV file with exception."""
        # Create test stats
        stats = StateLoadingStats()
        stats.state_cid = "test_cid"
        
        # Mock open to raise an exception
        mock_open_func.side_effect = Exception("Test exception")
        
        # Call the function
        from app import log_stats_to_csv
        log_stats_to_csv(stats)
        
        # Verify logger.error was called with the expected message
        mock_logger.error.assert_called_once_with("Failed to write stats to CSV: Test exception")

    @patch("app.logger")
    def test_save_state_mapping_exception(self, mock_logger) -> None:
        """Test save_state_mapping when a top-level exception occurs."""
        # Create a test mapping
        test_mapping = {
            "test_id": {
                "state_hash": "test_hash",
                "name": "Test Hivemind",
                "description": "Test Description",
                "num_options": 5
            }
        }
        
        # Force a top-level exception by patching STATES_DIR to raise an exception
        with patch("app.STATES_DIR", new_callable=PropertyMock) as mock_states_dir:
            mock_states_dir.side_effect = Exception("Test exception")
            
            # Call the function
            save_state_mapping(test_mapping)
            
            # Verify logger.error was called with any error message
            mock_logger.error.assert_called_once()
            # Extract the actual error message for verification
            actual_call_args = mock_logger.error.call_args[0][0]
            assert actual_call_args.startswith("Failed to save state mapping:")
    
@pytest.mark.unit
class TestStateManagement:
    """Test state management functions."""
    
    @patch("app.STATES_DIR")
    @patch("builtins.open", new_callable=mock_open, read_data='{"state_hash": "test_hash"}')
    def test_load_state_mapping(self, mock_file, mock_states_dir) -> None:
        """Test loading state mapping from files."""
        # Setup mock directory structure
        mock_states_dir.glob.return_value = [
            MagicMock(stem="test_id", __str__=lambda self: "test_id.json")
        ]
        
        # Call the function
        result = load_state_mapping()
        
        # Verify results
        assert "test_id" in result
        assert result["test_id"]["state_hash"] == "test_hash"
        mock_states_dir.glob.assert_called_once_with("*.json")
        
    @patch("app.STATES_DIR")
    def test_load_state_mapping_exception(self, mock_states_dir) -> None:
        """Test loading state mapping when an exception occurs."""
        # Setup mock directory to raise an exception
        mock_states_dir.glob.side_effect = Exception("Test exception")
        
        # Call the function
        result = load_state_mapping()
        
        # Verify results - should return empty dict on exception
        assert result == {}
        mock_states_dir.glob.assert_called_once_with("*.json")

    @patch("app.STATES_DIR")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_state_mapping(self, mock_json_dump, mock_file, mock_states_dir) -> None:
        """Test saving state mapping to files."""
        # Setup test data
        mapping: Dict[str, Dict[str, Any]] = {
            "test_id": {"state_hash": "test_hash", "name": "Test Name"}
        }
        
        # Call the function
        save_state_mapping(mapping)
        
        # Verify results
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        assert args[0] == {"state_hash": "test_hash", "name": "Test Name"}
        assert kwargs["indent"] == 2
        
    @patch("app.load_state_mapping")
    @pytest.mark.asyncio
    async def test_get_latest_state(self, mock_load_state_mapping) -> None:
        """Test retrieving the latest state for a specific hivemind ID."""
        # Setup test data
        mock_load_state_mapping.return_value = {
            "test_id": {"state_hash": "test_hash", "name": "Test Name"},
            "other_id": {"state_hash": "other_hash", "name": "Other Name"}
        }
        
        # Test with existing ID
        result = await get_latest_state("test_id")
        assert result["hivemind_id"] == "test_id"
        assert result["state_hash"] == "test_hash"
        assert result["name"] == "Test Name"
        
        # Test with non-existent ID - should raise HTTPException
        with pytest.raises(app.HTTPException) as excinfo:
            await get_latest_state("non_existent_id")
        assert excinfo.value.status_code == 404
        assert "Hivemind ID not found" in excinfo.value.detail
        
        # Verify load_state_mapping was called
        assert mock_load_state_mapping.call_count == 2


@pytest.mark.unit
class TestEndpoints:
    """Test FastAPI endpoints."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)
    
    def test_landing_page(self):
        """Test the landing page endpoint."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check for expected content in the HTML
        assert "<title>" in response.text
        
    def test_insights_page(self):
        """Test the insights page endpoint."""
        # Test without CID parameter
        response = self.client.get("/insights")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<title>" in response.text
        
        # Test with CID parameter
        response = self.client.get("/insights?cid=test_cid")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<title>" in response.text
        
    def test_create_page(self):
        """Test the create page endpoint."""
        response = self.client.get("/create")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<title>" in response.text
        
    @patch("app.load_state_mapping")
    def test_states_page(self, mock_load_state_mapping):
        """Test the states page endpoint."""
        # Setup mock data
        mock_load_state_mapping.return_value = {
            "test_id": {"state_hash": "test_hash", "name": "Test Name"},
            "other_id": {"state_hash": "other_hash", "name": "Other Name"}
        }
        
        # Mock Path.stat() for file modification times
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value = MagicMock(st_mtime=1234567890.0)
            
            # Test the endpoint
            response = self.client.get("/states")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            assert "<title>" in response.text
            
    @patch("app.load_state_mapping")
    def test_states_page_with_stat_exception(self, mock_load_state_mapping):
        """Test the states page endpoint when Path.stat() raises an exception."""
        # Setup mock data
        mock_load_state_mapping.return_value = {
            "test_id": {"state_hash": "test_hash", "name": "Test Name"},
            "error_id": {"state_hash": "error_hash", "name": "Error Name"}
        }
        
        # Mock Path.stat() to raise an exception
        with patch("pathlib.Path.stat") as mock_stat:
            # First call succeeds, second call raises exception
            mock_stat.side_effect = [
                MagicMock(st_mtime=1234567890.0),
                FileNotFoundError("Test exception")
            ]
            
            # Mock logger to capture error messages
            with patch("app.logger") as mock_logger:
                # Test the endpoint
                response = self.client.get("/states")
                
                # Verify the response was successful despite the error
                assert response.status_code == 200
                assert "text/html" in response.headers["content-type"]
                
                # Verify logger.error was called for the exception
                assert mock_logger.error.call_count >= 1
                # Check that at least one error log contains our expected message parts
                error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
                assert any("Failed to get modification time" in msg and "Test exception" in msg for msg in error_calls)
            
    @patch("app.load_state_mapping")
    def test_states_page_general_exception(self, mock_load_state_mapping):
        """Test the states page endpoint when a general exception occurs."""
        # Force load_state_mapping to raise an exception
        mock_load_state_mapping.side_effect = Exception("Test general exception")
        
        # Mock logger to capture error messages
        with patch("app.logger") as mock_logger:
            # Test the endpoint - should raise HTTPException with 500 status
            response = self.client.get("/states")
            
            # Verify the response has a 500 status code
            assert response.status_code == 500
            
            # Verify that the logger.error was called with the expected message
            mock_logger.error.assert_called_once_with("Error loading states page: Test general exception")
    
    def test_get_all_states(self):
        """Test the get_all_states endpoint."""
        with patch("app.load_state_mapping") as mock_load_state_mapping:
            # Setup mock data
            mock_load_state_mapping.return_value = {
                "test_id": {"state_hash": "test_hash", "name": "Test Name"},
                "other_id": {"state_hash": "other_hash", "name": "Other Name"}
            }
            
            # Test the endpoint
            response = self.client.get("/api/all_states")
            assert response.status_code == 200
            data = response.json()
            assert "states" in data
            states = data["states"]
            assert len(states) == 2
            assert any(state["hivemind_id"] == "test_id" for state in states)
            assert any(state["hivemind_id"] == "other_id" for state in states)
    
    @patch("app.HivemindIssue")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    @patch("app.HivemindOpinion")
    def test_fetch_state_success(self, mock_hivemind_opinion_class, mock_hivemind_option_class, mock_hivemind_state_class, mock_hivemind_issue_class):
        """Test the fetch_state endpoint with a successful state load."""
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_id"
        mock_state.options = {"option1": "value1", "option2": "value2"}
        mock_state.opinions = [
            {"address1": {"opinion_cid": "opinion1", "timestamp": "2023-01-01", "ranking": ["option1", "option2"]}}
        ]
        mock_state.final = False
        mock_state.get_questions.return_value = ["Question 1?"]
        mock_state.get_options_for_question.return_value = [
            {"id": "option1", "value": "value1", "text": "Option 1"},
            {"id": "option2", "value": "value2", "text": "Option 2"}
        ]
        mock_state.get_rankings.return_value = {
            "option1": {"rank": 1, "score": 1.0},
            "option2": {"rank": 2, "score": 0.5}
        }
        mock_state.get_participants.return_value = ["participant1"]
        mock_state.calculate_results.return_value = {
            "rankings": [
                {"id": "option1", "rank": 1, "score": 1.0},
                {"id": "option2", "rank": 2, "score": 0.5}
            ]
        }
        
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.tags = ["test", "mock"]
        mock_issue.questions = ["Question 1?"]
        mock_issue.answer_type = "ranked"
        mock_issue.constraints = {}
        mock_issue.restrictions = {}
        
        # Setup mock option instance
        mock_option = MagicMock()
        mock_option.value = "test_value"
        mock_option.text = "Test Option"
        
        # Setup mock opinion instance
        mock_opinion = MagicMock()
        mock_opinion.ranking = ["option1", "option2"]
        
        # Configure the mock classes to return our mock instances
        mock_hivemind_state_class.return_value = mock_state
        mock_hivemind_issue_class.return_value = mock_issue
        mock_hivemind_option_class.return_value = mock_option
        mock_hivemind_opinion_class.return_value = mock_opinion
        
        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_cid"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check basic structure
        assert data["hivemind_id"] == "test_id"
        assert data["num_options"] == 2
        assert data["num_opinions"] == 1
        assert data["is_final"] is False
        
        # Check issue data
        assert "issue" in data
        assert data["issue"]["name"] == "Test Issue"
        assert data["issue"]["description"] == "Test Description"
        
        # Check that other expected fields exist
        assert "full_opinions" in data
        assert "stats" in data
        
    def test_fetch_state_missing_cid(self):
        """Test the fetch_state endpoint with a missing CID."""
        # Test with empty CID
        response = self.client.post(
            "/fetch_state",
            json={"cid": ""}
        )
        assert response.status_code == 500
        data = response.json()
        assert "CID is required" in data["detail"]
        
        # Test with no CID field at all
        response = self.client.post(
            "/fetch_state",
            json={}
        )
        assert response.status_code == 422  # Validation error from Pydantic
        
    @patch("app.HivemindState")
    def test_fetch_state_exception(self, mock_hivemind_state):
        """Test the fetch_state endpoint when an exception occurs."""
        # Configure mock to raise an exception
        mock_hivemind_state.side_effect = Exception("IPFS error")
        
        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_cid"}
        )
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "IPFS error" in data["detail"]

    @patch("app.HivemindIssue")
    def test_create_issue(self, mock_hivemind_issue):
        """Test the create_issue endpoint."""
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data
        issue_data = {
            "name": "Test Issue",
            "description": "Test Description",
            "questions": ["Question 1?"],
            "tags": ["test", "mock"],
            "answer_type": "ranked",
            "constraints": {"min": 1, "max": 5},
            "restrictions": {"allowed_addresses": ["addr1", "addr2"]},
            "on_selection": None
        }
        
        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_hivemind_state.return_value = mock_state_instance
            
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_issue_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        assert mock_issue_instance.on_selection == issue_data["on_selection"]
        
        # Verify add_question was called for each question
        for question in issue_data["questions"]:
            mock_issue_instance.add_question.assert_any_call(question)
        
        # Verify set_constraints and set_restrictions were called
        mock_issue_instance.set_constraints.assert_called_once_with(issue_data["constraints"])
        mock_issue_instance.set_restrictions.assert_called_once_with(issue_data["restrictions"])
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()
    
    @patch("app.HivemindIssue")
    def test_add_option_page(self, mock_hivemind_issue):
        """Test the add_option_page endpoint."""
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.name = "Test Issue"
        mock_issue_instance.description = "Test Description"
        mock_issue_instance.questions = ["Question 1?"]
        mock_issue_instance.answer_type = "ranked"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Test the endpoint
        response = self.client.get("/options/add?hivemind_id=test_hivemind_id")
        
        # Verify response
        assert response.status_code == 200
        assert "<title>" in response.text
        
        # Verify the HivemindIssue was loaded with the correct ID
        mock_hivemind_issue.assert_called_once_with(cid="test_hivemind_id")
    
    @patch("app.HivemindOption")
    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    @patch("app.load_state_mapping")
    def test_create_option(self, mock_load_state_mapping, mock_hivemind_issue, mock_hivemind_state, mock_hivemind_option):
        """Test the create_option endpoint."""
        # Setup mock option instance
        mock_option_instance = MagicMock()
        mock_option_instance.save.return_value = "test_option_cid"
        mock_hivemind_option.return_value = mock_option_instance
        
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.answer_type = "string"
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.options = ["existing_option"]
        mock_state.save.return_value = "new_state_cid"
        mock_state.add_option = MagicMock()
        
        # Mock the add_option method to update the options list
        def side_effect_add_option(timestamp, option_hash):
            mock_state.options.append(option_hash)
        mock_state.add_option.side_effect = side_effect_add_option
        
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock state mapping
        mock_load_state_mapping.return_value = {
            "test_hivemind_id": {
                "state_hash": "test_state_cid"
            }
        }
        
        # Setup test data
        option_data = {
            "hivemind_id": "test_hivemind_id",
            "value": "test_value",
            "text": "Test Option"
        }
        
        # Test the endpoint
        with patch("app.update_state") as mock_update_state:
            mock_update_state.return_value = {"success": True}
            
            response = self.client.post(
                "/api/options/create",
                json=option_data
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["option_cid"] == "test_option_cid"
        assert data["state_cid"] == "new_state_cid"
        
        # Verify the HivemindOption was created with correct attributes
        mock_hivemind_option.assert_called_once()
        assert mock_option_instance.value == "test_value"
        assert mock_option_instance.text == "Test Option"
        
        # Verify the state was updated and saved
        assert "test_option_cid" in mock_state.options
    
    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    def test_add_opinion_page(self, mock_hivemind_issue, mock_hivemind_state):
        """Test the add_opinion_page endpoint."""
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.questions = ["Question 1?"]
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_hivemind_id"
        mock_state.options = ["option1", "option2"]
        mock_state.get_options_for_question.return_value = [
            {"id": "option1", "value": "value1", "text": "Option 1"},
            {"id": "option2", "value": "value2", "text": "Option 2"}
        ]
        mock_hivemind_state.return_value = mock_state
        
        # Test the endpoint
        response = self.client.get("/add_opinion?cid=test_state_cid")
        
        # Verify response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<title>" in response.text
        
        # Verify the HivemindState was loaded with the correct CID
        mock_hivemind_state.assert_called_once_with(cid="test_state_cid")
    
    def test_test_ipfs(self):
        """Test the test_ipfs endpoint."""
        # Test the endpoint
        with patch("ipfs_dict_chain.IPFS.connect") as mock_connect:
            # Configure mock to return successfully
            mock_connect.return_value = True
            
            response = self.client.post("/api/test_ipfs")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "message" in data
    
    @patch("app.load_state_mapping")
    @patch("builtins.open", new_callable=mock_open)
    def test_update_state(self, mock_file, mock_load_state_mapping):
        """Test the update_state endpoint."""
        # Setup mock data
        mock_load_state_mapping.return_value = {
            "test_id": {"state_hash": "old_hash", "name": "Old Name"}
        }
        
        # Setup test data
        state_update = {
            "hivemind_id": "test_id",
            "state_hash": "new_hash",
            "name": "New Name",
            "description": "New Description",
            "num_options": 5,
            "num_opinions": 10,
            "answer_type": "ranked",
            "questions": ["New Question?"],
            "tags": ["new", "tags"]
        }
        
        # Test the endpoint
        response = self.client.post(
            "/api/update_state",
            json=state_update
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["hivemind_id"] == "test_id"
        assert data["state_hash"] == "new_hash"
        assert data["name"] == "New Name"
        
        # Verify file was written
        mock_file.assert_called_once()
    
    @patch("app.HivemindOpinion")
    @patch("app.HivemindState")
    def test_submit_opinion(self, mock_hivemind_state, mock_hivemind_opinion):
        """Test the submit_opinion endpoint."""
        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_opinion_instance.save.return_value = "test_opinion_cid"
        mock_hivemind_opinion.return_value = mock_opinion_instance
        
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.save.return_value = "new_state_cid"
        mock_hivemind_state.return_value = mock_state
        
        # Setup test data
        opinion_data = {
            "hivemind_id": "test_hivemind_id",
            "question_index": 0,
            "ranking": ["option1", "option2"]
        }
        
        # Test the endpoint
        response = self.client.post(
            "/api/submit_opinion",
            json=opinion_data
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cid"] == "test_opinion_cid"
        
        # Verify the HivemindOpinion was created with correct attributes
        mock_hivemind_opinion.assert_called_once()
        # The ranking is set through the Ranking class, so we can't directly check mock_opinion_instance.ranking
    
    @patch("app.HivemindIssue")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    @patch("app.HivemindOpinion")
    def test_fetch_state_option_load_exception(self, mock_hivemind_opinion_class, mock_hivemind_option_class, mock_hivemind_state_class, mock_hivemind_issue_class):
        """Test the fetch_state endpoint when loading an option raises an exception."""
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_id"
        mock_state.options = {"option1": "value1", "option2": "value2"}
        mock_state.opinions = {}
        mock_state.final = False
        mock_state.get_questions.return_value = ["Question 1?"]
        
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.tags = ["test", "mock"]
        mock_issue.questions = ["Question 1?"]
        mock_issue.answer_type = "ranked"
        
        # Configure the mock classes to return our mock instances
        mock_hivemind_state_class.return_value = mock_state
        mock_hivemind_issue_class.return_value = mock_issue
        
        # Configure HivemindOption to raise an exception when initialized
        mock_hivemind_option_class.side_effect = Exception("Failed to load option")
        
        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_cid"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check that options were handled correctly despite the exception
        assert "options" in data
        options = data["options"]
        assert len(options) == 2  # Should still have 2 options
        
        # Verify that the options contain the error message
        for option in options:
            assert option["value"] is None
            assert "Failed to load:" in option["text"]

    @patch("app.HivemindIssue")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    @patch("app.HivemindOpinion")
    def test_fetch_state_opinion_ranking_formats(self, mock_hivemind_opinion_class, mock_hivemind_option_class, mock_hivemind_state_class, mock_hivemind_issue_class):
        """Test the fetch_state endpoint with different opinion ranking formats."""
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_id"
        mock_state.options = {"option1": "value1", "option2": "value2"}
        # Create three different opinions with different ranking formats
        mock_state.opinions = [
            {
                "address1": {"opinion_cid": "opinion1", "timestamp": "2023-01-01"},
                "address2": {"opinion_cid": "opinion2", "timestamp": "2023-01-01"},
                "address3": {"opinion_cid": "opinion3", "timestamp": "2023-01-01"}
            }
        ]
        mock_state.final = False
        mock_state.get_questions.return_value = ["Question 1?"]
        mock_state.calculate_results.return_value = {}
        mock_state.get_sorted_options.return_value = []
        mock_state.contributions.return_value = {}
        
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        
        # Setup mock option instance
        mock_option = MagicMock()
        mock_option.value = "test_value"
        mock_option.text = "Test Option"
        
        # Configure the mock classes to return our mock instances
        mock_hivemind_state_class.return_value = mock_state
        mock_hivemind_issue_class.return_value = mock_issue
        mock_hivemind_option_class.return_value = mock_option
        
        # Create three different opinion instances with different ranking formats
        # 1. Opinion with ranking as a list
        mock_opinion_list = MagicMock()
        mock_opinion_list.ranking = ["option1", "option2"]
        
        # 2. Opinion with ranking as a dict with 'fixed' key
        mock_opinion_dict = MagicMock()
        mock_opinion_dict.ranking = {"fixed": ["option2", "option1"]}
        
        # 3. Opinion with ranking as an object with 'fixed' attribute
        class RankingWithFixed:
            def __init__(self):
                self.fixed = ["option1"]
        
        mock_opinion_obj = MagicMock()
        mock_opinion_obj.ranking = RankingWithFixed()
        
        # Configure mock_hivemind_opinion_class to return different instances based on the CID
        def get_opinion(cid):
            if cid == "opinion1":
                return mock_opinion_list
            elif cid == "opinion2":
                return mock_opinion_dict
            elif cid == "opinion3":
                return mock_opinion_obj
        
        mock_hivemind_opinion_class.side_effect = lambda cid: get_opinion(cid)
        
        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_cid"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check that opinions were processed correctly
        assert "opinions" in data
        opinions = data["opinions"][0]  # First question's opinions
        
        # Check that each opinion has the correct ranking format
        assert opinions["address1"]["ranking"] == ["option1", "option2"]  # List format
        assert opinions["address2"]["ranking"] == ["option2", "option1"]  # Dict with 'fixed' key
        assert opinions["address3"]["ranking"] == ["option1"]  # Object with 'fixed' attribute

    @patch("app.HivemindState")
    def test_fetch_state_exception(self, mock_hivemind_state):
        """Test the fetch_state endpoint when an exception occurs."""
        # Configure mock to raise an exception
        mock_hivemind_state.side_effect = Exception("IPFS error")
        
        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_cid"}
        )
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "IPFS error" in data["detail"]

    @patch("app.HivemindIssue")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    @patch("app.HivemindOpinion")
    def test_fetch_state_opinion_load_exception(self, mock_hivemind_opinion_class, mock_hivemind_option_class, mock_hivemind_state_class, mock_hivemind_issue_class):
        """Test the fetch_state endpoint when loading an opinion raises an exception."""
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_id"
        mock_state.options = {"option1": "value1", "option2": "value2"}
        # Create opinions with one that will cause an exception
        mock_state.opinions = [
            {
                "address1": {"opinion_cid": "opinion1", "timestamp": "2023-01-01"},
                "address2": {"opinion_cid": "opinion2", "timestamp": "2023-01-01"}
            }
        ]
        mock_state.final = False
        mock_state.get_questions.return_value = ["Question 1?"]
        mock_state.calculate_results.return_value = {}
        mock_state.get_sorted_options.return_value = []
        mock_state.contributions.return_value = {}
        
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        
        # Setup mock option instance
        mock_option = MagicMock()
        mock_option.value = "test_value"
        mock_option.text = "Test Option"
        
        # Configure the mock classes to return our mock instances
        mock_hivemind_state_class.return_value = mock_state
        mock_hivemind_issue_class.return_value = mock_issue
        mock_hivemind_option_class.return_value = mock_option
        
        # Configure mock_hivemind_opinion_class to return a valid opinion for address1
        # but raise an exception for address2
        def get_opinion(cid):
            if cid == "opinion1":
                mock_opinion = MagicMock()
                mock_opinion.ranking = ["option1", "option2"]
                return mock_opinion
            elif cid == "opinion2":
                raise Exception("Failed to load opinion")
        
        mock_hivemind_opinion_class.side_effect = get_opinion
        
        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_cid"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check that opinions were processed correctly
        assert "opinions" in data
        opinions = data["opinions"][0]  # First question's opinions
        
        # Check that the successful opinion was loaded correctly
        assert opinions["address1"]["ranking"] == ["option1", "option2"]
        
        # Check that the failed opinion has the expected error structure
        assert opinions["address2"]["ranking"] is None
        assert "error" in opinions["address2"]
        assert "Failed to load opinion" in opinions["address2"]["error"]

if __name__ == "__main__":
    pytest.main(["-xvs", "test_app.py"])
