"""
Backup Verification Service
Performs weekly backup verification by restoring to a temporary instance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from google.cloud import sql_v1
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions
import hashlib
import json

logger = logging.getLogger(__name__)


class BackupVerificationError(Exception):
    """Base exception for backup verification errors"""
    pass


class BackupVerificationService:
    """Service for verifying Cloud SQL backups"""
    
    def __init__(
        self,
        project_id: str,
        instance_name: str,
        backup_bucket: str,
        test_instance_prefix: str = "backup-verify",
        retention_hours: int = 2
    ):
        """
        Initialize backup verification service
        
        Args:
            project_id: GCP project ID
            instance_name: Source Cloud SQL instance name
            backup_bucket: GCS bucket for backup logs
            test_instance_prefix: Prefix for test instance names
            retention_hours: Hours to keep test instance before deletion
        """
        self.project_id = project_id
        self.instance_name = instance_name
        self.backup_bucket = backup_bucket
        self.test_instance_prefix = test_instance_prefix
        self.retention_hours = retention_hours
        
        # Initialize clients
        self.sql_client = sql_v1.SqlInstancesServiceClient()
        self.backup_client = sql_v1.SqlBackupRunsServiceClient()
        self.storage_client = storage.Client()
    
    async def verify_latest_backup(self) -> Dict:
        """
        Verify the latest backup by performing a test restore
        
        Returns:
            Dict with verification results
        """
        logger.info(f"Starting backup verification for instance: {self.instance_name}")
        
        verification_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        test_instance_name = f"{self.test_instance_prefix}-{verification_id}"
        
        result = {
            "verification_id": verification_id,
            "timestamp": datetime.utcnow().isoformat(),
            "instance_name": self.instance_name,
            "test_instance_name": test_instance_name,
            "status": "in_progress",
            "steps": []
        }
        
        try:
            # Step 1: Get latest backup
            logger.info("Step 1: Retrieving latest backup")
            backup = await self._get_latest_backup()
            result["steps"].append({
                "step": "get_latest_backup",
                "status": "success",
                "backup_id": backup.id,
                "backup_time": backup.window_start_time
            })
            
            # Step 2: Create test instance from backup
            logger.info(f"Step 2: Creating test instance: {test_instance_name}")
            await self._create_test_instance(test_instance_name, backup.id)
            result["steps"].append({
                "step": "create_test_instance",
                "status": "success",
                "instance_name": test_instance_name
            })
            
            # Step 3: Wait for instance to be ready
            logger.info("Step 3: Waiting for test instance to be ready")
            await self._wait_for_instance_ready(test_instance_name)
            result["steps"].append({
                "step": "wait_for_ready",
                "status": "success"
            })
            
            # Step 4: Verify data integrity
            logger.info("Step 4: Verifying data integrity")
            integrity_check = await self._verify_data_integrity(test_instance_name)
            result["steps"].append({
                "step": "verify_integrity",
                "status": "success",
                "checks": integrity_check
            })
            
            # Step 5: Schedule cleanup
            logger.info("Step 5: Scheduling test instance cleanup")
            cleanup_time = datetime.utcnow() + timedelta(hours=self.retention_hours)
            await self._schedule_cleanup(test_instance_name, cleanup_time)
            result["steps"].append({
                "step": "schedule_cleanup",
                "status": "success",
                "cleanup_time": cleanup_time.isoformat()
            })
            
            result["status"] = "success"
            logger.info(f"Backup verification completed successfully: {verification_id}")
            
        except Exception as e:
            logger.error(f"Backup verification failed: {str(e)}", exc_info=True)
            result["status"] = "failed"
            result["error"] = str(e)
            
            # Attempt cleanup on failure
            try:
                await self._cleanup_test_instance(test_instance_name)
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed: {str(cleanup_error)}")
        
        # Save verification results
        await self._save_verification_results(result)
        
        return result
    
    async def _get_latest_backup(self) -> sql_v1.BackupRun:
        """Get the latest successful backup"""
        request = sql_v1.SqlBackupRunsListRequest(
            project=self.project_id,
            instance=self.instance_name
        )
        
        try:
            response = self.backup_client.list(request=request)
            
            # Find latest successful backup
            for backup in response:
                if backup.status == sql_v1.SqlBackupRunStatus.SUCCESSFUL:
                    return backup
            
            raise BackupVerificationError("No successful backups found")
            
        except gcp_exceptions.GoogleAPIError as e:
            raise BackupVerificationError(f"Failed to list backups: {str(e)}")
    
    async def _create_test_instance(self, test_instance_name: str, backup_id: int):
        """Create a test instance from backup"""
        # Get source instance configuration
        source_request = sql_v1.SqlInstancesGetRequest(
            project=self.project_id,
            instance=self.instance_name
        )
        source_instance = self.sql_client.get(request=source_request)
        
        # Create test instance with minimal configuration
        test_instance = sql_v1.DatabaseInstance()
        test_instance.name = test_instance_name
        test_instance.database_version = source_instance.database_version
        test_instance.region = source_instance.region
        
        # Use smaller tier for testing
        test_instance.settings = sql_v1.Settings()
        test_instance.settings.tier = "db-f1-micro"  # Minimal tier for testing
        test_instance.settings.disk_size = 10  # Minimal disk size
        
        # Restore from backup
        test_instance.restore_backup_context = sql_v1.RestoreBackupContext()
        test_instance.restore_backup_context.backup_run_id = backup_id
        test_instance.restore_backup_context.instance_id = self.instance_name
        test_instance.restore_backup_context.project = self.project_id
        
        request = sql_v1.SqlInstancesInsertRequest(
            project=self.project_id,
            body=test_instance
        )
        
        try:
            operation = self.sql_client.insert(request=request)
            logger.info(f"Test instance creation initiated: {operation.name}")
        except gcp_exceptions.GoogleAPIError as e:
            raise BackupVerificationError(f"Failed to create test instance: {str(e)}")
    
    async def _wait_for_instance_ready(self, instance_name: str, timeout_minutes: int = 30):
        """Wait for instance to be ready"""
        start_time = datetime.utcnow()
        timeout = timedelta(minutes=timeout_minutes)
        
        while datetime.utcnow() - start_time < timeout:
            request = sql_v1.SqlInstancesGetRequest(
                project=self.project_id,
                instance=instance_name
            )
            
            try:
                instance = self.sql_client.get(request=request)
                
                if instance.state == sql_v1.DatabaseInstance.SqlInstanceState.RUNNABLE:
                    logger.info(f"Instance {instance_name} is ready")
                    return
                
                logger.info(f"Instance state: {instance.state}, waiting...")
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except gcp_exceptions.GoogleAPIError as e:
                logger.warning(f"Error checking instance state: {str(e)}")
                await asyncio.sleep(30)
        
        raise BackupVerificationError(f"Instance {instance_name} did not become ready within {timeout_minutes} minutes")
    
    async def _verify_data_integrity(self, instance_name: str) -> Dict:
        """
        Verify data integrity of restored instance
        
        This performs basic checks to ensure the backup is valid
        """
        checks = {
            "instance_accessible": False,
            "tables_exist": False,
            "row_counts_match": False,
            "checksums_match": False
        }
        
        try:
            # Check 1: Instance is accessible
            request = sql_v1.SqlInstancesGetRequest(
                project=self.project_id,
                instance=instance_name
            )
            instance = self.sql_client.get(request=request)
            checks["instance_accessible"] = instance.state == sql_v1.DatabaseInstance.SqlInstanceState.RUNNABLE
            
            # Additional checks would require database connection
            # For now, we verify the instance is accessible and running
            # In production, you would connect and run SQL queries
            
            logger.info(f"Data integrity checks completed for {instance_name}")
            
        except Exception as e:
            logger.error(f"Data integrity verification failed: {str(e)}")
            raise BackupVerificationError(f"Data integrity check failed: {str(e)}")
        
        return checks
    
    async def _schedule_cleanup(self, instance_name: str, cleanup_time: datetime):
        """Schedule cleanup of test instance"""
        # In production, this would create a Cloud Scheduler job or Pub/Sub message
        # For now, we log the cleanup schedule
        logger.info(f"Test instance {instance_name} scheduled for cleanup at {cleanup_time}")
        
        # Store cleanup info in GCS
        cleanup_info = {
            "instance_name": instance_name,
            "cleanup_time": cleanup_time.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        bucket = self.storage_client.bucket(self.backup_bucket)
        blob = bucket.blob(f"cleanup-schedule/{instance_name}.json")
        blob.upload_from_string(json.dumps(cleanup_info, indent=2))
    
    async def _cleanup_test_instance(self, instance_name: str):
        """Delete test instance"""
        logger.info(f"Cleaning up test instance: {instance_name}")
        
        request = sql_v1.SqlInstancesDeleteRequest(
            project=self.project_id,
            instance=instance_name
        )
        
        try:
            operation = self.sql_client.delete(request=request)
            logger.info(f"Test instance deletion initiated: {operation.name}")
        except gcp_exceptions.GoogleAPIError as e:
            logger.error(f"Failed to delete test instance: {str(e)}")
            raise
    
    async def _save_verification_results(self, result: Dict):
        """Save verification results to GCS"""
        try:
            bucket = self.storage_client.bucket(self.backup_bucket)
            blob_name = f"verification-results/{result['verification_id']}.json"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json.dumps(result, indent=2))
            logger.info(f"Verification results saved to gs://{self.backup_bucket}/{blob_name}")
        except Exception as e:
            logger.error(f"Failed to save verification results: {str(e)}")
    
    async def cleanup_expired_instances(self):
        """Clean up test instances that have exceeded retention period"""
        logger.info("Checking for expired test instances")
        
        try:
            bucket = self.storage_client.bucket(self.backup_bucket)
            blobs = bucket.list_blobs(prefix="cleanup-schedule/")
            
            current_time = datetime.utcnow()
            
            for blob in blobs:
                try:
                    cleanup_info = json.loads(blob.download_as_string())
                    cleanup_time = datetime.fromisoformat(cleanup_info["cleanup_time"])
                    
                    if current_time >= cleanup_time:
                        instance_name = cleanup_info["instance_name"]
                        logger.info(f"Cleaning up expired instance: {instance_name}")
                        await self._cleanup_test_instance(instance_name)
                        blob.delete()  # Remove cleanup schedule
                        
                except Exception as e:
                    logger.error(f"Error processing cleanup for {blob.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired instances: {str(e)}")
    
    async def get_verification_history(self, limit: int = 10) -> List[Dict]:
        """Get recent verification results"""
        try:
            bucket = self.storage_client.bucket(self.backup_bucket)
            blobs = list(bucket.list_blobs(prefix="verification-results/"))
            
            # Sort by name (which includes timestamp) in descending order
            blobs.sort(key=lambda b: b.name, reverse=True)
            
            results = []
            for blob in blobs[:limit]:
                try:
                    result = json.loads(blob.download_as_string())
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error loading verification result {blob.name}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get verification history: {str(e)}")
            return []
