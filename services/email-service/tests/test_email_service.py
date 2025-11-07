"""Tests for email service core functionality."""
import pytest
from datetime import datetime, time
from unittest.mock import Mock, AsyncMock, patch

from src.email_service import EmailService
from src.models import EmailPreferences, EmailFrequency, SignalType, QuietHours


@pytest.mark.asyncio
async def test_send_daily_brief_to_user(
    sample_email_preferences,
    sample_daily_brief,
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates
):
    """Test sending daily brief to a single user."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    
    result = await service.send_daily_brief_to_user(
        sample_email_preferences,
        sample_daily_brief
    )
    
    assert result is True
    assert mock_email_templates.render_daily_brief.called
    assert mock_email_templates.render_plain_text.called
    assert mock_sendgrid_client.send_email.called


@pytest.mark.asyncio
async def test_send_daily_brief_during_quiet_hours(
    sample_email_preferences_with_quiet_hours,
    sample_daily_brief,
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates
):
    """Test that emails are not sent during quiet hours."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    
    # Mock current time to be within quiet hours (e.g., 23:00)
    with patch('src.email_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value.time.return_value = time(23, 0, 0)
        
        result = await service.send_daily_brief_to_user(
            sample_email_preferences_with_quiet_hours,
            sample_daily_brief
        )
    
    assert result is False
    assert not mock_sendgrid_client.send_email.called


@pytest.mark.asyncio
async def test_filter_insights_by_signal_type(
    sample_email_preferences,
    sample_daily_brief,
    sample_insight,
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates
):
    """Test filtering insights based on user preferences."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    
    # Add an insight with different signal type
    exchange_insight = sample_insight.model_copy()
    exchange_insight.signal_type = "exchange"
    exchange_insight.id = "insight_456"
    
    miner_insight = sample_insight.model_copy()
    miner_insight.signal_type = "miner"
    miner_insight.id = "insight_789"
    
    sample_daily_brief.insights = [sample_insight, exchange_insight, miner_insight]
    
    # User only wants mempool and exchange
    sample_email_preferences.signal_filters = [SignalType.MEMPOOL, SignalType.EXCHANGE]
    
    result = await service.send_daily_brief_to_user(
        sample_email_preferences,
        sample_daily_brief
    )
    
    assert result is True
    
    # Check that template was called with filtered insights
    call_args = mock_email_templates.render_daily_brief.call_args
    filtered_brief = call_args[0][0]
    
    # Should only have mempool and exchange insights
    assert len(filtered_brief.insights) == 2
    assert any(i.signal_type == "mempool" for i in filtered_brief.insights)
    assert any(i.signal_type == "exchange" for i in filtered_brief.insights)
    assert not any(i.signal_type == "miner" for i in filtered_brief.insights)


@pytest.mark.asyncio
async def test_no_insights_after_filtering(
    sample_email_preferences,
    sample_daily_brief,
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates
):
    """Test that email is not sent if no insights match filters."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    
    # User only wants whale insights, but brief only has mempool
    sample_email_preferences.signal_filters = [SignalType.WHALE]
    
    result = await service.send_daily_brief_to_user(
        sample_email_preferences,
        sample_daily_brief
    )
    
    assert result is False
    assert not mock_sendgrid_client.send_email.called


@pytest.mark.asyncio
async def test_send_daily_briefs_to_all_users(
    sample_email_preferences,
    sample_daily_brief,
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates,
    mock_api_client
):
    """Test sending daily briefs to all subscribed users."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    service.api_client = mock_api_client
    
    # Mock API client to return daily brief
    mock_api_client.get_daily_brief.return_value = sample_daily_brief
    
    # Mock BigQuery to return multiple users
    user1 = sample_email_preferences.model_copy()
    user1.user_id = "user_1"
    user1.email = "user1@example.com"
    
    user2 = sample_email_preferences.model_copy()
    user2.user_id = "user_2"
    user2.email = "user2@example.com"
    
    mock_bigquery_client.get_users_for_daily_brief.return_value = [user1, user2]
    
    result = await service.send_daily_briefs()
    
    assert result["success"] is True
    assert result["sent"] == 2
    assert result["failed"] == 0
    assert result["total_users"] == 2


@pytest.mark.asyncio
async def test_send_daily_briefs_no_brief_found(
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates,
    mock_api_client
):
    """Test handling when daily brief is not found."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    service.api_client = mock_api_client
    
    # Mock API client to return None (no brief found)
    mock_api_client.get_daily_brief.return_value = None
    
    result = await service.send_daily_briefs()
    
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert result["sent"] == 0


@pytest.mark.asyncio
async def test_send_daily_briefs_with_failures(
    sample_email_preferences,
    sample_daily_brief,
    mock_bigquery_client,
    mock_sendgrid_client,
    mock_email_templates,
    mock_api_client
):
    """Test handling partial failures when sending to multiple users."""
    service = EmailService()
    service.bq_client = mock_bigquery_client
    service.sendgrid_client = mock_sendgrid_client
    service.templates = mock_email_templates
    service.api_client = mock_api_client
    
    # Mock API client to return daily brief
    mock_api_client.get_daily_brief.return_value = sample_daily_brief
    
    # Mock BigQuery to return multiple users
    user1 = sample_email_preferences.model_copy()
    user1.user_id = "user_1"
    user1.email = "user1@example.com"
    
    user2 = sample_email_preferences.model_copy()
    user2.user_id = "user_2"
    user2.email = "user2@example.com"
    
    mock_bigquery_client.get_users_for_daily_brief.return_value = [user1, user2]
    
    # Make sendgrid fail for second user
    mock_sendgrid_client.send_email.side_effect = [
        "email_1",  # Success for first user
        Exception("SendGrid error")  # Failure for second user
    ]
    
    result = await service.send_daily_briefs()
    
    assert result["success"] is True
    assert result["sent"] == 1
    assert result["failed"] == 1
    assert result["total_users"] == 2


def test_is_in_quiet_hours():
    """Test quiet hours detection."""
    service = EmailService()
    
    # Test with quiet hours 22:00 - 08:00
    prefs = EmailPreferences(
        user_id="user_123",
        email="test@example.com",
        quiet_hours=QuietHours(start="22:00", end="08:00")
    )
    
    # Mock current time to be within quiet hours
    with patch('src.email_service.datetime') as mock_datetime:
        # 23:00 - should be in quiet hours
        mock_datetime.utcnow.return_value.time.return_value = time(23, 0, 0)
        assert service._is_in_quiet_hours(prefs) is True
        
        # 02:00 - should be in quiet hours
        mock_datetime.utcnow.return_value.time.return_value = time(2, 0, 0)
        assert service._is_in_quiet_hours(prefs) is True
        
        # 10:00 - should not be in quiet hours
        mock_datetime.utcnow.return_value.time.return_value = time(10, 0, 0)
        assert service._is_in_quiet_hours(prefs) is False


def test_is_in_quiet_hours_no_config():
    """Test quiet hours when not configured."""
    service = EmailService()
    
    prefs = EmailPreferences(
        user_id="user_123",
        email="test@example.com",
        quiet_hours=None
    )
    
    assert service._is_in_quiet_hours(prefs) is False
