"""Unit tests for RateLimiter service (no app import)."""
import pytest
from unittest.mock import AsyncMock
import redis.asyncio as redis

from src.services.rate_limiter_service import RateLimiter
from src.models.auth import UserSubscriptionTier


class TestRateLimiterService:
    """Test RateLimiter service class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly."""
        mock_redis = AsyncMock(spec=redis.Redis)
        rate_limiter = RateLimiter(mock_redis)
        
        assert rate_limiter.redis == mock_redis
        assert rate_limiter.window_seconds == 3600
        assert rate_limiter.tier_limits[UserSubscriptionTier.FREE] == 100
        assert rate_limiter.tier_limits[UserSubscriptionTier.PRO] == 1000
        assert rate_limiter.tier_limits[UserSubscriptionTier.POWER] == 10000
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self):
        """Test rate limit check when within limit."""
        mock_redis = AsyncMock(spec=redis.Redis)
        # Mock async methods properly
        mock_redis.incr = AsyncMock(return_value=50)  # 50 requests made
        mock_redis.ttl = AsyncMock(return_value=1800)  # 30 minutes remaining
        mock_redis.expire = AsyncMock(return_value=True)
        
        rate_limiter = RateLimiter(mock_redis)
        
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id="test_user",
            tier=UserSubscriptionTier.FREE
        )
        
        assert allowed is True
        assert remaining == 50  # 100 - 50 = 50 remaining
        assert reset_time == 1800
        mock_redis.incr.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit exceeded."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.incr = AsyncMock(return_value=101)  # Exceeded free tier limit
        mock_redis.ttl = AsyncMock(return_value=600)  # 10 minutes remaining
        mock_redis.expire = AsyncMock(return_value=True)
        
        rate_limiter = RateLimiter(mock_redis)
        
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id="test_user",
            tier=UserSubscriptionTier.FREE
        )
        
        assert allowed is False
        assert remaining == 0
        assert reset_time == 600
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_pro_tier(self):
        """Test rate limit for Pro tier."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.incr = AsyncMock(return_value=500)
        mock_redis.ttl = AsyncMock(return_value=1800)
        mock_redis.expire = AsyncMock(return_value=True)
        
        rate_limiter = RateLimiter(mock_redis)
        
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id="test_user",
            tier=UserSubscriptionTier.PRO
        )
        
        assert allowed is True
        assert remaining == 500  # 1000 - 500 = 500 remaining
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_power_tier(self):
        """Test rate limit for Power tier."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.incr = AsyncMock(return_value=5000)
        mock_redis.ttl = AsyncMock(return_value=1800)
        mock_redis.expire = AsyncMock(return_value=True)
        
        rate_limiter = RateLimiter(mock_redis)
        
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id="test_user",
            tier=UserSubscriptionTier.POWER
        )
        
        assert allowed is True
        assert remaining == 5000  # 10000 - 5000 = 5000 remaining
    
    @pytest.mark.asyncio
    async def test_rate_limit_counter_reset(self):
        """Test rate limit counter reset after window."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.incr = AsyncMock(return_value=1)  # First request in new window
        mock_redis.ttl = AsyncMock(return_value=3600)  # Full window remaining
        mock_redis.expire = AsyncMock(return_value=True)
        
        rate_limiter = RateLimiter(mock_redis)
        
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id="test_user",
            tier=UserSubscriptionTier.FREE
        )
        
        assert allowed is True
        assert remaining == 99  # 100 - 1 = 99 remaining
        assert reset_time == 3600
        # Verify expire was called on first request
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_rate_limit_info(self):
        """Test getting rate limit information."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value="75")
        mock_redis.ttl = AsyncMock(return_value=1200)
        
        rate_limiter = RateLimiter(mock_redis)
        
        info = await rate_limiter.get_rate_limit_info(
            user_id="test_user",
            tier=UserSubscriptionTier.PRO
        )
        
        assert info["limit"] == 1000
        assert info["remaining"] == 925  # 1000 - 75
        assert info["used"] == 75
        assert info["reset"] == 1200
        assert info["tier"] == "pro"
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit(self):
        """Test resetting rate limit for a user."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.delete = AsyncMock(return_value=1)
        
        rate_limiter = RateLimiter(mock_redis)
        
        result = await rate_limiter.reset_rate_limit("test_user")
        
        assert result is True
        mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self):
        """Test graceful handling of Redis errors."""
        mock_redis = AsyncMock(spec=redis.Redis)
        mock_redis.incr.side_effect = Exception("Redis connection error")
        
        rate_limiter = RateLimiter(mock_redis)
        
        # Should not raise exception, should allow request
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id="test_user",
            tier=UserSubscriptionTier.FREE
        )
        
        assert allowed is True  # Fail open on Redis error
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_within_limit(self):
        """Test handling of concurrent requests."""
        mock_redis = AsyncMock(spec=redis.Redis)
        # Simulate multiple requests
        mock_redis.incr = AsyncMock(side_effect=[1, 2, 3, 4, 5])
        mock_redis.ttl = AsyncMock(return_value=3600)
        mock_redis.expire = AsyncMock(return_value=True)
        
        rate_limiter = RateLimiter(mock_redis)
        
        # Make 5 requests
        for i in range(5):
            allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
                user_id="test_user",
                tier=UserSubscriptionTier.FREE
            )
            assert allowed is True
            assert remaining == 100 - (i + 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
