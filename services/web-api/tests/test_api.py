"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "utxoIQ API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication."""
    
    def test_get_public_insights(self):
        """Test public insights endpoint (Guest Mode)."""
        response = client.get("/insights/public")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_get_latest_insights(self):
        """Test latest insights endpoint."""
        response = client.get("/insights/latest?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "total" in data
        assert "has_more" in data
    
    def test_websocket_stats(self):
        """Test WebSocket stats endpoint."""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_connections" in data
        assert data["status"] == "operational"


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation endpoints."""
    
    def test_openapi_json(self):
        """Test OpenAPI JSON schema endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["openapi"] == "3.1.0"
        assert schema["info"]["title"] == "utxoIQ API"
        assert "components" in schema
        assert "securitySchemes" in schema["components"]
        assert "FirebaseAuth" in schema["components"]["securitySchemes"]
        assert "ApiKeyAuth" in schema["components"]["securitySchemes"]
    
    def test_swagger_ui(self):
        """Test Swagger UI documentation page."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_ui(self):
        """Test ReDoc documentation page."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication."""
    
    def test_get_alerts_without_auth(self):
        """Test that alerts endpoint requires authentication."""
        response = client.get("/alerts")
        assert response.status_code == 403  # Forbidden without auth
    
    def test_create_alert_without_auth(self):
        """Test that creating alert requires authentication."""
        response = client.post("/alerts", json={
            "signal_type": "mempool",
            "threshold": 50.0,
            "operator": "gt",
            "is_active": True
        })
        assert response.status_code == 403  # Forbidden without auth
    
    def test_chat_query_without_auth(self):
        """Test that chat endpoint requires authentication."""
        response = client.post("/chat/query", json={
            "query": "What is the current mempool fee?"
        })
        assert response.status_code == 403  # Forbidden without auth


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
