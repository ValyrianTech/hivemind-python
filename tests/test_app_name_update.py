"""Tests for the name update routes in the FastAPI web application."""
import os
import sys
import json
import pytest
import time
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, WebSocketDisconnect
from fastapi.websockets import WebSocket

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app

# Import required modules from src.hivemind
sys.path.append(os.path.join(project_root, "src"))
from hivemind.state import HivemindState, HivemindIssue
from hivemind.utils import generate_bitcoin_keypair, sign_message
from ipfs_dict_chain import IPFSDict


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
VALID_HIVEMIND_ID = "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
VALID_STATE_CID = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
VALID_IDENTIFICATION_CID = "QmSoLPppuBtQSGwKDZT2M73ULpjvfd3aZ6ha4oFGL1KrGM"


# Create a patched version of asyncio.to_thread that returns a coroutine
async def mock_to_thread(func, *args, **kwargs):
    """Mock implementation of asyncio.to_thread that runs the function and returns its result."""
    if callable(func):
        return func(*args, **kwargs)
    return func


@pytest.mark.unit
class TestNameUpdatePages:
    """Test the name update page rendering routes."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    def test_update_name_page_path(self):
        """Test the update_name_page_path route."""
        # Test the endpoint with a valid hivemind_id
        response = self.client.get(f"/update_name/{VALID_HIVEMIND_ID}")

        # Verify response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check that the hivemind_id is in the response
        assert VALID_HIVEMIND_ID in response.text

    def test_update_name_page_query_valid(self):
        """Test the update_name_page_query route with valid parameters."""
        # Test the endpoint with a valid hivemind_id
        response = self.client.get(f"/update_name?hivemind_id={VALID_HIVEMIND_ID}")

        # Verify response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Check that the hivemind_id is in the response
        assert VALID_HIVEMIND_ID in response.text

    def test_update_name_page_query_missing_hivemind_id(self):
        """Test the update_name_page_query route with missing hivemind_id."""
        # Test the endpoint without a hivemind_id
        response = self.client.get("/update_name")

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing hivemind_id parameter" in data["detail"]


@pytest.mark.unit
class TestPrepareNameUpdate:
    """Test the prepare_name_update API endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)

    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_prepare_name_update_success(self):
        """Test successful preparation of a name update."""
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.get_identification_cid.return_value = VALID_IDENTIFICATION_CID

        # Patch HivemindIssue
        with patch("app.HivemindIssue", return_value=mock_issue):
            # Test request data
            request_data = {
                "name": "Test User",
                "hivemind_id": VALID_HIVEMIND_ID
            }

            # Test the endpoint
            response = self.client.post("/api/prepare_name_update", json=request_data)

            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["identification_cid"] == VALID_IDENTIFICATION_CID

            # Verify that the name was registered for WebSocket connections
            assert "Test User" in app.name_update_connections

    def test_prepare_name_update_missing_fields(self):
        """Test prepare_name_update with missing required fields."""
        # Test request data with missing name
        request_data = {
            "hivemind_id": VALID_HIVEMIND_ID
        }

        # Test the endpoint
        response = self.client.post("/api/prepare_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["detail"]

        # Test request data with missing hivemind_id
        request_data = {
            "name": "Test User"
        }

        # Test the endpoint
        response = self.client.post("/api/prepare_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_prepare_name_update_exception(self):
        """Test prepare_name_update with an exception."""
        # Mock HivemindIssue to raise an exception
        mock_issue = MagicMock()
        mock_issue.get_identification_cid.side_effect = Exception("Test exception")

        # Patch HivemindIssue
        with patch("app.HivemindIssue", return_value=mock_issue):
            # Test request data
            request_data = {
                "name": "Test User",
                "hivemind_id": VALID_HIVEMIND_ID
            }

            # Test the endpoint
            response = self.client.post("/api/prepare_name_update", json=request_data)

            # Verify response
            assert response.status_code == 500
            data = response.json()
            assert "Test exception" in data["detail"]


@pytest.mark.unit
class TestSignNameUpdate:
    """Test the sign_name_update API endpoint."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)
        # Clear name_update_connections before each test
        app.name_update_connections.clear()
        # Add a test connection
        app.name_update_connections["Test User"] = [AsyncMock()]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    @patch("app.load_state_mapping")
    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    @patch("app.update_state")
    def test_sign_name_update_success(self, mock_update_state, mock_issue, mock_state,
                                      mock_load_state_mapping, mock_ipfs_dict, mock_connect):
        """Test successful name update with a signed message."""
        # Create a timestamp and test data
        timestamp = int(time.time())
        test_name = "Test User"
        test_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Example Bitcoin address
        test_signature = "valid_signature"

        # Mock IPFS Dict to return hivemind_id and name
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "hivemind_id": VALID_HIVEMIND_ID,
            "name": test_name
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Mock state mapping
        mock_load_state_mapping.return_value = {
            VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}
        }

        # Mock HivemindState
        mock_state_instance = MagicMock()
        mock_state_instance.update_participant_name.return_value = None
        mock_state_instance.save.return_value = "new_state_cid"
        mock_state_instance.options = ["option1", "option2"]
        mock_state_instance.opinions = [[{"address": "addr1"}, {"address": "addr2"}]]
        mock_state.return_value = mock_state_instance

        # Mock HivemindIssue
        mock_issue_instance = MagicMock()
        mock_issue_instance.name = "Test Issue"
        mock_issue_instance.description = "Test Description"
        mock_issue_instance.answer_type = "Text"
        mock_issue_instance.questions = ["Test Question"]
        mock_issue_instance.tags = ["test", "tag"]
        mock_issue.return_value = mock_issue_instance

        # Set up the hivemind_issue method to return the mock issue instance
        mock_state_instance.hivemind_issue.return_value = mock_issue_instance

        # Mock update_state to return success
        mock_update_state.return_value = {"success": True}

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": test_address,
            "message": message,
            "signature": test_signature,
            "data": {"name": test_name}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["cid"] == "new_state_cid"

        # Verify that the state was updated
        mock_state_instance.update_participant_name.assert_called_once_with(
            timestamp=timestamp,
            name=test_name,
            address=test_address,
            signature=test_signature,
            message=message
        )

        # Verify that WebSocket notification was sent
        app.name_update_connections["Test User"][0].send_json.assert_called_once()

    def test_sign_name_update_missing_fields(self):
        """Test sign_name_update with missing required fields."""
        # Test request data with missing fields
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": "1234567890cid",
            # Missing signature and data
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["detail"]

    def test_sign_name_update_invalid_message_format(self):
        """Test sign_name_update with invalid message format."""
        # Test request data with invalid message format
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": "invalid_message_format",  # Not timestamp + CID
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid message format" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    def test_sign_name_update_ipfs_error(self, mock_ipfs_dict, mock_connect):
        """Test sign_name_update with IPFS error."""
        # Create a timestamp and test data
        timestamp = int(time.time())

        # Mock IPFS Dict to raise an exception
        mock_ipfs_dict.side_effect = Exception("IPFS connection error")

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": message,
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Failed to load identification data" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    def test_sign_name_update_missing_hivemind_id(self, mock_ipfs_dict, mock_connect):
        """Test sign_name_update with missing hivemind ID in identification data."""
        # Create a timestamp and test data
        timestamp = int(time.time())

        # Mock IPFS Dict to return incomplete data (missing hivemind_id)
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "name": "Test User"
            # Missing hivemind_id
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": message,
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing hivemind ID in identification data" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    @patch("app.load_state_mapping")
    def test_sign_name_update_no_state_found(self, mock_load_state_mapping, mock_ipfs_dict, mock_connect):
        """Test sign_name_update with no state found for hivemind ID."""
        # Create a timestamp and test data
        timestamp = int(time.time())

        # Mock IPFS Dict to return hivemind_id and name
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "hivemind_id": VALID_HIVEMIND_ID,
            "name": "Test User"
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Mock state mapping to return empty dict (no state found)
        mock_load_state_mapping.return_value = {}

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": message,
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert f"No state found for hivemind ID: {VALID_HIVEMIND_ID}" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    @patch("app.load_state_mapping")
    @patch("app.HivemindState")
    def test_sign_name_update_state_exception(self, mock_state, mock_load_state_mapping,
                                              mock_ipfs_dict, mock_connect):
        """Test sign_name_update with exception during state update."""
        # Create a timestamp and test data
        timestamp = int(time.time())

        # Mock IPFS Dict to return hivemind_id and name
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "hivemind_id": VALID_HIVEMIND_ID,
            "name": "Test User"
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Mock state mapping
        mock_load_state_mapping.return_value = {
            VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}
        }

        # Mock HivemindState to raise an exception
        mock_state_instance = MagicMock()
        mock_state_instance.update_participant_name.side_effect = Exception("Signature verification failed")
        mock_state.return_value = mock_state_instance

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": message,
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Signature verification failed" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    @patch("app.load_state_mapping")
    def test_sign_name_update_no_state_hash(self, mock_load_state_mapping, mock_ipfs_dict, mock_connect):
        """Test sign_name_update with no state hash found for hivemind ID (line 1299)."""
        # Create a timestamp and test data
        timestamp = int(time.time())

        # Mock IPFS Dict to return hivemind_id and name
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "hivemind_id": VALID_HIVEMIND_ID,
            "name": "Test User"
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Mock state mapping to return a dict with the hivemind ID but no state_hash
        mock_load_state_mapping.return_value = {
            VALID_HIVEMIND_ID: {"other_field": "some_value"}  # Missing state_hash
        }

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": message,
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400  # The 404 is caught and returned as a 400
        data = response.json()
        assert f"No state hash found for hivemind ID: {VALID_HIVEMIND_ID}" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    def test_sign_name_update_missing_name(self, mock_ipfs_dict, mock_connect):
        """Test sign_name_update with missing name in identification data."""
        # Create a timestamp and test data
        timestamp = int(time.time())

        # Mock IPFS Dict to return incomplete data (missing name)
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "hivemind_id": VALID_HIVEMIND_ID
            # Missing name
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "message": message,
            "signature": "valid_signature",
            "data": {"name": "Test User"}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing name in identification data" in data["detail"]

    def test_sign_name_update_invalid_json(self):
        """Test sign_name_update with invalid JSON data (line 1362)."""
        # Create a client with a custom test_client that doesn't validate JSON
        client = TestClient(app.app)

        # Send a request with invalid JSON data
        response = client.post(
            "/api/sign_name_update",
            content="invalid{json:data",
            headers={"Content-Type": "application/json"}
        )

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid JSON data" in data["detail"]

    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.connect")
    @patch("app.IPFSDict")
    @patch("app.load_state_mapping")
    @patch("app.HivemindState")
    @patch("app.HivemindIssue")
    @patch("app.update_state")
    @patch("app.logger")
    def test_websocket_notification_exception(self, mock_logger, mock_update_state, mock_issue, mock_state,
                                              mock_load_state_mapping, mock_ipfs_dict, mock_connect):
        """Test exception handling when sending WebSocket notifications (lines 1344-1346)."""
        # Create a timestamp and test data
        timestamp = int(time.time())
        test_name = "Test User"
        test_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Example Bitcoin address
        test_signature = "valid_signature"

        # Mock IPFS Dict to return hivemind_id and name
        mock_ipfs_dict_instance = MagicMock()
        mock_ipfs_dict_instance.__getitem__.side_effect = lambda key: {
            "hivemind_id": VALID_HIVEMIND_ID,
            "name": test_name
        }.get(key)
        mock_ipfs_dict.return_value = mock_ipfs_dict_instance

        # Mock state mapping
        mock_load_state_mapping.return_value = {
            VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}
        }

        # Mock HivemindState
        mock_state_instance = MagicMock()
        mock_state_instance.update_participant_name.return_value = None
        mock_state_instance.save.return_value = "new_state_cid"
        mock_state_instance.options = ["option1", "option2"]
        mock_state_instance.opinions = [[{"address": "addr1"}, {"address": "addr2"}]]
        mock_state.return_value = mock_state_instance

        # Mock HivemindIssue
        mock_issue_instance = MagicMock()
        mock_issue_instance.name = "Test Issue"
        mock_issue_instance.description = "Test Description"
        mock_issue_instance.answer_type = "Text"
        mock_issue_instance.questions = ["Test Question"]
        mock_issue_instance.tags = ["test", "tag"]
        mock_issue.return_value = mock_issue_instance

        # Set up the hivemind_issue method to return the mock issue instance
        mock_state_instance.hivemind_issue.return_value = mock_issue_instance

        # Mock update_state to return success
        mock_update_state.return_value = {"success": True}

        # Create a WebSocket mock that raises an exception when send_json is called
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("WebSocket send error")
        app.name_update_connections[test_name] = [mock_websocket]

        # Create test request data
        message = f"{timestamp:010d}{VALID_IDENTIFICATION_CID}"
        request_data = {
            "address": test_address,
            "message": message,
            "signature": test_signature,
            "data": {"name": test_name}
        }

        # Test the endpoint
        response = self.client.post("/api/sign_name_update", json=request_data)

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["cid"] == "new_state_cid"

        # Verify that the WebSocket exception was logged
        mock_logger.error.assert_called_with(f"Failed to send WebSocket notification: WebSocket send error")

        # Verify that the state was updated despite the WebSocket error
        mock_state_instance.update_participant_name.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_name_update.py"])
