"""Tests for author signature WebSocket functionality in the FastAPI web application."""
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
from websocket_handlers import (
    register_websocket_routes, 
    websocket_author_signature_endpoint, 
    notify_author_signature, 
    author_signature_connections
)

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
class TestAuthorSignatureWebSocket:
    """Test author signature WebSocket endpoint functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment before each test."""
        # Clear active connections before each test
        author_signature_connections.clear()
        yield
        # Clean up after each test
        author_signature_connections.clear()

    async def test_author_signature_websocket_connection_management(self):
        """Test author signature WebSocket connection management functionality."""
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        hivemind_id = "test_hivemind_id"

        # Set up the WebSocketDisconnect exception for the receive_text call
        mock_websocket.receive_text.side_effect = WebSocketDisconnect("Connection closed")

        # Call the websocket author signature endpoint
        await websocket_author_signature_endpoint(mock_websocket, hivemind_id)

        # Verify the connection was accepted
        mock_websocket.accept.assert_called_once()

        # Verify the connection was removed from author_signature_connections after disconnect
        assert hivemind_id not in author_signature_connections

    async def test_author_signature_general_exception_handling(self):
        """Test handling of general exceptions in the author signature WebSocket endpoint."""
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        hivemind_id = "test_hivemind_id"

        # Set up a general exception for the receive_text call
        mock_websocket.receive_text.side_effect = Exception("Test exception")

        # Call the websocket author signature endpoint
        await websocket_author_signature_endpoint(mock_websocket, hivemind_id)

        # Verify the connection was accepted
        mock_websocket.accept.assert_called_once()

        # Verify the connection was removed from author_signature_connections after exception
        assert hivemind_id not in author_signature_connections

    async def test_multiple_author_signature_connections_same_id(self):
        """Test multiple WebSocket connections with the same hivemind ID."""
        # Create mock WebSockets
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        hivemind_id = "shared_hivemind_id"

        # Set up the first connection to stay alive for one receive_text call then disconnect
        mock_websocket1.receive_text.side_effect = asyncio.CancelledError

        # Set up the second connection to raise an exception
        mock_websocket2.receive_text.side_effect = Exception("Test exception")

        # First, add the first connection
        await websocket_author_signature_endpoint(mock_websocket1, hivemind_id)

        # Verify the first connection was accepted
        mock_websocket1.accept.assert_called_once()

        # Reset author_signature_connections for the second test
        # This is necessary because the first connection would have been removed
        # due to the exception
        author_signature_connections[hivemind_id] = [mock_websocket1]

        # Now test the second connection
        await websocket_author_signature_endpoint(mock_websocket2, hivemind_id)

        # Verify the second connection was accepted
        mock_websocket2.accept.assert_called_once()

        # Verify author_signature_connections was properly cleaned up for the second connection
        # but the first connection should still be there
        assert hivemind_id in author_signature_connections
        assert len(author_signature_connections[hivemind_id]) == 1
        assert mock_websocket1 in author_signature_connections[hivemind_id]
        assert mock_websocket2 not in author_signature_connections[hivemind_id]

    async def test_author_signature_route_registration(self):
        """Test author signature WebSocket route registration functionality."""
        # Create a test FastAPI app
        test_app = FastAPI()

        # Create a mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        hivemind_id = "test_hivemind_id"

        # Register the WebSocket routes with our test app
        register_websocket_routes(test_app)

        # Get the route handler that was registered
        author_signature_route = None
        for route in test_app.routes:
            if route.path == "/ws/author_signature/{hivemind_id}":
                author_signature_route = route
                break

        assert author_signature_route is not None, "Author signature WebSocket route was not registered"

        # Create a patch to intercept calls to the websocket_author_signature_endpoint
        with patch('websocket_handlers.websocket_author_signature_endpoint') as mock_endpoint:
            # Set up the mock to return immediately
            mock_endpoint.return_value = None

            # Call the route handler directly with our mock WebSocket
            # This simulates what FastAPI would do when a WebSocket connection is received
            await author_signature_route.endpoint(mock_websocket, hivemind_id)

            # Verify that the websocket_author_signature_endpoint function was called with the correct arguments
            mock_endpoint.assert_called_once_with(mock_websocket, hivemind_id)

    async def test_notify_author_signature(self):
        """Test notification of author signature events."""
        # Create mock WebSockets
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        hivemind_id = "test_hivemind_id"
        
        # Add the mock WebSockets to the author_signature_connections
        author_signature_connections[hivemind_id] = [mock_websocket1, mock_websocket2]
        
        # Create test data to send
        test_data = {"signature": "test_signature", "timestamp": "123456789"}
        
        # Call the notify_author_signature function
        await notify_author_signature(hivemind_id, test_data)
        
        # Verify that send_json was called on both WebSockets with the test data
        mock_websocket1.send_json.assert_called_once_with(test_data)
        mock_websocket2.send_json.assert_called_once_with(test_data)
        
        # Verify that close was called on both WebSockets
        mock_websocket1.close.assert_called_once()
        mock_websocket2.close.assert_called_once()
        
        # Verify that the connections were cleared
        assert hivemind_id in author_signature_connections
        assert len(author_signature_connections[hivemind_id]) == 0

    async def test_notify_author_signature_with_exception(self):
        """Test notification of author signature events with an exception."""
        # Create mock WebSockets
        mock_websocket = AsyncMock(spec=WebSocket)
        hivemind_id = "test_hivemind_id"
        
        # Configure the mock to raise an exception when send_json is called
        mock_websocket.send_json.side_effect = Exception("Test exception")
        
        # Add the mock WebSocket to the author_signature_connections
        author_signature_connections[hivemind_id] = [mock_websocket]
        
        # Create test data to send
        test_data = {"signature": "test_signature", "timestamp": "123456789"}
        
        # Call the notify_author_signature function
        with patch('websocket_handlers.logger') as mock_logger:
            await notify_author_signature(hivemind_id, test_data)
            
            # Verify that the error was logged
            mock_logger.error.assert_called_once()
            assert "Error sending author signature notification" in mock_logger.error.call_args[0][0]
        
        # Verify that the connections were cleared
        assert hivemind_id in author_signature_connections
        assert len(author_signature_connections[hivemind_id]) == 0

    async def test_notify_author_signature_nonexistent_id(self):
        """Test notification of author signature events for a nonexistent hivemind ID."""
        # Create test data to send
        test_data = {"signature": "test_signature", "timestamp": "123456789"}
        hivemind_id = "nonexistent_id"
        
        # Make sure the hivemind_id is not in author_signature_connections
        if hivemind_id in author_signature_connections:
            del author_signature_connections[hivemind_id]
        
        # Call the notify_author_signature function
        await notify_author_signature(hivemind_id, test_data)
        
        # Verify that nothing happened (no exceptions were raised)
        assert hivemind_id not in author_signature_connections


if __name__ == "__main__":
    pytest.main(["-xvs", "test_websocket_author_signature.py"])
