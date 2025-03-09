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

if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_error_handling.py"])
