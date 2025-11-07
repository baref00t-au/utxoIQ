"""Pytest configuration and fixtures."""
import pytest
from datetime import datetime
from typing import List
from unittest.mock import Mock, AsyncMock

from src.models import (
    EmailPreferences,
    DailyBrief,
    Insight,
    Citation,
    EmailFrequency,
    SignalType,
    QuietHours
)


@pytest.fixture
def sample_citation():
    """Sample citation for testing."""
    return Citation(
        type="block",
        id="800000",
        description="Block height reference",
        url="https://blockstream.info/block/800000"
    )


@pytest.fixture
def sample_insight(sample_citation):
    """Sample insight for testing."""
    return Insight(
        id="insight_123",
        signal_type="mempool",
        headline="Mempool fees spike to 50 sat/vB",
        summary="Bitcoin mempool fees have increased significantly due to high transaction volume.",
        confidence=0.85,
        timestamp=datetime(2025, 11, 6, 10, 30, 0),
        block_height=800000,
        evidence=[sample_citation],
        chart_url="https://storage.googleapis.com/charts/mempool_123.png",
        tags=["mempool", "fees"]
    )


@pytest.fixture
def sample_daily_brief(sample_insight):
    """Sample daily brief for testing."""
    return DailyBrief(
        date="2025-11-06",
        insights=[sample_insight],
        summary="Today's top blockchain events"
    )


@pytest.fixture
def sample_email_preferences():
    """Sample email preferences for testing."""
    return EmailPreferences(
        user_id="user_123",
        email="test@example.com",
        daily_brief_enabled=True,
        frequency=EmailFrequency.DAILY,
        signal_filters=[SignalType.MEMPOOL, SignalType.EXCHANGE],
        quiet_hours=None
    )


@pytest.fixture
def sample_email_preferences_with_quiet_hours():
    """Sample email preferences with quiet hours."""
    return EmailPreferences(
        user_id="user_456",
        email="test2@example.com",
        daily_brief_enabled=True,
        frequency=EmailFrequency.DAILY,
        signal_filters=[],
        quiet_hours=QuietHours(start="22:00", end="08:00")
    )


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client."""
    mock = Mock()
    mock.get_preferences = Mock(return_value=None)
    mock.save_preferences = Mock()
    mock.get_users_for_daily_brief = Mock(return_value=[])
    mock.track_engagement = Mock()
    mock.get_engagement_stats = Mock(return_value={})
    return mock


@pytest.fixture
def mock_sendgrid_client():
    """Mock SendGrid client."""
    mock = Mock()
    mock.send_email = Mock(return_value="email_123")
    mock.handle_webhook_event = Mock()
    return mock


@pytest.fixture
def mock_api_client():
    """Mock API client."""
    mock = Mock()
    mock.get_daily_brief = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_email_templates():
    """Mock email templates."""
    mock = Mock()
    mock.render_daily_brief = Mock(return_value="<html>Test Email</html>")
    mock.render_plain_text = Mock(return_value="Test Email Plain Text")
    return mock
