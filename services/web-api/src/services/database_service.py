"""Database service layer for persistent storage operations."""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
import logging
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
from sqlalchemy.exc import OperationalError, DatabaseError as SQLAlchemyDatabaseError

from src.models.db_models import BackfillJob, InsightFeedback, SystemMetric
from src.models.database_schemas import (
    BackfillJobCreate, BackfillJobUpdate, BackfillJobResponse,
    FeedbackCreate, FeedbackResponse, FeedbackStats,
    MetricCreate, MetricResponse
)
from src.database import AsyncSessionLocal
from src.services.database_exceptions import (
    DatabaseError, ConnectionError, QueryError, 
    IntegrityError, NotFoundError, ValidationError
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations with connection pool management."""
    
    def __init__(self):
        """Initialize database service."""
        self.session_factory = AsyncSessionLocal
        logger.info("DatabaseService initialized")
    
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
    
    def _handle_db_error(self, error: Exception, operation: str) -> None:
        """
        Handle database errors and convert to custom exceptions.
        
        Args:
            error: The original exception
            operation: Description of the operation that failed
        
        Raises:
            Custom database exception
        """
        if isinstance(error, SQLAlchemyIntegrityError):
            logger.error(f"Integrity error during {operation}: {error}")
            raise IntegrityError(f"Data constraint violation during {operation}")
        elif isinstance(error, OperationalError):
            logger.error(f"Connection error during {operation}: {error}")
            raise ConnectionError(f"Database connection failed during {operation}")
        elif isinstance(error, SQLAlchemyDatabaseError):
            logger.error(f"Database error during {operation}: {error}")
            raise QueryError(f"Database query failed during {operation}")
        else:
            logger.error(f"Unexpected error during {operation}: {error}")
            raise DatabaseError(f"Unexpected database error during {operation}")
    
    # ==================== Backfill Job Operations ====================
    
    async def create_backfill_job(
        self, 
        job_data: BackfillJobCreate
    ) -> BackfillJobResponse:
        """
        Create a new backfill job record.
        
        Args:
            job_data: Backfill job creation data
        
        Returns:
            Created backfill job
        
        Raises:
            ValidationError: If job data is invalid
            IntegrityError: If job violates constraints
            DatabaseError: If creation fails
        """
        try:
            # Validate block range
            if job_data.end_block < job_data.start_block:
                raise ValidationError("end_block must be greater than or equal to start_block")
            
            # Create job instance
            job = BackfillJob(
                job_type=job_data.job_type,
                start_block=job_data.start_block,
                end_block=job_data.end_block,
                current_block=job_data.start_block,
                status="running",
                progress_percentage=0.0,
                created_by=job_data.created_by
            )
            
            self.session.add(job)
            await self.session.flush()
            await self.session.refresh(job)
            
            logger.info(f"Created backfill job {job.id} for blocks {job.start_block}-{job.end_block}")
            return BackfillJobResponse.model_validate(job)
        
        except ValidationError:
            raise
        except Exception as e:
            self._handle_db_error(e, "create_backfill_job")
    
    async def update_backfill_progress(
        self,
        job_id: UUID,
        progress_data: BackfillJobUpdate
    ) -> BackfillJobResponse:
        """
        Update backfill job progress with optimistic locking.
        
        Args:
            job_id: Job UUID
            progress_data: Progress update data
        
        Returns:
            Updated backfill job
        
        Raises:
            NotFoundError: If job not found
            ValidationError: If update data is invalid
            DatabaseError: If update fails
        """
        try:
            # Fetch current job
            result = await self.session.execute(
                select(BackfillJob).where(BackfillJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise NotFoundError(f"Backfill job {job_id} not found")
            
            # Validate progress
            if progress_data.current_block < job.start_block:
                raise ValidationError("current_block cannot be less than start_block")
            if progress_data.current_block > job.end_block:
                raise ValidationError("current_block cannot exceed end_block")
            
            # Update fields
            job.current_block = progress_data.current_block
            job.progress_percentage = progress_data.progress_percentage
            
            if progress_data.estimated_completion:
                job.estimated_completion = progress_data.estimated_completion
            
            if progress_data.status:
                job.status = progress_data.status
                if progress_data.status == "completed":
                    job.completed_at = datetime.utcnow()
            
            if progress_data.error_message:
                job.error_message = progress_data.error_message
            
            await self.session.flush()
            await self.session.refresh(job)
            
            logger.info(f"Updated backfill job {job_id} progress to {progress_data.progress_percentage}%")
            return BackfillJobResponse.model_validate(job)
        
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._handle_db_error(e, "update_backfill_progress")
    
    async def get_backfill_job(self, job_id: UUID) -> Optional[BackfillJobResponse]:
        """
        Retrieve a backfill job by ID.
        
        Args:
            job_id: Job UUID
        
        Returns:
            Backfill job or None if not found
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            result = await self.session.execute(
                select(BackfillJob).where(BackfillJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                return BackfillJobResponse.model_validate(job)
            return None
        
        except Exception as e:
            self._handle_db_error(e, "get_backfill_job")
    
    async def list_backfill_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BackfillJobResponse]:
        """
        List backfill jobs with optional filtering.
        
        Args:
            status: Filter by status (optional)
            job_type: Filter by job type (optional)
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of backfill jobs
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = select(BackfillJob)
            
            # Apply filters
            if status:
                query = query.where(BackfillJob.status == status)
            if job_type:
                query = query.where(BackfillJob.job_type == job_type)
            
            # Order by most recent first
            query = query.order_by(BackfillJob.started_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            jobs = result.scalars().all()
            
            return [BackfillJobResponse.model_validate(job) for job in jobs]
        
        except Exception as e:
            self._handle_db_error(e, "list_backfill_jobs")
    
    async def complete_backfill_job(self, job_id: UUID) -> BackfillJobResponse:
        """
        Mark a backfill job as completed.
        
        Args:
            job_id: Job UUID
        
        Returns:
            Updated backfill job
        
        Raises:
            NotFoundError: If job not found
            DatabaseError: If update fails
        """
        try:
            result = await self.session.execute(
                select(BackfillJob).where(BackfillJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise NotFoundError(f"Backfill job {job_id} not found")
            
            job.status = "completed"
            job.progress_percentage = 100.0
            job.completed_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(job)
            
            logger.info(f"Completed backfill job {job_id}")
            return BackfillJobResponse.model_validate(job)
        
        except NotFoundError:
            raise
        except Exception as e:
            self._handle_db_error(e, "complete_backfill_job")
    
    async def fail_backfill_job(
        self, 
        job_id: UUID, 
        error_message: str
    ) -> BackfillJobResponse:
        """
        Mark a backfill job as failed.
        
        Args:
            job_id: Job UUID
            error_message: Error description
        
        Returns:
            Updated backfill job
        
        Raises:
            NotFoundError: If job not found
            DatabaseError: If update fails
        """
        try:
            result = await self.session.execute(
                select(BackfillJob).where(BackfillJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise NotFoundError(f"Backfill job {job_id} not found")
            
            job.status = "failed"
            job.error_message = error_message
            job.completed_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(job)
            
            logger.error(f"Failed backfill job {job_id}: {error_message}")
            return BackfillJobResponse.model_validate(job)
        
        except NotFoundError:
            raise
        except Exception as e:
            self._handle_db_error(e, "fail_backfill_job")

    # ==================== Feedback Operations ====================
    
    async def create_feedback(
        self,
        feedback_data: FeedbackCreate
    ) -> FeedbackResponse:
        """
        Create or update insight feedback with upsert logic.
        
        Ensures only one feedback per user-insight combination.
        
        Args:
            feedback_data: Feedback creation data
        
        Returns:
            Created or updated feedback
        
        Raises:
            ValidationError: If feedback data is invalid
            DatabaseError: If operation fails
        """
        try:
            # Validate rating if provided
            if feedback_data.rating is not None:
                if feedback_data.rating < 1 or feedback_data.rating > 5:
                    raise ValidationError("Rating must be between 1 and 5")
            
            # Check if feedback already exists
            result = await self.session.execute(
                select(InsightFeedback).where(
                    and_(
                        InsightFeedback.insight_id == feedback_data.insight_id,
                        InsightFeedback.user_id == feedback_data.user_id
                    )
                )
            )
            existing_feedback = result.scalar_one_or_none()
            
            if existing_feedback:
                # Update existing feedback
                if feedback_data.rating is not None:
                    existing_feedback.rating = feedback_data.rating
                if feedback_data.comment is not None:
                    existing_feedback.comment = feedback_data.comment
                if feedback_data.flag_type is not None:
                    existing_feedback.flag_type = feedback_data.flag_type
                if feedback_data.flag_reason is not None:
                    existing_feedback.flag_reason = feedback_data.flag_reason
                
                existing_feedback.updated_at = datetime.utcnow()
                
                await self.session.flush()
                await self.session.refresh(existing_feedback)
                
                logger.info(f"Updated feedback for insight {feedback_data.insight_id} by user {feedback_data.user_id}")
                return FeedbackResponse.model_validate(existing_feedback)
            else:
                # Create new feedback
                feedback = InsightFeedback(
                    insight_id=feedback_data.insight_id,
                    user_id=feedback_data.user_id,
                    rating=feedback_data.rating,
                    comment=feedback_data.comment,
                    flag_type=feedback_data.flag_type,
                    flag_reason=feedback_data.flag_reason
                )
                
                self.session.add(feedback)
                await self.session.flush()
                await self.session.refresh(feedback)
                
                logger.info(f"Created feedback for insight {feedback_data.insight_id} by user {feedback_data.user_id}")
                return FeedbackResponse.model_validate(feedback)
        
        except ValidationError:
            raise
        except Exception as e:
            self._handle_db_error(e, "create_feedback")
    
    async def get_feedback_stats(self, insight_id: str) -> FeedbackStats:
        """
        Get aggregated feedback statistics for an insight.
        
        Args:
            insight_id: Insight identifier
        
        Returns:
            Aggregated feedback statistics
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            # Get all feedback for the insight
            result = await self.session.execute(
                select(InsightFeedback).where(
                    InsightFeedback.insight_id == insight_id
                )
            )
            feedbacks = result.scalars().all()
            
            # Calculate statistics
            total_ratings = 0
            rating_sum = 0
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            total_comments = 0
            total_flags = 0
            flag_types: Dict[str, int] = {}
            
            for feedback in feedbacks:
                if feedback.rating is not None:
                    total_ratings += 1
                    rating_sum += feedback.rating
                    rating_distribution[feedback.rating] += 1
                
                if feedback.comment:
                    total_comments += 1
                
                if feedback.flag_type:
                    total_flags += 1
                    flag_types[feedback.flag_type] = flag_types.get(feedback.flag_type, 0) + 1
            
            average_rating = rating_sum / total_ratings if total_ratings > 0 else 0.0
            
            return FeedbackStats(
                insight_id=insight_id,
                total_ratings=total_ratings,
                average_rating=round(average_rating, 2),
                rating_distribution=rating_distribution,
                total_comments=total_comments,
                total_flags=total_flags,
                flag_types=flag_types
            )
        
        except Exception as e:
            self._handle_db_error(e, "get_feedback_stats")
    
    async def list_feedback(
        self,
        insight_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[FeedbackResponse]:
        """
        List feedback with filtering options.
        
        Args:
            insight_id: Filter by insight ID (optional)
            user_id: Filter by user ID (optional)
            start_date: Filter by creation date start (optional)
            end_date: Filter by creation date end (optional)
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of feedback entries
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = select(InsightFeedback)
            
            # Apply filters
            filters = []
            if insight_id:
                filters.append(InsightFeedback.insight_id == insight_id)
            if user_id:
                filters.append(InsightFeedback.user_id == user_id)
            if start_date:
                filters.append(InsightFeedback.created_at >= start_date)
            if end_date:
                filters.append(InsightFeedback.created_at <= end_date)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by most recent first
            query = query.order_by(InsightFeedback.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            feedbacks = result.scalars().all()
            
            return [FeedbackResponse.model_validate(fb) for fb in feedbacks]
        
        except Exception as e:
            self._handle_db_error(e, "list_feedback")

    # ==================== Metrics Operations ====================
    
    async def record_metric(
        self,
        metric_data: MetricCreate
    ) -> MetricResponse:
        """
        Record a single system metric.
        
        Args:
            metric_data: Metric creation data
        
        Returns:
            Created metric
        
        Raises:
            ValidationError: If metric data is invalid
            DatabaseError: If creation fails
        """
        try:
            metric = SystemMetric(
                service_name=metric_data.service_name,
                metric_type=metric_data.metric_type,
                metric_value=metric_data.metric_value,
                unit=metric_data.unit,
                metric_metadata=metric_data.metric_metadata
            )
            
            self.session.add(metric)
            await self.session.flush()
            await self.session.refresh(metric)
            
            logger.debug(f"Recorded metric {metric_data.metric_type} for {metric_data.service_name}")
            return MetricResponse.model_validate(metric)
        
        except Exception as e:
            self._handle_db_error(e, "record_metric")
    
    async def record_metrics_batch(
        self,
        metrics_data: List[MetricCreate]
    ) -> List[MetricResponse]:
        """
        Record multiple system metrics in a batch.
        
        Args:
            metrics_data: List of metric creation data
        
        Returns:
            List of created metrics
        
        Raises:
            ValidationError: If any metric data is invalid
            DatabaseError: If batch creation fails
        """
        try:
            metrics = []
            for metric_data in metrics_data:
                metric = SystemMetric(
                    service_name=metric_data.service_name,
                    metric_type=metric_data.metric_type,
                    metric_value=metric_data.metric_value,
                    unit=metric_data.unit,
                    metric_metadata=metric_data.metric_metadata
                )
                metrics.append(metric)
            
            self.session.add_all(metrics)
            await self.session.flush()
            
            # Refresh all metrics
            for metric in metrics:
                await self.session.refresh(metric)
            
            logger.info(f"Recorded batch of {len(metrics)} metrics")
            return [MetricResponse.model_validate(m) for m in metrics]
        
        except Exception as e:
            self._handle_db_error(e, "record_metrics_batch")
    
    async def get_metrics(
        self,
        service_name: Optional[str] = None,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[MetricResponse]:
        """
        Query metrics with time range filtering.
        
        Args:
            service_name: Filter by service name (optional)
            metric_type: Filter by metric type (optional)
            start_time: Filter by timestamp start (optional)
            end_time: Filter by timestamp end (optional)
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of metrics
        
        Raises:
            DatabaseError: If query fails
        """
        try:
            query = select(SystemMetric)
            
            # Apply filters
            filters = []
            if service_name:
                filters.append(SystemMetric.service_name == service_name)
            if metric_type:
                filters.append(SystemMetric.metric_type == metric_type)
            if start_time:
                filters.append(SystemMetric.timestamp >= start_time)
            if end_time:
                filters.append(SystemMetric.timestamp <= end_time)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order by timestamp descending
            query = query.order_by(SystemMetric.timestamp.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            metrics = result.scalars().all()
            
            return [MetricResponse.model_validate(m) for m in metrics]
        
        except Exception as e:
            self._handle_db_error(e, "get_metrics")
    
    async def aggregate_metrics(
        self,
        service_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "hour"
    ) -> List[Dict[str, Any]]:
        """
        Aggregate metrics for hourly or daily rollups.
        
        Args:
            service_name: Service name to aggregate
            metric_type: Metric type to aggregate
            start_time: Aggregation start time
            end_time: Aggregation end time
            interval: Aggregation interval ('hour' or 'day')
        
        Returns:
            List of aggregated metric data points
        
        Raises:
            ValidationError: If interval is invalid
            DatabaseError: If aggregation fails
        """
        try:
            if interval not in ["hour", "day"]:
                raise ValidationError("Interval must be 'hour' or 'day'")
            
            # Determine the date truncation function
            if interval == "hour":
                time_bucket = func.date_trunc('hour', SystemMetric.timestamp)
            else:  # day
                time_bucket = func.date_trunc('day', SystemMetric.timestamp)
            
            # Build aggregation query
            query = select(
                time_bucket.label('time_bucket'),
                func.avg(SystemMetric.metric_value).label('avg_value'),
                func.min(SystemMetric.metric_value).label('min_value'),
                func.max(SystemMetric.metric_value).label('max_value'),
                func.count(SystemMetric.id).label('count')
            ).where(
                and_(
                    SystemMetric.service_name == service_name,
                    SystemMetric.metric_type == metric_type,
                    SystemMetric.timestamp >= start_time,
                    SystemMetric.timestamp <= end_time
                )
            ).group_by(
                time_bucket
            ).order_by(
                time_bucket
            )
            
            result = await self.session.execute(query)
            rows = result.all()
            
            # Format results
            aggregated_data = []
            for row in rows:
                aggregated_data.append({
                    "timestamp": row.time_bucket,
                    "avg_value": float(row.avg_value) if row.avg_value else 0.0,
                    "min_value": float(row.min_value) if row.min_value else 0.0,
                    "max_value": float(row.max_value) if row.max_value else 0.0,
                    "count": row.count
                })
            
            logger.info(f"Aggregated {len(aggregated_data)} {interval}ly data points for {service_name}/{metric_type}")
            return aggregated_data
        
        except ValidationError:
            raise
        except Exception as e:
            self._handle_db_error(e, "aggregate_metrics")
