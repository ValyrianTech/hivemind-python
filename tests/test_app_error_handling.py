"""Tests for error handling in the FastAPI web application."""
import os
import sys
import pytest
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
    @patch("app.HivemindOption")
    @patch("app.asyncio.to_thread")
    def test_add_opinion_page_option_loading(self, mock_to_thread, mock_hivemind_option, mock_hivemind_issue, mock_hivemind_state):
        """Test the option loading functionality in the add_opinion_page endpoint."""
        # Setup mock issue instance
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.questions = ["Question 1?"]
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock state instance
        mock_state = MagicMock()
        mock_state.hivemind_id = "test_hivemind_id"
        mock_state.options = ["option1", "option2"]
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock option instance
        mock_option = MagicMock()
        mock_option.value = "test_value"
        mock_option.text = "Test Option"
        mock_hivemind_option.return_value = mock_option
        
        # Configure to_thread to return the mocked objects
        mock_to_thread.side_effect = lambda f, *args, **kwargs: f(*args, **kwargs)
        
        # Test the endpoint
        response = self.client.get("/add_opinion?cid=test_state_cid")
        
        # Verify response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Verify HivemindOption was called for each option in state.options
        assert mock_hivemind_option.call_count == 2
        mock_hivemind_option.assert_any_call(cid="option1")
        mock_hivemind_option.assert_any_call(cid="option2")

    @patch("app.load_state_mapping")
    @patch("app.asyncio.to_thread")
    @patch("app.logger")
    def test_create_option_unexpected_exception(self, mock_logger, mock_to_thread, mock_load_state_mapping):
        """Test the create_option endpoint when an unexpected exception occurs (lines 809-814)."""
        # Setup test client
        client = TestClient(app.app)
        
        # Configure mocks
        mock_mapping = {"test_hivemind_id": {"state_hash": "test_state_cid"}}
        mock_load_state_mapping.return_value = mock_mapping
        
        # Configure to_thread to raise an exception
        test_exception = Exception("Test unexpected error")
        mock_to_thread.side_effect = test_exception
        
        # Test the endpoint
        option_data = {
            "hivemind_id": "test_hivemind_id",
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)
        
        # Verify response
        assert response.status_code == 500
        data = response.json()
        assert "Internal error: Test unexpected error" in data["detail"]
        
        # Verify logger calls
        mock_logger.error.assert_any_call("Unexpected error in create_option: Test unexpected error")
        mock_logger.exception.assert_called_once_with("Full traceback:")

    @patch("app.load_state_mapping")
    @patch("app.asyncio.to_thread")
    def test_create_option_http_exception(self, mock_to_thread, mock_load_state_mapping):
        """Test the create_option endpoint when an HTTPException is raised (line 810)."""
        # Setup test client
        client = TestClient(app.app)
        
        # Configure mocks
        mock_mapping = {"test_hivemind_id": {"state_hash": "test_state_cid"}}
        mock_load_state_mapping.return_value = mock_mapping
        
        # Configure to_thread to raise an HTTPException
        http_exception = HTTPException(status_code=422, detail="Test HTTP exception")
        mock_to_thread.side_effect = http_exception
        
        # Test the endpoint
        option_data = {
            "hivemind_id": "test_hivemind_id",
            "value": "test_value",
            "text": "Test option text"
        }
        response = client.post("/api/options/create", json=option_data)
        
        # Verify response
        assert response.status_code == 422
        data = response.json()
        assert "Test HTTP exception" in data["detail"]

if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_error_handling.py"])
