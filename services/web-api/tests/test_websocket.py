"""WebSocket integration tests."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestWebSocketConnection:
    """Test WebSocket connection and messaging."""
    
    def test_websocket_connection_without_auth(self):
        """Test WebSocket connection without authentication (Guest Mode)."""
        with client.websocket_connect("/ws/insights") as websocket:
            # Receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["authenticated"] is False
            assert "connection_id" in data
            assert "message" in data
    
    def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong mechanism."""
        with client.websocket_connect("/ws/insights") as websocket:
            # Receive welcome message
            welcome = websocket.receive_json()
            assert welcome["type"] == "connected"
            
            # Send ping
            websocket.send_json({"type": "ping", "timestamp": "2025-11-07T10:30:00Z"})
            
            # Receive pong
            pong = websocket.receive_json()
            assert pong["type"] == "pong"
            assert pong["timestamp"] == "2025-11-07T10:30:00Z"
    
    def test_websocket_stats_endpoint(self):
        """Test WebSocket statistics endpoint."""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data
        assert "status" in data
        assert data["status"] == "operational"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
