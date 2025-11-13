"""Integration tests for database service operations."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.models.db_models import Base, BackfillJob, InsightFeedback, SystemMetric
from src.models.database_schemas import (
    BackfillJobCreate, BackfillJobUpdate,
    FeedbackCreate, MetricCreate
)
from src.services.database_service import DatabaseService
from src.services.database_exceptions import (
    NotFoundError, ValidationError, IntegrityError
)


# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def db_service(test_session):
    """Create database service with test session."""
    service = DatabaseService()
    service.session = test_session
    return service


# ==================== Backfill Job Tests ====================

@pytest.mark.asyncio
async def test_create_backfill_job(db_service):
    """Test creating a backfill job."""
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000,
        created_by="test_user"
    )
    
    result = await db_service.create_backfill_job(job_data)
    
    assert result.job_type == "blocks"
    assert result.start_block == 800000
    assert result.end_block == 810000
    assert result.current_block == 800000
    assert result.status == "running"
    assert result.progress_percentage == 0.0
    assert result.created_by == "test_user"


@pytest.mark.asyncio
async def test_create_backfill_job_invalid_range(db_service):
    """Test creating a backfill job with invalid block range."""
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=810000,
        end_block=800000  # Invalid: end < start
    )
    
    with pytest.raises(ValidationError):
        await db_service.create_backfill_job(job_data)


@pytest.mark.asyncio
async def test_update_backfill_progress(db_service):
    """Test updating backfill job progress."""
    # Create job
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    job = await db_service.create_backfill_job(job_data)
    
    # Update progress
    update_data = BackfillJobUpdate(
        current_block=805000,
        progress_percentage=50.0,
        status="running"
    )
    
    updated = await db_service.update_backfill_progress(job.id, update_data)
    
    assert updated.current_block == 805000
    assert updated.progress_percentage == 50.0
    assert updated.status == "running"


@pytest.mark.asyncio
async def test_update_backfill_progress_invalid_block(db_service):
    """Test updating with invalid current block."""
    # Create job
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    job = await db_service.create_backfill_job(job_data)
    
    # Try to update with invalid block
    update_data = BackfillJobUpdate(
        current_block=820000,  # Exceeds end_block
        progress_percentage=100.0
    )
    
    with pytest.raises(ValidationError):
        await db_service.update_backfill_progress(job.id, update_data)


@pytest.mark.asyncio
async def test_get_backfill_job(db_service):
    """Test retrieving a backfill job."""
    # Create job
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    created = await db_service.create_backfill_job(job_data)
    
    # Retrieve job
    retrieved = await db_service.get_backfill_job(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.job_type == "blocks"


@pytest.mark.asyncio
async def test_get_backfill_job_not_found(db_service):
    """Test retrieving non-existent job."""
    result = await db_service.get_backfill_job(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_backfill_jobs(db_service):
    """Test listing backfill jobs."""
    # Create multiple jobs
    for i in range(3):
        job_data = BackfillJobCreate(
            job_type="blocks",
            start_block=800000 + (i * 10000),
            end_block=810000 + (i * 10000)
        )
        await db_service.create_backfill_job(job_data)
    
    # List all jobs
    jobs = await db_service.list_backfill_jobs()
    assert len(jobs) == 3


@pytest.mark.asyncio
async def test_list_backfill_jobs_filtered(db_service):
    """Test listing backfill jobs with filters."""
    # Create jobs with different statuses
    job1_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    job1 = await db_service.create_backfill_job(job1_data)
    
    job2_data = BackfillJobCreate(
        job_type="transactions",
        start_block=810000,
        end_block=820000
    )
    await db_service.create_backfill_job(job2_data)
    
    # Complete first job
    await db_service.complete_backfill_job(job1.id)
    
    # List completed jobs
    completed_jobs = await db_service.list_backfill_jobs(status="completed")
    assert len(completed_jobs) == 1
    assert completed_jobs[0].status == "completed"
    
    # List by job type
    block_jobs = await db_service.list_backfill_jobs(job_type="blocks")
    assert len(block_jobs) == 1
    assert block_jobs[0].job_type == "blocks"


@pytest.mark.asyncio
async def test_complete_backfill_job(db_service):
    """Test completing a backfill job."""
    # Create job
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    job = await db_service.create_backfill_job(job_data)
    
    # Complete job
    completed = await db_service.complete_backfill_job(job.id)
    
    assert completed.status == "completed"
    assert completed.progress_percentage == 100.0
    assert completed.completed_at is not None


@pytest.mark.asyncio
async def test_fail_backfill_job(db_service):
    """Test failing a backfill job."""
    # Create job
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    job = await db_service.create_backfill_job(job_data)
    
    # Fail job
    error_msg = "Connection timeout"
    failed = await db_service.fail_backfill_job(job.id, error_msg)
    
    assert failed.status == "failed"
    assert failed.error_message == error_msg
    assert failed.completed_at is not None


# ==================== Feedback Tests ====================

@pytest.mark.asyncio
async def test_create_feedback(db_service):
    """Test creating insight feedback."""
    feedback_data = FeedbackCreate(
        insight_id="insight_123",
        user_id="user_456",
        rating=5,
        comment="Great insight!"
    )
    
    result = await db_service.create_feedback(feedback_data)
    
    assert result.insight_id == "insight_123"
    assert result.user_id == "user_456"
    assert result.rating == 5
    assert result.comment == "Great insight!"


@pytest.mark.asyncio
async def test_create_feedback_upsert(db_service):
    """Test upserting feedback (update existing)."""
    feedback_data = FeedbackCreate(
        insight_id="insight_123",
        user_id="user_456",
        rating=4,
        comment="Good"
    )
    
    # Create initial feedback
    first = await db_service.create_feedback(feedback_data)
    
    # Update with new rating
    updated_data = FeedbackCreate(
        insight_id="insight_123",
        user_id="user_456",
        rating=5,
        comment="Actually, excellent!"
    )
    
    second = await db_service.create_feedback(updated_data)
    
    # Should be same ID (updated, not created)
    assert first.id == second.id
    assert second.rating == 5
    assert second.comment == "Actually, excellent!"


@pytest.mark.asyncio
async def test_create_feedback_invalid_rating(db_service):
    """Test creating feedback with invalid rating."""
    feedback_data = FeedbackCreate(
        insight_id="insight_123",
        user_id="user_456",
        rating=6  # Invalid: must be 1-5
    )
    
    with pytest.raises(ValidationError):
        await db_service.create_feedback(feedback_data)


@pytest.mark.asyncio
async def test_get_feedback_stats(db_service):
    """Test getting aggregated feedback statistics."""
    insight_id = "insight_123"
    
    # Create multiple feedback entries
    ratings = [5, 4, 5, 3, 5]
    for i, rating in enumerate(ratings):
        feedback_data = FeedbackCreate(
            insight_id=insight_id,
            user_id=f"user_{i}",
            rating=rating,
            comment=f"Comment {i}" if i % 2 == 0 else None
        )
        await db_service.create_feedback(feedback_data)
    
    # Get stats
    stats = await db_service.get_feedback_stats(insight_id)
    
    assert stats.insight_id == insight_id
    assert stats.total_ratings == 5
    assert stats.average_rating == 4.4
    assert stats.rating_distribution[5] == 3
    assert stats.rating_distribution[4] == 1
    assert stats.rating_distribution[3] == 1
    assert stats.total_comments == 3


@pytest.mark.asyncio
async def test_get_feedback_stats_with_flags(db_service):
    """Test feedback stats with flags."""
    insight_id = "insight_123"
    
    # Create feedback with flags
    feedback1 = FeedbackCreate(
        insight_id=insight_id,
        user_id="user_1",
        rating=1,
        flag_type="inaccurate",
        flag_reason="Wrong data"
    )
    await db_service.create_feedback(feedback1)
    
    feedback2 = FeedbackCreate(
        insight_id=insight_id,
        user_id="user_2",
        rating=2,
        flag_type="spam",
        flag_reason="Looks like spam"
    )
    await db_service.create_feedback(feedback2)
    
    # Get stats
    stats = await db_service.get_feedback_stats(insight_id)
    
    assert stats.total_flags == 2
    assert stats.flag_types["inaccurate"] == 1
    assert stats.flag_types["spam"] == 1


@pytest.mark.asyncio
async def test_list_feedback(db_service):
    """Test listing feedback."""
    # Create feedback for multiple insights
    for i in range(3):
        feedback_data = FeedbackCreate(
            insight_id=f"insight_{i}",
            user_id="user_1",
            rating=5
        )
        await db_service.create_feedback(feedback_data)
    
    # List all feedback
    all_feedback = await db_service.list_feedback()
    assert len(all_feedback) == 3


@pytest.mark.asyncio
async def test_list_feedback_filtered(db_service):
    """Test listing feedback with filters."""
    # Create feedback
    feedback1 = FeedbackCreate(
        insight_id="insight_1",
        user_id="user_1",
        rating=5
    )
    await db_service.create_feedback(feedback1)
    
    feedback2 = FeedbackCreate(
        insight_id="insight_2",
        user_id="user_1",
        rating=4
    )
    await db_service.create_feedback(feedback2)
    
    feedback3 = FeedbackCreate(
        insight_id="insight_1",
        user_id="user_2",
        rating=3
    )
    await db_service.create_feedback(feedback3)
    
    # Filter by insight
    insight1_feedback = await db_service.list_feedback(insight_id="insight_1")
    assert len(insight1_feedback) == 2
    
    # Filter by user
    user1_feedback = await db_service.list_feedback(user_id="user_1")
    assert len(user1_feedback) == 2


# ==================== Metrics Tests ====================

@pytest.mark.asyncio
async def test_record_metric(db_service):
    """Test recording a single metric."""
    metric_data = MetricCreate(
        service_name="web-api",
        metric_type="cpu",
        metric_value=45.5,
        unit="percent",
        metric_metadata={"host": "server-01"}
    )
    
    result = await db_service.record_metric(metric_data)
    
    assert result.service_name == "web-api"
    assert result.metric_type == "cpu"
    assert result.metric_value == 45.5
    assert result.unit == "percent"
    assert result.metric_metadata == {"host": "server-01"}


@pytest.mark.asyncio
async def test_record_metrics_batch(db_service):
    """Test recording multiple metrics in batch."""
    metrics_data = [
        MetricCreate(
            service_name="web-api",
            metric_type="cpu",
            metric_value=45.5,
            unit="percent"
        ),
        MetricCreate(
            service_name="web-api",
            metric_type="memory",
            metric_value=2048.0,
            unit="MB"
        ),
        MetricCreate(
            service_name="web-api",
            metric_type="latency",
            metric_value=125.0,
            unit="ms"
        )
    ]
    
    results = await db_service.record_metrics_batch(metrics_data)
    
    assert len(results) == 3
    assert results[0].metric_type == "cpu"
    assert results[1].metric_type == "memory"
    assert results[2].metric_type == "latency"


@pytest.mark.asyncio
async def test_get_metrics(db_service):
    """Test querying metrics."""
    # Record metrics
    for i in range(5):
        metric_data = MetricCreate(
            service_name="web-api",
            metric_type="cpu",
            metric_value=40.0 + i,
            unit="percent"
        )
        await db_service.record_metric(metric_data)
    
    # Query all metrics
    metrics = await db_service.get_metrics()
    assert len(metrics) == 5


@pytest.mark.asyncio
async def test_get_metrics_filtered(db_service):
    """Test querying metrics with filters."""
    # Record metrics for different services
    metric1 = MetricCreate(
        service_name="web-api",
        metric_type="cpu",
        metric_value=45.0,
        unit="percent"
    )
    await db_service.record_metric(metric1)
    
    metric2 = MetricCreate(
        service_name="insight-generator",
        metric_type="cpu",
        metric_value=60.0,
        unit="percent"
    )
    await db_service.record_metric(metric2)
    
    metric3 = MetricCreate(
        service_name="web-api",
        metric_type="memory",
        metric_value=2048.0,
        unit="MB"
    )
    await db_service.record_metric(metric3)
    
    # Filter by service
    web_api_metrics = await db_service.get_metrics(service_name="web-api")
    assert len(web_api_metrics) == 2
    
    # Filter by metric type
    cpu_metrics = await db_service.get_metrics(metric_type="cpu")
    assert len(cpu_metrics) == 2


@pytest.mark.asyncio
async def test_get_metrics_time_range(db_service):
    """Test querying metrics with time range."""
    now = datetime.utcnow()
    
    # Record metrics at different times (simulated)
    for i in range(3):
        metric_data = MetricCreate(
            service_name="web-api",
            metric_type="cpu",
            metric_value=40.0 + i,
            unit="percent"
        )
        await db_service.record_metric(metric_data)
    
    # Query with time range
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    
    metrics = await db_service.get_metrics(
        service_name="web-api",
        start_time=start_time,
        end_time=end_time
    )
    
    assert len(metrics) == 3


@pytest.mark.asyncio
async def test_aggregate_metrics_hourly(db_service):
    """Test aggregating metrics by hour."""
    # Record multiple metrics
    for i in range(10):
        metric_data = MetricCreate(
            service_name="web-api",
            metric_type="cpu",
            metric_value=40.0 + (i * 2),
            unit="percent"
        )
        await db_service.record_metric(metric_data)
    
    # Aggregate
    now = datetime.utcnow()
    start_time = now - timedelta(hours=2)
    end_time = now + timedelta(hours=1)
    
    aggregated = await db_service.aggregate_metrics(
        service_name="web-api",
        metric_type="cpu",
        start_time=start_time,
        end_time=end_time,
        interval="hour"
    )
    
    # Should have at least one aggregated bucket
    assert len(aggregated) >= 1
    assert "avg_value" in aggregated[0]
    assert "min_value" in aggregated[0]
    assert "max_value" in aggregated[0]
    assert "count" in aggregated[0]


@pytest.mark.asyncio
async def test_aggregate_metrics_invalid_interval(db_service):
    """Test aggregating with invalid interval."""
    now = datetime.utcnow()
    
    with pytest.raises(ValidationError):
        await db_service.aggregate_metrics(
            service_name="web-api",
            metric_type="cpu",
            start_time=now - timedelta(hours=1),
            end_time=now,
            interval="minute"  # Invalid
        )


# ==================== Transaction Tests ====================

@pytest.mark.asyncio
async def test_transaction_rollback(test_session):
    """Test transaction rollback on error."""
    service = DatabaseService()
    service.session = test_session
    
    # Create a job
    job_data = BackfillJobCreate(
        job_type="blocks",
        start_block=800000,
        end_block=810000
    )
    
    try:
        async with service:
            await service.create_backfill_job(job_data)
            # Force an error
            raise Exception("Simulated error")
    except Exception:
        pass
    
    # Verify rollback - job should not exist
    service2 = DatabaseService()
    service2.session = test_session
    jobs = await service2.list_backfill_jobs()
    assert len(jobs) == 0


# ==================== Concurrent Operations Tests ====================

@pytest.mark.asyncio
async def test_concurrent_feedback_updates(db_service):
    """Test concurrent feedback updates (upsert behavior)."""
    insight_id = "insight_123"
    user_id = "user_456"
    
    # Simulate concurrent updates
    feedback1 = FeedbackCreate(
        insight_id=insight_id,
        user_id=user_id,
        rating=4
    )
    
    feedback2 = FeedbackCreate(
        insight_id=insight_id,
        user_id=user_id,
        rating=5
    )
    
    result1 = await db_service.create_feedback(feedback1)
    result2 = await db_service.create_feedback(feedback2)
    
    # Should be same record (upserted)
    assert result1.id == result2.id
    assert result2.rating == 5
