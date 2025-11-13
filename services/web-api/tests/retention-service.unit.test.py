"""Tests for data retention service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from src.services.retention_service import RetentionService, RetentionConfig
from src.models.db_models import BackfillJob, InsightFeedback, SystemMetric
from src.services.database_exceptions import DatabaseError


@pytest.fixture
def mock_gcs_client():
    """Mock Google Cloud Storage client."""
    with patch('src.services.retention_service.storage.Client') as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_client.return_value.bucket.return_value = mock_bucket
        yield mock_client


@pytest.fixture
async def retention_service(mock_gcs_client):
    """Create retention service instance with mocked GCS."""
    service = RetentionService(gcp_project_id="test-project")
    async with service:
        yield service


@pytest.fixture
async def old_backfill_jobs(clean_database):
    """Create old backfill jobs for testing."""
    from src.database import AsyncSessionLocal
    
    old_date = datetime.utcnow() - timedelta(days=200)  # Older than 180 days
    recent_date = datetime.utcnow() - timedelta(days=100)  # Newer than 180 days
    
    jobs = []
    async with AsyncSessionLocal() as session:
        # Create old jobs (should be archived)
        for i in range(3):
            job = BackfillJob(
                id=uuid4(),
                job_type="blocks",
                start_block=1000 + i * 1000,
                end_block=2000 + i * 1000,
                current_block=2000 + i * 1000,
                status="completed",
                progress_percentage=100.0,
                started_at=old_date,
                completed_at=old_date + timedelta(hours=2)
            )
            session.add(job)
            jobs.append(job)
        
        # Create recent jobs (should NOT be archived)
        for i in range(2):
            job = BackfillJob(
                id=uuid4(),
                job_type="transactions",
                start_block=3000 + i * 1000,
                end_block=4000 + i * 1000,
                current_block=4000 + i * 1000,
                status="completed",
                progress_percentage=100.0,
                started_at=recent_date,
                completed_at=recent_date + timedelta(hours=1)
            )
            session.add(job)
            jobs.append(job)
        
        await session.commit()
    
    return jobs


@pytest.fixture
async def old_feedback(clean_database):
    """Create old feedback for testing."""
    from src.database import AsyncSessionLocal
    
    old_date = datetime.utcnow() - timedelta(days=750)  # Older than 2 years
    recent_date = datetime.utcnow() - timedelta(days=365)  # Newer than 2 years
    
    feedbacks = []
    async with AsyncSessionLocal() as session:
        # Create old feedback (should be archived)
        for i in range(4):
            feedback = InsightFeedback(
                id=uuid4(),
                insight_id=f"insight_{i}",
                user_id=f"user_{i}",
                rating=4,
                comment=f"Test comment {i}",
                created_at=old_date,
                updated_at=old_date
            )
            session.add(feedback)
            feedbacks.append(feedback)
        
        # Create recent feedback (should NOT be archived)
        for i in range(2):
            feedback = InsightFeedback(
                id=uuid4(),
                insight_id=f"insight_recent_{i}",
                user_id=f"user_recent_{i}",
                rating=5,
                comment=f"Recent comment {i}",
                created_at=recent_date,
                updated_at=recent_date
            )
            session.add(feedback)
            feedbacks.append(feedback)
        
        await session.commit()
    
    return feedbacks


@pytest.fixture
async def old_metrics(clean_database):
    """Create old metrics for testing."""
    from src.database import AsyncSessionLocal
    
    old_date = datetime.utcnow() - timedelta(days=100)  # Older than 90 days
    very_old_date = datetime.utcnow() - timedelta(days=400)  # Older than 1 year
    recent_date = datetime.utcnow() - timedelta(days=30)  # Newer than 90 days
    
    metrics = []
    async with AsyncSessionLocal() as session:
        # Create old metrics (should be archived)
        for i in range(5):
            metric = SystemMetric(
                id=uuid4(),
                service_name="test-service",
                metric_type="cpu",
                metric_value=50.0 + i,
                unit="percent",
                timestamp=old_date - timedelta(hours=i)
            )
            session.add(metric)
            metrics.append(metric)
        
        # Create very old metrics (should be deleted)
        for i in range(3):
            metric = SystemMetric(
                id=uuid4(),
                service_name="test-service",
                metric_type="memory",
                metric_value=60.0 + i,
                unit="percent",
                timestamp=very_old_date - timedelta(hours=i)
            )
            session.add(metric)
            metrics.append(metric)
        
        # Create recent metrics (should NOT be archived)
        for i in range(2):
            metric = SystemMetric(
                id=uuid4(),
                service_name="test-service",
                metric_type="latency",
                metric_value=100.0 + i,
                unit="ms",
                timestamp=recent_date - timedelta(hours=i)
            )
            session.add(metric)
            metrics.append(metric)
        
        await session.commit()
    
    return metrics


class TestBackfillJobRetention:
    """Tests for backfill job retention."""
    
    @pytest.mark.asyncio
    async def test_archive_old_backfill_jobs(self, retention_service, old_backfill_jobs):
        """Test archiving old backfill jobs."""
        from src.database import AsyncSessionLocal
        from sqlalchemy import select
        
        # Run archival
        result = await retention_service.archive_old_backfill_jobs()
        
        # Verify results
        assert result["archived_count"] == 3  # Only old jobs
        assert result["deleted_count"] == 3
        assert result["archive_uri"] is not None
        assert "gs://" in result["archive_uri"]
        
        # Verify old jobs were deleted from database
        async with AsyncSessionLocal() as session:
            remaining_jobs = await session.execute(select(BackfillJob))
            remaining_jobs = remaining_jobs.scalars().all()
            assert len(remaining_jobs) == 2  # Only recent jobs remain
    
    @pytest.mark.asyncio
    async def test_archive_no_old_jobs(self, retention_service, clean_database):
        """Test archival when no old jobs exist."""
        result = await retention_service.archive_old_backfill_jobs()
        
        assert result["archived_count"] == 0
        assert result["deleted_count"] == 0
        assert result["archive_uri"] is None
    
    @pytest.mark.asyncio
    async def test_archive_verifies_data_integrity(self, retention_service, old_backfill_jobs, mock_gcs_client):
        """Test that archived data contains all required fields."""
        result = await retention_service.archive_old_backfill_jobs()
        
        # Get the uploaded data from mock
        mock_blob = mock_gcs_client.return_value.bucket.return_value.blob.return_value
        uploaded_data = mock_blob.upload_from_string.call_args[0][0]
        
        # Verify data structure
        import json
        archived_jobs = json.loads(uploaded_data)
        
        assert len(archived_jobs) == 3
        for job in archived_jobs:
            assert "id" in job
            assert "job_type" in job
            assert "start_block" in job
            assert "end_block" in job
            assert "status" in job
            assert "started_at" in job


class TestFeedbackRetention:
    """Tests for feedback retention."""
    
    @pytest.mark.asyncio
    async def test_archive_old_feedback(self, retention_service, old_feedback):
        """Test archiving old feedback."""
        from src.database import AsyncSessionLocal
        from sqlalchemy import select
        
        # Run archival
        result = await retention_service.archive_old_feedback()
        
        # Verify results
        assert result["archived_count"] == 4  # Only old feedback
        assert result["deleted_count"] == 4
        assert result["archive_uri"] is not None
        
        # Verify old feedback was deleted from database
        async with AsyncSessionLocal() as session:
            remaining_feedback = await session.execute(select(InsightFeedback))
            remaining_feedback = remaining_feedback.scalars().all()
            assert len(remaining_feedback) == 2  # Only recent feedback remains
    
    @pytest.mark.asyncio
    async def test_archive_no_old_feedback(self, retention_service, clean_database):
        """Test archival when no old feedback exists."""
        result = await retention_service.archive_old_feedback()
        
        assert result["archived_count"] == 0
        assert result["deleted_count"] == 0
        assert result["archive_uri"] is None


class TestMetricsRetention:
    """Tests for metrics retention."""
    
    @pytest.mark.asyncio
    async def test_archive_old_metrics(self, retention_service, old_metrics):
        """Test archiving old metrics."""
        from src.database import AsyncSessionLocal
        from sqlalchemy import select
        
        # Run archival
        result = await retention_service.archive_old_metrics()
        
        # Verify results
        assert result["archived_count"] == 8  # Old + very old metrics
        assert len(result["archive_uris"]) > 0
        
        # Note: Archival doesn't delete metrics, only archives them
        async with AsyncSessionLocal() as session:
            remaining_metrics = await session.execute(select(SystemMetric))
            remaining_metrics = remaining_metrics.scalars().all()
            assert len(remaining_metrics) == 10  # All metrics still in database
    
    @pytest.mark.asyncio
    async def test_delete_old_archived_metrics(self, retention_service, old_metrics):
        """Test deleting very old metrics."""
        from src.database import AsyncSessionLocal
        from sqlalchemy import select
        
        # Run deletion
        result = await retention_service.delete_old_archived_metrics()
        
        # Verify results
        assert result["deleted_count"] == 3  # Only very old metrics
        
        # Verify very old metrics were deleted
        async with AsyncSessionLocal() as session:
            remaining_metrics = await session.execute(select(SystemMetric))
            remaining_metrics = remaining_metrics.scalars().all()
            assert len(remaining_metrics) == 7  # Old + recent metrics remain
    
    @pytest.mark.asyncio
    async def test_archive_no_old_metrics(self, retention_service, clean_database):
        """Test archival when no old metrics exist."""
        result = await retention_service.archive_old_metrics()
        
        assert result["archived_count"] == 0
        assert len(result["archive_uris"]) == 0


class TestRetentionPolicyExecution:
    """Tests for running all retention policies."""
    
    @pytest.mark.asyncio
    async def test_run_all_retention_policies(
        self, 
        retention_service, 
        old_backfill_jobs, 
        old_feedback, 
        old_metrics
    ):
        """Test running all retention policies together."""
        result = await retention_service.run_all_retention_policies()
        
        # Verify all policies executed
        assert "execution_time" in result
        assert "backfill_jobs" in result
        assert "feedback" in result
        assert "metrics_archive" in result
        assert "metrics_delete" in result
        
        # Verify each policy returned results
        assert result["backfill_jobs"]["archived_count"] == 3
        assert result["feedback"]["archived_count"] == 4
        assert result["metrics_archive"]["archived_count"] == 8
        assert result["metrics_delete"]["deleted_count"] == 3
    
    @pytest.mark.asyncio
    async def test_run_all_policies_handles_partial_failures(self, retention_service, clean_database):
        """Test that one policy failure doesn't stop others."""
        # Mock one policy to fail
        with patch.object(retention_service, 'archive_old_backfill_jobs', side_effect=DatabaseError("Test error")):
            result = await retention_service.run_all_retention_policies()
            
            # Verify error was captured
            assert "error" in result["backfill_jobs"]
            
            # Verify other policies still ran
            assert result["feedback"]["archived_count"] == 0  # No data to archive
            assert result["metrics_archive"]["archived_count"] == 0


