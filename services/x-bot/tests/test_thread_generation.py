"""Tests for daily thread generation and scheduling."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import date, datetime
from src.daily_brief_service import DailyBriefService


class TestThreadGeneration:
    """Test cases for thread generation."""
    
    @pytest.fixture
    def daily_brief_service(self, mock_x_client, mock_redis_client, mock_api_client):
        """Create daily brief service with mocked dependencies."""
        with patch('src.daily_brief_service.XClient', return_value=mock_x_client), \
             patch('src.daily_brief_service.RedisClient', return_value=mock_redis_client), \
             patch('src.daily_brief_service.APIClient', return_value=mock_api_client):
            service = DailyBriefService()
            return service
    
    def test_thread_tweets_within_character_limit(self, daily_brief_service, mock_daily_brief):
        """Test that all thread tweets are within 280 character limit."""
        # Compose all tweets
        tweets = []
        tweets.append(daily_brief_service.compose_thread_intro(mock_daily_brief))
        
        for i, insight in enumerate(mock_daily_brief.top_insights, start=1):
            tweets.append(daily_brief_service.compose_insight_tweet(insight, i))
        
        tweets.append(daily_brief_service.compose_thread_outro())
        
        # Verify all tweets are within limit
        for i, tweet in enumerate(tweets):
            assert len(tweet) <= 280, f"Tweet {i} exceeds 280 characters: {len(tweet)}"
    
    def test_thread_numbering_sequential(self, daily_brief_service, mock_daily_brief):
        """Test that thread tweets are numbered sequentially."""
        insight_tweets = []
        for i, insight in enumerate(mock_daily_brief.top_insights, start=1):
            tweet = daily_brief_service.compose_insight_tweet(insight, i)
            insight_tweets.append(tweet)
        
        # Verify sequential numbering
        for i, tweet in enumerate(insight_tweets, start=1):
            assert f"{i}/" in tweet
    
    def test_thread_includes_signal_type_emojis(self, daily_brief_service, mock_insights):
        """Test that thread tweets include appropriate signal type emojis."""
        emoji_map = {
            "mempool": "📊",
            "exchange": "🏦",
            "miner": "⛏️",
            "whale": "🐋"
        }
        
        for i, insight in enumerate(mock_insights, start=1):
            tweet = daily_brief_service.compose_insight_tweet(insight, i)
            expected_emoji = emoji_map.get(insight.signal_type.value, "📈")
            assert expected_emoji in tweet
    
    def test_thread_includes_confidence_and_block(self, daily_brief_service, mock_insight):
        """Test that thread tweets include confidence and block height."""
        tweet = daily_brief_service.compose_insight_tweet(mock_insight, 1)
        
        # Check for confidence percentage
        confidence_pct = int(mock_insight.confidence * 100)
        assert f"{confidence_pct}%" in tweet
        
        # Check for block height
        assert str(mock_insight.block_height) in tweet
    
    @pytest.mark.asyncio
    async def test_thread_posting_order(self, daily_brief_service, mock_x_client, mock_daily_brief):
        """Test that thread tweets are posted in correct order."""
        today = date.today()
        
        await daily_brief_service.post_daily_brief(today)
        
        # Get the tweets that were posted
        call_args = mock_x_client.post_thread.call_args
        tweets = call_args[0][0]
        
        # Verify order: intro, insights, outro
        assert "Bitcoin Pulse" in tweets[0]  # Intro
        assert "utxoiq.com" in tweets[-1]  # Outro
        
        # Verify insights are in middle
        for i in range(1, len(tweets) - 1):
            # Should have numbering
            assert f"{i}/" in tweets[i]
    
    @pytest.mark.asyncio
    async def test_thread_handles_variable_insight_count(self, daily_brief_service, mock_x_client, mock_api_client):
        """Test that thread handles different numbers of insights."""
        from src.models import DailyBrief
        
        # Test with different insight counts
        for count in [1, 3, 5]:
            brief = DailyBrief(
                date=date.today().isoformat(),
                top_insights=mock_api_client.get_publishable_insights.return_value[:count],
                summary=f"Top {count} events"
            )
            
            mock_api_client.get_daily_brief.return_value = brief
            
            await daily_brief_service.post_daily_brief()
            
            # Verify correct number of tweets
            call_args = mock_x_client.post_thread.call_args
            tweets = call_args[0][0]
            
            # Should be: intro + insights + outro
            expected_count = 1 + count + 1
            assert len(tweets) == expected_count
    
    def test_thread_intro_includes_date(self, daily_brief_service, mock_daily_brief):
        """Test that thread intro includes formatted date."""
        intro = daily_brief_service.compose_thread_intro(mock_daily_brief)
        
        # Should include a date in some format
        assert any(month in intro for month in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
    
    def test_thread_outro_includes_cta(self, daily_brief_service):
        """Test that thread outro includes call-to-action."""
        outro = daily_brief_service.compose_thread_outro()
        
        assert "utxoiq.com" in outro
        assert "follow" in outro.lower()
    
    @pytest.mark.asyncio
    async def test_scheduling_time_check(self, daily_brief_service):
        """Test that scheduling checks time correctly."""
        # Test at correct time (07:00 UTC)
        with patch('src.daily_brief_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 7, 7, 0)
            
            result = await daily_brief_service.check_and_post_daily_brief()
            assert len(result) > 0  # Should post
        
        # Test at wrong time (10:00 UTC)
        with patch('src.daily_brief_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 7, 10, 0)
            
            result = await daily_brief_service.check_and_post_daily_brief()
            assert len(result) == 0  # Should not post
    
    @pytest.mark.asyncio
    async def test_scheduling_time_window(self, daily_brief_service):
        """Test that scheduling has a 5-minute window."""
        # Test within window (07:03 UTC)
        with patch('src.daily_brief_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 7, 7, 3)
            
            result = await daily_brief_service.check_and_post_daily_brief()
            assert len(result) > 0  # Should post within window
        
        # Test outside window (07:10 UTC)
        with patch('src.daily_brief_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 11, 7, 7, 10)
            
            result = await daily_brief_service.check_and_post_daily_brief()
            assert len(result) == 0  # Should not post outside window
