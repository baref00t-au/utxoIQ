"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.main import app
from src.models import EmailPreferences, EmailFrequency, SignalType


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "email-service"
    assert "timestamp" in data


@patch('src.main.bq_client')
def test_update_preferences_new_user(mock_bq_client, client):
    """Test updating preferences for new user."""
    mock_bq_client.get_preferences.return_value = None
    mock_bq_client.save_preferences.return_value = None
    
    response = client.post(
        "/preferences/user_123?email=test@example.com",
        json={
            "daily_brief_enabled": True,
            "frequency": "daily",
            "signal_filters": ["mempool", "exchange"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert data["email"] == "test@example.com"
    assert data["daily_brief_enabled"] is True
    assert mock_bq_client.save_preferences.called


@patch('src.main.bq_client')
def test_update_preferences_existing_user(mock_bq_client, client, sample_email_preferences):
    """Test updating preferences for existing user."""
    mock_bq_client.get_preferences.return_value = sample_email_preferences
    mock_bq_client.save_preferences.return_value = None
    
    response = client.post(
        "/preferences/user_123?email=test@example.com",
        json={
            "daily_brief_enabled": False,
            "frequency": "weekly"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["daily_brief_enabled"] is False
    assert data["frequency"] == "weekly"
    assert mock_bq_client.save_preferences.called


@patch('src.main.bq_client')
def test_get_preferences(mock_bq_client, client, sample_email_preferences):
    """Test getting user preferences."""
    mock_bq_client.get_preferences.return_value = sample_email_preferences
    
    response = client.get("/preferences/user_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert data["email"] == "test@example.com"


@patch('src.main.bq_client')
def test_get_preferences_not_found(mock_bq_client, client):
    """Test getting preferences for non-existent user."""
    mock_bq_client.get_preferences.return_value = None
    
    response = client.get("/preferences/user_999")
    
    assert response.status_code == 404


@patch('src.main.bq_client')
def test_unsubscribe(mock_bq_client, client, sample_email_preferences):
    """Test unsubscribe endpoint."""
    mock_bq_client.get_preferences.return_value = sample_email_preferences
    mock_bq_client.save_preferences.return_value = None
    
    response = client.post(
        "/unsubscribe",
        json={
            "user_id": "user_123",
            "reason": "Too many emails"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Successfully unsubscribed"
    assert data["user_id"] == "user_123"
    
    # Verify preferences were updated
    save_call = mock_bq_client.save_preferences.call_args[0][0]
    assert save_call.daily_brief_enabled is False
    assert save_call.frequency == EmailFrequency.NEVER


@patch('src.main.bq_client')
def test_unsubscribe_user_not_found(mock_bq_client, client):
    """Test unsubscribe for non-existent user."""
    mock_bq_client.get_preferences.return_value = None
    
    response = client.post(
        "/unsubscribe",
        json={"user_id": "user_999"}
    )
    
    assert response.status_code == 404


@patch('src.main.email_service')
def test_send_daily_brief_async(mock_email_service, client):
    """Test triggering daily brief send (async)."""
    response = client.post("/send-daily-brief")
    
    assert response.status_code == 200
    data = response.json()
    assert "Daily brief send job started" in data["message"]


@patch('src.main.email_service')
@pytest.mark.asyncio
async def test_send_daily_brief_sync(mock_email_service, client):
    """Test sending daily brief synchronously."""
    mock_email_service.send_daily_briefs = AsyncMock(return_value={
        "success": True,
        "date": "2025-11-06",
        "sent": 5,
        "failed": 0,
        "skipped": 1,
        "total_users": 6
    })
    
    response = client.post("/send-daily-brief/sync?date=2025-11-06")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["sent"] == 5
    assert data["total_users"] == 6


@patch('src.main.sendgrid_client')
def test_sendgrid_webhook(mock_sendgrid_client, client):
    """Test SendGrid webhook endpoint."""
    webhook_data = [{
        "event": "open",
        "email": "test@example.com",
        "user_id": "user_123",
        "email_id": "email_456",
        "timestamp": 1699372800
    }]
    
    response = client.post("/webhook/sendgrid", json=webhook_data)
    
    assert response.status_code == 200
    assert mock_sendgrid_client.handle_webhook_event.called


@patch('src.main.bq_client')
def test_get_engagement_stats(mock_bq_client, client):
    """Test getting engagement statistics."""
    mock_bq_client.get_engagement_stats.return_value = {
        "delivered": 100,
        "opened": 75,
        "clicked": 30
    }
    
    response = client.get("/stats/engagement?user_id=user_123&days=30")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_123"
    assert data["days"] == 30
    assert data["stats"]["delivered"] == 100
    assert data["stats"]["opened"] == 75


@patch('src.main.bq_client')
def test_get_engagement_stats_all_users(mock_bq_client, client):
    """Test getting engagement statistics for all users."""
    mock_bq_client.get_engagement_stats.return_value = {
        "delivered": 500,
        "opened": 350,
        "clicked": 120
    }
    
    response = client.get("/stats/engagement?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] is None
    assert data["days"] == 7
    assert data["stats"]["delivered"] == 500
