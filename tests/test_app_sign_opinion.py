"""Tests for the sign_opinion route in the FastAPI web application."""
import os
import sys
import json
import pytest
import time
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
from hivemind.state import HivemindState, HivemindOpinion, HivemindIssue
from hivemind.utils import generate_bitcoin_keypair, sign_message

# Valid IPFS CIDs for testing
VALID_STATE_CID = "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
VALID_OPINION_CID = "QmZ4tDuvesekSs4qM5ZBKpXiZGun7S2CYtEZRB3DYXkjGx"
VALID_OPTION1_CID = "QmSoLPppuBtQSGwKDZT2M73ULpjvfd3aZ6ha4oFGL1KrGM"
VALID_OPTION2_CID = "QmSoLV4Bbm51jM9C4gDYZQ9Cy3U6aXMJDAbzgu2fzaDs64"

# Create a patched version of asyncio.to_thread that runs synchronously
def mock_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)

@pytest.mark.unit
class TestSignOpinion:
    """Test the sign_opinion route in the FastAPI application."""
    
    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app.app)
        # Create a test keypair for signing
        self.private_key, self.address = generate_bitcoin_keypair()
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    def test_sign_opinion_success(self, mock_load_state_mapping, mock_verify_message):
        """Test successful signing of an opinion."""
        # Configure mocks
        mock_verify_message.return_value = True
        
        # Mock state mapping
        mock_mapping = {"test_hivemind_id": {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping
        
        # Mock HivemindOpinion
        mock_opinion = MagicMock()
        mock_opinion.hivemind_id = "test_hivemind_id"
        mock_opinion.question_index = 0
        
        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.options = [VALID_OPTION1_CID, VALID_OPTION2_CID]
        mock_state.opinions = [[]]  # Empty list for each question
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.calculate_results.return_value = {VALID_OPTION1_CID: {"score": 0.8}}
        
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.answer_type = "String"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        
        # Mock option for get_sorted_options
        mock_option = MagicMock()
        mock_option.cid.return_value = f"/ipfs/{VALID_OPTION1_CID}"
        mock_option.text = "Option 1"
        mock_option.value = "option1"
        mock_state.get_sorted_options.return_value = [mock_option]
        
        # Patch HivemindOpinion, HivemindState, and HivemindIssue
        with patch("app.HivemindOpinion", return_value=mock_opinion):
            with patch("app.HivemindState", return_value=mock_state):
                with patch("app.HivemindIssue", return_value=mock_issue):
                    # Create test data
                    timestamp = int(time.time())
                    opinion_hash = VALID_OPINION_CID
                    message = f"{timestamp}{opinion_hash}"
                    signature = sign_message(message, self.private_key)
                    
                    # Test request data
                    request_data = {
                        "address": self.address,
                        "message": message,
                        "signature": signature,
                        "data": {
                            "hivemind_id": "test_hivemind_id",
                            "question_index": 0,
                            "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
                        }
                    }
                    
                    # Test the endpoint
                    response = self.client.post("/api/sign_opinion", json=request_data)
                    
                    # Verify response
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["cid"] == VALID_STATE_CID
        
        # Verify mocks were called correctly
        mock_verify_message.assert_called_once_with(message, self.address, signature)
        mock_load_state_mapping.assert_called_once()
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    def test_sign_opinion_invalid_signature(self, mock_load_state_mapping, mock_verify_message):
        """Test sign_opinion with an invalid signature."""
        # Configure mocks
        mock_verify_message.return_value = False
        
        # Mock state mapping
        mock_mapping = {"test_hivemind_id": {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping
        
        # Mock HivemindOpinion
        mock_opinion = MagicMock()
        mock_opinion.hivemind_id = "test_hivemind_id"
        mock_opinion.question_index = 0
        
        # Patch HivemindOpinion
        with patch("app.HivemindOpinion", return_value=mock_opinion):
            # Create test data
            timestamp = int(time.time())
            opinion_hash = VALID_OPINION_CID
            message = f"{timestamp}{opinion_hash}"
            signature = "invalid_signature"
            
            # Test request data
            request_data = {
                "address": self.address,
                "message": message,
                "signature": signature,
                "data": {
                    "hivemind_id": "test_hivemind_id",
                    "question_index": 0,
                    "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
                }
            }
            
            # Test the endpoint
            response = self.client.post("/api/sign_opinion", json=request_data)
            
            # Verify response
            assert response.status_code == 400
            data = response.json()
            assert "Signature is invalid" in data["detail"]
        
        # Verify mocks were called correctly
        mock_verify_message.assert_called_once_with(message, self.address, signature)
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_sign_opinion_missing_fields(self):
        """Test sign_opinion with missing required fields."""
        # Test request data with missing fields
        request_data = {
            "address": self.address,
            # Missing message
            "signature": "test_signature",
            "data": {
                "hivemind_id": "test_hivemind_id",
                "question_index": 0,
                "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
            }
        }
        
        # Test the endpoint
        response = self.client.post("/api/sign_opinion", json=request_data)
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Missing required fields" in data["detail"]
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    def test_sign_opinion_invalid_message_format(self):
        """Test sign_opinion with invalid message format."""
        # Test request data with invalid message format
        request_data = {
            "address": self.address,
            "message": "invalid_format",  # Not in the format timestampCID
            "signature": "test_signature",
            "data": {
                "hivemind_id": "test_hivemind_id",
                "question_index": 0,
                "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
            }
        }
        
        # Test the endpoint
        response = self.client.post("/api/sign_opinion", json=request_data)
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid message format" in data["detail"]
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.load_state_mapping")
    def test_sign_opinion_no_hivemind_id(self, mock_load_state_mapping):
        """Test sign_opinion when opinion has no hivemind_id."""
        # Mock HivemindOpinion with no hivemind_id
        mock_opinion = MagicMock()
        mock_opinion.hivemind_id = None
        
        # Patch HivemindOpinion
        with patch("app.HivemindOpinion", return_value=mock_opinion):
            # Create test data
            timestamp = int(time.time())
            opinion_hash = VALID_OPINION_CID
            message = f"{timestamp}{opinion_hash}"
            
            # Test request data
            request_data = {
                "address": self.address,
                "message": message,
                "signature": "test_signature",
                "data": {
                    "hivemind_id": "test_hivemind_id",
                    "question_index": 0,
                    "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
                }
            }
            
            # Test the endpoint
            response = self.client.post("/api/sign_opinion", json=request_data)
            
            # Verify response
            assert response.status_code == 400
            data = response.json()
            assert "Opinion does not have an associated hivemind state" in data["detail"]
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.load_state_mapping")
    def test_sign_opinion_no_state_data(self, mock_load_state_mapping):
        """Test sign_opinion when no state data is found for the hivemind ID."""
        # Mock state mapping with no data for the hivemind ID
        mock_load_state_mapping.return_value = {}
        
        # Mock HivemindOpinion
        mock_opinion = MagicMock()
        mock_opinion.hivemind_id = "test_hivemind_id"
        
        # Patch HivemindOpinion
        with patch("app.HivemindOpinion", return_value=mock_opinion):
            # Create test data
            timestamp = int(time.time())
            opinion_hash = VALID_OPINION_CID
            message = f"{timestamp}{opinion_hash}"
            
            # Test request data
            request_data = {
                "address": self.address,
                "message": message,
                "signature": "test_signature",
                "data": {
                    "hivemind_id": "test_hivemind_id",
                    "question_index": 0,
                    "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
                }
            }
            
            # Test the endpoint
            response = self.client.post("/api/sign_opinion", json=request_data)
            
            # Verify response
            assert response.status_code == 400
            data = response.json()
            assert "No state data found for hivemind ID" in data["detail"]
    
    @patch("app.asyncio.to_thread", mock_to_thread)
    @patch("app.verify_message")
    @patch("app.load_state_mapping")
    def test_sign_opinion_websocket_notification(self, mock_load_state_mapping, mock_verify_message):
        """Test sign_opinion with WebSocket notification."""
        # Configure mocks
        mock_verify_message.return_value = True
        
        # Mock state mapping
        mock_mapping = {"test_hivemind_id": {"state_hash": VALID_STATE_CID}}
        mock_load_state_mapping.return_value = mock_mapping
        
        # Mock HivemindOpinion
        mock_opinion = MagicMock()
        mock_opinion.hivemind_id = "test_hivemind_id"
        mock_opinion.question_index = 0
        
        # Mock HivemindState
        mock_state = MagicMock()
        mock_state.options = [VALID_OPTION1_CID, VALID_OPTION2_CID]
        mock_state.opinions = [[]]  # Empty list for each question
        mock_state.save.return_value = VALID_STATE_CID
        mock_state.calculate_results.return_value = {VALID_OPTION1_CID: {"score": 0.8}}
        
        # Mock HivemindIssue
        mock_issue = MagicMock()
        mock_issue.name = "Test Issue"
        mock_issue.description = "Test Description"
        mock_issue.answer_type = "String"
        mock_issue.questions = ["Test Question"]
        mock_issue.tags = ["test"]
        
        # Mock option for get_sorted_options
        mock_option = MagicMock()
        mock_option.cid.return_value = f"/ipfs/{VALID_OPTION1_CID}"
        mock_option.text = "Option 1"
        mock_option.value = "option1"
        mock_state.get_sorted_options.return_value = [mock_option]
        
        # Mock WebSocket connection
        mock_websocket = MagicMock()
        mock_websocket.send_json = AsyncMock()
        
        # Add mock connection to active_connections
        opinion_hash = VALID_OPINION_CID
        app.active_connections[opinion_hash] = [mock_websocket]
        
        # Patch HivemindOpinion, HivemindState, and HivemindIssue
        with patch("app.HivemindOpinion", return_value=mock_opinion):
            with patch("app.HivemindState", return_value=mock_state):
                with patch("app.HivemindIssue", return_value=mock_issue):
                    # Create test data
                    timestamp = int(time.time())
                    message = f"{timestamp}{opinion_hash}"
                    signature = sign_message(message, self.private_key)
                    
                    # Test request data
                    request_data = {
                        "address": self.address,
                        "message": message,
                        "signature": signature,
                        "data": {
                            "hivemind_id": "test_hivemind_id",
                            "question_index": 0,
                            "ranking": [VALID_OPTION1_CID, VALID_OPTION2_CID]
                        }
                    }
                    
                    # Test the endpoint
                    response = self.client.post("/api/sign_opinion", json=request_data)
                    
                    # Verify response
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["cid"] == VALID_STATE_CID
        
        # Clean up
        del app.active_connections[opinion_hash]
    
    def test_sign_opinion_invalid_json(self):
        """Test sign_opinion with invalid JSON data."""
        # Test the endpoint with invalid JSON
        response = self.client.post(
            "/api/sign_opinion", 
            headers={"Content-Type": "application/json"},
            content="invalid json"
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid JSON data" in data["detail"]


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_sign_opinion.py"])
