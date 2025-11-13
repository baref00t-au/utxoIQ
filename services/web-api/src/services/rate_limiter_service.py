"""Rate limiting service using Redis backend."""
import logging
import time
from typing import Optional, Tuple
from enum import Enum
import redis.asyncio as redis

from ..config import settings
from ..models.auth import UserSubscriptionTier

logger = logging.getLogger(__name__)


class RateLimitWindow(str, Enum):
    """Rate limit window types."""
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


class RateLimiter:
    """
    Redis-based rate limiter with tier-based limits.
    
    This class implements a sliding window rate limiting algorithm using Redis.
    It supports different rate limits based on user subscription tiers and
    provides detailed information about remaining requests and reset times.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize rate limiter with Redis client.
        
        Args:
            redis_client: Async Redis client instance
        """
        self.redis = redis_client
        self.window_seconds = settings.rate_limit_window
        
        # Define limits per tier (requests per hour)
        self.tier_limits = {
            UserSubscriptionTier.FREE: settings.rate_limit_free_tier,
            UserSubscriptionTier.PRO: settings.rate_limit_pro_tier,
            UserSubscriptionTier.POWER: settings.rate_limit_power_tier,
            UserSubscriptionTier.WHITE_LABEL: settings.rate_limit_power_tier * 10
        }
    
    def _get_limit_for_tier(self, tier: UserSubscriptionTier) -> int:
        """
        Get rate limit for a subscription tier.
        
        Args:
            tier: User subscription tier
            
        Returns:
            Rate limit (requests per window)
        """
        return self.tier_limits.get(tier, settings.rate_limit_free_tier)
    
    def _get_redis_key(self, identifier: str) -> str:
        """
        Generate Redis key for rate limiting.
        
        Args:
            identifier: Unique identifier (user ID or IP address)
            
        Returns:
            Redis key string
        """
        # Use current time window for key
        current_window = int(time.time() // self.window_seconds)
        return f"rate_limit:{identifier}:{current_window}"
    
    async def check_rate_limit(
        self,
        user_id: str,
        tier: UserSubscriptionTier,
        window_seconds: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        """
        Check if user is within rate limit.
        
        This method implements a sliding window rate limiting algorithm.
        It increments a counter in Redis for the current time window and
        checks if the user has exceeded their tier-based limit.
        
        Args:
            user_id: Unique user identifier
            tier: User subscription tier
            window_seconds: Optional custom window size (defaults to config)
            
        Returns:
            Tuple of (allowed, remaining, reset_time):
                - allowed: True if request is within limit
                - remaining: Number of requests remaining in window
                - reset_time: Seconds until rate limit resets
        """
        if window_seconds is None:
            window_seconds = self.window_seconds
        
        # Get limit for tier
        limit = self._get_limit_for_tier(tier)
        
        # Generate Redis key
        key = self._get_redis_key(user_id)
        
        try:
            # Increment counter atomically
            current = await self.redis.incr(key)
            
            # Set expiry on first request in window
            if current == 1:
                await self.redis.expire(key, window_seconds)
            
            # Get TTL for reset time
            ttl = await self.redis.ttl(key)
            if ttl < 0:
                # Key has no expiry, set it
                await self.redis.expire(key, window_seconds)
                ttl = window_seconds
            
            # Calculate remaining requests
            remaining = max(0, limit - current)
            
            # Check if limit exceeded
            allowed = current <= limit
            
            logger.debug(
                f"Rate limit check: user={user_id}, tier={tier.value}, "
                f"current={current}, limit={limit}, remaining={remaining}, "
                f"reset_in={ttl}s, allowed={allowed}"
            )
            
            return allowed, remaining, ttl
            
        except Exception as e:
            logger.error(f"Rate limiting error for user {user_id}: {e}", exc_info=True)
            # On Redis error, allow request but log the issue
            # This ensures service availability even if Redis is down
            return True, limit, window_seconds
    
    async def get_rate_limit_info(
        self,
        user_id: str,
        tier: UserSubscriptionTier
    ) -> dict:
        """
        Get current rate limit information for a user.
        
        Args:
            user_id: Unique user identifier
            tier: User subscription tier
            
        Returns:
            Dictionary with rate limit information
        """
        limit = self._get_limit_for_tier(tier)
        key = self._get_redis_key(user_id)
        
        try:
            current = await self.redis.get(key)
            current = int(current) if current else 0
            
            ttl = await self.redis.ttl(key)
            if ttl < 0:
                ttl = self.window_seconds
            
            remaining = max(0, limit - current)
            
            return {
                "limit": limit,
                "remaining": remaining,
                "reset": ttl,
                "used": current,
                "tier": tier.value,
                "window_seconds": self.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info for user {user_id}: {e}")
            return {
                "limit": limit,
                "remaining": limit,
                "reset": self.window_seconds,
                "used": 0,
                "tier": tier.value,
                "window_seconds": self.window_seconds
            }
    
    async def reset_rate_limit(self, user_id: str) -> bool:
        """
        Reset rate limit for a user (admin function).
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if reset successful, False otherwise
        """
        key = self._get_redis_key(user_id)
        
        try:
            await self.redis.delete(key)
            logger.info(f"Rate limit reset for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limit for user {user_id}: {e}")
            return False


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        # Create Redis client
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
        
        _rate_limiter = RateLimiter(redis_client)
        logger.info("Rate limiter initialized successfully")
    
    return _rate_limiter
