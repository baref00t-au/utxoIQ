"""Redis client for duplicate prevention and caching."""
import redis
import logging
from typing import Optional
from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for tracking posted insights."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            decode_responses=True
        )
        logger.info("Redis client initialized")
    
    def mark_insight_posted(self, insight_id: str, signal_type: str, ttl: Optional[int] = None) -> bool:
        """
        Mark an insight as posted to prevent duplicates.
        
        Args:
            insight_id: Unique insight identifier
            signal_type: Signal category for duplicate prevention
            ttl: Time to live in seconds (default: duplicate_prevention_window)
            
        Returns:
            True if marked successfully, False otherwise
        """
        if ttl is None:
            ttl = settings.duplicate_prevention_window
        
        try:
            # Store insight ID with expiration
            key = f"posted:insight:{insight_id}"
            self.client.setex(key, ttl, "1")
            
            # Store signal type timestamp for category-based duplicate prevention
            signal_key = f"posted:signal:{signal_type}"
            self.client.setex(signal_key, ttl, insight_id)
            
            logger.info(f"Marked insight {insight_id} as posted (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark insight as posted: {e}")
            return False
    
    def is_insight_posted(self, insight_id: str) -> bool:
        """
        Check if an insight has already been posted.
        
        Args:
            insight_id: Unique insight identifier
            
        Returns:
            True if already posted, False otherwise
        """
        try:
            key = f"posted:insight:{insight_id}"
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check if insight posted: {e}")
            return False
    
    def is_signal_recently_posted(self, signal_type: str) -> bool:
        """
        Check if a signal of this type was recently posted.
        
        Args:
            signal_type: Signal category
            
        Returns:
            True if recently posted, False otherwise
        """
        try:
            signal_key = f"posted:signal:{signal_type}"
            return self.client.exists(signal_key) > 0
        except Exception as e:
            logger.error(f"Failed to check signal posting status: {e}")
            return False
    
    def get_last_daily_brief_date(self) -> Optional[str]:
        """
        Get the date of the last posted daily brief.
        
        Returns:
            Date string (YYYY-MM-DD) or None
        """
        try:
            return self.client.get("last_daily_brief_date")
        except Exception as e:
            logger.error(f"Failed to get last daily brief date: {e}")
            return None
    
    def set_last_daily_brief_date(self, date: str) -> bool:
        """
        Set the date of the last posted daily brief.
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            True if set successfully, False otherwise
        """
        try:
            self.client.set("last_daily_brief_date", date)
            logger.info(f"Set last daily brief date to {date}")
            return True
        except Exception as e:
            logger.error(f"Failed to set last daily brief date: {e}")
            return False
