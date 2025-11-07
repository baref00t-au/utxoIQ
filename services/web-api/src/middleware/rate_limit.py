"""Rate limiting middleware using Redis."""
import logging
from typing import Optional
from fastapi import HTTPException, Request, status
import redis.asyncio as redis
from ..config import settings
from ..models.auth import User, UserSubscriptionTier

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True
        )
    return redis_client


def get_rate_limit_for_tier(tier: UserSubscriptionTier) -> int:
    """
    Get rate limit for a subscription tier.
    
    Args:
        tier: User subscription tier
        
    Returns:
        Rate limit (requests per window)
    """
    limits = {
        UserSubscriptionTier.FREE: settings.rate_limit_free_tier,
        UserSubscriptionTier.PRO: settings.rate_limit_pro_tier,
        UserSubscriptionTier.POWER: settings.rate_limit_power_tier,
        UserSubscriptionTier.WHITE_LABEL: settings.rate_limit_power_tier * 10
    }
    return limits.get(tier, settings.rate_limit_free_tier)


async def check_rate_limit(
    request: Request,
    user: Optional[User] = None
) -> None:
    """
    Check if request is within rate limits.
    
    Args:
        request: The incoming request
        user: Optional authenticated user
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Determine identifier for rate limiting
    if user:
        identifier = f"user:{user.uid}"
        limit = get_rate_limit_for_tier(user.subscription_tier)
    else:
        # Use IP address for unauthenticated requests
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"
        limit = settings.rate_limit_free_tier
    
    # Create Redis key
    window = settings.rate_limit_window
    redis_key = f"rate_limit:{identifier}:{window}"
    
    try:
        client = await get_redis_client()
        
        # Increment counter
        current = await client.incr(redis_key)
        
        # Set expiry on first request
        if current == 1:
            await client.expire(redis_key, window)
        
        # Check if limit exceeded
        if current > limit:
            ttl = await client.ttl(redis_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers={"Retry-After": str(ttl)}
            )
        
        # Store rate limit info in request state for response headers
        request.state.rate_limit_remaining = limit - current
        request.state.rate_limit_limit = limit
        request.state.rate_limit_reset = ttl if current == 1 else await client.ttl(redis_key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        # Don't block requests if Redis is unavailable
        pass


async def rate_limit_dependency(
    request: Request,
    user: Optional[User] = None
) -> None:
    """
    FastAPI dependency for rate limiting.
    
    Args:
        request: The incoming request
        user: Optional authenticated user
    """
    await check_rate_limit(request, user)
