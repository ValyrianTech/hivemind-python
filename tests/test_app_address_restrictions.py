"""Tests for address restrictions handling in the FastAPI web application."""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app

# Import necessary classes from src.hivemind
sys.path.append(os.path.join(project_root, "src"))
from hivemind.option import HivemindOption
from hivemind.issue import HivemindIssue
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
class TestAddressRestrictions:
    """Test address restrictions handling in the FastAPI endpoints."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.load_state_mapping")
    @patch("app.asyncio.to_thread")
    @patch("app.HivemindState")
    @patch("app.HivemindOption")
    @patch("app.logger")
    def test_create_option_with_address_restrictions(self, mock_logger, mock_hivemind_option, 
                                                   mock_hivemind_state, mock_to_thread, 
                                                   mock_load_state_mapping):
        """Test the create_option endpoint with address restrictions."""
        # Configure the mock to return a mapping with the requested hivemind_id
        mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_hash",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }

        # Setup mock option
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_hivemind_option.return_value = mock_option

        # Setup mock issue with address restrictions
        mock_issue = MagicMock()
        mock_issue.restrictions = {
            "addresses": ["test_address1", "test_address2"]
        }
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args, **kwargs):
            if "hivemind_issue" in str(func):
                return mock_issue
            return func(*args, **kwargs)

        mock_to_thread.side_effect = mock_to_thread_return

        # Create test data
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "test_value",
            "text": "Test option text"
        }

        # Test the endpoint
        response = self.client.post("/api/options/create", json=option_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["option_cid"] == "test_option_cid"
        assert data["state_cid"] == "test_state_hash"
        assert data["needsSignature"] is True

        # Verify logger calls for address restrictions
        mock_logger.info.assert_any_call(f"Hivemind has address restrictions: {mock_issue.restrictions['addresses']}")


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_address_restrictions.py"])
