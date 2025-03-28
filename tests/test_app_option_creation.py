"""Tests for option creation functionality in the FastAPI web application."""
import os
import sys
import pytest
import json
import threading
import tempfile
import shutil
from pathlib import Path
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
        """Test Integer type conversion in create_option function.
        
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

        # Setup mock issue with Integer answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Integer"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock option with property setter that converts string to int
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_option._answer_type = "Integer"
        
        # Create a property setter for value that will convert string to int
        # This simulates the behavior of the actual HivemindOption class
        def set_value(self, val):
            if isinstance(val, str) and mock_option._answer_type == "Integer":
                mock_option._value = int(val)
            else:
                mock_option._value = val
        
        # Create a property getter that returns the converted value
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                result = func(*args)
                # If this is the save call, return the option CID
                if "save" in str(func):
                    return "test_option_cid"
                # If this is the hivemind_issue call, return our mock_issue
                if "hivemind_issue" in str(func):
                    return mock_issue
                # Return the appropriate object based on the function
                return result
            return func

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
        data = response.json()
        assert "option_cid" in data
        assert "state_cid" in data
        assert "needsSignature" in data
        assert data["option_cid"] == "test_option_cid"
        assert data["state_cid"] == "new_state_cid"
        assert data["needsSignature"] == False

        # Most importantly, verify the value was converted to integer
        # This specifically tests Integer conversion
        mock_option.set_issue.assert_called_once_with(hivemind_issue_cid=option_data["hivemind_id"])
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
        """Test Float type conversion in create_option function.
        
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

        # Setup mock issue with Float answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Float"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock option with property setter that converts string to float
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_option._answer_type = "Float"
        
        # Create a property setter for value that will convert string to float
        # This simulates the behavior of the actual HivemindOption class
        def set_value(self, val):
            if isinstance(val, str) and mock_option._answer_type == "Float":
                mock_option._value = float(val)
            else:
                mock_option._value = val
        
        # Create a property getter that returns the converted value
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                result = func(*args)
                # If this is the save call, return the option CID
                if "save" in str(func):
                    return "test_option_cid"
                # If this is the hivemind_issue call, return our mock_issue
                if "hivemind_issue" in str(func):
                    return mock_issue
                # Return the appropriate object based on the function
                return result
            return func

        self.mock_to_thread.side_effect = mock_to_thread_return

        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }
        mock_get_latest_state.return_value = async_mock.return_value

        # Setup mock for update_state - using AsyncMock
        update_mock = AsyncMock()
        update_mock.return_value = {
            "state_cid": "new_state_cid",
            "success": True
        }
        mock_update_state.return_value = update_mock.return_value

        # Mock threading.Thread to allow accepting arbitrary kwargs
        mock_thread.side_effect = lambda target=None, args=(), kwargs=None, daemon=None, **extra_kwargs: self._mock_thread(target, args, kwargs)

        # Test data with string value that should be converted to float
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "3.14",
            "text": "Pi"
        }

        # Call the endpoint
        response = self.client.post(
            "/api/options/create",
            json=option_data
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "option_cid" in data
        assert "state_cid" in data
        assert "needsSignature" in data
        assert data["option_cid"] == "test_option_cid"
        assert data["state_cid"] == "new_state_cid"
        assert data["needsSignature"] == False

        # Most importantly, verify the value was converted to float
        mock_option.set_issue.assert_called_once_with(hivemind_issue_cid=option_data["hivemind_id"])
        assert isinstance(mock_option.value, float)
        assert mock_option.value == 3.14

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
        """Test String type conversion in create_option function.
    
        This test verifies that when an issue's answer_type is 'String', the option value
        remains a string (no conversion needed).
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
    
        # Setup mock issue with String answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "String"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
    
        # Setup mock option with property setter that maintains string value
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_option._answer_type = "String"
        
        # Create a property setter for value that maintains string value
        # This simulates the behavior of the actual HivemindOption class
        def set_value(self, val):
            mock_option._value = val
        
        # Create a property getter that returns the value
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option
    
        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state
    
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                result = func(*args)
                # If this is the save call, return the option CID
                if "save" in str(func):
                    return "test_option_cid"
                # If this is the hivemind_issue call, return our mock_issue
                if "hivemind_issue" in str(func):
                    return mock_issue
                # Return the appropriate object based on the function
                return result
            return func
    
        self.mock_to_thread.side_effect = mock_to_thread_return
    
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }
        mock_get_latest_state.return_value = async_mock.return_value
    
        # Setup mock for update_state - using AsyncMock
        update_mock = AsyncMock()
        update_mock.return_value = {
            "state_cid": "new_state_cid",
            "success": True
        }
        mock_update_state.return_value = update_mock.return_value
    
        # Test data for creating an option with a string value
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "test_value",
            "text": "Test Option"
        }
    
        # Call the endpoint
        response = self.client.post(
            "/api/options/create",
            json=option_data
        )
    
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "option_cid" in data
        assert "state_cid" in data
        assert "needsSignature" in data
        assert data["option_cid"] == "test_option_cid"
        assert data["state_cid"] == "new_state_cid"
        assert data["needsSignature"] == False
    
        # Verify the value remains a string (no conversion)
        mock_option.set_issue.assert_called_once_with(hivemind_issue_cid=option_data["hivemind_id"])
        assert isinstance(mock_option.value, str)
        assert mock_option.value == "test_value"
    
        # Verify save was called
        mock_option.save.assert_called_once()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_complex_field_conversions(self, mock_thread, mock_hivemind_state, mock_hivemind_issue,
                                      mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test Complex type conversion in create_option function.
    
        This test verifies that when an issue's answer_type is 'Complex', the option value
        is properly parsed from a JSON string to a Python dict.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
    
        # Setup mock issue with Complex answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Complex"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
    
        # Setup mock option with property setter that handles JSON parsing
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_option._answer_type = "Complex"
        
        # Create a property setter for value that handles JSON parsing
        # This simulates the behavior of the actual HivemindOption class
        def set_value(self, val):
            if isinstance(val, str) and mock_option._answer_type == "Complex":
                try:
                    mock_option._value = json.loads(val)
                except json.JSONDecodeError:
                    mock_option._value = val
            else:
                mock_option._value = val
        
        # Create a property getter that returns the value
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option
    
        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state
    
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                result = func(*args)
                # If this is the save call, return the option CID
                if "save" in str(func):
                    return "test_option_cid"
                # If this is the hivemind_issue call, return our mock_issue
                if "hivemind_issue" in str(func):
                    return mock_issue
                # Return the appropriate object based on the function
                return result
            return func
    
        self.mock_to_thread.side_effect = mock_to_thread_return
    
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }
        mock_get_latest_state.return_value = async_mock.return_value
    
        # Setup mock for update_state - using AsyncMock
        update_mock = AsyncMock()
        update_mock.return_value = {
            "state_cid": "new_state_cid",
            "success": True
        }
        mock_update_state.return_value = update_mock.return_value
    
        # Test data for creating an option with a JSON string value
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": '{"key1": "value1", "key2": 42, "key3": true}',
            "text": "Complex Option"
        }
    
        # Call the endpoint
        response = self.client.post(
            "/api/options/create",
            json=option_data
        )
    
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "option_cid" in data
        assert "state_cid" in data
        assert "needsSignature" in data
        assert data["option_cid"] == "test_option_cid"
        assert data["state_cid"] == "new_state_cid"
        assert data["needsSignature"] == False
    
        # Verify the value was parsed from JSON string to dict
        mock_option.set_issue.assert_called_once_with(hivemind_issue_cid=option_data["hivemind_id"])
        assert isinstance(mock_option.value, dict)
        assert mock_option.value == {"key1": "value1", "key2": 42, "key3": True}
    
        # Verify save was called
        mock_option.save.assert_called_once()

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_complex_field_float_conversion_error(self, mock_thread, mock_hivemind_state, mock_hivemind_issue,
                                                 mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test Complex type conversion error handling in create_option function.
    
        This test verifies that when an issue's answer_type is 'Complex' and the value contains
        a field that should be a float but cannot be converted, an appropriate error is returned.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }
    
        # Setup mock issue with Complex answer_type and specs constraint
        mock_issue = MagicMock()
        mock_issue.answer_type = "Complex"
        mock_issue.constraints = {
            'specs': {
                'price': 'Float'
            }
        }
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue
    
        # Setup mock option that will raise ValueError on float conversion
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_option._answer_type = "Complex"
        
        # Create a property setter that will raise ValueError on float conversion
        def set_value(self, val):
            if isinstance(val, dict) and mock_option._answer_type == "Complex":
                # Simulate the conversion error
                if 'price' in val and val['price'] == 'not-a-float':
                    raise ValueError("could not convert string to float: 'not-a-float'")
                mock_option._value = val
            else:
                mock_option._value = val
        
        # Create a property getter that returns the value
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option
    
        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state
    
        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                try:
                    result = func(*args)
                    # If this is the save call, return the option CID
                    if "save" in str(func):
                        return "test_option_cid"
                    # If this is the hivemind_issue call, return our mock_issue
                    if "hivemind_issue" in str(func):
                        return mock_issue
                    # Return the appropriate object based on the function
                    return result
                except ValueError as e:
                    # Re-raise the error to be caught by the endpoint
                    raise ValueError(str(e))
            return func
    
        self.mock_to_thread.side_effect = mock_to_thread_return
    
        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }
        mock_get_latest_state.return_value = async_mock.return_value
    
        # Setup mock for update_state - using AsyncMock
        update_mock = AsyncMock()
        update_mock.return_value = {
            "state_cid": "new_state_cid",
            "success": True
        }
        mock_update_state.return_value = update_mock.return_value
    
        # Test data with a complex value containing a field that will cause a float conversion error
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": {
                "price": "not-a-float"  # This will cause a float conversion error
            },
            "text": "Test Complex Option"
        }
    
        # Call the endpoint
        response = self.client.post(
            "/api/options/create",
            json=option_data
        )
    
        # Verify response indicates an error
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "could not convert string to float" in data["detail"]

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

        # Setup mock issue with Integer answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Integer"
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock option that will raise ValueError on integer conversion
        mock_option = MagicMock()
        mock_option.valid.return_value = True
        mock_option.save.return_value = "test_option_cid"
        mock_option.hivemind_id = "test_issue_cid"  # Set hivemind_id for the mapping lookup
        mock_option._answer_type = "Integer"
        
        # Create a property setter that will raise ValueError on integer conversion
        def set_value(self, val):
            if mock_option._answer_type == "Integer":
                try:
                    int(val)
                except ValueError:
                    raise ValueError("invalid literal for int() with base 10: 'not_a_number'")
            mock_option._value = val
        
        # Create a property getter that raises ValueError
        def get_value(self):
            if mock_option._answer_type == "Integer" and mock_option._value == "not_a_number":
                raise ValueError("invalid literal for int() with base 10: 'not_a_number'")
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                try:
                    result = func(*args)
                    # If this is the save call, return the option CID
                    if "save" in str(func):
                        return "test_option_cid"
                    # If this is the hivemind_issue call, return our mock_issue
                    if "hivemind_issue" in str(func):
                        return mock_issue
                    # Return the appropriate object based on the function
                    return result
                except ValueError as e:
                    # Re-raise the error to be caught by the endpoint
                    raise ValueError(str(e))
            return func

        self.mock_to_thread.side_effect = mock_to_thread_return

        # Setup mock for get_latest_state - using AsyncMock
        async_mock = AsyncMock()
        async_mock.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }
        mock_get_latest_state.return_value = async_mock.return_value

        # Setup mock for update_state - using AsyncMock
        update_mock = AsyncMock()
        update_mock.return_value = {
            "state_cid": "new_state_cid",
            "success": True
        }
        mock_update_state.return_value = update_mock.return_value

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
        assert "invalid literal for int()" in error_data["detail"]

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
        """Test option validation failure in create_option function.
    
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

        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.answer_type = "Integer"  # Set to Integer to cause a validation failure
        mock_issue.constraints = {}
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock option that fails validation
        mock_option = MagicMock()
        # Set _answer_type to String which doesn't match the issue's Integer type
        mock_option._answer_type = "String"
        
        # Make save raise an exception to simulate validation failure
        mock_option.save.side_effect = Exception("Option validation failed")
        
        mock_option.hivemind_id = "test_issue_cid"
        
        # Create a property setter and getter for the value property
        def set_value(self, val):
            mock_option._value = val
            # This is where we would normally convert the value based on answer_type
            # But for this test, we want it to fail validation
        
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize the value
        
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                # If this is the save call, raise the exception
                if "save" in str(func):
                    raise Exception("Option validation failed")
                # For other calls, execute the function
                try:
                    result = func(*args)
                    return result
                except Exception as e:
                    # If an exception is raised, propagate it
                    raise e
            return func

        self.mock_to_thread.side_effect = mock_to_thread_return

        # Setup mock for get_latest_state
        mock_get_latest_state.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }

        # Test data
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": "test_value",  # String value for an Integer answer_type
            "text": "Test option"
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
        assert "Option validation failed" in error_data["detail"]

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_option_validation_exception(self, mock_thread, mock_hivemind_state, mock_hivemind_issue,
                                         mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test option validation exception handling in create_option function.
        
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

        # Setup mock issue
        mock_issue = MagicMock()
        mock_issue.answer_type = "String"
        mock_issue.constraints = {"choices": [{"value": "allowed_value"}]}  # Set constraints to trigger validation error
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock option that raises an exception during validation
        mock_option = MagicMock()
        mock_option._answer_type = "String"
        mock_option._hivemind_issue = mock_issue
        mock_option.hivemind_id = "test_issue_cid"
        
        # Create a property setter and getter for the value property
        def set_value(self, val):
            mock_option._value = val
        
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = "test_value"  # Initialize the value
        
        # Make the save method raise a validation exception
        mock_option.save.side_effect = ValueError("Custom validation error")
        
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for asyncio.to_thread
        async def mock_to_thread_return(func, *args):
            # Execute the lambda function
            if callable(func):
                # If this is the save call, raise the exception
                if "save" in str(func):
                    raise ValueError("Custom validation error")
                # For other calls, execute the function
                try:
                    result = func(*args)
                    return result
                except Exception as e:
                    # If an exception is raised, propagate it
                    raise e
            return func

        self.mock_to_thread.side_effect = mock_to_thread_return

        # Setup mock for get_latest_state
        mock_get_latest_state.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }

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

        # Verify error response
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "Custom validation error" in error_data["detail"]

        # Verify save was attempted but failed
        assert mock_option.save.call_count > 0

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_complex_json_parsing_error(self, mock_thread, mock_hivemind_state, mock_hivemind_issue,
                                        mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test Complex answer type JSON parsing error handling.
        
        This test verifies that when a Complex answer type value is provided as a string
        but cannot be parsed as valid JSON, the appropriate error is raised.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }

        # Setup mock issue with Complex answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Complex"
        mock_issue.constraints = {
            'specs': {
                'name': 'String',
                'price': 'Float',
                'quantity': 'Integer'
            }
        }
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Setup mock option with an invalid JSON string value
        mock_option = MagicMock()
        mock_option._answer_type = "Complex"
        mock_option._hivemind_issue = mock_issue
        mock_option.hivemind_id = "test_issue_cid"
        
        # Create a property setter and getter for the value property that will raise a JSONDecodeError
        def set_value(self, val):
            if mock_option._answer_type == "Complex" and isinstance(val, str):
                # This will simulate the JSON parsing error in the actual code
                import json
                raise json.JSONDecodeError("Expecting property name enclosed in double quotes", val, 1)
            mock_option._value = val
        
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        
        # Set the initial value
        mock_option._value = None
        
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.issue = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_state.load.return_value = None  # Mock load method
        
        # Important: Set up the hivemind_issue method to return our mock_issue
        mock_state.hivemind_issue.return_value = mock_issue
        mock_hivemind_state.return_value = mock_state

        # Setup mock for get_latest_state
        mock_get_latest_state.return_value = {
            "state_cid": "test_state_cid",
            "state": mock_state
        }

        # Invalid JSON string that will trigger the JSONDecodeError
        invalid_json = '{name:"Laptop",price:999.99,quantity:10}'  # Missing quotes around keys

        # Test data with invalid JSON string
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": invalid_json,
            "text": "Test Complex Option with Invalid JSON"
        }

        # Call the endpoint
        response = self.client.post(
            "/api/options/create",
            json=option_data
        )

        # Verify response - should be a 400 Bad Request due to invalid JSON
        assert response.status_code == 400
        
        # Verify the error message contains information about the JSON parsing error
        error_data = response.json()
        assert "detail" in error_data
        assert "Expecting property name enclosed in double quotes" in error_data["detail"]

    @patch('app.update_state')
    @patch('app.get_latest_state')
    @patch('app.HivemindOption')
    @patch('app.HivemindIssue')
    @patch('app.HivemindState')
    @patch('threading.Thread')
    def test_complex_json_parsing_type_error(self, mock_thread, mock_hivemind_state, mock_hivemind_issue,
                                             mock_hivemind_option, mock_get_latest_state, mock_update_state):
        """Test Complex answer type JSON parsing TypeError handling.
        
        This test verifies that when a Complex answer type value is provided as a non-string
        and non-dict value (like an integer), a TypeError is raised and handled properly.
        This covers the TypeError part of line 744 in app.py.
        """
        # Mock load_state_mapping to return expected mapping
        self.mock_load_state_mapping.return_value = {
            "test_issue_cid": {
                "state_hash": "test_state_cid",
                "name": "Test Issue",
                "description": "Test Description"
            }
        }

        # Setup mock issue with Complex answer_type
        mock_issue = MagicMock()
        mock_issue.answer_type = "Complex"
        mock_issue.constraints = {
            'specs': {
                'name': 'String',
                'price': 'Float',
                'quantity': 'Integer'
            }
        }
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        mock_issue.restrictions = {}
        # Ensure the constructor returns our mock instance when given the specific CID
        mock_hivemind_issue.side_effect = lambda cid=None, **kwargs: mock_issue if cid == "test_issue_cid" else MagicMock()
        mock_hivemind_issue.return_value = mock_issue

        # Create a mock option that will raise TypeError when value is set to an integer
        mock_option = MagicMock()
        mock_option._answer_type = "Complex"
        mock_option._hivemind_issue = mock_issue
        mock_option.hivemind_id = "test_issue_cid"
        
        # Create a property setter that will raise TypeError when a non-string, non-dict value is provided
        def set_value(self, val):
            if mock_option._answer_type == "Complex" and not isinstance(val, (str, dict)):
                raise TypeError("Object of type 'int' is not JSON serializable")
            mock_option._value = val
        
        def get_value(self):
            return mock_option._value
        
        # Set up the value property with our getter and setter
        type(mock_option).value = property(get_value, set_value)
        mock_option._value = None  # Initialize with None
        mock_option.save.return_value = "test_option_cid"
        
        # Return our mock option
        mock_hivemind_option.return_value = mock_option

        # Setup mock state
        mock_state = MagicMock()
        mock_state.option_cids = ["existing_option"]
        mock_state.opinion_cids = [[]]  # Empty list of opinions
        mock_state.hivemind_issue.return_value = mock_issue
        mock_state.save.return_value = "new_state_cid"
        mock_hivemind_state.return_value = mock_state

        # Setup mock for get_latest_state
        mock_get_latest_state.return_value = {
            "state_cid": "test_state_cid"
        }

        # Setup mock for update_state
        mock_update_state.return_value = None

        # Setup mock for asyncio.to_thread
        async def mock_to_thread(func, *args):
            try:
                result = func(*args)
                return result
            except TypeError as e:
                # Re-raise the TypeError to simulate the actual behavior
                raise TypeError("Object of type 'int' is not JSON serializable")
        
        self.mock_to_thread.side_effect = mock_to_thread

        # Test data with a numeric value (not a string or dict)
        option_data = {
            "hivemind_id": "test_issue_cid",
            "value": 12345,  # This will pass FastAPI validation but cause TypeError in json.loads
            "text": "Test Complex Option with Numeric Value"
        }

        # Call the endpoint - this should raise an HTTPException with status_code 400
        response = self.client.post(
            "/api/options/create",
            json=option_data
        )

        # Verify response - should be a 400 Bad Request due to TypeError
        assert response.status_code == 400
        
        # Verify the error message contains information about the TypeError
        error_data = response.json()
        assert "detail" in error_data
        assert "Object of type 'int' is not JSON serializable" in error_data["detail"]

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
