"""Tests for daily brief service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import date, datetime
from src.daily_brief_service import DailyBriefService


class TestDailyBriefService:
    """Test cases for DailyBriefService."""
    
    @pytest.fixture
    def daily_brief_service(self, mock_x_client, mock_redis_client, mock_api_client):
        """Create daily brief service with mocked dependencies."""
        with patch('src.daily_brief_service.XClient', return_value=mock_x_client), \
             patch('src.daily_brief_service.RedisClient', return_value=mock_redis_client), \
             patch('src.daily_brief_service.APIClient', return_value=mock_api_client):
            service = DailyBriefService()
            return service
    
    def test_compose_thread_intro(self, daily_brief_service, mock_daily_brief):
        """Test thread intro composition."""
        intro = daily_brief_service.compose_thread_intro(mock_daily_brief)
        
        assert "Bitcoin Pulse" in intro
        assert "Top 3 blockchain events" in intro
        assert "Thread below" in intro
        assert len(intro) <= 280
    
    def test_compose_insight_tweet(self, daily_brief_service, mock_insight):
        """Test insight tweet composition for thread."""
        tweet = daily_brief_service.compose_insight_tweet(mock_insight, 1)
        
        assert "1/" in tweet  # Thread numbering
        assert "MEMPOOL" in tweet  # Signal type
        assert mock_insight.headline in tweet
        assert "85%" in tweet  # Confidence
        assert "820000" in tweet  # Block height
        assert len(tweet) <= 280
    
    def test_compose_insight_tweet_truncates_long_summary(self, daily_brief_service, mock_insight):
        """Test that long summaries are truncated."""
        mock_insight.summary = "A" * 500  # Very long summary
        
        tweet = daily_brief_service.compose_insight_tweet(mock_insight, 1)
        
        assert len(tweet) <= 280
        assert "..." in tweet or len(mock_insight.summary) > len(tweet)
    
    def test_compose_thread_outro(self, daily_brief_service):
        """Test thread outro composition."""
        outro = daily_brief_service.compose_thread_outro()
        
        assert "utxoiq.com" in outro
        assert "follow" in outro.lower()
        assert len(outro) <= 280
    
    @pytest.mark.asyncio
    async def test_should_post_daily_brief_success(self, daily_brief_service, mock_redis_client):
        """Test should_post_daily_brief returns True when ready."""
        today = date.today()
        
        should_post, reason = await daily_brief_service.should_post_daily_brief(today)
        
        assert should_post is True
        assert reason == "Ready to post"
    
    @pytest.mark.asyncio
    async def test_should_post_daily_brief_already_posted(self, daily_brief_service, mock_redis_client):
        """Test should_post_daily_brief rejects already posted briefs."""
        today = date.today()
        mock_redis_client.get_last_daily_brief_date.return_value = today.isoformat()
        
        should_post, reason = await daily_brief_service.should_post_daily_brief(today)
        
        assert should_post is False
        assert "already posted" in reason
    
    @pytest.mark.asyncio
    async def test_should_post_daily_brief_not_available(self, daily_brief_service, mock_api_client):
        """Test should_post_daily_brief rejects when brief not available."""
        today = date.today()
        mock_api_client.get_daily_brief.return_value = None
        
        should_post, reason = await daily_brief_service.should_post_daily_brief(today)
        
        assert should_post is False
        assert "not available" in reason
    
    @pytest.mark.asyncio
    async def test_post_daily_brief_success(self, daily_brief_service, mock_x_client, mock_redis_client):
        """Test successful daily brief posting."""
        today = date.today()
        
        tweet_ids = await daily_brief_service.post_daily_brief(today)
        
        assert len(tweet_ids) > 0
        assert all(tid is not None for tid in tweet_ids)
        
        # Verify thread was posted
        mock_x_client.post_thread.assert_called_once()
        
        # Verify Redis was updated
        mock_redis_client.set_last_daily_brief_date.assert_called_once_with(today.isoformat())
    
    @pytest.mark.asyncio
    async def test_post_daily_brief_already_posted(self, daily_brief_service, mock_redis_client):
        """Test daily brief skips if already posted."""
        today = date.today()
        mock_redis_client.get_last_daily_brief_date.return_value = today.isoformat()
        
        tweet_ids = await daily_brief_service.post_daily_brief(today)
        
        assert len(tweet_ids) == 0
    
    @pytest.mark.asyncio
    async def test_post_daily_brief_thread_structure(self, daily_brief_service, mock_x_client, mock_daily_brief):
        """Test that daily brief thread has correct structure."""
        today = date.today()
        
        await daily_brief_service.post_daily_brief(today)
        
        # Get the tweets that were posted
        call_args = mock_x_client.post_thread.call_args
        tweets = call_args[0][0]
        
        # Verify structure: intro + insights + outro
        expected_count = 1 + len(mock_daily_brief.top_insights) + 1
        assert len(tweets) == expected_count
        
        # Verify intro
        assert "Bitcoin Pulse" in tweets[0]
        
        # Verify insights are numbered
        for i in range(1, len(mock_daily_brief.top_insights) + 1):
            assert f"{i}/" in tweets[i]
        
        # Verify outro
        assert "utxoiq.com" in tweets[-1]
    
    @pytest.mark.asyncio
    async def test_check_and_post_daily_brief_correct_time(self, daily_brief_service):
        """Test check_and_post_daily_brief posts at correct time."""
        # Mock datetime to be at 07:00 UTC
        with patch('src.daily_brief_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 7, 7, 0)
            
            tweet_ids = await daily_brief_service.check_and_post_daily_brief()
            
            # Should post at 07:00
            assert len(tweet_ids) > 0
    
    @pytest.mark.asyncio
    async def test_check_and_post_daily_brief_wrong_time(self, daily_brief_service):
        """Test check_and_post_daily_brief skips at wrong time."""
        # Mock datetime to be at 10:00 UTC (not 07:00)
        with patch('src.daily_brief_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 7, 10, 0)
            
            tweet_ids = await daily_brief_service.check_and_post_daily_brief()
            
            # Should not post at wrong time
            assert len(tweet_ids) == 0
