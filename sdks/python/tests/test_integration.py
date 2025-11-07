"""Integration tests for Python SDK.

These tests verify end-to-end functionality with the API.
They are skipped by default and require a valid API key.
Run with: pytest -m integration --api-key=YOUR_KEY
"""
import pytest
import os
from datetime import date
from utxoiq import UtxoIQClient


@pytest.fixture
def api_key():
    """Get API key from environment or pytest option."""
    return os.getenv("UTXOIQ_API_KEY") or pytest.config.getoption("--api-key", default=None)


@pytest.fixture
def client(api_key):
    """Create authenticated client."""
    if not api_key:
        pytest.skip("API key not provided")
    return UtxoIQClient(api_key=api_key)


@pytest.fixture
def guest_client():
    """Create unauthenticated client for Guest Mode."""
    return UtxoIQClient()


@pytest.mark.integration
class TestInsightsIntegration:
    """Integration tests for insights endpoints."""
    
    def test_get_latest_insights(self, client):
        """Test getting latest insights."""
        insights = client.insights.get_latest(limit=5)
        assert isinstance(insights, list)
        assert len(insights) <= 5
        if insights:
            assert hasattr(insights[0], 'id')
            assert hasattr(insights[0], 'headline')
            assert hasattr(insights[0], 'confidence')
    
    def test_get_public_insights_guest_mode(self, guest_client):
        """Test getting public insights without authentication."""
        insights = guest_client.insights.get_public(limit=10)
        assert isinstance(insights, list)
        assert len(insights) <= 20  # Guest Mode limit
    
    def test_get_insight_by_id(self, client):
        """Test getting specific insight."""
        # First get latest to get a valid ID
        insights = client.insights.get_latest(limit=1)
        if insights:
            insight_id = insights[0].id
            insight = client.insights.get_by_id(insight_id)
            assert insight.id == insight_id
    
    def test_filter_by_category(self, client):
        """Test filtering insights by category."""
        insights = client.insights.get_latest(
            limit=10,
            category="mempool"
        )
        assert isinstance(insights, list)
        if insights:
            assert all(i.signal_type == "mempool" for i in insights)
    
    def test_filter_by_confidence(self, client):
        """Test filtering insights by minimum confidence."""
        insights = client.insights.get_latest(
            limit=10,
            min_confidence=0.8
        )
        assert isinstance(insights, list)
        if insights:
            assert all(i.confidence >= 0.8 for i in insights)


@pytest.mark.integration
class TestAlertsIntegration:
    """Integration tests for alerts endpoints."""
    
    def test_create_and_delete_alert(self, client):
        """Test creating and deleting an alert."""
        # Create alert
        alert = client.alerts.create(
            signal_type="mempool",
            threshold=100.0,
            operator="gt"
        )
        assert alert.id is not None
        assert alert.signal_type == "mempool"
        
        # Delete alert
        result = client.alerts.delete(alert.id)
        assert result is True
    
    def test_list_alerts(self, client):
        """Test listing user alerts."""
        alerts = client.alerts.list()
        assert isinstance(alerts, list)
    
    def test_update_alert(self, client):
        """Test updating an alert."""
        # Create alert first
        alert = client.alerts.create(
            signal_type="exchange",
            threshold=500.0,
            operator="gt"
        )
        
        # Update it
        updated = client.alerts.update(
            alert.id,
            threshold=750.0,
            is_active=False
        )
        assert updated.threshold == 750.0
        assert updated.is_active is False
        
        # Clean up
        client.alerts.delete(alert.id)


@pytest.mark.integration
class TestDailyBriefIntegration:
    """Integration tests for daily brief endpoints."""
    
    def test_get_latest_daily_brief(self, client):
        """Test getting latest daily brief."""
        brief = client.daily_brief.get_latest()
        assert brief.date is not None
        assert isinstance(brief.insights, list)
    
    def test_get_daily_brief_by_date(self, client):
        """Test getting daily brief for specific date."""
        today = date.today()
        brief = client.daily_brief.get_by_date(today)
        assert brief.date is not None


@pytest.mark.integration
class TestFeedbackIntegration:
    """Integration tests for feedback endpoints."""
    
    def test_get_accuracy_leaderboard(self, client):
        """Test getting accuracy leaderboard."""
        leaderboard = client.feedback.get_accuracy_leaderboard()
        assert isinstance(leaderboard, list)
        if leaderboard:
            assert hasattr(leaderboard[0], 'model_version')
            assert hasattr(leaderboard[0], 'accuracy_rating')


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    def test_invalid_api_key(self):
        """Test authentication error with invalid API key."""
        from utxoiq.exceptions import AuthenticationError
        
        client = UtxoIQClient(api_key="invalid-key")
        with pytest.raises(AuthenticationError):
            client.insights.get_latest()
    
    def test_not_found_error(self, client):
        """Test not found error."""
        from utxoiq.exceptions import NotFoundError
        
        with pytest.raises(NotFoundError):
            client.insights.get_by_id("nonexistent-id-12345")


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--api-key",
        action="store",
        default=None,
        help="API key for integration tests"
    )
