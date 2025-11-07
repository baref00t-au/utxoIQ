"""Tests for posting service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.posting_service import PostingService
from src.models import PostResult


class TestPostingService:
    """Test cases for PostingService."""
    
    @pytest.fixture
    def posting_service(self, mock_x_client, mock_redis_client, mock_api_client):
        """Create posting service with mocked dependencies."""
        with patch('src.posting_service.XClient', return_value=mock_x_client), \
             patch('src.posting_service.RedisClient', return_value=mock_redis_client), \
             patch('src.posting_service.APIClient', return_value=mock_api_client):
            service = PostingService()
            return service
    
    def test_compose_tweet(self, posting_service, mock_insight):
        """Test tweet composition from insight."""
        tweet = posting_service.compose_tweet(mock_insight)
        
        # Check tweet contains key elements
        assert mock_insight.headline in tweet
        assert "85%" in tweet  # Confidence
        assert "820000" in tweet  # Block height
        assert "utxoiq.com/insight/" in tweet  # Link
        assert len(tweet) <= 280  # Twitter character limit
    
    def test_compose_tweet_truncates_long_headline(self, posting_service, mock_insight):
        """Test that long headlines are truncated to fit 280 characters."""
        # Create insight with very long headline
        mock_insight.headline = "A" * 300
        
        tweet = posting_service.compose_tweet(mock_insight)
        
        assert len(tweet) <= 280
        assert "..." in tweet  # Truncation indicator
    
    def test_should_post_insight_success(self, posting_service, mock_insight):
        """Test should_post_insight returns True for valid insight."""
        should_post, reason = posting_service.should_post_insight(mock_insight)
        
        assert should_post is True
        assert reason == "Ready to post"
    
    def test_should_post_insight_low_confidence(self, posting_service, mock_insight):
        """Test should_post_insight rejects low confidence insights."""
        mock_insight.confidence = 0.5  # Below threshold
        
        should_post, reason = posting_service.should_post_insight(mock_insight)
        
        assert should_post is False
        assert "below threshold" in reason
    
    def test_should_post_insight_already_posted(self, posting_service, mock_insight, mock_redis_client):
        """Test should_post_insight rejects already posted insights."""
        mock_redis_client.is_insight_posted.return_value = True
        
        should_post, reason = posting_service.should_post_insight(mock_insight)
        
        assert should_post is False
        assert "already posted" in reason
    
    def test_should_post_insight_duplicate_signal(self, posting_service, mock_insight, mock_redis_client):
        """Test should_post_insight rejects duplicate signal types."""
        mock_redis_client.is_signal_recently_posted.return_value = True
        
        should_post, reason = posting_service.should_post_insight(mock_insight)
        
        assert should_post is False
        assert "duplicate prevention" in reason
    
    @pytest.mark.asyncio
    async def test_post_insight_success(self, posting_service, mock_insight, mock_x_client, mock_redis_client):
        """Test successful insight posting."""
        result = await posting_service.post_insight(mock_insight)
        
        assert result.success is True
        assert result.tweet_id == "tweet-123"
        assert result.insight_id == mock_insight.id
        
        # Verify X client was called
        mock_x_client.upload_media.assert_called_once()
        mock_x_client.post_tweet.assert_called_once()
        
        # Verify Redis marking
        mock_redis_client.mark_insight_posted.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_insight_without_chart(self, posting_service, mock_insight, mock_x_client):
        """Test posting insight without chart image."""
        mock_insight.chart_url = None
        
        result = await posting_service.post_insight(mock_insight)
        
        assert result.success is True
        
        # Verify media upload was not called
        mock_x_client.upload_media.assert_not_called()
        
        # Verify tweet was posted without media
        call_args = mock_x_client.post_tweet.call_args
        assert call_args[1]['media_ids'] is None
    
    @pytest.mark.asyncio
    async def test_post_insight_failed_tweet(self, posting_service, mock_insight, mock_x_client):
        """Test handling of failed tweet posting."""
        mock_x_client.post_tweet.return_value = None  # Simulate failure
        
        result = await posting_service.post_insight(mock_insight)
        
        assert result.success is False
        assert result.error == "Failed to post tweet"
    
    @pytest.mark.asyncio
    async def test_process_hourly_insights(self, posting_service, mock_insights):
        """Test hourly insight processing."""
        results = await posting_service.process_hourly_insights()
        
        assert len(results) == len(mock_insights)
        
        # Check that all results are PostResult objects
        for result in results:
            assert isinstance(result, PostResult)
    
    @pytest.mark.asyncio
    async def test_process_hourly_insights_no_insights(self, posting_service, mock_api_client):
        """Test hourly processing with no available insights."""
        mock_api_client.get_publishable_insights.return_value = []
        
        results = await posting_service.process_hourly_insights()
        
        assert len(results) == 0
