"""
Integration tests for backup verification service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from src.services.backup_verification_service import (
    BackupVerificationService,
    BackupVerificationError
)


@pytest.fixture
def mock_sql_client():
    """Mock Cloud SQL client"""
    return Mock()


@pytest.fixture
def mock_storage_client():
    """Mock Cloud Storage client"""
    return Mock()


@pytest.fixture
def verification_service(mock_sql_client, mock_storage_client):
    """Create backup verification service with mocked clients"""
    service = BackupVerificationService(
        project_id="test-project",
        instance_name="test-instance",
        backup_bucket="test-bucket"
    )
    service.sql_client = mock_sql_client
    service.backup_client = Mock()
    service.storage_client = mock_storage_client
    return service


class TestBackupVerificationService:
    """Test backup verification service"""
    
    @pytest.mark.asyncio
    async def test_get_latest_backup_success(self, verification_service):
        """Test getting latest successful backup"""
        # Mock backup response
        mock_backup = Mock()
        mock_backup.id = 12345
        mock_backup.status = 1  # SUCCESSFUL
        mock_backup.window_start_time = datetime.utcnow()
        
        verification_service.backup_client.list = Mock(return_value=[mock_backup])
        
        # Execute
        backup = await verification_service._get_latest_backup()
        
        # Verify
        assert backup.id == 12345
        assert backup.status == 1
    
    @pytest.mark.asyncio
    async def test_get_latest_backup_no_backups(self, verification_service):
        """Test error when no backups exist"""
        verification_service.backup_client.list = Mock(return_value=[])
        
        # Execute and verify
        with pytest.raises(BackupVerificationError, match="No successful backups found"):
            await verification_service._get_latest_backup()
    
    @pytest.mark.asyncio
    async def test_create_test_instance(self, verification_service):
        """Test creating test instance from backup"""
        # Mock source instance
        mock_source = Mock()
        mock_source.database_version = "POSTGRES_15"
        mock_source.region = "us-central1"
        
        verification_service.sql_client.get = Mock(return_value=mock_source)
        verification_service.sql_client.insert = Mock(return_value=Mock(name="operation-123"))
        
        # Execute
        await verification_service._create_test_instance("test-instance-123", 12345)
        
        # Verify
        verification_service.sql_client.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_wait_for_instance_ready_success(self, verification_service):
        """Test waiting for instance to become ready"""
        # Mock instance that becomes ready
        mock_instance = Mock()
        mock_instance.state = 2  # RUNNABLE
        
        verification_service.sql_client.get = Mock(return_value=mock_instance)
        
        # Execute (should complete without error)
        await verification_service._wait_for_instance_ready("test-instance", timeout_minutes=1)
    
    @pytest.mark.asyncio
    async def test_wait_for_instance_ready_timeout(self, verification_service):
        """Test timeout when instance doesn't become ready"""
        # Mock instance that never becomes ready
        mock_instance = Mock()
        mock_instance.state = 0  # PENDING
        
        verification_service.sql_client.get = Mock(return_value=mock_instance)
        
        # Execute and verify timeout
        with pytest.raises(BackupVerificationError, match="did not become ready"):
            await verification_service._wait_for_instance_ready("test-instance", timeout_minutes=0.01)
    
    @pytest.mark.asyncio
    async def test_verify_data_integrity(self, verification_service):
        """Test data integrity verification"""
        # Mock instance
        mock_instance = Mock()
        mock_instance.state = 2  # RUNNABLE
        
        verification_service.sql_client.get = Mock(return_value=mock_instance)
        
        # Execute
        checks = await verification_service._verify_data_integrity("test-instance")
        
        # Verify
        assert checks["instance_accessible"] is True
    
    @pytest.mark.asyncio
    async def test_schedule_cleanup(self, verification_service):
        """Test scheduling cleanup of test instance"""
        # Mock storage
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob = Mock(return_value=mock_blob)
        verification_service.storage_client.bucket = Mock(return_value=mock_bucket)
        
        # Execute
        cleanup_time = datetime.utcnow() + timedelta(hours=2)
        await verification_service._schedule_cleanup("test-instance", cleanup_time)
        
        # Verify
        mock_blob.upload_from_string.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_test_instance(self, verification_service):
        """Test deleting test instance"""
        verification_service.sql_client.delete = Mock(return_value=Mock(name="operation-456"))
        
        # Execute
        await verification_service._cleanup_test_instance("test-instance")
        
        # Verify
        verification_service.sql_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_verification_results(self, verification_service):
        """Test saving verification results to GCS"""
        # Mock storage
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob = Mock(return_value=mock_blob)
        verification_service.storage_client.bucket = Mock(return_value=mock_bucket)
        
        # Execute
        result = {
            "verification_id": "test-123",
            "status": "success"
        }
        await verification_service._save_verification_results(result)
        
        # Verify
        mock_blob.upload_from_string.assert_called_once()
        uploaded_data = mock_blob.upload_from_string.call_args[0][0]
        assert "test-123" in uploaded_data
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_instances(self, verification_service):
        """Test cleaning up expired test instances"""
        # Mock storage with expired cleanup schedule
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.name = "cleanup-schedule/test-instance.json"
        
        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        cleanup_info = {
            "instance_name": "test-instance",
            "cleanup_time": expired_time
        }
        mock_blob.download_as_string = Mock(return_value=json.dumps(cleanup_info).encode())
        
        mock_bucket.list_blobs = Mock(return_value=[mock_blob])
        verification_service.storage_client.bucket = Mock(return_value=mock_bucket)
        verification_service.sql_client.delete = Mock(return_value=Mock())
        
        # Execute
        await verification_service.cleanup_expired_instances()
        
        # Verify
        verification_service.sql_client.delete.assert_called_once()
        mock_blob.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_verification_history(self, verification_service):
        """Test retrieving verification history"""
        # Mock storage with verification results
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.name = "verification-results/20240115-120000.json"
        
        result = {
            "verification_id": "20240115-120000",
            "status": "success"
        }
        mock_blob.download_as_string = Mock(return_value=json.dumps(result).encode())
        
        mock_bucket.list_blobs = Mock(return_value=[mock_blob])
        verification_service.storage_client.bucket = Mock(return_value=mock_bucket)
        
        # Execute
        history = await verification_service.get_verification_history(limit=10)
        
        # Verify
        assert len(history) == 1
        assert history[0]["verification_id"] == "20240115-120000"
        assert history[0]["status"] == "success"


