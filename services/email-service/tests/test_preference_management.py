"""Tests for email preference management."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.models import EmailPreferences, EmailFrequency, SignalType, QuietHours


def test_create_new_preferences():
    """Test creating new email preferences."""
    prefs = EmailPreferences(
        user_id="user_123",
        email="test@example.com",
        daily_brief_enabled=True,
        frequency=EmailFrequency.DAILY,
        signal_filters=[SignalType.MEMPOOL]
    )
    
    assert prefs.user_id == "user_123"
    assert prefs.email == "test@example.com"
    assert prefs.daily_brief_enabled is True
    assert prefs.frequency == EmailFrequency.DAILY
    assert SignalType.MEMPOOL in prefs.signal_filters


def test_preferences_with_quiet_hours():
    """Test preferences with quiet hours configuration."""
    quiet_hours = QuietHours(start="22:00", end="08:00")
    
    prefs = EmailPreferences(
        user_id="user_123",
        email="test@example.com",
        daily_brief_enabled=True,
        frequency=EmailFrequency.DAILY,
        signal_filters=[],
        quiet_hours=quiet_hours
    )
    
    assert prefs.quiet_hours is not None
    assert prefs.quiet_hours.start == "22:00"
    assert prefs.quiet_hours.end == "08:00"


def test_preferences_default_values():
    """Test default values for preferences."""
    prefs = EmailPreferences(
        user_id="user_123",
        email="test@example.com"
    )
    
    assert prefs.daily_brief_enabled is True
    assert prefs.frequency == EmailFrequency.DAILY
    assert prefs.signal_filters == []
    assert prefs.quiet_hours is None


def test_frequency_enum_values():
    """Test email frequency enum values."""
    assert EmailFrequency.DAILY.value == "daily"
    assert EmailFrequency.WEEKLY.value == "weekly"
    assert EmailFrequency.NEVER.value == "never"


def test_signal_type_enum_values():
    """Test signal type enum values."""
    assert SignalType.MEMPOOL.value == "mempool"
    assert SignalType.EXCHANGE.value == "exchange"
    assert SignalType.MINER.value == "miner"
    assert SignalType.WHALE.value == "whale"


@patch('src.bigquery_client.bigquery.Client')
def test_save_preferences_to_bigquery(mock_bq_client, sample_email_preferences):
    """Test saving preferences to BigQuery."""
    from src.bigquery_client import BigQueryClient
    
    client = BigQueryClient()
    client.save_preferences(sample_email_preferences)
    
    # Verify query was called
    assert mock_bq_client.return_value.query.called


@patch('src.bigquery_client.bigquery.Client')
def test_get_preferences_from_bigquery(mock_bq_client):
    """Test retrieving preferences from BigQuery."""
    from src.bigquery_client import BigQueryClient
    
    # Mock query result
    mock_row = Mock()
    mock_row.user_id = "user_123"
    mock_row.email = "test@example.com"
    mock_row.daily_brief_enabled = True
    mock_row.frequency = "daily"
    mock_row.signal_filters_json = '["mempool"]'
    mock_row.quiet_hours_json = None
    mock_row.created_at = datetime.utcnow()
    mock_row.updated_at = datetime.utcnow()
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([mock_row]))
    mock_bq_client.return_value.query.return_value.result.return_value = mock_result
    
    client = BigQueryClient()
    prefs = client.get_preferences("user_123")
    
    assert prefs is not None
    assert prefs.user_id == "user_123"
    assert prefs.email == "test@example.com"


@patch('src.bigquery_client.bigquery.Client')
def test_get_users_for_daily_brief(mock_bq_client):
    """Test getting users subscribed to daily brief."""
    from src.bigquery_client import BigQueryClient
    
    # Mock query result with multiple users
    mock_row1 = Mock()
    mock_row1.user_id = "user_1"
    mock_row1.email = "user1@example.com"
    mock_row1.daily_brief_enabled = True
    mock_row1.frequency = "daily"
    mock_row1.signal_filters_json = None
    mock_row1.quiet_hours_json = None
    mock_row1.created_at = datetime.utcnow()
    mock_row1.updated_at = datetime.utcnow()
    
    mock_row2 = Mock()
    mock_row2.user_id = "user_2"
    mock_row2.email = "user2@example.com"
    mock_row2.daily_brief_enabled = True
    mock_row2.frequency = "daily"
    mock_row2.signal_filters_json = None
    mock_row2.quiet_hours_json = None
    mock_row2.created_at = datetime.utcnow()
    mock_row2.updated_at = datetime.utcnow()
    
    mock_result = Mock()
    mock_result.__iter__ = Mock(return_value=iter([mock_row1, mock_row2]))
    mock_bq_client.return_value.query.return_value.result.return_value = mock_result
    
    client = BigQueryClient()
    users = client.get_users_for_daily_brief()
    
    assert len(users) == 2
    assert users[0].user_id == "user_1"
    assert users[1].user_id == "user_2"
