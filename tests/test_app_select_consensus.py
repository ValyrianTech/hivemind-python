"""Tests for the select_consensus route in the FastAPI web application."""
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
from hivemind.issue import HivemindIssue
from hivemind.option import HivemindOption
from hivemind.opinion import HivemindOpinion
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
VALID_HIVEMIND_ID = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
VALID_OPTION_CID = "QmSoLPppuBtQSGwKDZT2M73ULpjvfd3aZ6ha4oFGL1KrGM"
VALID_OPINION_CID = "QmSoLV749fYgUsEqVgRpFogUXeLdUxpTJUdpVYxXvwcV8S"


# Create a patched version of asyncio.to_thread that returns a coroutine
async def mock_to_thread(func, *args, **kwargs):
    """Mock implementation of asyncio.to_thread that runs the function and returns its result."""
    if callable(func):
        return func(*args, **kwargs)
    return func


# Mock for notify_author_signature
async def mock_notify_author_signature(*args, **kwargs):
    """Mock implementation of notify_author_signature."""
    return None


@pytest.mark.unit
class TestSelectConsensus:
    """Test the select_consensus route in the FastAPI application."""

    def setup_method(self):
        """Set up test client for each test."""
        # Apply patches globally for all tests in this class
        self.asyncio_patch = patch("app.asyncio.to_thread", side_effect=mock_to_thread)
        self.notify_patch = patch("app.notify_author_signature", side_effect=mock_notify_author_signature)
        
        # Start the patches
        self.asyncio_patch.start()
        self.notify_patch.start()
        
        # Create the test client
        self.client = TestClient(app.app)
        
        # Create a test keypair for signing
        self.private_key, self.address = generate_bitcoin_keypair()

    def teardown_method(self):
        """Clean up after each test."""
        # Stop the patches
        self.asyncio_patch.stop()
        self.notify_patch.stop()

    def test_select_consensus_success(self):
        """Test successful consensus selection."""
        # Create test data
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{VALID_HIVEMIND_ID}"
        signature = sign_message(message, self.private_key)

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.questions = ["Test Question"]
        mock_issue.author = self.address
        mock_issue.on_selection = "Finalize"

        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.option_cids = [VALID_OPTION_CID]
        mock_state.calculate_results.return_value = {VALID_OPTION_CID: 1.0}
        mock_state.select_consensus.return_value = [VALID_OPTION_CID]
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.hivemind_issue.return_value = mock_issue
        mock_state._hivemind_issue = mock_issue
        mock_state.hivemind_id = VALID_HIVEMIND_ID

        # Test request data
        request_data = {
            "address": self.address,
            "message": message,
            "signature": signature
        }

        # Patch all necessary functions
        with patch("app.verify_message", return_value=True):
            with patch("app.load_state_mapping", return_value=mock_mapping):
                with patch("app.save_state_mapping", return_value=None):
                    with patch("app.HivemindState", return_value=mock_state):
                        # Test the endpoint
                        response = self.client.post("/api/select_consensus", json=request_data)

                        # Verify response
                        assert response.status_code == 200
                        response_data = response.json()
                        assert response_data["success"] is True
                        assert response_data["state_cid"] == VALID_STATE_CID
                        assert response_data["selected_options"] == [VALID_OPTION_CID]

                        # Verify state methods were called correctly
                        mock_state.select_consensus.assert_called_once_with(
                            timestamp=timestamp,
                            address=self.address,
                            signature=signature
                        )

    def test_select_consensus_invalid_signature(self):
        """Test select_consensus with an invalid signature."""
        # Create test data
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{VALID_HIVEMIND_ID}"
        signature = "invalid_signature"

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.questions = ["Test Question"]
        mock_issue.author = self.address
        
        # Mock HivemindState to raise an error on select_consensus
        mock_state = MagicMock()
        mock_state.hivemind_issue.return_value = mock_issue
        mock_state._hivemind_issue = mock_issue
        mock_state.hivemind_id = VALID_HIVEMIND_ID
        mock_state.select_consensus.side_effect = ValueError("Invalid signature")

        # Test request data
        request_data = {
            "address": self.address,
            "message": message,
            "signature": signature
        }

        # Patch necessary functions
        with patch("app.verify_message", return_value=True):  # This doesn't matter as the state will raise the error
            with patch("app.load_state_mapping", return_value=mock_mapping):
                with patch("app.HivemindState", return_value=mock_state):
                    # Test the endpoint
                    response = self.client.post("/api/select_consensus", json=request_data)

                    # Verify response - the app returns 400 for errors in the select_consensus method
                    assert response.status_code == 400
                    data = response.json()
                    assert "Invalid signature" in data["detail"]

    def test_select_consensus_missing_fields(self):
        """Test select_consensus with missing required fields."""
        # Test request data with missing fields
        request_data = {
            "address": self.address,
            # Missing message and signature
        }

        # Test the endpoint
        response = self.client.post("/api/select_consensus", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["detail"]

    def test_select_consensus_invalid_message_format(self):
        """Test select_consensus with invalid message format."""
        # Create test data with invalid message format
        timestamp = int(time.time())
        message = f"{timestamp}:invalid_format:{VALID_HIVEMIND_ID}"
        signature = sign_message(message, self.private_key)

        # Test request data
        request_data = {
            "address": self.address,
            "message": message,
            "signature": signature
        }

        # Test the endpoint
        response = self.client.post("/api/select_consensus", json=request_data)

        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid message format" in data["detail"]

    def test_select_consensus_hivemind_not_found(self):
        """Test select_consensus with a hivemind ID that doesn't exist."""
        # Create test data
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{VALID_HIVEMIND_ID}"
        signature = sign_message(message, self.private_key)

        # Test request data
        request_data = {
            "address": self.address,
            "message": message,
            "signature": signature
        }

        # Patch verify_message to return True and load_state_mapping to return empty mapping
        with patch("app.verify_message", return_value=True):
            with patch("app.load_state_mapping", return_value={}):
                # Test the endpoint
                response = self.client.post("/api/select_consensus", json=request_data)

                # Verify response
                assert response.status_code == 400
                data = response.json()
                assert f"No state data found for hivemind ID: {VALID_HIVEMIND_ID}" in data["detail"]

    def test_select_consensus_no_options(self):
        """Test select_consensus with no options in the state."""
        # Create test data
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{VALID_HIVEMIND_ID}"
        signature = sign_message(message, self.private_key)

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.questions = ["Test Question"]
        mock_issue.author = self.address

        # Mock HivemindState with no options
        mock_state = MagicMock()
        mock_state.option_cids = []  # No options
        mock_state.hivemind_issue.return_value = mock_issue
        mock_state._hivemind_issue = mock_issue
        mock_state.hivemind_id = VALID_HIVEMIND_ID

        # Test request data
        request_data = {
            "address": self.address,
            "message": message,
            "signature": signature
        }

        # Patch all necessary functions
        with patch("app.verify_message", return_value=True):
            with patch("app.load_state_mapping", return_value=mock_mapping):
                with patch("app.HivemindState", return_value=mock_state):
                    # Test the endpoint
                    response = self.client.post("/api/select_consensus", json=request_data)

                    # Verify response
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["success"] is False
                    assert "No options found" in response_data["error"]

    def test_select_consensus_state_error(self):
        """Test select_consensus with an error in state loading."""
        # Create test data
        timestamp = int(time.time())
        message = f"{timestamp}:select_consensus:{VALID_HIVEMIND_ID}"
        signature = sign_message(message, self.private_key)

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}

        # Test request data
        request_data = {
            "address": self.address,
            "message": message,
            "signature": signature
        }

        # Patch necessary functions
        with patch("app.verify_message", return_value=True):
            with patch("app.load_state_mapping", return_value=mock_mapping):
                with patch("app.HivemindState", side_effect=Exception("Error loading state")):
                    # Test the endpoint
                    response = self.client.post("/api/select_consensus", json=request_data)

                    # Verify response
                    assert response.status_code == 400
                    data = response.json()
                    assert "Error loading state" in data["detail"]

    def test_select_consensus_message_in_data_field(self):
        """Test select_consensus with message in the data field instead of message field."""
        # Create test data
        timestamp = int(time.time())
        message_content = f"{timestamp}:select_consensus:{VALID_HIVEMIND_ID}"
        signature = sign_message(message_content, self.private_key)

        # Mock state mapping
        mock_mapping = {VALID_HIVEMIND_ID: {"state_hash": VALID_STATE_CID}}
        
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.questions = ["Test Question"]
        mock_issue.author = self.address
        mock_issue.on_selection = "Finalize"

        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.option_cids = [VALID_OPTION_CID]
        mock_state.calculate_results.return_value = {VALID_OPTION_CID: 1.0}
        mock_state.select_consensus.return_value = [VALID_OPTION_CID]
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.hivemind_issue.return_value = mock_issue
        mock_state._hivemind_issue = mock_issue
        mock_state.hivemind_id = VALID_HIVEMIND_ID

        # Test request data with message in data field instead of message field
        request_data = {
            "address": self.address,
            "data": message_content,  # Use data field instead of message field
            "signature": signature
        }

        # Patch all necessary functions
        with patch("app.verify_message", return_value=True):
            with patch("app.load_state_mapping", return_value=mock_mapping):
                with patch("app.save_state_mapping", return_value=None):
                    with patch("app.HivemindState", return_value=mock_state):
                        # Test the endpoint
                        response = self.client.post("/api/select_consensus", json=request_data)

                        # Verify response
                        assert response.status_code == 200
                        response_data = response.json()
                        assert response_data["success"] is True
                        assert response_data["state_cid"] == VALID_STATE_CID
                        assert response_data["selected_options"] == [VALID_OPTION_CID]

                        # Verify state methods were called correctly
                        mock_state.select_consensus.assert_called_once_with(
                            timestamp=timestamp,
                            address=self.address,
                            signature=signature
                        )


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_select_consensus.py"])
