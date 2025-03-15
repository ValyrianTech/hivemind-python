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

if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_name_update.py"])
