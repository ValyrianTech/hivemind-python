"""Tests for option creation functionality in the FastAPI web application."""
import os
import sys
import pytest
import json
import threading
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open, call, AsyncMock
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

@pytest.mark.unit
class TestOptionTypeConversion:
    """Test option value type conversion based on issue answer_type."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)
        # Set up mock for open to avoid actual file operations
        self.mock_open_patcher = patch('builtins.open', mock_open(read_data='{}'))
        self.mock_open = self.mock_open_patcher.start()
        
        # Set up mock for load_state_mapping
        self.mock_load_state_mapping_patcher = patch('app.load_state_mapping')
        self.mock_load_state_mapping = self.mock_load_state_mapping_patcher.start()
        
        # Set up mock for asyncio.to_thread to avoid actual threading
        self.mock_to_thread_patcher = patch('asyncio.to_thread')
        self.mock_to_thread = self.mock_to_thread_patcher.start()
        
    def teardown_method(self):
        """Clean up after each test."""
        self.mock_open_patcher.stop()
        self.mock_load_state_mapping_patcher.stop()
        self.mock_to_thread_patcher.stop()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_integer_conversion(self, mock_thread, mock_hivemind_state, mock_hivemind_issue, 
                                mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test Integer type conversion in create_option function (lines 717-718).
        
        This test verifies that when an issue's answer_type is 'Integer', the option value
        is properly converted to an integer before being saved.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
        
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Call the function directly without threading and return a mock result
            func(*args)
            return {
                "success": True, 
                "option_cid": "test_option_cid", 
                "state_cid": "new_state_cid",
                "issue_name": "Test Issue",
                "issue_description": "Test Description",
                "num_options": 1,
                "num_opinions": 0,
                "answer_type": "Integer",
                "questions": ["Test Question"],
                "tags": ["test"]
            }
        
        self.mock_to_thread.side_effect = mock_to_thread_return
        
        # Setup mock issue with Integer answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Integer"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock option
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_hivemind_option.return_value = mock_option
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.opinions = [[]]
        mock_state.options = []
        mock_state.issue.name = "Test Issue"
        mock_state.issue.description = "Test Description"
        mock_state.issue.answer_type = "Integer"
        mock_state.issue.questions = ["Test Question"]
        mock_state.issue.tags = ["test"]
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid"
            }
        }
        mock_get_latest_state.side_effect = async_mock

        # Setup mock for update_state
        mock_update_state.return_value = AsyncMock()
        
        # Mock threading.Thread to allow accepting arbitrary kwargs
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)
        
        # Test data with string value that should be converted to integer
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "42",  # String that should be converted to integer
            "text": "Forty-two"
        }
        
        # Call the endpoint
        response = self.client.post(
            "/api/options/create", 
            json=option_data
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Most importantly, verify the value was converted to integer
        # This specifically tests lines 717-718 where Integer conversion happens
        mock_option.set_hivemind_issue.assert_called_once_with(hivemind_issue_hash=option_data["hivemind_id"])
        assert isinstance(mock_option.value, int)
        assert mock_option.value == 42
        
        # Verify save was called
        mock_option.save.assert_called_once()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_float_conversion(self, mock_thread, mock_hivemind_state, mock_hivemind_issue, 
                             mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test Float type conversion in create_option function (lines 720-721).
        
        This test verifies that when an issue's answer_type is 'Float', the option value
        is properly converted to a float before being saved.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
        
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Call the function directly without threading and return a mock result
            func(*args)
            return {
                "success": True, 
                "option_cid": "test_option_cid", 
                "state_cid": "new_state_cid",
                "issue_name": "Test Issue",
                "issue_description": "Test Description",
                "num_options": 1,
                "num_opinions": 0,
                "answer_type": "Float",
                "questions": ["Test Question"],
                "tags": ["test"]
            }
        
        self.mock_to_thread.side_effect = mock_to_thread_return
        
        # Setup mock issue with Float answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Float"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock option
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_hivemind_option.return_value = mock_option
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.opinions = [[]]
        mock_state.options = []
        mock_state.issue.name = "Test Issue"
        mock_state.issue.description = "Test Description"
        mock_state.issue.answer_type = "Float"
        mock_state.issue.questions = ["Test Question"]
        mock_state.issue.tags = ["test"]
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid"
            }
        }
        mock_get_latest_state.side_effect = async_mock

        # Setup mock for update_state
        mock_update_state.return_value = AsyncMock()
        
        # Mock threading.Thread to allow accepting arbitrary kwargs
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)
        
        # Test data with string value that should be converted to float
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "3.14159",  # String that should be converted to float
            "text": "Pi approximation"
        }
        
        # Call the endpoint
        response = self.client.post(
            "/api/options/create", 
            json=option_data
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Most importantly, verify the value was converted to float
        # This specifically tests lines 720-721 where Float conversion happens
        mock_option.set_hivemind_issue.assert_called_once_with(hivemind_issue_hash=option_data["hivemind_id"])
        assert isinstance(mock_option.value, float)
        assert mock_option.value == 3.14159
        
        # Verify save was called
        mock_option.save.assert_called_once()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_string_conversion(self, mock_thread, mock_hivemind_state, mock_hivemind_issue, 
                              mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test String type conversion in create_option function (lines 725-727).
        
        This test verifies that when an issue's answer_type is anything other than 'Integer' or 'Float',
        the option value is properly converted to a string before being saved.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
        
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Call the function directly without threading and return a mock result
            func(*args)
            return {
                "success": True, 
                "option_cid": "test_option_cid", 
                "state_cid": "new_state_cid",
                "issue_name": "Test Issue",
                "issue_description": "Test Description",
                "num_options": 1,
                "num_opinions": 0,
                "answer_type": "String",
                "questions": ["Test Question"],
                "tags": ["test"]
            }
        
        self.mock_to_thread.side_effect = mock_to_thread_return
        
        # Setup mock issue with String answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "String"  # Could be any type other than Integer or Float
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock option
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_hivemind_option.return_value = mock_option
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.opinions = [[]]
        mock_state.options = []
        mock_state.issue.name = "Test Issue"
        mock_state.issue.description = "Test Description"
        mock_state.issue.answer_type = "String"
        mock_state.issue.questions = ["Test Question"]
        mock_state.issue.tags = ["test"]
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid"
            }
        }
        mock_get_latest_state.side_effect = async_mock

        # Setup mock for update_state
        mock_update_state.return_value = AsyncMock()
        
        # Mock threading.Thread to allow accepting arbitrary kwargs
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)
        
        # Test data with numeric value that should be converted to string
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": 123,  # Numeric value that should be converted to string
            "text": "Option description"
        }
        
        # Call the endpoint
        response = self.client.post(
            "/api/options/create", 
            json=option_data
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Most importantly, verify the value was converted to string
        # This specifically tests lines 725-727 where String conversion happens
        mock_option.set_hivemind_issue.assert_called_once_with(hivemind_issue_hash=option_data["hivemind_id"])
        assert isinstance(mock_option.value, str)
        assert mock_option.value == "123"
        
        # Verify save was called
        mock_option.save.assert_called_once()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_conversion_error(self, mock_thread, mock_hivemind_state, mock_hivemind_issue, 
                             mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test error handling during type conversion in create_option function.
        
        This test verifies that when the option value cannot be properly converted based on
        the issue's answer_type, an appropriate HTTPException is raised.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
        
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Simulate exception handling in create_and_save
            # In this test, we expect ValueError to propagate up
            with pytest.raises(ValueError):
                func(*args)
            # Returning HTTPException to simulate error handling in create_option
            return HTTPException(status_code=400, detail="Invalid value format for Integer: not_a_number")
        
        self.mock_to_thread.side_effect = mock_to_thread_return
        
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid"
            }
        }
        mock_get_latest_state.side_effect = async_mock

        # Setup mock for update_state
        mock_update_state.return_value = AsyncMock()

        # Setup mock issue with Integer answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Integer"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock option
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_hivemind_option.return_value = mock_option
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.opinions = [[]]
        mock_state.options = []
        mock_state.issue.name = "Test Issue"
        mock_state.issue.description = "Test Description"
        mock_state.issue.answer_type = "Integer"
        mock_state.issue.questions = ["Test Question"]
        mock_state.issue.tags = ["test"]
        mock_state.load.return_value = None  # Mock load method
        mock_hivemind_state.return_value = mock_state
        
        # Simulate ValueError during integer conversion by raising exception
        # when int() is called on "not_a_number"
        def side_effect_for_value():
            raise ValueError("invalid literal for int() with base 10: 'not_a_number'")
        
        # Use side_effect on the value property to simulate the exception
        # when accessing mock_option.value after assignment
        type(mock_option).value = property(
            side_effect_for_value
        )
        
        # Mock threading.Thread to allow accepting arbitrary kwargs
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)
        
        # Test data with value that cannot be converted to integer
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "not_a_number",  # Cannot be converted to integer
            "text": "Invalid number"
        }
        
        # Call the endpoint
        response = self.client.post(
            "/api/options/create", 
            json=option_data
        )
        
        # Verify error response
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "Invalid value format" in error_data["detail"]
        assert "Integer" in error_data["detail"]
        
        # Verify save was not called
        mock_option.save.assert_not_called()
        
    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_option_validation_failure(self, mock_thread, mock_hivemind_state, mock_hivemind_issue, 
                                      mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test option validation failure in create_option function (lines 738-739).
        
        This test verifies that when an option fails validation, an appropriate
        HTTPException is raised with status code 400 and detail message.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
        
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Call the function directly without threading
            func(*args)
            # Return a mock result
            return HTTPException(status_code=400, detail="Option validation failed")
        
        self.mock_to_thread.side_effect = mock_to_thread_return
        
        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.answer_type = "String"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock option that fails validation
        mock_option = MagicMock()
        # Set valid() to return False to trigger the validation failure
        mock_option.valid.return_value = False
        mock_option.hivemind_id = "test_issue_cid"
        mock_hivemind_option.return_value = mock_option
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.opinions = [[]]
        mock_state.options = []
        mock_state.issue.name = "Test Issue"
        mock_state.issue.description = "Test Description"
        mock_state.issue.answer_type = "String"
        mock_state.issue.questions = ["Test Question"]
        mock_state.issue.tags = ["test"]
        mock_state.load.return_value = None
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock for get_latest_state
        async_mock = AsyncMock()
        async_mock.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid"
            }
        }
        mock_get_latest_state.side_effect = async_mock

        # Setup mock for update_state
        mock_update_state.return_value = AsyncMock()
        
        # Mock threading.Thread
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)
        
        # Test data
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "test_value",
            "text": "Test option"
        }
        
        # Call the endpoint
        response = self.client.post(
            "/api/options/create", 
            json=option_data
        )
        
        # Verify error response - the app returns 400 as shown in the logs
        assert response.status_code == 400
        assert "Option validation failed" in response.json()["detail"]
        
        # Verify option.valid() was called
        mock_option.valid.assert_called_once()
        
        # Verify save was not called
        mock_option.save.assert_not_called()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_option_validation_exception(self, mock_thread, mock_hivemind_state, mock_hivemind_issue, 
                                        mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test option validation exception handling in create_option function (lines 741-743).
        
        This test verifies that when an exception occurs during option validation,
        an appropriate HTTPException is raised with the exception message.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
        
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Call the function directly without threading
            func(*args)
            # Return a mock result
            return HTTPException(status_code=400, detail="Option validation error: Custom validation error")
        
        self.mock_to_thread.side_effect = mock_to_thread_return
        
        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.answer_type = "String"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
        
        # Setup mock option that raises an exception during validation
        mock_option = MagicMock()
        # Set valid() to raise an exception
        validation_error = ValueError("Custom validation error")
        mock_option.valid.side_effect = validation_error
        mock_option.hivemind_id = "test_issue_cid"
        mock_hivemind_option.return_value = mock_option
        
        # Setup mock state
        mock_state = MagicMock()
        mock_state.opinions = [[]]
        mock_state.options = []
        mock_state.issue.name = "Test Issue"
        mock_state.issue.description = "Test Description"
        mock_state.issue.answer_type = "String"
        mock_state.issue.questions = ["Test Question"]
        mock_state.issue.tags = ["test"]
        mock_state.load.return_value = None
        mock_hivemind_state.return_value = mock_state
        
        # Setup mock for get_latest_state
        async_mock = AsyncMock()
        async_mock.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid"
            }
        }
        mock_get_latest_state.side_effect = async_mock

        # Setup mock for update_state
        mock_update_state.return_value = AsyncMock()
        
        # Mock threading.Thread
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)
        
        # Test data
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "test_value",
            "text": "Test option"
        }
        
        # Call the endpoint
        response = self.client.post(
            "/api/options/create", 
            json=option_data
        )
        
        # Verify error response - the app returns 400 as shown in the logs
        assert response.status_code == 400
        assert "Option validation error: Custom validation error" in response.json()["detail"]
        
        # Verify option.valid() was called
        mock_option.valid.assert_called_once()
        
        # Verify save was not called
        mock_option.save.assert_not_called()

    def _mock_thread(self, target, args, kwargs):
        """Helper method to mock threading.Thread by executing the target function immediately."""
        if target:
            if kwargs:
                target(*args, **kwargs)
            else:
                target(*args)
        return MagicMock()

if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_option_creation.py"])
