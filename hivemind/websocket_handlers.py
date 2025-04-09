"""WebSocket handlers for the Hivemind application."""
import logging
import asyncio
from typing import Dict, List
from fastapi import WebSocket, FastAPI
from starlette.websockets import WebSocketDisconnect

# Initialize logging
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}
# Store active WebSocket connections for name updates
name_update_connections: Dict[str, List[WebSocket]] = {}
# Store active WebSocket connections for author signatures
author_signature_connections: Dict[str, List[WebSocket]] = {}


async def websocket_opinion_endpoint(websocket: WebSocket, opinion_hash: str):
    """WebSocket endpoint for opinion notifications."""
    await websocket.accept()

    if opinion_hash not in active_connections:
        active_connections[opinion_hash] = []
    active_connections[opinion_hash].append(websocket)

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except (WebSocketDisconnect, Exception, asyncio.CancelledError):
        # Handle any type of exception, including WebSocketDisconnect and CancelledError
        if opinion_hash in active_connections and websocket in active_connections[opinion_hash]:
            active_connections[opinion_hash].remove(websocket)
            if not active_connections[opinion_hash]:
                del active_connections[opinion_hash]


async def websocket_option_endpoint(websocket: WebSocket, option_hash: str):
    """WebSocket endpoint for option signing notifications.
    
    Args:
        websocket: The WebSocket connection
        option_hash: The option hash to subscribe to
    """
    await websocket.accept()

    # Add the connection to the active connections
    if option_hash not in active_connections:
        active_connections[option_hash] = []
    active_connections[option_hash].append(websocket)

    try:
        # Keep the connection open until the client disconnects
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception, asyncio.CancelledError):
        # Handle any type of exception, including WebSocketDisconnect and CancelledError
        if option_hash in active_connections and websocket in active_connections[option_hash]:
            active_connections[option_hash].remove(websocket)
            if not active_connections[option_hash]:
                del active_connections[option_hash]


async def websocket_name_update_endpoint(websocket: WebSocket, name: str):
    """WebSocket endpoint for name update notifications."""
    await websocket.accept()

    if name not in name_update_connections:
        name_update_connections[name] = []
    name_update_connections[name].append(websocket)

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except (WebSocketDisconnect, Exception, asyncio.CancelledError):
        # Handle any type of exception, including WebSocketDisconnect and CancelledError
        if name in name_update_connections and websocket in name_update_connections[name]:
            name_update_connections[name].remove(websocket)
            if not name_update_connections[name]:
                del name_update_connections[name]


async def websocket_author_signature_endpoint(websocket: WebSocket, hivemind_id: str):
    """WebSocket endpoint for author signature notifications.
    
    Args:
        websocket: The WebSocket connection
        hivemind_id: The hivemind ID to subscribe to
    """
    await websocket.accept()

    # Add the connection to the active connections
    if hivemind_id not in author_signature_connections:
        author_signature_connections[hivemind_id] = []
    author_signature_connections[hivemind_id].append(websocket)

    try:
        # Keep the connection open until the client disconnects
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception, asyncio.CancelledError):
        # Handle any type of exception, including WebSocketDisconnect and CancelledError
        if hivemind_id in author_signature_connections and websocket in author_signature_connections[hivemind_id]:
            author_signature_connections[hivemind_id].remove(websocket)
            if not author_signature_connections[hivemind_id]:
                del author_signature_connections[hivemind_id]


async def notify_author_signature(hivemind_id: str, data: dict):
    """Notify clients about author signature events.
    
    Args:
        hivemind_id: The hivemind ID
        data: The data to send to the clients
    """
    if hivemind_id in author_signature_connections:
        connections_to_notify = author_signature_connections[hivemind_id].copy()
        for connection in connections_to_notify:
            try:
                await connection.send_json(data)
                # Close the connection after sending the notification
                await connection.close()
                logger.info(f"Closed websocket connection after sending author signature notification")
            except Exception as e:
                logger.error(f"Error sending author signature notification: {str(e)}")

        # Clear the connections for this hivemind_id
        author_signature_connections[hivemind_id] = []


def register_websocket_routes(app: FastAPI):
    """Register WebSocket routes with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """

    @app.websocket("/ws/opinion/{opinion_hash}")
    async def opinion_endpoint(websocket: WebSocket, opinion_hash: str):
        await websocket_opinion_endpoint(websocket, opinion_hash)

    @app.websocket("/ws/option/{option_hash}")
    async def option_endpoint(websocket: WebSocket, option_hash: str):
        await websocket_option_endpoint(websocket, option_hash)

    @app.websocket("/ws/name_update/{name}")
    async def name_update_endpoint(websocket: WebSocket, name: str):
        await websocket_name_update_endpoint(websocket, name)

    @app.websocket("/ws/author_signature/{hivemind_id}")
    async def author_signature_endpoint(websocket: WebSocket, hivemind_id: str):
        await websocket_author_signature_endpoint(websocket, hivemind_id)
