"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app
from src.models import PostResult


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_posting_service():
    """Create mock posting service."""
    service = AsyncMock()
    service.process_hourly_insights = AsyncMock(return_value=[
        PostResult(success=True, tweet_id="tweet-1", insight_id="insight-1"),
        PostResult(success=True, tweet_id="tweet-2", insight_id="insight-2"),
        PostResult(success=False, error="Failed", insight_id="insight-3")
    ])
    service.post_insight = AsyncMock(return_value=PostResult(
        success=True,
        tweet_id="tweet-123",
        insight_id="insight-123"
    ))
    return service


@pytest.fixture
def mock_daily_brief_service():
    """Create mock daily brief service."""
    service = AsyncMock()
    service.post_daily_brief = AsyncMock(return_value=["tweet-1", "tweet-2", "tweet-3"])
    return service


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "utxoIQ X Bot"
        assert "version" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_post_hourly_insights(self, client, mock_posting_service):
        """Test hourly insights posting endpoint."""
        with patch('src.main.posting_service', mock_posting_service):
            response = client.post("/post/hourly")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "completed"
            assert data["total_processed"] == 3
            assert data["successful_posts"] == 2
            assert data["failed_posts"] == 1
            assert len(data["results"]) == 3
    
    def test_post_hourly_insights_disabled(self, client):
        """Test hourly posting when disabled."""
        with patch('src.main.settings') as mock_settings:
            mock_settings.hourly_check_enabled = False
            
            response = client.post("/post/hourly")
            
            assert response.status_code == 503
    
    def test_post_daily_brief(self, client, mock_daily_brief_service):
        """Test daily brief posting endpoint."""
        with patch('src.main.daily_brief_service', mock_daily_brief_service):
            response = client.post("/post/daily-brief")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "completed"
            assert data["total_tweets"] == 3
            assert data["successful_tweets"] == 3
            assert len(data["tweet_ids"]) == 3
    
    def test_post_daily_brief_with_date(self, client, mock_daily_brief_service):
        """Test daily brief posting with specific date."""
        with patch('src.main.daily_brief_service', mock_daily_brief_service):
            response = client.post("/post/daily-brief?brief_date=2025-11-07")
            
            assert response.status_code == 200
            
            # Verify service was called with correct date
            mock_daily_brief_service.post_daily_brief.assert_called_once()
    
    def test_post_daily_brief_invalid_date(self, client):
        """Test daily brief posting with invalid date format."""
        response = client.post("/post/daily-brief?brief_date=invalid-date")
        
        assert response.status_code == 400
    
    def test_post_daily_brief_skipped(self, client, mock_daily_brief_service):
        """Test daily brief skipped when already posted."""
        mock_daily_brief_service.post_daily_brief.return_value = []
        
        with patch('src.main.daily_brief_service', mock_daily_brief_service):
            response = client.post("/post/daily-brief")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "skipped"
    
    def test_post_single_insight_success(self, client, mock_posting_service):
        """Test posting single insight."""
        # Mock API client to return insights
        mock_api_client = AsyncMock()
        mock_api_client.get_publishable_insights = AsyncMock(return_value=[
            type('Insight', (), {'id': 'insight-123'})()
        ])
        
        with patch('src.main.posting_service', mock_posting_service):
            mock_posting_service.api_client = mock_api_client
            
            response = client.post("/post/insight/insight-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["tweet_id"] == "tweet-123"
    
    def test_post_single_insight_not_found(self, client, mock_posting_service):
        """Test posting non-existent insight."""
        mock_api_client = AsyncMock()
        mock_api_client.get_publishable_insights = AsyncMock(return_value=[])
        
        with patch('src.main.posting_service', mock_posting_service):
            mock_posting_service.api_client = mock_api_client
            
            response = client.post("/post/insight/nonexistent")
            
            assert response.status_code == 404
    
    def test_get_recent_posts_status(self, client):
        """Test getting recent posts status."""
        with patch('src.main.posting_service') as mock_service:
            mock_service.redis_client.get_last_daily_brief_date.return_value = "2025-11-07"
            
            response = client.get("/status/recent-posts")
            
            assert response.status_code == 200
            data = response.json()
            assert "last_daily_brief_date" in data
            assert "duplicate_prevention_window" in data
            assert "confidence_threshold" in data