class TestRetentionConfiguration:
    """Tests for retention configuration."""
    
    def test_retention_config_values(self):
        """Test retention configuration constants."""
        assert RetentionConfig.BACKFILL_JOB_RETENTION_DAYS == 180
        assert RetentionConfig.FEEDBACK_RETENTION_DAYS == 730
        assert RetentionConfig.METRICS_HOT_STORAGE_DAYS == 90
        assert RetentionConfig.METRICS_COLD_STORAGE_DAYS == 365
        assert RetentionConfig.ARCHIVE_BUCKET_NAME == "utxoiq-archives"


class TestGCSUpload:
    """Tests for GCS upload functionality."""
    
    @pytest.mark.asyncio
    async def test_upload_to_gcs_success(self, retention_service, mock_gcs_client):
        """Test successful upload to GCS."""
        test_data = [{"id": "1", "value": "test"}]
        
        uri = retention_service._upload_to_gcs(
            test_data,
            "test_path",
            "test_file.json"
        )
        
        assert uri == "gs://utxoiq-archives/test_path/test_file.json"
        
        # Verify upload was called
        mock_blob = mock_gcs_client.return_value.bucket.return_value.blob.return_value
        mock_blob.upload_from_string.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_to_gcs_failure(self, retention_service, mock_gcs_client):
        """Test GCS upload failure handling."""
        # Mock upload failure
        mock_blob = mock_gcs_client.return_value.bucket.return_value.blob.return_value
        mock_blob.upload_from_string.side_effect = Exception("Upload failed")
        
        test_data = [{"id": "1", "value": "test"}]
        
        with pytest.raises(DatabaseError, match="Archive upload failed"):
            retention_service._upload_to_gcs(
                test_data,
                "test_path",
                "test_file.json"
            )
