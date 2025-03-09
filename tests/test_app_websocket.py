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
        mock_websocket2 = AsyncMock(spec=WebSocket)
        opinion_hash = "test_hash"
        
        # Test connection and disconnection to cover lines 209-221
        # First connection with WebSocketDisconnect
        mock_websocket1.receive_text.side_effect = WebSocketDisconnect("Connection closed")
        
        try:
            await app.websocket_endpoint(mock_websocket1, opinion_hash)
        except WebSocketDisconnect:
            pass
        
        # Verify the connection was accepted
        mock_websocket1.accept.assert_called_once()
        
        # Second connection with general Exception
        mock_websocket2.receive_text.side_effect = Exception("Some error")
        
        try:
            await app.websocket_endpoint(mock_websocket2, opinion_hash)
        except Exception:
            pass
        
        # Verify the second connection was accepted
        mock_websocket2.accept.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", "test_app_websocket.py"])
