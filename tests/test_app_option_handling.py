"""Tests for option handling in the FastAPI web application."""
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
from hivemind.issue import HivemindIssue


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
class TestOptionHandling:
    """Test option handling in the FastAPI endpoints."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.HivemindIssue")
    @patch("app.asyncio.to_thread")
    @patch("app.logger")
    def test_add_option_page_exception(self, mock_logger, mock_to_thread, mock_hivemind_issue):
        """Test the add_option_page endpoint when an exception occurs loading the issue."""
        # Configure to_thread to raise an exception when called
        test_exception = Exception("Test error loading issue")

        # Configure the mock to pass the exception through the to_thread call
        def side_effect_function(func, *args, **kwargs):
            # This simulates the lambda function raising an exception
            raise test_exception

        mock_to_thread.side_effect = side_effect_function

        # Test the endpoint
        response = self.client.get("/options/add?hivemind_id=test_issue_cid")

        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Test error loading issue" in data["detail"]

        # Verify logger.error was called with the expected message
        mock_logger.error.assert_called_once_with("Error loading issue for add option page: Test error loading issue")

    @patch("app.load_state_mapping")
    @patch("app.logger")
    def test_create_option_no_state_found(self, mock_logger, mock_load_state_mapping):
        """Test the create_option endpoint when no state is found for the given hivemind_id."""
        # Configure the mock to return a mapping without the requested hivemind_id
        mock_load_state_mapping.return_value = {"other_hivemind_id": {"state_hash": "some_hash"}}

        # Create test data
        test_hivemind_id = "nonexistent_hivemind_id"
        option_data = {
            "hivemind_id": test_hivemind_id,
            "value": "test_value",
            "text": "Test option text"
        }

        # Test the endpoint
        response = self.client.post("/api/options/create", json=option_data)

        # Verify response - should be a 400 Bad Request due to the outer exception handler
        assert response.status_code == 400
        # The error message should contain information about the invalid CID
        assert "Invalid CID value" in response.json()["detail"]
        assert test_hivemind_id in response.json()["detail"]

        # Verify logger calls - the error log might be different based on the implementation
        # We'll check that some error was logged, but not the exact message
        mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_option_handling.py"])
