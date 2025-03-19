"""Tests for the FastAPI web application API endpoints."""
import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

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
class TestAPIEndpoints:
    """Test FastAPI API endpoints."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.HivemindState")
    @patch("app.HivemindOpinion")
    def test_submit_opinion_success(self, mock_hivemind_opinion, mock_hivemind_state):
        """Test the submit_opinion endpoint with successful submission."""
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

    @patch("app.HivemindState")
    @patch("app.HivemindOpinion")
    @patch("app.logger")
    def test_submit_opinion_exception(self, mock_logger, mock_hivemind_opinion, mock_hivemind_state):
        """Test the submit_opinion endpoint when an exception occurs."""
        # Setup mock opinion instance to raise an exception
        mock_hivemind_opinion.side_effect = Exception("Test error message")

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
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error submitting opinion: Test error message" in data["detail"]

        # Verify logger was called with the expected error message
        mock_logger.error.assert_called_once_with("Error submitting opinion: Test error message")

    @patch("app.load_state_mapping")
    def test_get_latest_state_endpoint_success(self, mock_load_state_mapping):
        """Test the /api/latest_state/{hivemind_id} endpoint with an existing hivemind ID."""
        # Setup mock state mapping
        mock_load_state_mapping.return_value = {
            "test_hivemind_id": {
                "state_hash": "test_hash",
                "name": "Test Hivemind",
                "description": "Test description"
            }
        }

        # Test the endpoint
        response = self.client.get("/api/latest_state/test_hivemind_id")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["hivemind_id"] == "test_hivemind_id"
        assert data["state_hash"] == "test_hash"
        assert data["name"] == "Test Hivemind"
        assert data["description"] == "Test description"

    @patch("app.load_state_mapping")
    def test_get_latest_state_endpoint_not_found(self, mock_load_state_mapping):
        """Test the /api/latest_state/{hivemind_id} endpoint with a non-existent hivemind ID."""
        # Setup mock state mapping
        mock_load_state_mapping.return_value = {
            "existing_id": {"state_hash": "some_hash", "name": "Some Name"}
        }

        # Test the endpoint with non-existent ID
        response = self.client.get("/api/latest_state/non_existent_id")

        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Hivemind ID not found" in data["detail"]


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_api.py"])
