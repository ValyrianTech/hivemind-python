"""WebSocket handlers for the Hivemind application."""
import logging
from typing import Dict, List
from fastapi import WebSocket, FastAPI

# Initialize logging
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

async def websocket_endpoint(websocket: WebSocket, opinion_hash: str):
    """WebSocket endpoint for opinion notifications."""
    await websocket.accept()
    
    if opinion_hash not in active_connections:
        active_connections[opinion_hash] = []
    active_connections[opinion_hash].append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        active_connections[opinion_hash].remove(websocket)
        if not active_connections[opinion_hash]:
            del active_connections[opinion_hash]

def register_websocket_routes(app: FastAPI):
    """Register WebSocket routes with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    @app.websocket("/ws/opinion/{opinion_hash}")
    async def ws_endpoint(websocket: WebSocket, opinion_hash: str):
        await websocket_endpoint(websocket, opinion_hash)
