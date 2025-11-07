"""WebSocket connection manager for real-time streaming."""
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from ..models.insights import Insight

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time insight streaming."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_metadata: Dict[str, dict] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            connection_id: Unique identifier for this connection
            user_id: Optional authenticated user ID
        """
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow()
        }
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(user: {user_id}, total: {len(self.active_connections)})"
        )
        
        # Start heartbeat task if not already running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and unregister a WebSocket connection.
        
        Args:
            connection_id: The connection ID to disconnect
        """
        if connection_id in self.active_connections:
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove connection
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            
            logger.info(
                f"WebSocket disconnected: {connection_id} "
                f"(user: {user_id}, remaining: {len(self.active_connections)})"
            )
    
    async def send_personal_message(
        self,
        message: dict,
        connection_id: str
    ) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            message: The message to send
            connection_id: The target connection ID
            
        Returns:
            True if sent successfully, False otherwise
        """
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                await self.disconnect(connection_id)
                return False
        return False
    
    async def send_to_user(self, message: dict, user_id: str) -> int:
        """
        Send a message to all connections for a specific user.
        
        Args:
            message: The message to send
            user_id: The target user ID
            
        Returns:
            Number of connections successfully sent to
        """
        if user_id not in self.user_connections:
            return 0
        
        connection_ids = list(self.user_connections[user_id])
        sent_count = 0
        
        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: dict) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
            
        Returns:
            Number of connections successfully sent to
        """
        connection_ids = list(self.active_connections.keys())
        sent_count = 0
        
        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_insight(self, insight: Insight) -> int:
        """
        Broadcast a new insight to all connected clients.
        
        Args:
            insight: The insight to broadcast
            
        Returns:
            Number of connections successfully sent to
        """
        message = {
            "type": "insight",
            "data": insight.model_dump(mode="json"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sent_count = await self.broadcast(message)
        logger.info(f"Broadcasted insight {insight.id} to {sent_count} connections")
        return sent_count
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages to maintain connections."""
        while self.active_connections:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                connection_ids = list(self.active_connections.keys())
                for connection_id in connection_ids:
                    try:
                        websocket = self.active_connections[connection_id]
                        await websocket.send_json(heartbeat_message)
                        self.connection_metadata[connection_id]["last_heartbeat"] = datetime.utcnow()
                    except Exception as e:
                        logger.warning(f"Heartbeat failed for {connection_id}: {e}")
                        await self.disconnect(connection_id)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get the number of connections for a specific user."""
        return len(self.user_connections.get(user_id, set()))


# Global connection manager instance
connection_manager = ConnectionManager()
