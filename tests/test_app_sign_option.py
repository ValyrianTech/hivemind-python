"""Tests for the sign_option route in the FastAPI web application."""
import os
import sys
import json
import pytest
import time
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

# Import required modules from src.hivemind
sys.path.append(os.path.join(project_root, "src"))
from hivemind.state import HivemindState
from hivemind.option import HivemindOption
from hivemind.utils import generate_bitcoin_keypair, sign_message


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


# Valid IPFS CIDs for testing
VALID_STATE_CID = "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
VALID_OPTION_CID = "QmSoLPppuBtQSGwKDZT2M73ULpjvfd3aZ6ha4oFGL1KrGM"
VALID_HIVEMIND_ID = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"


# Create a patched version of asyncio.to_thread that returns a coroutine
async def mock_to_thread(func, *args, **kwargs):
    """Mock implementation of asyncio.to_thread that runs the function and returns its result."""
    if callable(func):
        return func(*args, **kwargs)
    return func


@pytest.mark.unit
class TestSignOption:
    """Test the sign_option route in the FastAPI application."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)
        # Create a test keypair for signing
        self.private_key, self.address = generate_bitcoin_keypair()

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    def test_sign_option_success(self, mock_load_state_mapping, mock_verify_message):
        """Test successful signing of an option."""
        # Configure mocks
        mock_verify_message.return_value = True

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping

        # Mock HivemindOption
        mock_option = MagicMock()
        mock_option.value = "Test Option"
        mock_option.hivemind_id = VALID_HIVEMIND_ID
        mock_option._answer_type = "String"

        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.option_cids = [VALID_OPTION_CID]
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.add_option.return_value = None

        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.answer_type = "String"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]

        # Set up the hivemind_issue method to return the mock issue
        mock_state.hivemind_issue.return_value = mock_issue

        # Patch update_state to be a coroutine that returns None
        async def mock_update_state(*args, **kwargs):
            return None

        # Patch HivemindOption, HivemindState, and update_state
        with patch("app.HivemindOption", return_value=mock_option):
            with patch("app.HivemindState", return_value=mock_state):
                with patch("app.update_state", side_effect=mock_update_state):
                    # Create test data
                    timestamp = int(time.time())
                    option_hash = VALID_OPTION_CID
                    message = f"{timestamp}{option_hash}"
                    signature = sign_message(message, self.private_key)

                    # Test request data
                    request_data = {
                        "address": self.address,
                        "message": message,
                        "signature": signature,
                        "data": {
                            "hivemind_id": VALID_HIVEMIND_ID,
                            "value": "Test Option"
                        }
                    }

                    # Test the endpoint
                    response = self.client.post("/api/sign_option", json=request_data)

                    # Verify response
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["success"] is True
                    assert "cid" in response_data

        # Verify mocks were called correctly
        mock_verify_message.assert_called_once_with(message, self.address, signature)
        mock_load_state_mapping.assert_called_once()
        mock_state.add_option.assert_called_once_with(
            timestamp=timestamp,
            option_hash=option_hash,
            signature=signature,
            address=self.address
        )

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    def test_sign_option_invalid_signature(self, mock_load_state_mapping, mock_verify_message):
        """Test sign_option with an invalid signature."""
        # Configure mocks
        mock_verify_message.return_value = False

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping

        # Mock HivemindOption
        mock_option = MagicMock()
        mock_option.value = "Test Option"
        mock_option.hivemind_id = VALID_HIVEMIND_ID
        mock_option._answer_type = "String"

        # Mock HivemindState
        mock_state = MagicMock()

        # Patch HivemindOption and HivemindState
        with patch("app.HivemindOption", return_value=mock_option):
            with patch("app.HivemindState", return_value=mock_state):
                # Create test data
                timestamp = int(time.time())
                option_hash = VALID_OPTION_CID
                message = f"{timestamp}{option_hash}"
                signature = "invalid_signature"

                # Test request data
                request_data = {
                    "address": self.address,
                    "message": message,
                    "signature": signature,
                    "data": {
                        "hivemind_id": VALID_HIVEMIND_ID,
                        "value": "Test Option"
                    }
                }

                # Test the endpoint
                response = self.client.post("/api/sign_option", json=request_data)

                # Verify response
                assert response.status_code == 400
                data = response.json()
                assert "Signature is invalid" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_sign_option_missing_fields(self):
        """Test sign_option with missing required fields."""
        # Test request data with missing fields
        request_data = {
            "address": self.address,
            # Missing message, signature, and data
        }

        # Test the endpoint
        response = self.client.post("/api/sign_option", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_sign_option_invalid_message_format(self):
        """Test sign_option with invalid message format."""
        # Test request data with invalid message format
        request_data = {
            "address": self.address,
            "message": "invalid-message-format",  # Not in the format timestamp+CID
            "signature": "some-signature",
            "data": {
                "hivemind_id": VALID_HIVEMIND_ID,
                "value": "Test Option"
            }
        }

        # Test the endpoint
        response = self.client.post("/api/sign_option", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid message format" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_sign_option_invalid_json(self):
        """Test sign_option with invalid JSON data."""
        # Test the endpoint with invalid JSON
        response = self.client.post(
            "/api/sign_option", 
            content="invalid-json-data",
            headers={"Content-Type": "application/json"}
        )

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid JSON data" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.load_state_mapping")
    def test_sign_option_no_hivemind_id(self, mock_load_state_mapping):
        """Test sign_option with option that has no hivemind_id."""
        # Mock HivemindOption with no hivemind_id
        mock_option = MagicMock()
        mock_option.value = "Test Option"
        mock_option.hivemind_id = None  # No hivemind_id
        mock_option._answer_type = "String"

        # Patch HivemindOption
        with patch("app.HivemindOption", return_value=mock_option):
            # Create test data
            timestamp = int(time.time())
            option_hash = VALID_OPTION_CID
            message = f"{timestamp}{option_hash}"
            signature = "some-signature"

            # Test request data
            request_data = {
                "address": self.address,
                "message": message,
                "signature": signature,
                "data": {
                    "value": "Test Option"
                }
            }

            # Test the endpoint
            response = self.client.post("/api/sign_option", json=request_data)

            # Verify response
            assert response.status_code == 400
            data = response.json()
            assert "Option does not have an associated hivemind state" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.load_state_mapping")
    def test_sign_option_no_state_data(self, mock_load_state_mapping):
        """Test sign_option with no state data for the hivemind ID."""
        # Mock state mapping with no data for the hivemind ID
        mock_mapping = {}  # Empty mapping
        mock_load_state_mapping.return_value = mock_mapping

        # Mock HivemindOption
        mock_option = MagicMock()
        mock_option.value = "Test Option"
        mock_option.hivemind_id = VALID_HIVEMIND_ID
        mock_option._answer_type = "String"

        # Patch HivemindOption
        with patch("app.HivemindOption", return_value=mock_option):
            # Create test data
            timestamp = int(time.time())
            option_hash = VALID_OPTION_CID
            message = f"{timestamp}{option_hash}"
            signature = "some-signature"

            # Test request data
            request_data = {
                "address": self.address,
                "message": message,
                "signature": signature,
                "data": {
                    "hivemind_id": VALID_HIVEMIND_ID,
                    "value": "Test Option"
                }
            }

            # Test the endpoint
            response = self.client.post("/api/sign_option", json=request_data)

            # Verify response
            assert response.status_code == 400
            data = response.json()
            assert "No state data found for hivemind ID" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    @patch("app.active_connections")
    def test_sign_option_with_websocket_notification(self, mock_active_connections, mock_load_state_mapping, mock_verify_message):
        """Test sign_option with WebSocket notification."""
        # Configure mocks
        mock_verify_message.return_value = True

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping

        # Mock HivemindOption
        mock_option = MagicMock()
        mock_option.value = "Test Option"
        mock_option.hivemind_id = VALID_HIVEMIND_ID
        mock_option._answer_type = "String"

        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.option_cids = [VALID_OPTION_CID]
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.add_option.return_value = None

        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.answer_type = "String"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]

        # Set up the hivemind_issue method to return the mock issue
        mock_state.hivemind_issue.return_value = mock_issue

        # Mock WebSocket connections
        mock_connection = AsyncMock()
        mock_active_connections.__getitem__.return_value = [mock_connection]
        mock_active_connections.__contains__.return_value = True

        # Patch update_state to be a coroutine that returns None
        async def mock_update_state(*args, **kwargs):
            return None

        # Patch HivemindOption, HivemindState, and update_state
        with patch("app.HivemindOption", return_value=mock_option):
            with patch("app.HivemindState", return_value=mock_state):
                with patch("app.update_state", side_effect=mock_update_state):
                    # Create test data
                    timestamp = int(time.time())
                    option_hash = VALID_OPTION_CID
                    message = f"{timestamp}{option_hash}"
                    signature = sign_message(message, self.private_key)

                    # Test request data
                    request_data = {
                        "address": self.address,
                        "message": message,
                        "signature": signature,
                        "data": {
                            "hivemind_id": VALID_HIVEMIND_ID,
                            "value": "Test Option"
                        }
                    }

                    # Test the endpoint
                    response = self.client.post("/api/sign_option", json=request_data)

                    # Verify response
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["success"] is True
                    assert "cid" in response_data

        # Verify WebSocket notification was sent
        mock_connection.send_json.assert_called_once()
        notification_data = mock_connection.send_json.call_args[0][0]
        assert notification_data["success"] is True
        assert notification_data["option_hash"] == option_hash
        assert notification_data["hivemind_id"] == VALID_HIVEMIND_ID

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    @patch("app.active_connections")
    def test_sign_option_websocket_notification_exception(self, mock_active_connections, mock_load_state_mapping, mock_verify_message):
        """Test sign_option with WebSocket notification that raises an exception."""
        # Configure mocks
        mock_verify_message.return_value = True

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping

        # Mock HivemindOption
        mock_option = MagicMock()
        mock_option.value = "Test Option"
        mock_option.hivemind_id = VALID_HIVEMIND_ID
        mock_option._answer_type = "String"

        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.option_cids = [VALID_OPTION_CID]
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.add_option.return_value = None

        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.answer_type = "String"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]

        # Set up the hivemind_issue method to return the mock issue
        mock_state.hivemind_issue.return_value = mock_issue

        # Mock WebSocket connections - one that works and one that raises an exception
        mock_connection_success = AsyncMock()
        mock_connection_failure = AsyncMock()
        # Make the second connection raise an exception when send_json is called
        mock_connection_failure.send_json.side_effect = Exception("WebSocket connection error")
        
        # Set up active_connections to contain both connections
        mock_active_connections.__getitem__.return_value = [mock_connection_success, mock_connection_failure]
        mock_active_connections.__contains__.return_value = True

        # Patch update_state to be a coroutine that returns None
        async def mock_update_state(*args, **kwargs):
            return None

        # Patch HivemindOption, HivemindState, and update_state
        with patch("app.HivemindOption", return_value=mock_option):
            with patch("app.HivemindState", return_value=mock_state):
                with patch("app.update_state", side_effect=mock_update_state):
                    # Create test data
                    timestamp = int(time.time())
                    option_hash = VALID_OPTION_CID
                    message = f"{timestamp}{option_hash}"
                    signature = sign_message(message, self.private_key)

                    # Test request data
                    request_data = {
                        "address": self.address,
                        "message": message,
                        "signature": signature,
                        "data": {
                            "hivemind_id": VALID_HIVEMIND_ID,
                            "value": "Test Option"
                        }
                    }

                    # Test the endpoint
                    response = self.client.post("/api/sign_option", json=request_data)

                    # Verify response
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["success"] is True
                    assert "cid" in response_data

        # Verify both WebSocket connections were attempted
        mock_connection_success.send_json.assert_called_once()
        mock_connection_failure.send_json.assert_called_once()
        
        # The exception in the second connection should not have affected the overall result
        notification_data = mock_connection_success.send_json.call_args[0][0]
        assert notification_data["success"] is True
        assert notification_data["option_hash"] == option_hash
        assert notification_data["hivemind_id"] == VALID_HIVEMIND_ID


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_sign_option.py"])
