"""Tests for issue creation functionality in the FastAPI web application."""
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
class TestIssueCreationFunctionality:
    """Test create_issue functionality, specifically Boolean constraint handling."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.HivemindIssue")
    def test_create_issue_bool_constraints(self, mock_hivemind_issue):
        """Test Boolean constraint handling in create_issue function (lines 538-546).
        
        This test specifically verifies that when a Boolean issue type is created with
        custom true/false labels in the 'choices' array, the constraints are properly
        modified to use the expected format with 'true_value' and 'false_value' keys.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Bool answer_type and custom true/false labels
        issue_data = {
            "name": "Boolean Test Issue",
            "description": "Test Description for Boolean Issue",
            "questions": ["Do you agree?"],
            "tags": ["test", "boolean"],
            "answer_type": "Bool",
            "constraints": {
                "choices": ["Yes", "No"]  # Custom true/false labels
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
        assert data["issue_cid"] == "test_issue_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
        # Most importantly, verify set_constraints was called with the modified constraints
        # This specifically tests lines 538-546 where the Boolean constraints are modified
        expected_modified_constraints = {
            "true_value": "Yes",
            "false_value": "No"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_modified_constraints)
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_bool_constraints_default_labels(self, mock_hivemind_issue):
        """Test Boolean constraint handling with default labels in create_issue function.
        
        This test verifies that when a Boolean issue type is created without custom labels
        or with an empty 'choices' array, the default 'True' and 'False' labels are used.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Bool answer_type but empty choices array
        issue_data = {
            "name": "Default Boolean Test Issue",
            "description": "Test Description for Default Boolean Issue",
            "questions": ["Do you agree?"],
            "tags": ["test", "boolean", "default"],
            "answer_type": "Bool",
            "constraints": {
                "choices": []  # Empty choices array should use default labels
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
        assert data["issue_cid"] == "test_issue_cid"
        
        # Verify the default labels were used
        expected_default_constraints = {
            "true_value": "True",
            "false_value": "False"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_default_constraints)

    @patch("app.HivemindIssue")
    def test_create_issue_bool_no_constraints(self, mock_hivemind_issue):
        """Test Boolean issue creation without constraints (lines 594-596).
        
        This test verifies that when a Boolean issue type is created without any constraints,
        default 'True' and 'False' labels are automatically applied.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_bool_no_constraints_cid"
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data with Bool answer_type but NO constraints
        issue_data = {
            "name": "Bool Issue Without Constraints",
            "description": "Test Description for Bool Issue Without Constraints",
            "questions": ["Do you agree with the proposal?"],
            "tags": ["test", "boolean", "no-constraints"],
            "answer_type": "Bool",
            "constraints": None,  # No constraints provided
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
        assert data["issue_cid"] == "test_bool_no_constraints_cid"
        
        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()
        
        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
        # Most importantly, verify set_constraints was called with the default Bool constraints
        # This specifically tests lines 594-596 where default Bool constraints are applied
        expected_default_constraints = {
            "true_value": "True",
            "false_value": "False"
        }
        mock_issue_instance.set_constraints.assert_called_once_with(expected_default_constraints)
        
        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_exception_handling(self, mock_hivemind_issue):
        """Test exception handling in create_issue function (lines 645-647).
        
        This test verifies that when an exception occurs during issue creation,
        it is properly logged and re-raised to the caller.
        """
        # Setup mock issue instance to raise an exception during save
        mock_issue_instance = MagicMock()
        test_exception = ValueError("Test exception during issue save")
        mock_issue_instance.save.side_effect = test_exception
        mock_hivemind_issue.return_value = mock_issue_instance
        
        # Setup test data
        issue_data = {
            "name": "Exception Test Issue",
            "description": "Test Description for Exception Handling",
            "questions": ["Will this throw an exception?"],
            "tags": ["test", "exception"],
            "answer_type": "Text",
            "constraints": None,
            "restrictions": None,
            "on_selection": None
        }
        
        # Test the endpoint with logger patched to verify error logging
        with patch("app.HivemindState"), patch("app.logger") as mock_logger:
            # When testing through FastAPI TestClient, exceptions are converted to HTTP responses
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )
            
            # Verify the response indicates an error
            assert response.status_code == 400
            
            # Verify that the error was logged
            # The logger.error is called twice with different messages
            assert mock_logger.error.call_count == 2
            
            # Check for our specific error message (lines 645-647)
            create_and_save_error_call = False
            for call in mock_logger.error.call_args_list:
                if "Error in create_and_save:" in call[0][0] and str(test_exception) in call[0][0]:
                    create_and_save_error_call = True
                    break
            
            assert create_and_save_error_call, "Expected error log message not found"


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_issue_creation.py"])
