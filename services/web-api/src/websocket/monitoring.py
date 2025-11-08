"""
WebSocket handlers for real-time monitoring updates
"""

import asyncio
import json
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MonitoringConnectionManager:
    """Manages WebSocket connections for monitoring updates"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.broadcast_task = None
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
        # Start broadcast task if not running
        if self.broadcast_task is None or self.broadcast_task.done():
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def _broadcast_loop(self):
        """Periodically broadcast system status to all clients"""
        while self.active_connections:
            try:
                # Fetch current system status
                status = await self._get_system_status()
                
                # Broadcast to all clients
                await self.broadcast({
                    "type": "status_update",
                    "data": status,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Wait 5 seconds before next broadcast
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5)
    
    async def _get_system_status(self) -> dict:
        """Fetch current system status"""
        # TODO: Implement actual status fetching
        # For now, return mock data
        return {
            "status": "healthy",
            "blocks_behind": 2,
            "processing_rate": 0.95,
            "active_jobs": 1
        }


# Global connection manager
monitoring_manager = MonitoringConnectionManager()


async def monitoring_websocket_handler(websocket: WebSocket):
    """Handle WebSocket connections for monitoring"""
    await monitoring_manager.connect(websocket)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await monitoring_manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )
            elif message.get("type") == "subscribe":
                # Client wants to subscribe to specific updates
                await monitoring_manager.send_personal_message(
                    {"type": "subscribed", "message": "Subscribed to monitoring updates"},
                    websocket
                )
            
    except WebSocketDisconnect:
        monitoring_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        monitoring_manager.disconnect(websocket)


async def broadcast_backfill_update(job_id: str, progress: dict):
    """Broadcast backfill progress update to all connected clients"""
    await monitoring_manager.broadcast({
        "type": "backfill_update",
        "job_id": job_id,
        "data": progress,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_insight_generated(insight: dict):
    """Broadcast new insight to all connected clients"""
    await monitoring_manager.broadcast({
        "type": "insight_generated",
        "data": insight,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_signal_computed(signal: dict):
    """Broadcast new signal to all connected clients"""
    await monitoring_manager.broadcast({
        "type": "signal_computed",
        "data": signal,
        "timestamp": datetime.utcnow().isoformat()
    })
