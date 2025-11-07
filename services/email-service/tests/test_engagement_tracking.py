"""Tests for email engagement tracking."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.models import EmailEngagement, EmailEvent
from src.sendgrid_client import SendGridClient


@patch('src.sendgrid_client.SendGridAPIClient')
@patch('src.sendgrid_client.BigQueryClient')
def test_track_email_delivery(mock_bq_client_class, mock_sg_client_class):
    """Test tracking email delivery event."""
    mock_bq_client = Mock()
    mock_bq_client_class.return_value = mock_bq_client
    
    client = SendGridClient()
    
    # Mock successful send
    mock_response = Mock()
    mock_response.status_code = 202
    mock_sg_client_class.return_value.send.return_value = mock_response
    
    email_id = client.send_email(
        to_email="test@example.com",
        subject="Test Email",
        html_content="<html>Test</html>",
        plain_text_content="Test",
        user_id="user_123"
    )
    
    # Verify engagement was tracked
    assert mock_bq_client.track_engagement.called
    engagement = mock_bq_client.track_engagement.call_args[0][0]
    assert engagement.event == EmailEvent.DELIVERED
    assert engagement.user_id == "user_123"


@patch('src.sendgrid_client.SendGridAPIClient')
@patch('src.sendgrid_client.BigQueryClient')
def test_handle_open_event(mock_bq_client_class, mock_sg_client_class):
    """Test handling email open event from webhook."""
    mock_bq_client = Mock()
    mock_bq_client_class.return_value = mock_bq_client
    
    client = SendGridClient()
    
    event_data = {
        "event": "open",
        "email": "test@example.com",
        "user_id": "user_123",
        "email_id": "email_456",
        "timestamp": 1699372800
    }
    
    client.handle_webhook_event(event_data)
    
    # Verify engagement was tracked
    assert mock_bq_client.track_engagement.called
    engagement = mock_bq_client.track_engagement.call_args[0][0]
    assert engagement.event == EmailEvent.OPENED
    assert engagement.user_id == "user_123"
    assert engagement.email_id == "email_456"


@patch('src.sendgrid_client.SendGridAPIClient')
@patch('src.sendgrid_client.BigQueryClient')
def test_handle_click_event(mock_bq_client_class, mock_sg_client_class):
    """Test handling email click event from webhook."""
    mock_bq_client = Mock()
    mock_bq_client_class.return_value = mock_bq_client
    
    client = SendGridClient()
    
    event_data = {
        "event": "click",
        "email": "test@example.com",
        "user_id": "user_123",
        "email_id": "email_456",
        "url": "https://utxoiq.com/insight/123",
        "timestamp": 1699372800
    }
    
    client.handle_webhook_event(event_data)
    
    # Verify engagement was tracked
    assert mock_bq_client.track_engagement.called
    engagement = mock_bq_client.track_engagement.call_args[0][0]
    assert engagement.event == EmailEvent.CLICKED
    assert engagement.metadata is not None


@patch('src.sendgrid_client.SendGridAPIClient')
@patch('src.sendgrid_client.BigQueryClient')
def test_handle_bounce_event(mock_bq_client_class, mock_sg_client_class):
    """Test handling email bounce event from webhook."""
    mock_bq_client = Mock()
    mock_bq_client_class.return_value = mock_bq_client
    
    client = SendGridClient()
    
    event_data = {
        "event": "bounce",
        "email": "test@example.com",
        "user_id": "user_123",
        "email_id": "email_456",
        "reason": "Invalid email address",
        "timestamp": 1699372800
    }
    
    client.handle_webhook_event(event_data)
    
    # Verify engagement was tracked
    assert mock_bq_client.track_engagement.called
    engagement = mock_bq_client.track_engagement.call_args[0][0]
    assert engagement.event == EmailEvent.BOUNCED


@patch('src.sendgrid_client.SendGridAPIClient')
@patch('src.sendgrid_client.BigQueryClient')
def test_handle_unsubscribe_event(mock_bq_client_class, mock_sg_client_class):
    """Test handling unsubscribe event from webhook."""
    mock_bq_client = Mock()
    mock_bq_client_class.return_value = mock_bq_client
    
    client = SendGridClient()
    
    event_data = {
        "event": "unsubscribe",
        "email": "test@example.com",
        "user_id": "user_123",
        "email_id": "email_456",
        "timestamp": 1699372800
    }
    
    client.handle_webhook_event(event_data)
    
    # Verify engagement was tracked
    assert mock_bq_client.track_engagement.called
    engagement = mock_bq_client.track_engagement.call_args[0][0]
    assert engagement.event == EmailEvent.UNSUBSCRIBED


@patch('src.sendgrid_client.SendGridAPIClient')
@patch('src.sendgrid_client.BigQueryClient')
def test_handle_unknown_event(mock_bq_client_class, mock_sg_client_class):
    """Test handling unknown event type from webhook."""
    mock_bq_client = Mock()
    mock_bq_client_class.return_value = mock_bq_client
    
    client = SendGridClient()
    
    event_data = {
        "event": "unknown_event",
        "email": "test@example.com",
        "user_id": "user_123",
        "email_id": "email_456"
    }
    
    # Should not raise exception
    client.handle_webhook_event(event_data)
    
    # Should not track unknown events
    assert not mock_bq_client.track_engagement.called


@patch('src.bigquery_client.bigquery.Client')
def test_get_engagement_stats(mock_bq_client):
    """Test getting engagement statistics from BigQuery."""
    from src.bigquery_client import BigQueryClient
    
    # Mock query result
    mock_row1 = Mock()
    mock_row1.event = "delivered"
    mock_row1.count = 100
    
    mock_row2 = Mock()
    mock_row2.event = "opened"
    mock_row2.count = 75
    
    mock_row3 = Mock()
    mock_row3.event = "clicked"
    mock_row3.count = 30
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([mock_row1, mock_row2, mock_row3]))
    mock_bq_client.return_value.query.return_value.result.return_value = mock_result
    
    client = BigQueryClient()
    stats = client.get_engagement_stats(user_id="user_123", days=30)
    
    assert stats["delivered"] == 100
    assert stats["opened"] == 75
    assert stats["clicked"] == 30


@patch('src.bigquery_client.bigquery.Client')
def test_track_engagement_to_bigquery(mock_bq_client):
    """Test tracking engagement event to BigQuery."""
    from src.bigquery_client import BigQueryClient
    
    mock_bq_client.return_value.insert_rows_json.return_value = []
    
    client = BigQueryClient()
    
    engagement = EmailEngagement(
        email_id="email_123",
        user_id="user_456",
        event=EmailEvent.OPENED,
        metadata={"ip": "192.168.1.1"}
    )
    
    client.track_engagement(engagement)
    
    # Verify insert was called
    assert mock_bq_client.return_value.insert_rows_json.called
    
    # Verify data format
    call_args = mock_bq_client.return_value.insert_rows_json.call_args
    rows = call_args[0][1]
    assert len(rows) == 1
    assert rows[0]["email_id"] == "email_123"
    assert rows[0]["user_id"] == "user_456"
    assert rows[0]["event"] == "opened"
