"""WebSocket routes for real-time streaming."""
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from ..websocket import connection_manager
from ..websocket.monitoring import monitoring_websocket_handler
from ..middleware.auth import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/insights")
async def websocket_insights(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time insight streaming.
    
    Clients can optionally provide a Firebase Auth token for authenticated access.
    Unauthenticated connections are supported for Guest Mode.
    
    Args:
        websocket: The WebSocket connection
        token: Optional Firebase Auth token for authentication
    """
    connection_id = str(uuid.uuid4())
    user_id = None
    
    # Verify token if provided
    if token:
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token["uid"]
            logger.info(f"Authenticated WebSocket connection for user: {user_id}")
        except Exception as e:
            logger.warning(f"Invalid WebSocket auth token: {e}")
            # Continue as guest connection
    
    try:
        # Accept and register connection
        await connection_manager.connect(websocket, connection_id, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "authenticated": user_id is not None,
            "message": "Connected to utxoIQ real-time insight stream"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (e.g., ping/pong)
                data = await websocket.receive_json()
                
                # Handle ping messages
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })
                
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    
    finally:
        # Clean up connection
        await connection_manager.disconnect(connection_id)


@router.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system monitoring.
    
    Streams system status, backfill progress, and processing metrics.
    """
    await monitoring_websocket_handler(websocket)


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Connection statistics including total connections
    """
    return {
        "total_connections": connection_manager.get_connection_count(),
        "status": "operational"
    }
