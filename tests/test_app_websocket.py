"""Tests for WebSocket functionality in the FastAPI web application."""
import os
import sys
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app
from app import active_connections
from websocket_handlers import register_websocket_routes, websocket_endpoint

from fastapi import FastAPI
from fastapi.websockets import WebSocket, WebSocketDisconnect

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

@pytest.mark.asyncio
class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear active connections before each test
        active_connections.clear()
        yield
        # Clean up after each test
        active_connections.clear()
    
    async def test_websocket_connection_management(self):
        """Test WebSocket connection management functionality."""
        # Create mock WebSockets
        mock_websocket1 = AsyncMock(spec=WebSocket)
        opinion_hash = "test_hash"
        
        # Set up the WebSocketDisconnect exception for the receive_text call
        mock_websocket1.receive_text.side_effect = WebSocketDisconnect("Connection closed")
        
        # Call the websocket endpoint
        await app.websocket_endpoint(mock_websocket1, opinion_hash)
        
        # Verify the connection was accepted
        mock_websocket1.accept.assert_called_once()
        
        # Verify the connection was removed from active_connections after disconnect
        assert opinion_hash not in active_connections
    
    async def test_general_exception_handling(self):
        """Test handling of general exceptions in the WebSocket endpoint."""
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        opinion_hash = "test_hash"
        
        # Set up a general exception for the receive_text call
        mock_websocket.receive_text.side_effect = Exception("Test exception")
        
        # Call the websocket endpoint
        await app.websocket_endpoint(mock_websocket, opinion_hash)
        
        # Verify the connection was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify the connection was removed from active_connections after exception
        assert opinion_hash not in active_connections
    
    async def test_multiple_connections_same_hash(self):
        """Test multiple WebSocket connections with the same opinion hash."""
        # Create mock WebSockets
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        opinion_hash = "shared_hash"
        
        # Set up the first connection to stay alive for one receive_text call then disconnect
        mock_websocket1.receive_text.side_effect = asyncio.CancelledError
        
        # Set up the second connection to raise an exception
        mock_websocket2.receive_text.side_effect = Exception("Test exception")
        
        # First, add the first connection
        await app.websocket_endpoint(mock_websocket1, opinion_hash)
        
        # Verify the first connection was accepted
        mock_websocket1.accept.assert_called_once()
        
        # Reset active_connections for the second test
        # This is necessary because the first connection would have been removed
        # due to the exception
        active_connections[opinion_hash] = [mock_websocket1]
        
        # Now test the second connection
        await app.websocket_endpoint(mock_websocket2, opinion_hash)
        
        # Verify the second connection was accepted
        mock_websocket2.accept.assert_called_once()
        
        # Verify active_connections was properly cleaned up for the second connection
        # but the first connection should still be there
        assert opinion_hash in active_connections
        assert len(active_connections[opinion_hash]) == 1
        assert mock_websocket1 in active_connections[opinion_hash]
        assert mock_websocket2 not in active_connections[opinion_hash]

    async def test_route_registration(self):
        """Test WebSocket route registration functionality."""
        # Create a test FastAPI app
        test_app = FastAPI()
        
        # Create a mock for the websocket_endpoint function
        original_endpoint = websocket_endpoint
        
        # Create a mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        opinion_hash = "test_registration_hash"
        
        # Register the WebSocket routes with our test app
        register_websocket_routes(test_app)
        
        # Get the route handler that was registered
        websocket_route = None
        for route in test_app.routes:
            if route.path == "/ws/opinion/{opinion_hash}":
                websocket_route = route
                break
        
        assert websocket_route is not None, "WebSocket route was not registered"
        
        # Create a patch to intercept calls to the original websocket_endpoint
        with patch('websocket_handlers.websocket_endpoint') as mock_endpoint:
            # Set up the mock to return immediately
            mock_endpoint.return_value = None
            
            # Call the route handler directly with our mock WebSocket
            # This simulates what FastAPI would do when a WebSocket connection is received
            await websocket_route.endpoint(mock_websocket, opinion_hash)
            
            # Verify that the websocket_endpoint function was called with the correct arguments
            mock_endpoint.assert_called_once_with(mock_websocket, opinion_hash)


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_websocket.py"])
