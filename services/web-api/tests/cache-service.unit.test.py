"""Integration tests for cache service."""
import pytest
import pytest_asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.cache_service import CacheService
from src.models.database_schemas import (
    FeedbackStats, BackfillJobResponse, MetricResponse
)


@pytest_asyncio.fixture
async def cache_service():
    """Provide test cache service."""
    service = CacheService()
    await service.connect()
    
    # Clear test data before each test
    if service.client:
        try:
            await service.client.flushdb()
        except Exception:
            pass  # Redis might not be running
    
    yield service
    
    # Cleanup
    if service.client:
        try:
            await service.client.flushdb()
        except Exception:
            pass
    await service.disconnect()


@pytest.fixture
def sample_feedback_stats():
    """Sample feedback statistics."""
    return FeedbackStats(
        insight_id="test_insight_123",
        total_ratings=42,
        average_rating=4.5,
        rating_distribution={1: 1, 2: 2, 3: 5, 4: 14, 5: 20},
        total_comments=15,
        total_flags=2,
        flag_types={"inaccurate": 1, "spam": 1}
    )


@pytest.fixture
def sample_backfill_job():
    """Sample backfill job."""
    return BackfillJobResponse(
        id=uuid4(),
        job_type="blocks",
        start_block=800000,
        end_block=810000,
        current_block=805000,
        status="running",
        progress_percentage=50.0,
        estimated_completion=datetime.utcnow() + timedelta(hours=1),
        error_message=None,
        started_at=datetime.utcnow(),
        completed_at=None,
        created_by="test_user"
    )


@pytest.fixture
def sample_metrics():
    """Sample metrics list."""
    return [
        MetricResponse(
            id=uuid4(),
            service_name="web-api",
            metric_type="cpu",
            metric_value=45.5,
            unit="percent",
            timestamp=datetime.utcnow(),
            metric_metadata={"host": "server-01"}
        ),
        MetricResponse(
            id=uuid4(),
            service_name="web-api",
            metric_type="cpu",
            metric_value=48.2,
            unit="percent",
            timestamp=datetime.utcnow(),
            metric_metadata={"host": "server-01"}
        )
    ]


