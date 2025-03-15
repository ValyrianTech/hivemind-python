"""WebSocket handlers for the Hivemind application."""
import logging
from typing import Dict, List
from fastapi import WebSocket, FastAPI

# Initialize logging
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}
# Store active WebSocket connections for name updates
name_update_connections: Dict[str, List[WebSocket]] = {}

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

async def websocket_name_update_endpoint(websocket: WebSocket, name: str):
    """WebSocket endpoint for name update notifications."""
    await websocket.accept()
    
    if name not in name_update_connections:
        name_update_connections[name] = []
    name_update_connections[name].append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except:
        name_update_connections[name].remove(websocket)
        if not name_update_connections[name]:
            del name_update_connections[name]

def register_websocket_routes(app: FastAPI):
    """Register WebSocket routes with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    @app.websocket("/ws/opinion/{opinion_hash}")
    async def ws_endpoint(websocket: WebSocket, opinion_hash: str):
        await websocket_endpoint(websocket, opinion_hash)
    
    @app.websocket("/ws/name_update/{name}")
    async def ws_name_update_endpoint(websocket: WebSocket, name: str):
        await websocket_name_update_endpoint(websocket, name)