class TestBackupVerificationIntegration:
    """Integration tests for backup verification"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_verification_flow(self, verification_service):
        """Test complete verification flow (mocked)"""
        # Mock all dependencies
        mock_backup = Mock()
        mock_backup.id = 12345
        mock_backup.status = 1
        mock_backup.window_start_time = datetime.utcnow()
        
        verification_service.backup_client.list = Mock(return_value=[mock_backup])
        
        mock_source = Mock()
        mock_source.database_version = "POSTGRES_15"
        mock_source.region = "us-central1"
        
        mock_instance = Mock()
        mock_instance.state = 2  # RUNNABLE
        
        verification_service.sql_client.get = Mock(return_value=mock_source)
        verification_service.sql_client.insert = Mock(return_value=Mock())
        verification_service.sql_client.delete = Mock(return_value=Mock())
        
        # Override wait to return immediately
        async def mock_wait(*args, **kwargs):
            return
        verification_service._wait_for_instance_ready = mock_wait
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob = Mock(return_value=mock_blob)
        verification_service.storage_client.bucket = Mock(return_value=mock_bucket)
        
        # Execute
        result = await verification_service.verify_latest_backup()
        
        # Verify
        assert result["status"] == "success"
        assert "verification_id" in result
        assert len(result["steps"]) > 0
        
        # Verify all steps completed
        step_names = [step["step"] for step in result["steps"]]
        assert "get_latest_backup" in step_names
        assert "create_test_instance" in step_names
        assert "verify_integrity" in step_names


class TestBackupVerificationAPI:
    """Test backup verification API endpoints"""
    
    @pytest.mark.asyncio
    async def test_trigger_verification_endpoint(self):
        """Test triggering verification via API"""
        # This would test the actual API endpoint
        # Requires FastAPI test client setup
        pass
    
    @pytest.mark.asyncio
    async def test_get_verification_history_endpoint(self):
        """Test getting verification history via API"""
        # This would test the actual API endpoint
        # Requires FastAPI test client setup
        pass


# Performance tests
class TestBackupVerificationPerformance:
    """Performance tests for backup verification"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_verification_completes_within_time_limit(self, verification_service):
        """Test that verification completes within acceptable time"""
        # Mock fast responses
        mock_backup = Mock()
        mock_backup.id = 12345
        mock_backup.status = 1
        mock_backup.window_start_time = datetime.utcnow()
        
        verification_service.backup_client.list = Mock(return_value=[mock_backup])
        verification_service.sql_client.get = Mock(return_value=Mock())
        verification_service.sql_client.insert = Mock(return_value=Mock())
        verification_service.sql_client.delete = Mock(return_value=Mock())
        
        async def mock_wait(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate quick wait
        verification_service._wait_for_instance_ready = mock_wait
        
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob = Mock(return_value=mock_blob)
        verification_service.storage_client.bucket = Mock(return_value=mock_bucket)
        
        # Execute with timeout
        start_time = datetime.utcnow()
        result = await asyncio.wait_for(
            verification_service.verify_latest_backup(),
            timeout=5.0  # Should complete within 5 seconds (mocked)
        )
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify
        assert result["status"] == "success"
        assert duration < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
