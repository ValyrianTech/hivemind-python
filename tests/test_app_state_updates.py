"""Tests for state update functionality in the FastAPI web application."""
import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app
from app import load_state_mapping, save_state_mapping

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
class TestStateUpdateFunctionality:
    """Test state update functionality in fetch_state function."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.load_state_mapping")
    @patch("app.save_state_mapping")
    @patch("app.logger")
    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    @patch("app.HivemindOption")
    @patch("app.HivemindOpinion")
    def test_fetch_state_update_existing_state(
            self,
            mock_hivemind_opinion,
            mock_hivemind_option,
            mock_hivemind_issue,
            mock_hivemind_state,
            mock_logger,
            mock_save_state_mapping,
            mock_load_state_mapping
    ):
        """Test updating results for an existing state that is the latest we're tracking."""
        # Setup mock state instance
        mock_state_instance = MagicMock()
        mock_state_instance.hivemind_id = "test_id"
        mock_state_instance.options = ["option1", "option2"]
        mock_state_instance.opinions = [{"address1": {"opinion_cid": "opinion1", "timestamp": "2023-01-01"}}]
        mock_state_instance.final = False
        mock_state_instance.previous_cid = None
        mock_state_instance.cid.return_value = "test_state_cid"
        mock_state_instance.calculate_results.return_value = {
            "option1": {"score": 0.8},
            "option2": {"score": 0.2}
        }
        mock_state_instance.get_sorted_options.return_value = [
            MagicMock(cid=lambda: "option1", value="value1", text="Option 1"),
            MagicMock(cid=lambda: "option2", value="value2", text="Option 2")
        ]
        mock_state_instance.contributions.return_value = {"address1": 0.5}

        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.name = "Test Issue"
        mock_issue_instance.description = "Test Description"
        mock_issue_instance.tags = ["test", "mock"]
        mock_issue_instance.questions = ["Question 1?"]
        mock_issue_instance.answer_type = "ranked"
        mock_issue_instance.constraints = {}
        mock_issue_instance.restrictions = {}

        # Setup mock option instance
        mock_option_instance = MagicMock()
        mock_option_instance.value = "test_value"
        mock_option_instance.text = "Test Option"

        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_opinion_instance.ranking = ["option1", "option2"]

        # Configure the mock classes to return our mock instances
        mock_hivemind_state.return_value = mock_state_instance
        mock_hivemind_issue.return_value = mock_issue_instance
        mock_hivemind_option.return_value = mock_option_instance
        mock_hivemind_opinion.return_value = mock_opinion_instance

        # Mock the state mapping to simulate an existing state
        mock_load_state_mapping.return_value = {
            "test_id": {
                "state_hash": "test_state_cid",  # Same as the current state.cid()
                "name": "Test Issue",
                "description": "Test Description",
                "num_options": 2,
                "num_opinions": 1,
                "answer_type": "ranked",
                "questions": ["Question 1?"],
                "tags": ["test", "mock"],
                "results": [{"text": "Old Result", "value": "old_value", "score": 75.0}]
            }
        }

        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "test_state_cid"}
        )

        # Verify response
        assert response.status_code == 200

        # Verify that save_state_mapping was called with updated results
        # This confirms lines 489-492 were executed
        mock_save_state_mapping.assert_called_once()

        # Verify the log message was generated (line 492)
        mock_logger.info.assert_any_call("Updated results for latest state of test_id")

        # Verify the mapping was updated with new results
        call_args = mock_save_state_mapping.call_args[0][0]
        assert "test_id" in call_args
        assert call_args["test_id"]["results"] != [{"text": "Old Result", "value": "old_value", "score": 75.0}]

    @patch("app.load_state_mapping")
    @patch("app.save_state_mapping")
    @patch("app.logger")
    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    @patch("app.HivemindOption")
    @patch("app.HivemindOpinion")
    def test_fetch_state_skip_historical_state(
            self,
            mock_hivemind_opinion,
            mock_hivemind_option,
            mock_hivemind_issue,
            mock_hivemind_state,
            mock_logger,
            mock_save_state_mapping,
            mock_load_state_mapping
    ):
        """Test skipping state update for a historical state."""
        # Setup mock state instance
        mock_state_instance = MagicMock()
        mock_state_instance.hivemind_id = "test_id"
        mock_state_instance.options = ["option1", "option2"]
        mock_state_instance.opinions = [{"address1": {"opinion_cid": "opinion1", "timestamp": "2023-01-01"}}]
        mock_state_instance.final = False
        mock_state_instance.previous_cid = None
        mock_state_instance.cid.return_value = "historical_state_cid"  # Different from the latest state
        mock_state_instance.calculate_results.return_value = {
            "option1": {"score": 0.8},
            "option2": {"score": 0.2}
        }
        mock_state_instance.get_sorted_options.return_value = [
            MagicMock(cid=lambda: "option1", value="value1", text="Option 1"),
            MagicMock(cid=lambda: "option2", value="value2", text="Option 2")
        ]
        mock_state_instance.contributions.return_value = {"address1": 0.5}

        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.name = "Test Issue"
        mock_issue_instance.description = "Test Description"
        mock_issue_instance.tags = ["test", "mock"]
        mock_issue_instance.questions = ["Question 1?"]
        mock_issue_instance.answer_type = "ranked"
        mock_issue_instance.constraints = {}
        mock_issue_instance.restrictions = {}

        # Setup mock option instance
        mock_option_instance = MagicMock()
        mock_option_instance.value = "test_value"
        mock_option_instance.text = "Test Option"

        # Setup mock opinion instance
        mock_opinion_instance = MagicMock()
        mock_opinion_instance.ranking = ["option1", "option2"]

        # Configure the mock classes to return our mock instances
        mock_hivemind_state.return_value = mock_state_instance
        mock_hivemind_issue.return_value = mock_issue_instance
        mock_hivemind_option.return_value = mock_option_instance
        mock_hivemind_opinion.return_value = mock_opinion_instance

        # Mock the state mapping to simulate an existing state with a different hash
        mock_load_state_mapping.return_value = {
            "test_id": {
                "state_hash": "latest_state_cid",  # Different from the current state.cid()
                "name": "Test Issue",
                "description": "Test Description",
                "num_options": 2,
                "num_opinions": 1,
                "answer_type": "ranked",
                "questions": ["Question 1?"],
                "tags": ["test", "mock"],
                "results": [{"text": "Latest Result", "value": "latest_value", "score": 75.0}]
            }
        }

        # Test the endpoint
        response = self.client.post(
            "/fetch_state",
            json={"cid": "historical_state_cid"}
        )

        # Verify response
        assert response.status_code == 200

        # Verify that save_state_mapping was NOT called
        mock_save_state_mapping.assert_not_called()

        # Verify the log message was generated (line 494)
        mock_logger.info.assert_any_call(f"Skipping state update for historical state historical_state_cid of test_id")

        # Verify the mapping was not updated
        assert mock_load_state_mapping.return_value["test_id"]["results"] == [{"text": "Latest Result", "value": "latest_value", "score": 75.0}]


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_state_updates.py"])
