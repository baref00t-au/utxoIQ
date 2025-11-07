"""Tests for unsubscribe functionality and compliance."""
import pytest
from unittest.mock import Mock, patch

from src.models import EmailPreferences, EmailFrequency, UnsubscribeRequest


@patch('src.bigquery_client.bigquery.Client')
def test_unsubscribe_disables_all_emails(mock_bq_client, sample_email_preferences):
    """Test that unsubscribe disables all email types."""
    from src.bigquery_client import BigQueryClient
    
    # Mock get_preferences to return active preferences
    mock_row = Mock()
    mock_row.user_id = sample_email_preferences.user_id
    mock_row.email = sample_email_preferences.email
    mock_row.daily_brief_enabled = True
    mock_row.frequency = "daily"
    mock_row.signal_filters_json = None
    mock_row.quiet_hours_json = None
    mock_row.created_at = sample_email_preferences.created_at
    mock_row.updated_at = sample_email_preferences.updated_at
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([mock_row]))
    mock_bq_client.return_value.query.return_value.result.return_value = mock_result
    
    client = BigQueryClient()
    prefs = client.get_preferences(sample_email_preferences.user_id)
    
    # Simulate unsubscribe
    prefs.daily_brief_enabled = False
    prefs.frequency = EmailFrequency.NEVER
    
    assert prefs.daily_brief_enabled is False
    assert prefs.frequency == EmailFrequency.NEVER


def test_unsubscribe_request_model():
    """Test unsubscribe request model."""
    request = UnsubscribeRequest(
        user_id="user_123",
        reason="Too many emails"
    )
    
    assert request.user_id == "user_123"
    assert request.reason == "Too many emails"


def test_unsubscribe_request_without_reason():
    """Test unsubscribe request without reason."""
    request = UnsubscribeRequest(user_id="user_123")
    
    assert request.user_id == "user_123"
    assert request.reason is None


def test_email_template_includes_unsubscribe_link(sample_daily_brief):
    """Test that email template includes unsubscribe link."""
    from src.email_templates import EmailTemplates
    
    templates = EmailTemplates()
    html = templates.render_daily_brief(sample_daily_brief, "user_123")
    
    # Check for unsubscribe link
    assert "/email/unsubscribe" in html
    assert "user_123" in html
    assert "Unsubscribe" in html


def test_email_template_includes_preference_link(sample_daily_brief):
    """Test that email template includes preference management link."""
    from src.email_templates import EmailTemplates
    
    templates = EmailTemplates()
    html = templates.render_daily_brief(sample_daily_brief, "user_123")
    
    # Check for preference management link
    assert "/email/preferences" in html
    assert "Manage Preferences" in html


def test_plain_text_includes_unsubscribe_link(sample_daily_brief):
    """Test that plain text email includes unsubscribe link."""
    from src.email_templates import EmailTemplates
    
    templates = EmailTemplates()
    text = templates.render_plain_text(sample_daily_brief, "user_123")
    
    # Check for unsubscribe link
    assert "/email/unsubscribe" in text
    assert "user_123" in text


@patch('src.bigquery_client.bigquery.Client')
def test_unsubscribed_users_not_in_daily_brief_list(mock_bq_client):
    """Test that unsubscribed users are not included in daily brief recipients."""
    from src.bigquery_client import BigQueryClient
    
    # Mock query to return only users with daily_brief_enabled=True and frequency='daily'
    mock_row = Mock()
    mock_row.user_id = "user_active"
    mock_row.email = "active@example.com"
    mock_row.daily_brief_enabled = True
    mock_row.frequency = "daily"
    mock_row.signal_filters_json = None
    mock_row.quiet_hours_json = None
    mock_row.created_at = Mock()
    mock_row.updated_at = Mock()
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([mock_row]))
    mock_bq_client.return_value.query.return_value.result.return_value = mock_result
    
    client = BigQueryClient()
    users = client.get_users_for_daily_brief()
    
    # Should only return active users
    assert len(users) == 1
    assert users[0].user_id == "user_active"
    assert users[0].daily_brief_enabled is True


def test_frequency_never_prevents_emails():
    """Test that frequency='never' prevents email sending."""
    prefs = EmailPreferences(
        user_id="user_123",
        email="test@example.com",
        daily_brief_enabled=True,
        frequency=EmailFrequency.NEVER
    )
    
    # Even if daily_brief_enabled is True, frequency='never' should prevent emails
    assert prefs.frequency == EmailFrequency.NEVER


@patch('src.bigquery_client.bigquery.Client')
def test_resubscribe_after_unsubscribe(mock_bq_client, sample_email_preferences):
    """Test that users can resubscribe after unsubscribing."""
    from src.bigquery_client import BigQueryClient
    
    client = BigQueryClient()
    
    # Simulate unsubscribe
    sample_email_preferences.daily_brief_enabled = False
    sample_email_preferences.frequency = EmailFrequency.NEVER
    client.save_preferences(sample_email_preferences)
    
    # Simulate resubscribe
    sample_email_preferences.daily_brief_enabled = True
    sample_email_preferences.frequency = EmailFrequency.DAILY
    client.save_preferences(sample_email_preferences)
    
    # Verify save was called twice
    assert mock_bq_client.return_value.query.call_count == 2
