"""Unit tests for database model structure and validation."""
import pytest
from datetime import datetime
from uuid import uuid4


def test_backfill_job_model_structure():
    """Test BackfillJob model has required attributes."""
    try:
        from src.models.db_models import BackfillJob
        
        # Check that the model has all required columns
        assert hasattr(BackfillJob, 'id')
        assert hasattr(BackfillJob, 'job_type')
        assert hasattr(BackfillJob, 'start_block')
        assert hasattr(BackfillJob, 'end_block')
        assert hasattr(BackfillJob, 'current_block')
        assert hasattr(BackfillJob, 'status')
        assert hasattr(BackfillJob, 'progress_percentage')
        assert hasattr(BackfillJob, 'estimated_completion')
        assert hasattr(BackfillJob, 'error_message')
        assert hasattr(BackfillJob, 'started_at')
        assert hasattr(BackfillJob, 'completed_at')
        assert hasattr(BackfillJob, 'created_by')
        
        # Check table name
        assert BackfillJob.__tablename__ == 'backfill_jobs'
        
    except ImportError:
        pytest.skip("SQLAlchemy not installed")


def test_insight_feedback_model_structure():
    """Test InsightFeedback model has required attributes."""
    try:
        from src.models.db_models import InsightFeedback
        
        # Check that the model has all required columns
        assert hasattr(InsightFeedback, 'id')
        assert hasattr(InsightFeedback, 'insight_id')
        assert hasattr(InsightFeedback, 'user_id')
        assert hasattr(InsightFeedback, 'rating')
        assert hasattr(InsightFeedback, 'comment')
        assert hasattr(InsightFeedback, 'flag_type')
        assert hasattr(InsightFeedback, 'flag_reason')
        assert hasattr(InsightFeedback, 'created_at')
        assert hasattr(InsightFeedback, 'updated_at')
        
        # Check table name
        assert InsightFeedback.__tablename__ == 'insight_feedback'
        
    except ImportError:
        pytest.skip("SQLAlchemy not installed")


def test_system_metric_model_structure():
    """Test SystemMetric model has required attributes."""
    try:
        from src.models.db_models import SystemMetric
        
        # Check that the model has all required columns
        assert hasattr(SystemMetric, 'id')
        assert hasattr(SystemMetric, 'service_name')
        assert hasattr(SystemMetric, 'metric_type')
        assert hasattr(SystemMetric, 'metric_value')
        assert hasattr(SystemMetric, 'unit')
        assert hasattr(SystemMetric, 'timestamp')
        assert hasattr(SystemMetric, 'metric_metadata')
        
        # Check table name
        assert SystemMetric.__tablename__ == 'system_metrics'
        
    except ImportError:
        pytest.skip("SQLAlchemy not installed")


def test_pydantic_schemas_structure():
    """Test Pydantic schemas are properly defined."""
    try:
        from src.models.database_schemas import (
            BackfillJobCreate, BackfillJobUpdate, BackfillJobResponse,
            FeedbackCreate, FeedbackResponse, FeedbackStats,
            MetricCreate, MetricResponse, MetricQuery
        )
        
        # Test BackfillJob schemas
        assert hasattr(BackfillJobCreate, 'model_fields')
        assert hasattr(BackfillJobUpdate, 'model_fields')
        assert hasattr(BackfillJobResponse, 'model_fields')
        
        # Test Feedback schemas
        assert hasattr(FeedbackCreate, 'model_fields')
        assert hasattr(FeedbackResponse, 'model_fields')
        assert hasattr(FeedbackStats, 'model_fields')
        
        # Test Metric schemas
        assert hasattr(MetricCreate, 'model_fields')
        assert hasattr(MetricResponse, 'model_fields')
        assert hasattr(MetricQuery, 'model_fields')
        
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_backfill_job_create_schema_validation():
    """Test BackfillJobCreate schema validation."""
    try:
        from src.models.database_schemas import BackfillJobCreate
        
        # Valid data
        valid_data = {
            "job_type": "blocks",
            "start_block": 800000,
            "end_block": 810000,
            "created_by": "test_user"
        }
        
        job = BackfillJobCreate(**valid_data)
        assert job.job_type == "blocks"
        assert job.start_block == 800000
        assert job.end_block == 810000
        assert job.created_by == "test_user"
        
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_feedback_create_schema_validation():
    """Test FeedbackCreate schema validation."""
    try:
        from src.models.database_schemas import FeedbackCreate
        
        # Valid data with rating
        valid_data = {
            "insight_id": "insight_123",
            "user_id": "user_456",
            "rating": 5,
            "comment": "Great insight!"
        }
        
        feedback = FeedbackCreate(**valid_data)
        assert feedback.insight_id == "insight_123"
        assert feedback.user_id == "user_456"
        assert feedback.rating == 5
        assert feedback.comment == "Great insight!"
        
    except ImportError:
        pytest.skip("Pydantic not installed")


def test_metric_create_schema_validation():
    """Test MetricCreate schema validation."""
    try:
        from src.models.database_schemas import MetricCreate
        
        # Valid data
        valid_data = {
            "service_name": "web-api",
            "metric_type": "cpu",
            "metric_value": 45.5,
            "unit": "percent",
            "metric_metadata": {"host": "server-01"}
        }
        
        metric = MetricCreate(**valid_data)
        assert metric.service_name == "web-api"
        assert metric.metric_type == "cpu"
        assert metric.metric_value == 45.5
        assert metric.unit == "percent"
        assert metric.metric_metadata == {"host": "server-01"}
        
    except ImportError:
        pytest.skip("Pydantic not installed")
