"""Rate limiting middleware using Redis."""
import logging
from typing import Optional
from fastapi import HTTPException, Request, status, Depends

from ..config import settings
from ..models.auth import UserSubscriptionTier
from ..models.db_models import User
from ..models.errors import RateLimitExceededError
from ..services.rate_limiter_service import get_rate_limiter, RateLimiter

logger = logging.getLogger(__name__)


async def check_rate_limit(
    request: Request,
    user = None
) -> None:
    """
    Check if request is within rate limits.
    
    This function checks the rate limit for the current request based on
    the user's subscription tier (if authenticated) or IP address (if not).
    It stores rate limit information in the request state for use in
    response headers.
    
    Args:
        request: The incoming request
        user: Optional authenticated user
        rate_limiter: Rate limiter service instance
        
    Raises:
        HTTPException: 429 if rate limit is exceeded
    """
    # Determine identifier and tier for rate limiting
    if user:
        identifier = str(user.id)
        tier = UserSubscriptionTier(user.subscription_tier)
    else:
        # Use IP address for unauthenticated requests
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"
        tier = UserSubscriptionTier.FREE
    
    try:
        # Get rate limiter instance
        rate_limiter = await get_rate_limiter()
        
        # Check rate limit
        allowed, remaining, reset_time = await rate_limiter.check_rate_limit(
            user_id=identifier,
            tier=tier
        )
        
        # Store rate limit info in request state for response headers
        limit = rate_limiter._get_limit_for_tier(tier)
        request.state.rate_limit_limit = limit
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset_time
        
        # Raise exception if limit exceeded
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: identifier={identifier}, tier={tier.value}, "
                f"limit={limit}, reset_in={reset_time}s"
            )
            
            raise RateLimitExceededError(
                message=f"Rate limit exceeded. Try again in {reset_time} seconds.",
                retry_after=reset_time,
                limit=limit,
                remaining=0
            )
        
        logger.debug(
            f"Rate limit check passed: identifier={identifier}, tier={tier.value}, "
            f"remaining={remaining}/{limit}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting error: {e}", exc_info=True)
        # Don't block requests if Redis is unavailable
        # Set default values in request state
        request.state.rate_limit_limit = settings.rate_limit_free_tier
        request.state.rate_limit_remaining = settings.rate_limit_free_tier
        request.state.rate_limit_reset = settings.rate_limit_window


async def rate_limit_dependency(
    request: Request,
    user = None
) -> None:
    """
    FastAPI dependency for rate limiting.
    
    This dependency can be added to any endpoint to enforce rate limiting.
    It works with both authenticated and unauthenticated requests.
    
    Args:
        request: The incoming request
        user: Optional authenticated user
        
    Raises:
        HTTPException: 429 if rate limit is exceeded
    """
    await check_rate_limit(request, user)
