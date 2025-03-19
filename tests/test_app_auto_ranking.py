"""Tests for auto ranking functionality in the submit_opinion endpoint."""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module
sys.path.append(os.path.join(project_root, "hivemind"))
import app

# Import required modules from src.hivemind
sys.path.append(os.path.join(project_root, "src"))
from hivemind.state import HivemindState, HivemindOpinion
from hivemind.ranking import Ranking


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


# Create a patched version of asyncio.to_thread that returns a coroutine
async def mock_to_thread(func, *args, **kwargs):
    """Mock implementation of asyncio.to_thread that runs the function and returns its result."""
    if callable(func):
        return func(*args, **kwargs)
    return func


@pytest.mark.unit
class TestAutoRanking:
    """Test auto ranking functionality in the submit_opinion endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.HivemindState")
    @patch("app.HivemindOpinion")
    @patch("app.Ranking")
    def test_submit_opinion_auto_high(self, mock_ranking, mock_hivemind_opinion, mock_hivemind_state):
        """Test the submit_opinion endpoint with auto_high ranking type."""
        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_opinion_instance.save.return_value = "test_opinion_cid"
        mock_hivemind_opinion.return_value = mock_opinion_instance

        # Setup mock state instance
        mock_state_instance = MagicMock()
        mock_hivemind_state.return_value = mock_state_instance

        # Setup mock ranking instance
        mock_ranking_instance = MagicMock()
        mock_ranking_instance.to_dict.return_value = {"auto_high": "option1"}
        mock_ranking.return_value = mock_ranking_instance

        # Setup test data for auto_high ranking
        opinion_data = {
            "hivemind_id": "test_hivemind_id",
            "question_index": 0,
            "ranking": ["option1"],  # Auto ranking requires exactly one preferred option
            "ranking_type": "auto_high"
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

        # Verify the state was loaded with the correct hivemind_id
        mock_hivemind_state.assert_called_once()
        mock_state_instance.load.assert_called_once_with("test_hivemind_id")

        # Verify the ranking was set to auto_high with the correct option
        mock_ranking_instance.set_auto_high.assert_called_once_with("option1")
        mock_ranking_instance.to_dict.assert_called_once()

        # Verify the opinion ranking was set to the ranking dictionary
        assert mock_opinion_instance.ranking == mock_ranking_instance.to_dict()

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.HivemindState")
    @patch("app.HivemindOpinion")
    @patch("app.Ranking")
    def test_submit_opinion_auto_low(self, mock_ranking, mock_hivemind_opinion, mock_hivemind_state):
        """Test the submit_opinion endpoint with auto_low ranking type."""
        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_opinion_instance.save.return_value = "test_opinion_cid"
        mock_hivemind_opinion.return_value = mock_opinion_instance

        # Setup mock state instance
        mock_state_instance = MagicMock()
        mock_hivemind_state.return_value = mock_state_instance

        # Setup mock ranking instance
        mock_ranking_instance = MagicMock()
        mock_ranking_instance.to_dict.return_value = {"auto_low": "option1"}
        mock_ranking.return_value = mock_ranking_instance

        # Setup test data for auto_low ranking
        opinion_data = {
            "hivemind_id": "test_hivemind_id",
            "question_index": 0,
            "ranking": ["option1"],  # Auto ranking requires exactly one preferred option
            "ranking_type": "auto_low"
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

        # Verify the state was loaded with the correct hivemind_id
        mock_hivemind_state.assert_called_once()
        mock_state_instance.load.assert_called_once_with("test_hivemind_id")

        # Verify the ranking was set to auto_low with the correct option
        mock_ranking_instance.set_auto_low.assert_called_once_with("option1")
        mock_ranking_instance.to_dict.assert_called_once()

        # Verify the opinion ranking was set to the ranking dictionary
        assert mock_opinion_instance.ranking == mock_ranking_instance.to_dict()

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.HivemindState")
    @patch("app.HivemindOpinion")
    @patch("app.Ranking")
    def test_submit_opinion_auto_ranking_invalid_options(self, mock_ranking, mock_hivemind_opinion, mock_hivemind_state):
        """Test the submit_opinion endpoint with auto ranking but invalid number of options."""
        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_hivemind_opinion.return_value = mock_opinion_instance

        # Setup test data with empty ranking list
        opinion_data = {
            "hivemind_id": "test_hivemind_id",
            "question_index": 0,
            "ranking": [],  # Empty ranking list, should raise error
            "ranking_type": "auto_high"
        }

        # Test the endpoint
        response = self.client.post(
            "/api/submit_opinion",
            json=opinion_data
        )

        # Verify response indicates error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Auto ranking requires exactly one preferred option" in data["detail"]

        # Test with multiple options
        opinion_data["ranking"] = ["option1", "option2"]  # Multiple options, should raise error

        response = self.client.post(
            "/api/submit_opinion",
            json=opinion_data
        )

        # Verify response indicates error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Auto ranking requires exactly one preferred option" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.HivemindState")
    @patch("app.HivemindOpinion")
    def test_submit_opinion_invalid_ranking_type(self, mock_hivemind_opinion, mock_hivemind_state):
        """Test the submit_opinion endpoint with an invalid ranking type."""
        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_hivemind_opinion.return_value = mock_opinion_instance

        # Setup test data with invalid ranking type
        opinion_data = {
            "hivemind_id": "test_hivemind_id",
            "question_index": 0,
            "ranking": ["option1"],
            "ranking_type": "invalid_type"  # Invalid ranking type
        }

        # Test the endpoint
        response = self.client.post(
            "/api/submit_opinion",
            json=opinion_data
        )

        # Verify response indicates error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Invalid ranking type: invalid_type" in data["detail"]


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_auto_ranking.py"])
