"""Tests for File answer type functionality in the Hivemind application."""
import os
import sys
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
class TestFileAnswerType:
    """Test File answer type functionality in the Hivemind application."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.HivemindIssue")
    def test_create_issue_file_with_filetype_constraint(self, mock_hivemind_issue):
        """Test File constraint handling with filetype in create_issue function (lines 532-543).
        
        This test verifies that when a File issue type is created with a filetype constraint,
        the constraint is properly validated and set on the HivemindIssue instance.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_file_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with File answer_type and filetype constraint
        issue_data = {
            "name": "File Test Issue",
            "description": "Test Description for File Issue",
            "questions": ["Upload a file that represents your idea"],
            "tags": ["test", "file"],
            "answer_type": "File",
            "constraints": {
                "filetype": "jpg"
            },
            "restrictions": None,
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
        assert data["issue_cid"] == "test_file_issue_cid"

        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()

        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]

        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])

        # Most importantly, verify set_constraints was called with the expected file constraints
        # This specifically tests lines 532-543 where the File constraints are processed
        expected_file_constraints = {
            "filetype": "jpg"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_file_constraints)

        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_file_with_choices_constraint(self, mock_hivemind_issue):
        """Test File constraint handling with choices in create_issue function (lines 532-543).
        
        This test verifies that when a File issue type is created with a choices constraint,
        the constraint is properly validated and set on the HivemindIssue instance.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_file_choices_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with File answer_type and choices constraint
        issue_data = {
            "name": "File Choices Test Issue",
            "description": "Test Description for File with Choices",
            "questions": ["Select a file from the options"],
            "tags": ["test", "file", "choices"],
            "answer_type": "File",
            "constraints": {
                "choices": ["QmHash1", "QmHash2", "QmHash3"]
            },
            "restrictions": None,
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
        assert data["issue_cid"] == "test_file_choices_cid"

        # Verify the expected constraints were used
        expected_constraints = {
            "choices": ["QmHash1", "QmHash2", "QmHash3"]
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_constraints)

    @patch("app.HivemindIssue")
    def test_create_issue_file_with_multiple_constraints(self, mock_hivemind_issue):
        """Test File constraint handling with multiple constraints in create_issue function.
        
        This test verifies that when a File issue type is created with multiple constraints,
        all constraints are properly validated and set on the HivemindIssue instance.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_file_multiple_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with File answer_type and multiple constraints
        issue_data = {
            "name": "File Multiple Constraints Test",
            "description": "Test Description for File with Multiple Constraints",
            "questions": ["Upload or select a file"],
            "tags": ["test", "file", "multiple"],
            "answer_type": "File",
            "constraints": {
                "filetype": "pdf",
                "choices": ["QmHash1", "QmHash2"]
            },
            "restrictions": None,
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
        assert data["issue_cid"] == "test_file_multiple_cid"

        # Verify the expected constraints were used
        expected_constraints = {
            "filetype": "pdf",
            "choices": ["QmHash1", "QmHash2"]
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_constraints)


if __name__ == "__main__":
    pytest.main(["-xvs", "test_file_answer_type.py"])
