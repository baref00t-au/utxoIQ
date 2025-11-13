"""Data retention service for archiving and deleting old records."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from google.cloud import storage
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import BackfillJob, InsightFeedback, SystemMetric
from src.database import AsyncSessionLocal
from src.services.database_exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class RetentionConfig:
    """Configuration for data retention policies."""
    
    # Retention periods in days
    BACKFILL_JOB_RETENTION_DAYS = 180
    FEEDBACK_RETENTION_DAYS = 730  # 2 years
    METRICS_HOT_STORAGE_DAYS = 90
    METRICS_COLD_STORAGE_DAYS = 365  # 1 year total
    
    # Cloud Storage bucket for archives
    ARCHIVE_BUCKET_NAME = "utxoiq-archives"
    
    # Archive paths
    BACKFILL_ARCHIVE_PATH = "backfill_jobs"
    FEEDBACK_ARCHIVE_PATH = "feedback"
    METRICS_ARCHIVE_PATH = "metrics"


class RetentionService:
    """Service for implementing data retention policies."""
    
    def __init__(self, gcp_project_id: str):
        """
        Initialize retention service.
        
        Args:
            gcp_project_id: Google Cloud project ID
        """
        self.session_factory = AsyncSessionLocal
        self.storage_client = storage.Client(project=gcp_project_id)
        self.bucket = self.storage_client.bucket(RetentionConfig.ARCHIVE_BUCKET_NAME)
        logger.info("RetentionService initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = self.session_factory()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        try:
            if exc_type is not None:
                await self.session.rollback()
                logger.error(f"Transaction rolled back due to error: {exc_val}")
            else:
                try:
                    await self.session.commit()
                except Exception as e:
                    await self.session.rollback()
                    logger.error(f"Failed to commit transaction: {e}")
                    raise
        finally:
            await self.session.close()
    
    def _upload_to_gcs(
        self,
        data: List[Dict[str, Any]],
        archive_path: str,
        filename: str
    ) -> str:
        """
        Upload data to Google Cloud Storage as JSON.
        
        Args:
            data: List of records to archive
            archive_path: Base path in bucket (e.g., 'backfill_jobs')
            filename: Name of the archive file
        
        Returns:
            GCS URI of the uploaded file
        
        Raises:
            DatabaseError: If upload fails
        """
        try:
            blob_name = f"{archive_path}/{filename}"
            blob = self.bucket.blob(blob_name)
            
            # Convert data to JSON
            json_data = json.dumps(data, default=str, indent=2)
            
            # Upload to GCS
            blob.upload_from_string(
                json_data,
                content_type='application/json'
            )
            
            gcs_uri = f"gs://{RetentionConfig.ARCHIVE_BUCKET_NAME}/{blob_name}"
            logger.info(f"Archived {len(data)} records to {gcs_uri}")
            return gcs_uri
        
        except Exception as e:
            logger.error(f"Failed to upload to GCS: {e}")
            raise DatabaseError(f"Archive upload failed: {e}")
    
    # ==================== Backfill Job Retention ====================
    
    async def archive_old_backfill_jobs(self) -> Dict[str, Any]:
        """
        Archive and delete backfill jobs older than 180 days.
        
        Returns:
            Dictionary with archival statistics
        
        Raises:
            DatabaseError: If archival or deletion fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(
                days=RetentionConfig.BACKFILL_JOB_RETENTION_DAYS
            )
            
            logger.info(f"Starting backfill job retention for records older than {cutoff_date}")
            
            # Query old jobs
            result = await self.session.execute(
                select(BackfillJob).where(
                    BackfillJob.started_at < cutoff_date
                )
            )
            old_jobs = result.scalars().all()
            
            if not old_jobs:
                logger.info("No backfill jobs to archive")
                return {
                    "archived_count": 0,
                    "deleted_count": 0,
                    "archive_uri": None
                }
            
            # Convert jobs to dictionaries for archival
            jobs_data = []
            job_ids = []
            for job in old_jobs:
                jobs_data.append({
                    "id": str(job.id),
                    "job_type": job.job_type,
                    "start_block": job.start_block,
                    "end_block": job.end_block,
                    "current_block": job.current_block,
                    "status": job.status,
                    "progress_percentage": job.progress_percentage,
                    "estimated_completion": job.estimated_completion.isoformat() if job.estimated_completion else None,
                    "error_message": job.error_message,
                    "started_at": job.started_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "created_by": job.created_by
                })
                job_ids.append(job.id)
            
            # Archive to Cloud Storage
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"backfill_jobs_{timestamp}.json"
            archive_uri = self._upload_to_gcs(
                jobs_data,
                RetentionConfig.BACKFILL_ARCHIVE_PATH,
                filename
            )
            
            # Delete archived jobs from database
            delete_stmt = delete(BackfillJob).where(
                BackfillJob.id.in_(job_ids)
            )
            result = await self.session.execute(delete_stmt)
            deleted_count = result.rowcount
            
            await self.session.commit()
            
            logger.info(
                f"Archived {len(jobs_data)} backfill jobs to {archive_uri}, "
                f"deleted {deleted_count} records from database"
            )
            
            return {
                "archived_count": len(jobs_data),
                "deleted_count": deleted_count,
                "archive_uri": archive_uri,
                "cutoff_date": cutoff_date.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to archive backfill jobs: {e}")
            raise DatabaseError(f"Backfill job archival failed: {e}")
    
    # ==================== Feedback Retention ====================
    
    async def archive_old_feedback(self) -> Dict[str, Any]:
        """
        Archive and delete feedback older than 2 years.
        
        Returns:
            Dictionary with archival statistics
        
        Raises:
            DatabaseError: If archival or deletion fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(
                days=RetentionConfig.FEEDBACK_RETENTION_DAYS
            )
            
            logger.info(f"Starting feedback retention for records older than {cutoff_date}")
            
            # Query old feedback
            result = await self.session.execute(
                select(InsightFeedback).where(
                    InsightFeedback.created_at < cutoff_date
                )
            )
            old_feedback = result.scalars().all()
            
            if not old_feedback:
                logger.info("No feedback to archive")
                return {
                    "archived_count": 0,
                    "deleted_count": 0,
                    "archive_uri": None
                }
            
            # Convert feedback to dictionaries for archival
            feedback_data = []
            feedback_ids = []
            for feedback in old_feedback:
                feedback_data.append({
                    "id": str(feedback.id),
                    "insight_id": feedback.insight_id,
                    "user_id": feedback.user_id,
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "flag_type": feedback.flag_type,
                    "flag_reason": feedback.flag_reason,
                    "created_at": feedback.created_at.isoformat(),
                    "updated_at": feedback.updated_at.isoformat()
                })
                feedback_ids.append(feedback.id)
            
            # Archive to Cloud Storage
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"feedback_{timestamp}.json"
            archive_uri = self._upload_to_gcs(
                feedback_data,
                RetentionConfig.FEEDBACK_ARCHIVE_PATH,
                filename
            )
            
            # Delete archived feedback from database
            delete_stmt = delete(InsightFeedback).where(
                InsightFeedback.id.in_(feedback_ids)
            )
            result = await self.session.execute(delete_stmt)
            deleted_count = result.rowcount
            
            await self.session.commit()
            
            logger.info(
                f"Archived {len(feedback_data)} feedback records to {archive_uri}, "
                f"deleted {deleted_count} records from database"
            )
            
            return {
                "archived_count": len(feedback_data),
                "deleted_count": deleted_count,
                "archive_uri": archive_uri,
                "cutoff_date": cutoff_date.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to archive feedback: {e}")
            raise DatabaseError(f"Feedback archival failed: {e}")
    
    # ==================== Metrics Retention ====================
    
    async def archive_old_metrics(self) -> Dict[str, Any]:
        """
        Archive metrics older than 90 days to cold storage.
        
        Returns:
            Dictionary with archival statistics
        
        Raises:
            DatabaseError: If archival fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(
                days=RetentionConfig.METRICS_HOT_STORAGE_DAYS
            )
            
            logger.info(f"Starting metrics archival for records older than {cutoff_date}")
            
            # Query old metrics (batch processing to avoid memory issues)
            batch_size = 10000
            offset = 0
            total_archived = 0
            archive_uris = []
            
            while True:
                result = await self.session.execute(
                    select(SystemMetric)
                    .where(SystemMetric.timestamp < cutoff_date)
                    .limit(batch_size)
                    .offset(offset)
                )
                old_metrics = result.scalars().all()
                
                if not old_metrics:
                    break
                
                # Convert metrics to dictionaries for archival
                metrics_data = []
                for metric in old_metrics:
                    metrics_data.append({
                        "id": str(metric.id),
                        "service_name": metric.service_name,
                        "metric_type": metric.metric_type,
                        "metric_value": metric.metric_value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat(),
                        "metadata": metric.metric_metadata
                    })
                
                # Archive batch to Cloud Storage
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"metrics_{timestamp}_batch_{offset}.json"
                archive_uri = self._upload_to_gcs(
                    metrics_data,
                    RetentionConfig.METRICS_ARCHIVE_PATH,
                    filename
                )
                archive_uris.append(archive_uri)
                
                total_archived += len(metrics_data)
                offset += batch_size
                
                logger.info(f"Archived batch of {len(metrics_data)} metrics (total: {total_archived})")
            
            if total_archived == 0:
                logger.info("No metrics to archive")
                return {
                    "archived_count": 0,
                    "archive_uris": []
                }
            
            logger.info(f"Archived {total_archived} metrics to {len(archive_uris)} files")
            
            return {
                "archived_count": total_archived,
                "archive_uris": archive_uris,
                "cutoff_date": cutoff_date.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to archive metrics: {e}")
            raise DatabaseError(f"Metrics archival failed: {e}")
    
    async def delete_old_archived_metrics(self) -> Dict[str, Any]:
        """
        Delete metrics older than 1 year from database (after archival).
        
        Returns:
            Dictionary with deletion statistics
        
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(
                days=RetentionConfig.METRICS_COLD_STORAGE_DAYS
            )
            
            logger.info(f"Starting metrics deletion for records older than {cutoff_date}")
            
            # Delete old metrics
            delete_stmt = delete(SystemMetric).where(
                SystemMetric.timestamp < cutoff_date
            )
            result = await self.session.execute(delete_stmt)
            deleted_count = result.rowcount
            
            await self.session.commit()
            
            logger.info(f"Deleted {deleted_count} metrics older than {cutoff_date}")
            
            return {
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to delete old metrics: {e}")
            raise DatabaseError(f"Metrics deletion failed: {e}")
    
    # ==================== Cleanup for Partitioned Tables ====================
    
    async def cleanup_partitioned_metrics(
        self,
        partition_date: datetime
    ) -> Dict[str, Any]:
        """
        Drop old partitions for metrics table (if using table partitioning).
        
        This is more efficient than DELETE for partitioned tables.
        
        Args:
            partition_date: Date of partition to drop
        
        Returns:
            Dictionary with cleanup statistics
        
        Raises:
            DatabaseError: If cleanup fails
        """
        try:
            # Note: This assumes metrics table is partitioned by month
            # Partition naming convention: system_metrics_YYYYMM
            partition_name = f"system_metrics_{partition_date.strftime('%Y%m')}"
            
            logger.info(f"Dropping partition {partition_name}")
            
            # Execute DROP TABLE for partition
            drop_sql = f"DROP TABLE IF EXISTS {partition_name}"
            await self.session.execute(drop_sql)
            await self.session.commit()
            
            logger.info(f"Successfully dropped partition {partition_name}")
            
            return {
                "partition_name": partition_name,
                "partition_date": partition_date.isoformat(),
                "status": "dropped"
            }
        
        except Exception as e:
            logger.error(f"Failed to drop partition: {e}")
            raise DatabaseError(f"Partition cleanup failed: {e}")
    
    # ==================== Run All Retention Policies ====================
    
    async def run_all_retention_policies(self) -> Dict[str, Any]:
        """
        Execute all retention policies in sequence.
        
        Returns:
            Dictionary with results from all retention operations
        
        Raises:
            DatabaseError: If any retention operation fails
        """
        try:
            logger.info("Starting all retention policies")
            
            results = {
                "execution_time": datetime.utcnow().isoformat(),
                "backfill_jobs": None,
                "feedback": None,
                "metrics_archive": None,
                "metrics_delete": None
            }
            
            # Archive old backfill jobs
            try:
                results["backfill_jobs"] = await self.archive_old_backfill_jobs()
            except Exception as e:
                logger.error(f"Backfill job retention failed: {e}")
                results["backfill_jobs"] = {"error": str(e)}
            
            # Archive old feedback
            try:
                results["feedback"] = await self.archive_old_feedback()
            except Exception as e:
                logger.error(f"Feedback retention failed: {e}")
                results["feedback"] = {"error": str(e)}
            
            # Archive old metrics
            try:
                results["metrics_archive"] = await self.archive_old_metrics()
            except Exception as e:
                logger.error(f"Metrics archival failed: {e}")
                results["metrics_archive"] = {"error": str(e)}
            
            # Delete very old metrics
            try:
                results["metrics_delete"] = await self.delete_old_archived_metrics()
            except Exception as e:
                logger.error(f"Metrics deletion failed: {e}")
                results["metrics_delete"] = {"error": str(e)}
            
            logger.info("Completed all retention policies")
            return results
        
        except Exception as e:
            logger.error(f"Failed to run retention policies: {e}")
            raise DatabaseError(f"Retention policy execution failed: {e}")
