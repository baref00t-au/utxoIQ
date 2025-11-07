"""Guest Mode integration tests."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestGuestMode:
    """Test Guest Mode functionality."""
    
    def test_public_insights_no_auth_required(self):
        """Test that public insights endpoint works without authentication."""
        response = client.get("/insights/public")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_more"] is False
    
    def test_public_insights_limited_to_20(self):
        """Test that public insights are limited to 20 items."""
        response = client.get("/insights/public")
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 20
        # Actual count may be less if there aren't 20 insights yet
        assert len(data["insights"]) <= 20
    
    def test_latest_insights_works_without_auth(self):
        """Test that latest insights endpoint works without authentication."""
        response = client.get("/insights/latest?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "total" in data
        assert "has_more" in data
    
    def test_insight_detail_works_without_auth(self):
        """Test that insight detail endpoint works without authentication."""
        # This will return 404 since we don't have real data, but it should not require auth
        response = client.get("/insights/test_insight_id")
        # Should get 404 (not found) not 401/403 (auth required)
        assert response.status_code in [404, 500]
    
    def test_daily_brief_works_without_auth(self):
        """Test that daily brief endpoint works without authentication."""
        response = client.get("/daily-brief/2025-11-07")
        # Should get 404 (not found) not 401/403 (auth required)
        assert response.status_code in [404, 500]
    
    def test_accuracy_leaderboard_works_without_auth(self):
        """Test that accuracy leaderboard works without authentication."""
        response = client.get("/insights/accuracy-leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert "updated_at" in data
    
    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication."""
        # Alerts endpoint should require auth
        response = client.get("/alerts")
        assert response.status_code == 403
        
        # Chat endpoint should require auth
        response = client.post("/chat/query", json={"query": "test"})
        assert response.status_code == 403
        
        # Billing endpoint should require auth
        response = client.get("/billing/subscription")
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
