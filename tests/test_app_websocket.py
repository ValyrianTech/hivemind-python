"""Tests for WebSocket functionality in the FastAPI web application."""
import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the app module using a direct import with sys.path manipulation
sys.path.append(os.path.join(project_root, "hivemind"))
import app
from app import active_connections

from fastapi.websockets import WebSocket, WebSocketDisconnect


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


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_websocket.py"])
