"""Integration tests for database-backed API endpoints.

These tests require Docker services to be running:
    docker-compose up -d postgres redis

Run tests with:
    pytest tests/test_api_database_integration.py -v
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from uuid import uuid4

from src.main import app

client = TestClient(app)


@pytest.mark.asyncio
class TestBackfillAPIEndpoints:
    """Test backfill API endpoints with database integration."""
    
    async def test_start_backfill_job(self, clean_database, async_client):
        """Test starting a new backfill job creates database record."""
        job_data = {
            "job_type": "blocks",
            "start_block": 800000,
            "end_block": 810000,
            "created_by": "test@utxoiq.com"
        }
        
        response = await async_client.post("/api/v1/monitoring/backfill/start", json=job_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["job_type"] == "blocks"
        assert data["start_block"] == 800000
        assert data["end_block"] == 810000
        assert data["status"] == "running"
        assert data["progress_percentage"] == 0.0
        assert "id" in data
    
    async def test_start_backfill_job_validation_error(self, clean_database):
        """Test backfill job creation with invalid data."""
        job_data = {
            "job_type": "blocks",
            "start_block": 810000,
            "end_block": 800000,  # Invalid: end < start
            "created_by": "test@utxoiq.com"
        }
        
        response = client.post("/api/v1/monitoring/backfill/start", json=job_data)
        assert response.status_code == 400
    
    async def test_update_backfill_progress(self, clean_database, async_client):
        """Test updating backfill job progress updates database."""
        # First create a job via API
        job_data = {
            "job_type": "blocks",
            "start_block": 800000,
            "end_block": 810000,
            "created_by": "test@utxoiq.com"
        }
        create_response = await async_client.post("/api/v1/monitoring/backfill/start", json=job_data)
        assert create_response.status_code == 200
        job_id = create_response.json()["id"]
        
        # Update progress
        progress_data = {
            "current_block": 805000,
            "progress_percentage": 50.0,
            "status": "running"
        }
        
        response = await async_client.post(
            f"/api/v1/monitoring/backfill/progress?job_id={job_id}",
            json=progress_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_block"] == 805000
        assert data["progress_percentage"] == 50.0
        assert data["status"] == "running"
    
    async def test_get_backfill_status(self, clean_database, async_client):
        """Test querying backfill job status from database."""
        # Create test jobs via API
        job1_data = {
            "job_type": "blocks",
            "start_block": 800000,
            "end_block": 810000
        }
        job2_data = {
            "job_type": "transactions",
            "start_block": 810000,
            "end_block": 820000
        }
        
        await async_client.post("/api/v1/monitoring/backfill/start", json=job1_data)
        await async_client.post("/api/v1/monitoring/backfill/start", json=job2_data)
        
        # Query all jobs
        response = await async_client.get("/api/v1/monitoring/backfill/status")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    async def test_get_backfill_status_with_filter(self, clean_database, async_client):
        """Test querying backfill jobs with status filter."""
        # Create a job and mark it as completed
        job_data = {
            "job_type": "blocks",
            "start_block": 800000,
            "end_block": 810000
        }
        create_response = await async_client.post("/api/v1/monitoring/backfill/start", json=job_data)
        assert create_response.status_code == 200
        job_id = create_response.json()["id"]
        
        # Complete the job
        progress_data = {
            "current_block": 810000,
            "progress_percentage": 100.0,
            "status": "completed"
        }
        update_response = await async_client.post(
            f"/api/v1/monitoring/backfill/progress?job_id={job_id}",
            json=progress_data
        )
        assert update_response.status_code == 200
        
        # Query completed jobs
        response = await async_client.get("/api/v1/monitoring/backfill/status?status=completed")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        assert all(job["status"] == "completed" for job in data)
    
    async def test_get_backfill_job_by_id(self, clean_database, async_client):
        """Test retrieving specific backfill job with caching."""
        # Create a job via API
        job_data = {
            "job_type": "blocks",
            "start_block": 800000,
            "end_block": 810000
        }
        create_response = await async_client.post("/api/v1/monitoring/backfill/start", json=job_data)
        job_id = create_response.json()["id"]
        
        # Get job by ID
        response = await async_client.get(f"/api/v1/monitoring/backfill/{job_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == job_id
        assert data["job_type"] == "blocks"
    
    async def test_get_backfill_job_not_found(self, clean_database, async_client):
        """Test retrieving non-existent backfill job."""
        fake_id = uuid4()
        response = await async_client.get(f"/api/v1/monitoring/backfill/{fake_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestFeedbackAPIEndpoints:
    """Test feedback API endpoints with database integration."""
    
    async def test_rate_insight(self, clean_database, async_client):
        """Test rating an insight stores in database and invalidates cache."""
        feedback_data = {
            "insight_id": "insight_123",
            "user_id": "user_456",
            "rating": 5,
            "comment": "Very insightful"
        }
        
        response = await async_client.post("/api/v1/feedback/rate", json=feedback_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["insight_id"] == "insight_123"
        assert data["user_id"] == "user_456"
        assert data["rating"] == 5
        assert data["comment"] == "Very insightful"
        assert "id" in data
    
    async def test_rate_insight_validation_error(self, clean_database):
        """Test rating with invalid value."""
        feedback_data = {
            "insight_id": "insight_123",
            "user_id": "user_456",
            "rating": 6  # Invalid: must be 1-5
        }
        
        response = client.post("/api/v1/feedback/rate", json=feedback_data)
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422
    
    async def test_comment_on_insight(self, clean_database, async_client):
        """Test adding comment to insight stores in database."""
        feedback_data = {
            "insight_id": "insight_123",
            "user_id": "user_456",
            "comment": "Great analysis of the mempool situation"
        }
        
        response = await async_client.post("/api/v1/feedback/comment", json=feedback_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["insight_id"] == "insight_123"
        assert data["comment"] == "Great analysis of the mempool situation"
    
    async def test_flag_insight(self, clean_database, async_client):
        """Test flagging insight stores in database."""
        feedback_data = {
            "insight_id": "insight_123",
            "user_id": "user_456",
            "flag_type": "inaccurate",
            "flag_reason": "Data seems incorrect"
        }
        
        response = await async_client.post("/api/v1/feedback/flag", json=feedback_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["insight_id"] == "insight_123"
        assert data["flag_type"] == "inaccurate"
    
    async def test_get_feedback_stats(self, clean_database, async_client):
        """Test retrieving feedback stats uses cached aggregations."""
        # Create feedback via API
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_123",
            "user_id": "user_1",
            "rating": 5
        })
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_123",
            "user_id": "user_2",
            "rating": 4
        })
        
        # Get stats
        response = await async_client.get("/api/v1/feedback/stats?insight_id=insight_123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["insight_id"] == "insight_123"
        assert data["total_ratings"] == 2
        assert data["average_rating"] > 0
        assert "rating_distribution" in data
    
    async def test_get_insight_comments(self, clean_database, async_client):
        """Test retrieving comments for an insight."""
        # Create feedback with comments via API
        await async_client.post("/api/v1/feedback/comment", json={
            "insight_id": "insight_123",
            "user_id": "user_1",
            "comment": "Great insight!"
        })
        await async_client.post("/api/v1/feedback/comment", json={
            "insight_id": "insight_123",
            "user_id": "user_2",
            "comment": "Very helpful"
        })
        
        # Get comments
        response = await async_client.get("/api/v1/feedback/comments?insight_id=insight_123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["insight_id"] == "insight_123"
        assert len(data["comments"]) >= 2
    
    async def test_get_user_feedback(self, clean_database, async_client):
        """Test retrieving user's feedback history."""
        # Create feedback via API
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_1",
            "user_id": "user_123",
            "rating": 5
        })
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_2",
            "user_id": "user_123",
            "rating": 4
        })
        
        # Get user feedback
        response = await async_client.get("/api/v1/feedback/user?user_id=user_123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == "user_123"
        assert len(data["feedback"]) >= 2


@pytest.mark.asyncio
class TestMetricsAPIEndpoints:
    """Test metrics API endpoints with database integration."""
    
    async def test_record_metric(self, clean_database, async_client):
        """Test recording a metric in database."""
        metric_data = {
            "service_name": "web-api",
            "metric_type": "cpu",
            "metric_value": 45.5,
            "unit": "percent",
            "metric_metadata": {"host": "server-01"}
        }
        
        response = await async_client.post("/api/v1/monitoring/metrics", json=metric_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "web-api"
        assert data["metric_type"] == "cpu"
        assert data["metric_value"] == 45.5
        assert "id" in data
    
    async def test_record_metrics_batch(self, clean_database, async_client):
        """Test recording multiple metrics in a batch."""
        metrics_data = [
            {
                "service_name": "web-api",
                "metric_type": "cpu",
                "metric_value": 45.5,
                "unit": "percent"
            },
            {
                "service_name": "web-api",
                "metric_type": "memory",
                "metric_value": 2048.0,
                "unit": "MB"
            }
        ]
        
        response = await async_client.post("/api/v1/monitoring/metrics/batch", json=metrics_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert all("id" in metric for metric in data)
    
    async def test_get_metrics_with_time_range(self, clean_database, async_client):
        """Test querying metrics with time range filters."""
        # Create metric via API
        metric_data = {
            "service_name": "web-api",
            "metric_type": "cpu",
            "metric_value": 45.5,
            "unit": "percent"
        }
        await async_client.post("/api/v1/monitoring/metrics", json=metric_data)
        
        # Query metrics
        now = datetime.utcnow()
        start_time = (now - timedelta(hours=1)).isoformat()
        end_time = now.isoformat()
        
        response = await async_client.get(
            f"/api/v1/monitoring/metrics?service_name=web-api&metric_type=cpu"
            f"&start_time={start_time}&end_time={end_time}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_get_aggregated_metrics(self, clean_database, async_client):
        """Test retrieving aggregated metrics for hourly/daily rollups."""
        # Create metrics via API
        for i in range(5):
            metric_data = {
                "service_name": "web-api",
                "metric_type": "cpu",
                "metric_value": 40.0 + i,
                "unit": "percent"
            }
            await async_client.post("/api/v1/monitoring/metrics", json=metric_data)
        
        # Get aggregated metrics
        now = datetime.utcnow()
        start_time = (now - timedelta(hours=24)).isoformat()
        end_time = now.isoformat()
        
        response = await async_client.get(
            f"/api/v1/monitoring/metrics/aggregate?service_name=web-api&metric_type=cpu"
            f"&start_time={start_time}&end_time={end_time}&interval=hour"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["service_name"] == "web-api"
        assert data["metric_type"] == "cpu"
        assert data["interval"] == "hour"
        assert "data" in data


@pytest.mark.asyncio
class TestCacheBehavior:
    """Test cache behavior through API calls."""
    
    async def test_feedback_stats_cache_hit(self, clean_database, async_client):
        """Test that feedback stats are cached after first query."""
        # Create feedback via API
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_cache_test",
            "user_id": "user_1",
            "rating": 5
        })
        
        # First request (cache miss)
        response1 = await async_client.get("/api/v1/feedback/stats?insight_id=insight_cache_test")
        assert response1.status_code == 200
        
        # Second request (should hit cache)
        response2 = await async_client.get("/api/v1/feedback/stats?insight_id=insight_cache_test")
        assert response2.status_code == 200
        assert response1.json() == response2.json()
    
    async def test_cache_invalidation_on_update(self, clean_database, async_client):
        """Test that cache is invalidated when feedback is updated."""
        # Create initial feedback via API
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_invalidate_test",
            "user_id": "user_1",
            "rating": 3
        })
        
        # Get stats (cache)
        response1 = await async_client.get("/api/v1/feedback/stats?insight_id=insight_invalidate_test")
        stats1 = response1.json()
        
        # Add new rating
        await async_client.post("/api/v1/feedback/rate", json={
            "insight_id": "insight_invalidate_test",
            "user_id": "user_2",
            "rating": 5
        })
        
        # Get stats again (should be updated)
        response2 = await async_client.get("/api/v1/feedback/stats?insight_id=insight_invalidate_test")
        stats2 = response2.json()
        
        assert stats2["total_ratings"] > stats1["total_ratings"]


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error responses for database failures."""
    
    async def test_database_error_handling(self, clean_database, async_client):
        """Test that database errors return appropriate HTTP status codes."""
        # Try to update non-existent job
        fake_id = uuid4()
        progress_data = {
            "current_block": 805000,
            "progress_percentage": 50.0
        }
        
        response = await async_client.post(
            f"/api/v1/monitoring/backfill/progress?job_id={fake_id}",
            json=progress_data
        )
        assert response.status_code == 404
    
    async def test_validation_error_handling(self, clean_database):
        """Test that validation errors return 422 status code (FastAPI standard)."""
        # Invalid rating value
        feedback_data = {
            "insight_id": "insight_123",
            "user_id": "user_456",
            "rating": 10  # Invalid
        }
        
        response = client.post("/api/v1/feedback/rate", json=feedback_data)
        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
