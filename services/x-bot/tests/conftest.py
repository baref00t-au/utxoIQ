"""Pytest configuration and fixtures."""
import os
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, date
from typing import List

# Set test environment variables before importing any src modules
os.environ['X_API_KEY'] = 'test_key'
os.environ['X_API_SECRET'] = 'test_secret'
os.environ['X_ACCESS_TOKEN'] = 'test_token'
os.environ['X_ACCESS_TOKEN_SECRET'] = 'test_token_secret'
os.environ['X_BEARER_TOKEN'] = 'test_bearer'
os.environ['GCP_PROJECT_ID'] = 'test_project'
os.environ['WEB_API_KEY'] = 'test_api_key'

from src.models import Insight, SignalType, Citation, DailyBrief


@pytest.fixture
def mock_insight():
    """Create a mock insight for testing."""
    return Insight(
        id="test-insight-123",
        signal_type=SignalType.MEMPOOL,
        headline="Mempool fees spike to 150 sat/vB",
        summary="Average fee rates increased 3x in the last hour due to high transaction volume.",
        confidence=0.85,
        timestamp=datetime.utcnow(),
        block_height=820000,
        evidence=[
            Citation(
                type="block",
                id="820000",
                description="Block with high fees",
                url="https://mempool.space/block/820000"
            )
        ],
        chart_url="https://storage.googleapis.com/utxoiq-charts/chart-123.png",
        tags=["mempool", "fees"],
        is_predictive=False
    )


@pytest.fixture
def mock_insights():
    """Create multiple mock insights for testing."""
    return [
        Insight(
            id=f"insight-{i}",
            signal_type=SignalType.MEMPOOL if i % 2 == 0 else SignalType.EXCHANGE,
            headline=f"Test insight {i}",
            summary=f"Summary for insight {i}",
            confidence=0.7 + (i * 0.05),
            timestamp=datetime.utcnow(),
            block_height=820000 + i,
            evidence=[],
            chart_url=f"https://storage.googleapis.com/utxoiq-charts/chart-{i}.png",
            tags=["test"],
            is_predictive=False
        )
        for i in range(5)
    ]


@pytest.fixture
def mock_daily_brief(mock_insights):
    """Create a mock daily brief for testing."""
    return DailyBrief(
        date=date.today().isoformat(),
        top_insights=mock_insights[:3],
        summary="Top 3 blockchain events from the past 24 hours"
    )


@pytest.fixture
def mock_x_client():
    """Create a mock X client."""
    client = Mock()
    client.upload_media = Mock(return_value="media-123")
    client.post_tweet = Mock(return_value="tweet-123")
    client.post_thread = Mock(return_value=["tweet-1", "tweet-2", "tweet-3"])
    return client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock()
    client.mark_insight_posted = Mock(return_value=True)
    client.is_insight_posted = Mock(return_value=False)
    client.is_signal_recently_posted = Mock(return_value=False)
    client.get_last_daily_brief_date = Mock(return_value=None)
    client.set_last_daily_brief_date = Mock(return_value=True)
    return client


@pytest.fixture
def mock_api_client(mock_insights, mock_daily_brief):
    """Create a mock API client."""
    client = Mock()
    client.get_publishable_insights = AsyncMock(return_value=mock_insights)
    client.get_daily_brief = AsyncMock(return_value=mock_daily_brief)
    client.download_chart_image = AsyncMock(return_value=b"fake-image-data")
    return client


@pytest.fixture
def chart_image_bytes():
    """Create fake chart image bytes for testing."""
    return b"fake-png-image-data"
