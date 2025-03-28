"""Tests for error handling in the FastAPI web application."""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app

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
class TestErrorHandling:
    """Test error handling in the FastAPI endpoints."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    def test_add_opinion_page_exception(self, mock_hivemind_issue, mock_hivemind_state):
        """Test the add_opinion_page endpoint when an exception occurs."""
        # Configure mock to raise an exception
        mock_hivemind_state.side_effect = Exception("Test error message")

        # Test the endpoint
        response = self.client.get("/add_opinion?cid=test_state_cid")

        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "Test error message" in data["detail"]

        # Verify the logger was called with the error message
        with patch("app.logger") as mock_logger:
            # Re-run the test with the logger patched
            mock_hivemind_state.side_effect = Exception("Test error message")
            response = self.client.get("/add_opinion?cid=test_state_cid")

            # Verify logger.error was called with the expected message
            mock_logger.error.assert_called_once_with("Error rendering add opinion page: Test error message")

    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    def test_add_opinion_page_option_loading(self, mock_hivemind_issue, mock_hivemind_state):
        """Test the option loading functionality in the add_opinion_page endpoint."""
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.questions = ["Question 1?"]
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_hivemind_id"
        mock_state.option_cids = ["option1", "option2"]
        # Configure get_option to raise an exception for the second option
        mock_option1 = MagicMock()
        mock_option1.value = "test_value1"
        mock_option1.text = "Test Option 1"
        mock_option2 = MagicMock()
        mock_option2.value = "test_value2"
        mock_option2.text = "Test Option 2"
        mock_state.get_option.side_effect = [mock_option1, Exception("Failed to load option")]
        mock_hivemind_state.return_value = mock_state

        # Test the endpoint
        response = self.client.get("/add_opinion?cid=test_state_cid")

        # Verify response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Verify get_option was called for each option in state.option_cids
        assert mock_state.get_option.call_count == 2
        mock_state.get_option.assert_any_call(cid="option1")
        mock_state.get_option.assert_any_call(cid="option2")

    @patch("app.load_state_mapping")
    @patch("app.HivemindOption")
    @patch("app.logger")
    def test_create_option_unexpected_exception(self, mock_logger, mock_hivemind_option, mock_load_state_mapping):
        """Test the create_option endpoint when an unexpected exception occurs."""
        # Setup test client
        client = TestClient(app.app)

        # Configure mocks
        valid_cid = "QmXG8yk8UJjMT6qtE2zSxzz3U7z5jSYRgQEjuFKXTVYWoL"
        mock_mapping = {valid_cid: {"state_hash": "test_state_cid"}}
        mock_load_state_mapping.return_value = mock_mapping

        # Configure HivemindOption to raise an exception
        test_exception = Exception("Test unexpected error")
        mock_hivemind_option.return_value.set_issue.side_effect = test_exception

        # Test the endpoint
        option_data = {
            "hivemind_id": valid_cid,
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)

        # Verify response - app.py returns 400 for all exceptions
        assert response.status_code == 400
        data = response.json()
        assert "Test unexpected error" in data["detail"]

        # Verify logger calls
        mock_logger.error.assert_any_call(f"Failed to create option: {test_exception}")

    @patch("app.load_state_mapping")
    @patch("app.HivemindOption")
    def test_create_option_http_exception(self, mock_hivemind_option, mock_load_state_mapping):
        """Test the create_option endpoint when an HTTPException is raised."""
        # Setup test client
        client = TestClient(app.app)

        # Configure mocks
        valid_cid = "QmXG8yk8UJjMT6qtE2zSxzz3U7z5jSYRgQEjuFKXTVYWoL"
        mock_mapping = {valid_cid: {"state_hash": "test_state_cid"}}
        mock_load_state_mapping.return_value = mock_mapping

        # Configure HivemindOption to raise an HTTPException
        http_exception = HTTPException(status_code=422, detail="Test HTTP exception")
        mock_hivemind_option.return_value.set_issue.side_effect = http_exception

        # Test the endpoint
        option_data = {
            "hivemind_id": valid_cid,
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)

        # Verify response - app.py returns 400 for all exceptions
        assert response.status_code == 400
        data = response.json()
        assert "Test HTTP exception" in data["detail"]

    @patch("app.load_state_mapping")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    @patch("app.logger")
    def test_create_and_save_exception_handling(self, mock_logger, mock_hivemind_option, 
                                             mock_hivemind_state, mock_load_state_mapping):
        """Test exception handling in the create_and_save function."""
        # Setup test client
        client = TestClient(app.app)

        # Configure state mapping mock
        valid_cid = "QmXG8yk8UJjMT6qtE2zSxzz3U7z5jSYRgQEjuFKXTVYWoL"
        mock_mapping = {valid_cid: {"state_hash": "test_state_cid"}}
        mock_load_state_mapping.return_value = mock_mapping

        # Make HivemindOption constructor work but then cause an exception later
        mock_option = MagicMock()
        mock_hivemind_option.return_value = mock_option
        
        # Make HivemindState constructor work
        mock_state = MagicMock()
        mock_hivemind_state.return_value = mock_state
        
        # Make the state.add_option method raise an exception
        test_exception = Exception("Test error in create_and_save")
        mock_state.add_option.side_effect = test_exception

        # Test the endpoint
        option_data = {
            "hivemind_id": valid_cid,
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)

        # Verify response - app.py returns 400 for all exceptions
        assert response.status_code == 400
        data = response.json()
        assert "Test error in create_and_save" in data["detail"]

        # Verify logger calls - the error message includes the status code
        mock_logger.error.assert_any_call("Failed to add option to state: Test error in create_and_save")
        mock_logger.error.assert_any_call("Failed to create option: 400: Test error in create_and_save")

    @patch("app.load_state_mapping")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    def test_create_and_save_http_exception_handling(self, mock_hivemind_option, 
                                                  mock_hivemind_state, mock_load_state_mapping):
        """Test HTTPException handling in the create_and_save function."""
        # Setup test client
        client = TestClient(app.app)

        # Configure state mapping mock
        valid_cid = "QmXG8yk8UJjMT6qtE2zSxzz3U7z5jSYRgQEjuFKXTVYWoL"
        mock_mapping = {valid_cid: {"state_hash": "test_state_cid"}}
        mock_load_state_mapping.return_value = mock_mapping

        # Make HivemindOption constructor work
        mock_option = MagicMock()
        mock_hivemind_option.return_value = mock_option
        
        # Make HivemindState constructor work
        mock_state = MagicMock()
        mock_hivemind_state.return_value = mock_state
        
        # Make the state.add_option method raise an HTTPException
        http_exception = HTTPException(status_code=422, detail="Validation error in create_and_save")
        mock_state.add_option.side_effect = http_exception

        # Test the endpoint
        option_data = {
            "hivemind_id": valid_cid,
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)

        # Verify response - app.py returns 400 for all exceptions
        assert response.status_code == 400
        data = response.json()
        assert "Validation error in create_and_save" in data["detail"]

    @patch("app.asyncio.to_thread")
    @patch("app.logger")
    def test_create_issue_exception_handling(self, mock_logger, mock_to_thread):
        """Test exception handling in the create_issue endpoint."""
        # Setup test client
        client = TestClient(app.app)

        # Configure to_thread to raise an exception
        test_exception = Exception("Test issue creation error")
        mock_to_thread.side_effect = test_exception

        # Test data for creating an issue
        issue_data = {
            "name": "Test Issue",
            "description": "Test description",
            "questions": ["Test question?"],
            "tags": ["test", "error-handling"],
            "answer_type": "ranked"
        }

        # Test the endpoint
        response = client.post("/api/create_issue", json=issue_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Test issue creation error" in data["detail"]

        # Verify logger calls
        mock_logger.error.assert_called_once_with("Failed to create issue: Test issue creation error")

    @patch("app.load_state_mapping")
    @patch("app.HivemindOption")
    @patch("app.logger")
    def test_create_option_no_state_data(self, mock_logger, mock_hivemind_option, mock_load_state_mapping):
        """Test the create_option endpoint when state_data is None for the hivemind ID."""
        # Setup test client
        client = TestClient(app.app)

        # Configure mocks
        test_hivemind_id = "QmXG8yk8UJjMT6qtE2zSxzz3U7z5jSYRgQEjuFKXTVYWoL"
        
        # Mock HivemindOption to work normally
        mock_option = MagicMock()
        mock_option.save.return_value = "test_option_cid"
        mock_hivemind_option.return_value = mock_option
        
        # Configure load_state_mapping to return a dict that has the hivemind_id but with None value
        # This will make state_data evaluate to None in the condition at line 724-726
        mock_mapping = {test_hivemind_id: None}
        mock_load_state_mapping.return_value = mock_mapping

        # Test the endpoint
        option_data = {
            "hivemind_id": test_hivemind_id,
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)

        # Verify response
        assert response.status_code == 400  # It will be 400 because of the outer exception handler
        data = response.json()
        assert "No state data found for hivemind ID" in data["detail"]

        # Verify logger calls
        mock_logger.error.assert_called_with(f"Failed to create option: 404: No state data found for hivemind ID")

    @pytest.mark.asyncio
    @patch("app.logger")
    @patch("app.HivemindState")
    async def test_load_opinions_for_question_exception(self, mock_hivemind_state, mock_logger):
        """Test exception handling in the load_opinions_for_question function."""
        # Create test data for question_opinions
        question_index = 0
        question_opinions = {
            "test_address": {
                "opinion_cid": "test_opinion_cid",
                "timestamp": "2023-01-01T12:00:00Z"
            }
        }

        # Configure state mock to raise an exception
        test_exception = Exception("Test opinion loading error")
        mock_state = mock_hivemind_state.return_value
        mock_state.get_opinion.side_effect = test_exception

        # Call the function
        result = await app.load_opinions_for_question(mock_state, question_index, question_opinions)

        # Verify the result contains the error information
        assert "test_address" in result
        assert result["test_address"]["opinion_cid"] == "test_opinion_cid"
        assert result["test_address"]["timestamp"] == "2023-01-01T12:00:00Z"
        assert result["test_address"]["ranking"] is None
        assert result["test_address"]["ranking_type"] is None
        assert "error" in result["test_address"]
        assert "Test opinion loading error" in result["test_address"]["error"]

        # Verify logger.error was called with the expected message
        mock_logger.error.assert_called_once_with(
            f"Failed to load opinion for test_address in question {question_index}: Test opinion loading error"
        )


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_error_handling.py"])
