"""Redis caching service layer for performance optimization."""
from typing import Optional, Dict, Any, Callable
import json
import logging
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from src.config import settings
from src.models.database_schemas import FeedbackStats, BackfillJobResponse, MetricResponse

logger = logging.getLogger(__name__)


class CacheService:
    """Service for Redis caching operations with fallback strategies."""
    
    # Cache key patterns
    CACHE_KEYS = {
        "feedback_stats": "feedback:stats:{insight_id}",
        "backfill_job": "backfill:job:{job_id}",
        "recent_metrics": "metrics:{service}:{metric_type}:recent",
        "aggregated_metrics": "metrics:{service}:{metric_type}:agg:{interval}:{start}:{end}",
    }
    
    # Cache TTL values (in seconds)
    CACHE_TTL = {
        "feedback_stats": 3600,      # 1 hour
        "backfill_job": 300,          # 5 minutes
        "recent_metrics": 300,        # 5 minutes
        "aggregated_metrics": 3600,   # 1 hour
    }
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_url = self._build_redis_url()
        self.client: Optional[redis.Redis] = None
        logger.info("CacheService initialized")
    
    def _build_redis_url(self) -> str:
        """Build Redis connection URL from settings."""
        if settings.redis_password:
            return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/0"
        return f"redis://{settings.redis_host}:{settings.redis_port}/0"
    
    async def connect(self):
        """Establish Redis connection."""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def _generate_key(self, pattern: str, **kwargs) -> str:
        """
        Generate cache key from pattern and parameters.
        
        Args:
            pattern: Key pattern name from CACHE_KEYS
            **kwargs: Parameters to format into the key
        
        Returns:
            Formatted cache key
        """
        key_template = self.CACHE_KEYS.get(pattern)
        if not key_template:
            raise ValueError(f"Unknown cache key pattern: {pattern}")
        return key_template.format(**kwargs)
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get cached value by key.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or error
        """
        if not self.client:
            logger.warning("Redis client not available")
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached value with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available")
            return False
        
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            logger.debug(f"Cache set for key: {key} (TTL: {ttl}s)")
            return True
        except RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete cached value.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("Redis client not available")
            return False
        
        try:
            await self.client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
            return True
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "feedback:stats:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.client:
            logger.warning("Redis client not available")
            return 0
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.client.delete(*keys)
                logger.debug(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except RedisError as e:
            logger.error(f"Redis delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists, False otherwise
        """
        if not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    # ==================== Feedback Statistics Caching ====================
    
    async def get_feedback_stats(self, insight_id: str) -> Optional[FeedbackStats]:
        """
        Get cached feedback statistics.
        
        Args:
            insight_id: Insight identifier
        
        Returns:
            Cached feedback stats or None
        """
        key = self._generate_key("feedback_stats", insight_id=insight_id)
        cached = await self.get(key)
        
        if cached:
            try:
                data = json.loads(cached)
                return FeedbackStats(**data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to deserialize feedback stats: {e}")
                await self.delete(key)  # Remove corrupted cache
                return None
        return None
    
    async def cache_feedback_stats(
        self, 
        insight_id: str, 
        stats: FeedbackStats
    ) -> bool:
        """
        Cache feedback statistics.
        
        Args:
            insight_id: Insight identifier
            stats: Feedback statistics to cache
        
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_key("feedback_stats", insight_id=insight_id)
        ttl = self.CACHE_TTL["feedback_stats"]
        
        try:
            value = stats.model_dump_json()
            return await self.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Failed to serialize feedback stats: {e}")
            return False
    
    async def invalidate_feedback_cache(self, insight_id: str) -> bool:
        """
        Invalidate feedback cache for an insight.
        
        Args:
            insight_id: Insight identifier
        
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_key("feedback_stats", insight_id=insight_id)
        result = await self.delete(key)
        logger.info(f"Invalidated feedback cache for insight {insight_id}")
        return result
    
    # ==================== Backfill Job Caching ====================
    
    async def get_backfill_job(self, job_id: str) -> Optional[BackfillJobResponse]:
        """
        Get cached backfill job.
        
        Args:
            job_id: Job UUID as string
        
        Returns:
            Cached backfill job or None
        """
        key = self._generate_key("backfill_job", job_id=job_id)
        cached = await self.get(key)
        
        if cached:
            try:
                data = json.loads(cached)
                return BackfillJobResponse(**data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to deserialize backfill job: {e}")
                await self.delete(key)
                return None
        return None
    
    async def cache_backfill_job(
        self, 
        job_id: str, 
        job: BackfillJobResponse
    ) -> bool:
        """
        Cache backfill job with 5-minute TTL.
        
        Args:
            job_id: Job UUID as string
            job: Backfill job to cache
        
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_key("backfill_job", job_id=job_id)
        ttl = self.CACHE_TTL["backfill_job"]
        
        try:
            value = job.model_dump_json()
            return await self.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Failed to serialize backfill job: {e}")
            return False
    
    async def invalidate_backfill_cache(self, job_id: str) -> bool:
        """
        Invalidate backfill job cache.
        
        Args:
            job_id: Job UUID as string
        
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_key("backfill_job", job_id=job_id)
        result = await self.delete(key)
        logger.info(f"Invalidated backfill cache for job {job_id}")
        return result
    
    # ==================== Metrics Caching ====================
    
    async def get_recent_metrics(
        self, 
        service: str, 
        metric_type: str
    ) -> Optional[list]:
        """
        Get cached recent metrics (last 1 hour).
        
        Args:
            service: Service name
            metric_type: Metric type
        
        Returns:
            List of cached metrics or None
        """
        key = self._generate_key(
            "recent_metrics", 
            service=service, 
            metric_type=metric_type
        )
        cached = await self.get(key)
        
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to deserialize recent metrics: {e}")
                await self.delete(key)
                return None
        return None
    
    async def cache_recent_metrics(
        self, 
        service: str, 
        metric_type: str, 
        metrics: list
    ) -> bool:
        """
        Cache recent metrics with 5-minute TTL.
        
        Args:
            service: Service name
            metric_type: Metric type
            metrics: List of metrics to cache
        
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_key(
            "recent_metrics", 
            service=service, 
            metric_type=metric_type
        )
        ttl = self.CACHE_TTL["recent_metrics"]
        
        try:
            # Convert Pydantic models to dicts for JSON serialization
            serializable_metrics = []
            for metric in metrics:
                if hasattr(metric, 'model_dump'):
                    serializable_metrics.append(metric.model_dump())
                else:
                    serializable_metrics.append(metric)
            
            value = json.dumps(serializable_metrics, default=str)
            return await self.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Failed to serialize recent metrics: {e}")
            return False
    
    async def get_aggregated_metrics(
        self, 
        service: str, 
        metric_type: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[list]:
        """
        Get cached aggregated metrics.
        
        Args:
            service: Service name
            metric_type: Metric type
            interval: Aggregation interval ('hour' or 'day')
            start_time: Start timestamp
            end_time: End timestamp
        
        Returns:
            List of cached aggregated metrics or None
        """
        key = self._generate_key(
            "aggregated_metrics",
            service=service,
            metric_type=metric_type,
            interval=interval,
            start=start_time.isoformat(),
            end=end_time.isoformat()
        )
        cached = await self.get(key)
        
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to deserialize aggregated metrics: {e}")
                await self.delete(key)
                return None
        return None
    
    async def cache_aggregated_metrics(
        self, 
        service: str, 
        metric_type: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        metrics: list
    ) -> bool:
        """
        Cache aggregated metrics with 1-hour TTL.
        
        Args:
            service: Service name
            metric_type: Metric type
            interval: Aggregation interval
            start_time: Start timestamp
            end_time: End timestamp
            metrics: List of aggregated metrics to cache
        
        Returns:
            True if successful, False otherwise
        """
        key = self._generate_key(
            "aggregated_metrics",
            service=service,
            metric_type=metric_type,
            interval=interval,
            start=start_time.isoformat(),
            end=end_time.isoformat()
        )
        ttl = self.CACHE_TTL["aggregated_metrics"]
        
        try:
            value = json.dumps(metrics, default=str)
            return await self.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Failed to serialize aggregated metrics: {e}")
            return False
    
    # ==================== Cache Fallback Strategy ====================
    
    async def get_with_fallback(
        self,
        cache_key: str,
        db_query: Callable,
        ttl: Optional[int] = None,
        serialize_fn: Optional[Callable] = None
    ) -> Any:
        """
        Try cache first, fallback to database query.
        
        This implements the cache-aside pattern with automatic fallback.
        
        Args:
            cache_key: Cache key to check
            db_query: Async callable that queries the database
            ttl: TTL for caching the result (optional)
            serialize_fn: Function to serialize result for caching (optional)
        
        Returns:
            Data from cache or database
        """
        # Try cache first
        try:
            cached = await self.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for key: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache error for key {cache_key}: {e}, falling back to database")
        
        # Fallback to database
        logger.debug(f"Cache miss for key: {cache_key}, querying database")
        result = await db_query()
        
        # Try to cache result (best effort)
        try:
            if result is not None:
                if serialize_fn:
                    value = serialize_fn(result)
                elif hasattr(result, 'model_dump_json'):
                    value = result.model_dump_json()
                elif hasattr(result, 'model_dump'):
                    value = json.dumps(result.model_dump(), default=str)
                else:
                    value = json.dumps(result, default=str)
                
                await self.set(cache_key, value, ttl)
                logger.debug(f"Cached result for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache result for key {cache_key}: {e}")
        
        return result
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "feedback:stats:*")
        
        Returns:
            Number of keys invalidated
        """
        deleted = await self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache keys matching pattern: {pattern}")
        return deleted


# Global cache service instance
cache_service = CacheService()