class TestCacheBasicOperations:
    """Test basic cache operations."""
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service):
        """Test basic set and get operations."""
        key = "test:key"
        value = "test_value"
        
        # Set value
        result = await cache_service.set(key, value)
        assert result is True
        
        # Get value
        cached = await cache_service.get(key)
        assert cached == value
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Test getting a non-existent key returns None."""
        cached = await cache_service.get("nonexistent:key")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_service):
        """Test setting value with TTL."""
        key = "test:ttl"
        value = "expires_soon"
        ttl = 1  # 1 second
        
        result = await cache_service.set(key, value, ttl)
        assert result is True
        
        # Value should exist immediately
        cached = await cache_service.get(key)
        assert cached == value
        
        # Wait for expiration
        import asyncio
        await asyncio.sleep(1.5)
        
        # Value should be expired
        cached = await cache_service.get(key)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_service):
        """Test deleting a cached value."""
        key = "test:delete"
        value = "to_be_deleted"
        
        await cache_service.set(key, value)
        assert await cache_service.get(key) == value
        
        # Delete
        result = await cache_service.delete(key)
        assert result is True
        
        # Verify deleted
        cached = await cache_service.get(key)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_exists(self, cache_service):
        """Test checking if key exists."""
        key = "test:exists"
        
        # Key doesn't exist
        assert await cache_service.exists(key) is False
        
        # Set key
        await cache_service.set(key, "value")
        
        # Key exists
        assert await cache_service.exists(key) is True


class TestFeedbackStatsCaching:
    """Test feedback statistics caching."""
    
    @pytest.mark.asyncio
    async def test_cache_and_get_feedback_stats(
        self, 
        cache_service, 
        sample_feedback_stats
    ):
        """Test caching and retrieving feedback stats."""
        insight_id = sample_feedback_stats.insight_id
        
        # Cache stats
        result = await cache_service.cache_feedback_stats(
            insight_id, 
            sample_feedback_stats
        )
        assert result is True
        
        # Retrieve stats
        cached_stats = await cache_service.get_feedback_stats(insight_id)
        assert cached_stats is not None
        assert cached_stats.insight_id == sample_feedback_stats.insight_id
        assert cached_stats.total_ratings == sample_feedback_stats.total_ratings
        assert cached_stats.average_rating == sample_feedback_stats.average_rating
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_feedback_stats(self, cache_service):
        """Test getting non-existent feedback stats returns None."""
        cached_stats = await cache_service.get_feedback_stats("nonexistent_insight")
        assert cached_stats is None
    
    @pytest.mark.asyncio
    async def test_invalidate_feedback_cache(
        self, 
        cache_service, 
        sample_feedback_stats
    ):
        """Test invalidating feedback cache."""
        insight_id = sample_feedback_stats.insight_id
        
        # Cache stats
        await cache_service.cache_feedback_stats(insight_id, sample_feedback_stats)
        assert await cache_service.get_feedback_stats(insight_id) is not None
        
        # Invalidate
        result = await cache_service.invalidate_feedback_cache(insight_id)
        assert result is True
        
        # Verify invalidated
        cached_stats = await cache_service.get_feedback_stats(insight_id)
        assert cached_stats is None


class TestBackfillJobCaching:
    """Test backfill job caching."""
    
    @pytest.mark.asyncio
    async def test_cache_and_get_backfill_job(
        self, 
        cache_service, 
        sample_backfill_job
    ):
        """Test caching and retrieving backfill job."""
        job_id = str(sample_backfill_job.id)
        
        # Cache job
        result = await cache_service.cache_backfill_job(job_id, sample_backfill_job)
        assert result is True
        
        # Retrieve job
        cached_job = await cache_service.get_backfill_job(job_id)
        assert cached_job is not None
        assert str(cached_job.id) == job_id
        assert cached_job.status == sample_backfill_job.status
        assert cached_job.progress_percentage == sample_backfill_job.progress_percentage
    
    @pytest.mark.asyncio
    async def test_invalidate_backfill_cache(
        self, 
        cache_service, 
        sample_backfill_job
    ):
        """Test invalidating backfill job cache."""
        job_id = str(sample_backfill_job.id)
        
        # Cache job
        await cache_service.cache_backfill_job(job_id, sample_backfill_job)
        assert await cache_service.get_backfill_job(job_id) is not None
        
        # Invalidate
        result = await cache_service.invalidate_backfill_cache(job_id)
        assert result is True
        
        # Verify invalidated
        cached_job = await cache_service.get_backfill_job(job_id)
        assert cached_job is None


class TestMetricsCaching:
    """Test metrics caching."""
    
    @pytest.mark.asyncio
    async def test_cache_and_get_recent_metrics(
        self, 
        cache_service, 
        sample_metrics
    ):
        """Test caching and retrieving recent metrics."""
        service = "web-api"
        metric_type = "cpu"
        
        # Cache metrics
        result = await cache_service.cache_recent_metrics(
            service, 
            metric_type, 
            sample_metrics
        )
        assert result is True
        
        # Retrieve metrics
        cached_metrics = await cache_service.get_recent_metrics(service, metric_type)
        assert cached_metrics is not None
        assert len(cached_metrics) == len(sample_metrics)
    
    @pytest.mark.asyncio
    async def test_cache_and_get_aggregated_metrics(self, cache_service):
        """Test caching and retrieving aggregated metrics."""
        service = "web-api"
        metric_type = "cpu"
        interval = "hour"
        start_time = datetime.utcnow() - timedelta(hours=24)
        end_time = datetime.utcnow()
        
        aggregated_data = [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=i),
                "avg_value": 45.0 + i,
                "min_value": 40.0,
                "max_value": 50.0,
                "count": 100
            }
            for i in range(24)
        ]
        
        # Cache aggregated metrics
        result = await cache_service.cache_aggregated_metrics(
            service, 
            metric_type, 
            interval, 
            start_time, 
            end_time, 
            aggregated_data
        )
        assert result is True
        
        # Retrieve aggregated metrics
        cached_metrics = await cache_service.get_aggregated_metrics(
            service, 
            metric_type, 
            interval, 
            start_time, 
            end_time
        )
        assert cached_metrics is not None
        assert len(cached_metrics) == len(aggregated_data)


class TestCacheFallbackStrategy:
    """Test cache fallback strategy."""
    
    @pytest.mark.asyncio
    async def test_get_with_fallback_cache_hit(self, cache_service):
        """Test fallback with cache hit."""
        key = "test:fallback:hit"
        expected_value = {"data": "from_cache"}
        
        # Pre-populate cache
        await cache_service.set(key, json.dumps(expected_value))
        
        # Database query should not be called
        db_called = False
        async def db_query():
            nonlocal db_called
            db_called = True
            return {"data": "from_db"}
        
        result = await cache_service.get_with_fallback(key, db_query)
        
        assert result == expected_value
        assert db_called is False  # DB should not be called
    
    @pytest.mark.asyncio
    async def test_get_with_fallback_cache_miss(self, cache_service):
        """Test fallback with cache miss."""
        key = "test:fallback:miss"
        expected_value = {"data": "from_db"}
        
        # Database query
        async def db_query():
            return expected_value
        
        result = await cache_service.get_with_fallback(key, db_query, ttl=300)
        
        assert result == expected_value
        
        # Verify value was cached
        cached = await cache_service.get(key)
        assert cached is not None
        assert json.loads(cached) == expected_value
    
    @pytest.mark.asyncio
    async def test_fallback_when_redis_unavailable(self):
        """Test fallback behavior when Redis is unavailable."""
        # Create service with invalid Redis connection
        service = CacheService()
        service.redis_url = "redis://invalid-host:9999/0"
        await service.connect()  # Will fail but not raise
        
        expected_value = {"data": "from_db"}
        
        async def db_query():
            return expected_value
        
        # Should fallback to database without error
        result = await service.get_with_fallback(
            "test:key", 
            db_query
        )
        
        assert result == expected_value
        
        await service.disconnect()


class TestCacheInvalidationPatterns:
    """Test cache invalidation patterns."""
    
    @pytest.mark.asyncio
    async def test_delete_pattern(self, cache_service):
        """Test deleting keys by pattern."""
        # Set multiple keys
        await cache_service.set("feedback:stats:insight1", "data1")
        await cache_service.set("feedback:stats:insight2", "data2")
        await cache_service.set("feedback:stats:insight3", "data3")
        await cache_service.set("other:key", "other_data")
        
        # Delete pattern
        deleted = await cache_service.delete_pattern("feedback:stats:*")
        assert deleted == 3
        
        # Verify feedback keys deleted
        assert await cache_service.get("feedback:stats:insight1") is None
        assert await cache_service.get("feedback:stats:insight2") is None
        assert await cache_service.get("feedback:stats:insight3") is None
        
        # Verify other key still exists
        assert await cache_service.get("other:key") == "other_data"
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache_service):
        """Test invalidating keys by pattern."""
        # Set multiple backfill job keys
        await cache_service.set("backfill:job:job1", "data1")
        await cache_service.set("backfill:job:job2", "data2")
        
        # Invalidate pattern
        deleted = await cache_service.invalidate_pattern("backfill:job:*")
        assert deleted == 2
        
        # Verify keys deleted
        assert await cache_service.get("backfill:job:job1") is None
        assert await cache_service.get("backfill:job:job2") is None


class TestCacheHitRate:
    """Test cache hit rate measurement."""
    
    @pytest.mark.asyncio
    async def test_measure_cache_hit_rate(self, cache_service, sample_feedback_stats):
        """Measure cache hit rate with sample workload."""
        insight_ids = [f"insight_{i}" for i in range(10)]
        
        # Populate cache for half the insights
        for i in range(5):
            stats = FeedbackStats(
                insight_id=insight_ids[i],
                total_ratings=10,
                average_rating=4.0,
                rating_distribution={1: 0, 2: 1, 3: 2, 4: 3, 5: 4},
                total_comments=5,
                total_flags=0,
                flag_types={}
            )
            await cache_service.cache_feedback_stats(insight_ids[i], stats)
        
        # Simulate workload
        hits = 0
        misses = 0
        
        for insight_id in insight_ids:
            cached = await cache_service.get_feedback_stats(insight_id)
            if cached:
                hits += 1
            else:
                misses += 1
        
        # Calculate hit rate
        hit_rate = hits / (hits + misses) * 100
        
        assert hits == 5
        assert misses == 5
        assert hit_rate == 50.0
        
        # Simulate second pass (all should hit)
        hits = 0
        misses = 0
        
        # Cache remaining insights
        for i in range(5, 10):
            stats = FeedbackStats(
                insight_id=insight_ids[i],
                total_ratings=10,
                average_rating=4.0,
                rating_distribution={1: 0, 2: 1, 3: 2, 4: 3, 5: 4},
                total_comments=5,
                total_flags=0,
                flag_types={}
            )
            await cache_service.cache_feedback_stats(insight_ids[i], stats)
        
        for insight_id in insight_ids:
            cached = await cache_service.get_feedback_stats(insight_id)
            if cached:
                hits += 1
            else:
                misses += 1
        
        hit_rate = hits / (hits + misses) * 100
        
        assert hits == 10
        assert misses == 0
        assert hit_rate == 100.0
