"""Tests for rate limiting and duplicate prevention."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from src.posting_service import PostingService
from src.models import SignalType


class TestRateLimiting:
    """Test cases for rate limiting and duplicate prevention."""
    
    @pytest.fixture
    def posting_service(self, mock_x_client, mock_redis_client, mock_api_client):
        """Create posting service with mocked dependencies."""
        with patch('src.posting_service.XClient', return_value=mock_x_client), \
             patch('src.posting_service.RedisClient', return_value=mock_redis_client), \
             patch('src.posting_service.APIClient', return_value=mock_api_client):
            service = PostingService()
            return service
    
    def test_duplicate_prevention_by_insight_id(self, posting_service, mock_insight, mock_redis_client):
        """Test that duplicate insights are prevented by ID."""
        # First check - should pass
        mock_redis_client.is_insight_posted.return_value = False
        should_post, _ = posting_service.should_post_insight(mock_insight)
        assert should_post is True
        
        # Second check - should fail (already posted)
        mock_redis_client.is_insight_posted.return_value = True
        should_post, reason = posting_service.should_post_insight(mock_insight)
        assert should_post is False
        assert "already posted" in reason
    
    def test_duplicate_prevention_by_signal_type(self, posting_service, mock_insight, mock_redis_client):
        """Test that duplicate signal types are prevented within window."""
        # First insight of type - should pass
        mock_redis_client.is_signal_recently_posted.return_value = False
        should_post, _ = posting_service.should_post_insight(mock_insight)
        assert should_post is True
        
        # Second insight of same type within window - should fail
        mock_redis_client.is_signal_recently_posted.return_value = True
        should_post, reason = posting_service.should_post_insight(mock_insight)
        assert should_post is False
        assert "duplicate prevention" in reason
    
    def test_different_signal_types_allowed(self, posting_service, mock_insights, mock_redis_client):
        """Test that different signal types can be posted simultaneously."""
        # Mock Redis to allow different signal types
        def is_signal_posted(signal_type):
            # Only mempool is recently posted
            return signal_type == SignalType.MEMPOOL.value
        
        mock_redis_client.is_signal_recently_posted.side_effect = is_signal_posted
        
        # Mempool insight should be blocked
        mempool_insight = mock_insights[0]  # Even index = mempool
        should_post, _ = posting_service.should_post_insight(mempool_insight)
        assert should_post is False
        
        # Exchange insight should be allowed
        exchange_insight = mock_insights[1]  # Odd index = exchange
        should_post, _ = posting_service.should_post_insight(exchange_insight)
        assert should_post is True
    
    @pytest.mark.asyncio
    async def test_redis_marking_after_successful_post(self, posting_service, mock_insight, mock_redis_client):
        """Test that Redis is marked after successful post."""
        await posting_service.post_insight(mock_insight)
        
        # Verify Redis was called to mark as posted
        mock_redis_client.mark_insight_posted.assert_called_once_with(
            mock_insight.id,
            mock_insight.signal_type.value
        )
    
    @pytest.mark.asyncio
    async def test_redis_not_marked_after_failed_post(self, posting_service, mock_insight, mock_x_client, mock_redis_client):
        """Test that Redis is not marked after failed post."""
        # Simulate failed post
        mock_x_client.post_tweet.return_value = None
        
        await posting_service.post_insight(mock_insight)
        
        # Verify Redis was NOT called to mark as posted
        mock_redis_client.mark_insight_posted.assert_not_called()
    
    def test_confidence_threshold_filtering(self, posting_service, mock_insight):
        """Test that insights below confidence threshold are filtered."""
        # High confidence - should pass
        mock_insight.confidence = 0.85
        should_post, _ = posting_service.should_post_insight(mock_insight)
        assert should_post is True
        
        # At threshold - should pass
        mock_insight.confidence = 0.7
        should_post, _ = posting_service.should_post_insight(mock_insight)
        assert should_post is True
        
        # Below threshold - should fail
        mock_insight.confidence = 0.65
        should_post, reason = posting_service.should_post_insight(mock_insight)
        assert should_post is False
        assert "below threshold" in reason
    
    @pytest.mark.asyncio
    async def test_hourly_processing_respects_filters(self, posting_service, mock_insights, mock_redis_client):
        """Test that hourly processing respects all filters."""
        # Set up Redis to block some insights
        posted_ids = {mock_insights[0].id, mock_insights[2].id}
        mock_redis_client.is_insight_posted.side_effect = lambda id: id in posted_ids
        
        results = await posting_service.process_hourly_insights()
        
        # Should have results for all insights
        assert len(results) == len(mock_insights)
        
        # But only some should be successful (not the blocked ones)
        successful = [r for r in results if r.success]
        assert len(successful) < len(mock_insights)
