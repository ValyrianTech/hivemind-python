"""Tests for the FastAPI web application."""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
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
            
    def test_generate_keypair(self):
        """Test the generate_keypair endpoint."""
        response = self.client.get("/generate_keypair")
        assert response.status_code == 200
        data = response.json()
        assert "private_key" in data
        assert "address" in data
        
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
