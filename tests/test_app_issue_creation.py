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
    def test_create_issue_with_author(self, mock_hivemind_issue):
        """Test author setting in create_issue function (lines 573-574).
        
        This test verifies that when both author and on_selection are provided,
        the author attribute is properly set on the HivemindIssue.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_with_author_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with both author and on_selection
        issue_data = {
            "name": "Issue With Author",
            "description": "Test Description for Issue With Author",
            "questions": ["What is your opinion?"],
            "tags": ["test", "author"],
            "answer_type": "Text",
            "constraints": None,
            "restrictions": None,
            "on_selection": "some_selection_action",
            "author": "test_author_address"
        }

        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state, patch("app.logger") as mock_logger:
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
        assert data["issue_cid"] == "test_issue_with_author_cid"

        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()

        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]
        assert mock_issue_instance.on_selection == issue_data["on_selection"]
        
        # Most importantly, verify author was set correctly (line 573)
        assert mock_issue_instance.author == issue_data["author"]
        
        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])
        
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

    @patch("app.HivemindIssue")
    def test_create_issue_with_string_choices(self, mock_hivemind_issue):
        """Test choices formatting for non-Bool answer types (lines 648-652).
        
        This test verifies that when a non-Bool issue type is created with simple string choices,
        the choices are properly formatted to include both 'text' and 'value' keys before
        calling add_predefined_options.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_with_choices_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with String answer_type and simple string choices
        issue_data = {
            "name": "String Issue With Choices",
            "description": "Test Description for String Issue With Choices",
            "questions": ["Select an option:"],
            "tags": ["test", "string", "choices"],
            "answer_type": "String",
            "constraints": {
                "choices": ["Option A", "Option B", "Option C"]  # Simple string choices
            },
            "restrictions": None,
            "on_selection": None
        }

        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state, patch("app.logger") as mock_logger:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_state_instance._issue = MagicMock()
            mock_state_instance._issue.constraints = {'choices': issue_data["constraints"]["choices"]}
            mock_state_instance.add_predefined_options.return_value = {
                "option1_cid": {"text": "Option A", "value": "Option A"},
                "option2_cid": {"text": "Option B", "value": "Option B"},
                "option3_cid": {"text": "Option C", "value": "Option C"}
            }
            mock_hivemind_state.return_value = mock_state_instance

            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_issue_with_choices_cid"

        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()

        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]

        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])

        # Verify set_constraints was called with the original constraints
        mock_issue_instance.set_constraints.assert_called_once_with(issue_data["constraints"])

        # Verify add_predefined_options was called
        mock_state_instance.add_predefined_options.assert_called_once()

        # Verify that the constraints were formatted correctly before calling add_predefined_options
        # This specifically tests lines 648-652 where choices are formatted
        # The formatted choices should have been logged
        format_log_call = False
        for call in mock_logger.info.call_args_list:
            if "Formatted choices:" in call[0][0] and "text" in call[0][0] and "value" in call[0][0]:
                format_log_call = True
                break

        assert format_log_call, "Expected log message for formatted choices not found"

        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_with_mixed_choices(self, mock_hivemind_issue):
        """Test choices formatting for mixed format choices (lines 648-652).
        
        This test verifies that when a non-Bool issue type is created with a mix of
        simple values and incomplete dictionaries as choices, they are all properly
        formatted to include both 'text' and 'value' keys.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_issue_with_mixed_choices_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with Integer answer_type and mixed format choices
        issue_data = {
            "name": "Integer Issue With Mixed Choices",
            "description": "Test Description for Integer Issue With Mixed Choices",
            "questions": ["Select a number:"],
            "tags": ["test", "integer", "choices", "mixed"],
            "answer_type": "Integer",
            "constraints": {
                "choices": [
                    10,  # Simple value
                    {"value": 20},  # Dict with only value
                    {"text": "Thirty"}  # Dict with only text
                ]
            },
            "restrictions": None,
            "on_selection": None
        }

        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state, patch("app.logger") as mock_logger:
            # Configure mock state to return a successful save
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            mock_state_instance._issue = MagicMock()
            mock_state_instance._issue.constraints = {'choices': issue_data["constraints"]["choices"]}
            mock_state_instance.add_predefined_options.return_value = {
                "option1_cid": {"text": "10", "value": 10},
                "option2_cid": {"text": "20", "value": 20},
                "option3_cid": {"text": "Thirty", "value": "Thirty"}
            }
            mock_hivemind_state.return_value = mock_state_instance

            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_issue_with_mixed_choices_cid"

        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()

        # Verify add_predefined_options was called
        mock_state_instance.add_predefined_options.assert_called_once()

        # Verify that the constraints were formatted correctly
        # The formatted choices should have been logged
        format_log_call = False
        for call in mock_logger.info.call_args_list:
            if "Formatted choices:" in call[0][0]:
                log_message = call[0][0]
                # Check that all choices have both text and value keys
                assert "'text': '10'" in log_message and "'value': 10" in log_message
                assert "'text': '20'" in log_message and "'value': 20" in log_message
                assert "'text': 'Thirty'" in log_message and "'value': 'Thirty'" in log_message
                format_log_call = True
                break

        assert format_log_call, "Expected log message for formatted choices not found"

        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_complex_constraints(self, mock_hivemind_issue):
        """Test Complex answer type constraint handling in create_issue function.
        
        This test verifies that when a Complex issue type is created with choices
        that are string representations of JSON objects, they are properly parsed
        into actual dictionaries using ast.literal_eval.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_complex_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with Complex answer_type and string JSON choices
        issue_data = {
            "name": "Complex Test Issue",
            "description": "Test Description for Complex Issue",
            "questions": ["Which option do you prefer?"],
            "tags": ["test", "complex"],
            "answer_type": "Complex",
            "constraints": {
                "specs": {
                    "field1": "String",
                    "field2": "Integer"
                },
                "choices": [
                    '{"field1": "value1", "field2": 123}',
                    '{"field1": "value2", "field2": 456}'
                ]
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
        assert data["issue_cid"] == "test_complex_issue_cid"

        # Verify the HivemindIssue was created with correct attributes
        mock_hivemind_issue.assert_called_once()

        # Verify attributes were set correctly
        assert mock_issue_instance.name == issue_data["name"]
        assert mock_issue_instance.description == issue_data["description"]
        assert mock_issue_instance.tags == issue_data["tags"]
        assert mock_issue_instance.answer_type == issue_data["answer_type"]

        # Verify add_question was called for the question
        mock_issue_instance.add_question.assert_called_once_with(issue_data["questions"][0])

        # Most importantly, verify set_constraints was called with the parsed constraints
        # The string JSON objects should be converted to actual dictionaries
        expected_modified_constraints = {
            "specs": {
                "field1": "String",
                "field2": "Integer"
            },
            "choices": [
                {"field1": "value1", "field2": 123},
                {"field1": "value2", "field2": 456}
            ]
        }
        mock_issue_instance.set_constraints.assert_called_once()
        # Get the actual call arguments
        actual_constraints = mock_issue_instance.set_constraints.call_args[0][0]
        assert actual_constraints["specs"] == expected_modified_constraints["specs"]
        # Verify each choice was properly parsed from string to dict
        for i, choice in enumerate(actual_constraints["choices"]):
            assert isinstance(choice, dict)
            assert choice["field1"] == expected_modified_constraints["choices"][i]["field1"]
            assert choice["field2"] == expected_modified_constraints["choices"][i]["field2"]

        # Verify save was called
        mock_issue_instance.save.assert_called_once()

    @patch("app.HivemindIssue")
    def test_create_issue_complex_constraints_after_formatting(self, mock_hivemind_issue):
        """Test Complex answer type constraint handling after formatting in create_issue function.
        
        This test verifies that when a Complex issue type is created with choices,
        the formatted choices (with 'text' and 'value' keys) are properly handled,
        ensuring the 'value' field is a dictionary, not a string representation.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_complex_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with Complex answer_type
        issue_data = {
            "name": "Complex Formatting Test",
            "description": "Test Description for Complex Formatting",
            "questions": ["Which option do you prefer?"],
            "tags": ["test", "complex", "formatting"],
            "answer_type": "Complex",
            "constraints": {
                "specs": {
                    "field1": "String",
                    "field2": "Integer"
                },
                "choices": [
                    {"field1": "value1", "field2": 123},
                    {"field1": "value2", "field2": 456}
                ]
            },
            "restrictions": None,
            "on_selection": None
        }

        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state instance
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            
            # Mock the _issue attribute and its constraints
            mock_state_instance._issue = MagicMock()
            mock_state_instance._issue.constraints = {
                "specs": {
                    "field1": "String",
                    "field2": "Integer"
                },
                "choices": [
                    {"text": "{'field1': 'value1', 'field2': 123}", "value": "{'field1': 'value1', 'field2': 123}"},
                    {"text": "{'field1': 'value2', 'field2': 456}", "value": "{'field1': 'value2', 'field2': 456}"}
                ]
            }
            
            # Mock add_predefined_options to return some options
            mock_state_instance.add_predefined_options.return_value = ["option1", "option2"]
            
            mock_hivemind_state.return_value = mock_state_instance

            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["issue_cid"] == "test_complex_issue_cid"

        # Verify add_predefined_options was called
        mock_state_instance.add_predefined_options.assert_called_once()
        
        # Verify that the choices in the state's issue constraints were properly processed
        # The 'value' field should have been converted from string to dict
        choices = mock_state_instance._issue.constraints["choices"]
        for choice in choices:
            # After our code runs, the 'value' should be a dict, not a string
            assert isinstance(choice["value"], dict)
            # Verify the dict has the expected structure
            assert "field1" in choice["value"]
            assert "field2" in choice["value"]

    @patch("app.HivemindIssue")
    def test_create_issue_complex_constraints_after_formatting_invalid_json(self, mock_hivemind_issue):
        """Test Complex answer type constraint handling after formatting with invalid JSON.
        
        This test verifies that when a Complex issue type is created and the formatted choices
        contain invalid JSON strings in the 'value' field, the appropriate error is raised and logged.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_complex_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with Complex answer_type
        issue_data = {
            "name": "Complex Formatting Invalid JSON Test",
            "description": "Test Description for Complex Formatting with Invalid JSON",
            "questions": ["Which option do you prefer?"],
            "tags": ["test", "complex", "formatting", "invalid"],
            "answer_type": "Complex",
            "constraints": {
                "specs": {
                    "field1": "String",
                    "field2": "Integer"
                },
                "choices": [
                    {"field1": "value1", "field2": 123},
                    {"field1": "value2", "field2": 456}
                ]
            },
            "restrictions": None,
            "on_selection": None
        }

        # Test the endpoint
        with patch("app.HivemindState") as mock_hivemind_state:
            # Configure mock state instance
            mock_state_instance = MagicMock()
            mock_state_instance.save.return_value = "test_state_cid"
            
            # Mock the _issue attribute and its constraints with invalid JSON in value
            mock_state_instance._issue = MagicMock()
            mock_state_instance._issue.constraints = {
                "specs": {
                    "field1": "String",
                    "field2": "Integer"
                },
                "choices": [
                    {"text": "{'field1': 'value1', 'field2': 123}", "value": "{'field1': 'value1', 'field2': 123}"},
                    {"text": "Invalid JSON", "value": "{'field1': 'value2', field2: 456}"}  # Missing quotes around field2
                ]
            }
            
            # Mock add_predefined_options to return some options
            mock_state_instance.add_predefined_options.return_value = ["option1", "option2"]
            
            # This will cause the ast.literal_eval to fail
            mock_hivemind_state.return_value = mock_state_instance

            # We need to patch ast.literal_eval to raise an exception for the second value
            with patch("ast.literal_eval") as mock_literal_eval:
                # Make the first call succeed and the second call fail
                mock_literal_eval.side_effect = [
                    {"field1": "value1", "field2": 123},  # First call succeeds
                    SyntaxError("invalid syntax")         # Second call fails
                ]
                
                # The request should fail with a 400 Bad Request
                response = self.client.post(
                    "/api/create_issue",
                    json=issue_data
                )

        # Verify response indicates failure
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid JSON in Complex choice" in data["detail"]

    @patch("app.HivemindIssue")
    def test_create_issue_complex_constraints_invalid_json(self, mock_hivemind_issue):
        """Test Complex answer type constraint handling with invalid JSON.
        
        This test verifies that when a Complex issue type is created with choices
        that contain invalid JSON strings, the appropriate error is raised and logged.
        """
        # Setup mock issue instance
        mock_issue_instance = MagicMock()
        mock_issue_instance.save.return_value = "test_complex_issue_cid"
        mock_hivemind_issue.return_value = mock_issue_instance

        # Setup test data with Complex answer_type and invalid JSON choices
        issue_data = {
            "name": "Complex Invalid JSON Test",
            "description": "Test Description for Complex Issue with Invalid JSON",
            "questions": ["Which option do you prefer?"],
            "tags": ["test", "complex", "invalid"],
            "answer_type": "Complex",
            "constraints": {
                "specs": {
                    "field1": "String",
                    "field2": "Integer"
                },
                "choices": [
                    '{"field1": "value1", "field2": 123',  # Missing closing brace
                    '{"field1": "value2", field2: 456}'    # Missing quotes around field2
                ]
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

            # The request should fail with a 400 Bad Request
            response = self.client.post(
                "/api/create_issue",
                json=issue_data
            )

        # Verify response indicates failure
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid JSON in Complex choice" in data["detail"]


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_issue_creation.py"])
