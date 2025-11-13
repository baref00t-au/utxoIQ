"""
Monitoring and system status endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID
import logging

from src.services.database_service import DatabaseService
from src.services.cache_service import CacheService
from src.services.retention_service import RetentionService
from src.services.tracing_service import TracingService
from src.services.log_aggregation_service import LogAggregationService
from src.models.database_schemas import (
    BackfillJobCreate, BackfillJobUpdate, BackfillJobResponse,
    MetricCreate, MetricResponse
)
from src.models.monitoring_schemas import (
    AlertConfigCreate,
    AlertConfigUpdate,
    AlertConfigResponse,
    AlertConfigListResponse,
    AlertHistoryResponse,
    AlertHistoryListResponse,
    AlertAnalyticsResponse,
    AlertFrequencyByService,
    AlertTypeFrequency,
    AlertTrendData,
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardListResponse,
    DashboardShareResponse,
    WidgetDataRequest,
    WidgetDataResponse,
    DashboardCopyRequest
)
from src.services.database_exceptions import NotFoundError, ValidationError, DatabaseError
from src.config import settings
from src.monitoring.database_monitor import get_database_monitor
from src.database import engine
from src.middleware.auth import require_role
from src.middleware import rate_limit_dependency
from src.models.auth import Role
from src.models.db_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class BackfillStatus(str, Enum):
    """Backfill job status"""
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ServiceHealth(BaseModel):
    """Individual service health"""
    name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class BackfillProgress(BaseModel):
    """Backfill job progress"""
    job_id: str
    status: BackfillStatus
    start_block: int
    end_block: int
    current_block: int
    blocks_processed: int
    blocks_remaining: int
    progress_percent: float
    rate_blocks_per_sec: float
    estimated_completion: Optional[datetime] = None
    started_at: datetime
    updated_at: datetime
    error_count: int


class ProcessingMetrics(BaseModel):
    """Real-time processing metrics"""
    blocks_processed_24h: int
    insights_generated_24h: int
    signals_computed_24h: int
    avg_block_processing_time_ms: float
    avg_insight_generation_time_ms: float
    current_block_height: int
    last_processed_block: int
    blocks_behind: int


class SystemStatus(BaseModel):
    """Overall system status"""
    status: ServiceStatus
    services: List[ServiceHealth]
    backfill_jobs: List[BackfillProgress]
    processing_metrics: ProcessingMetrics
    timestamp: datetime


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get overall system status including all services and backfill progress.
    
    Requires admin role.
    """
    # TODO: Implement actual health checks
    # For now, return mock data
    
    services = [
        ServiceHealth(
            name="feature-engine",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            response_time_ms=45.2
        ),
        ServiceHealth(
            name="insight-generator",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            response_time_ms=120.5
        ),
        ServiceHealth(
            name="data-ingestion",
            status=ServiceStatus.HEALTHY,
            last_check=datetime.utcnow(),
            response_time_ms=30.1
        ),
    ]
    
    # Get backfill jobs from database
    try:
        async with DatabaseService() as db:
            db_jobs = await db.list_backfill_jobs(limit=5)
            # Convert to BackfillProgress format for compatibility
            backfill_jobs = []
            for job in db_jobs:
                backfill_jobs.append(BackfillProgress(
                    job_id=str(job.id),
                    status=BackfillStatus(job.status),
                    start_block=job.start_block,
                    end_block=job.end_block,
                    current_block=job.current_block,
                    blocks_processed=job.current_block - job.start_block,
                    blocks_remaining=job.end_block - job.current_block,
                    progress_percent=job.progress_percentage,
                    rate_blocks_per_sec=0.0,  # TODO: Calculate from metrics
                    estimated_completion=job.estimated_completion,
                    started_at=job.started_at,
                    updated_at=job.started_at,  # Use started_at as fallback
                    error_count=1 if job.error_message else 0
                ))
    except DatabaseError as e:
        logger.error(f"Failed to retrieve backfill jobs for status: {e}")
        backfill_jobs = []
    
    # TODO: Query actual metrics from BigQuery
    processing_metrics = ProcessingMetrics(
        blocks_processed_24h=144,
        insights_generated_24h=42,
        signals_computed_24h=156,
        avg_block_processing_time_ms=2500.0,
        avg_insight_generation_time_ms=8500.0,
        current_block_height=870000,
        last_processed_block=869998,
        blocks_behind=2
    )
    
    return SystemStatus(
        status=ServiceStatus.HEALTHY,
        services=services,
        backfill_jobs=backfill_jobs,
        processing_metrics=processing_metrics,
        timestamp=datetime.utcnow()
    )


@router.post("/backfill/start", response_model=BackfillJobResponse)
async def start_backfill_job(
    job_data: BackfillJobCreate,
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Start a new backfill job and create database record.
    
    Requires admin role.
    
    Args:
        job_data: Backfill job creation data
    
    Returns:
        Created backfill job
    
    Raises:
        HTTPException: If job creation fails
    """
    try:
        async with DatabaseService() as db:
            job = await db.create_backfill_job(job_data)
            logger.info(f"Started backfill job {job.id} for blocks {job.start_block}-{job.end_block}")
            return job
    except ValidationError as e:
        logger.error(f"Validation error creating backfill job: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating backfill job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backfill job")


@router.post("/backfill/progress", response_model=BackfillJobResponse)
async def update_backfill_progress(
    job_id: UUID,
    progress_data: BackfillJobUpdate
):
    """
    Update backfill job progress in database.
    
    Args:
        job_id: Job UUID
        progress_data: Progress update data
    
    Returns:
        Updated backfill job
    
    Raises:
        HTTPException: If update fails
    """
    try:
        async with DatabaseService() as db:
            # Update database
            job = await db.update_backfill_progress(job_id, progress_data)
            
            # Invalidate cache
            async with CacheService() as cache:
                await cache.invalidate_backfill_cache(str(job_id))
            
            logger.info(f"Updated backfill job {job_id} progress to {progress_data.progress_percentage}%")
            return job
    except NotFoundError as e:
        logger.error(f"Backfill job not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        logger.error(f"Validation error updating backfill job: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error updating backfill job: {e}")
        raise HTTPException(status_code=500, detail="Failed to update backfill job")


@router.get("/backfill/status", response_model=List[BackfillJobResponse])
async def get_backfill_status(
    status: Optional[str] = Query(None, pattern="^(running|completed|failed|paused)$"),
    job_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Query backfill job status from database with caching.
    
    Args:
        status: Filter by job status (optional)
        job_type: Filter by job type (optional)
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        List of backfill jobs
    
    Raises:
        HTTPException: If query fails
    """
    try:
        async with DatabaseService() as db:
            jobs = await db.list_backfill_jobs(
                status=status,
                job_type=job_type,
                limit=limit,
                offset=offset
            )
            logger.debug(f"Retrieved {len(jobs)} backfill jobs")
            return jobs
    except DatabaseError as e:
        logger.error(f"Database error querying backfill jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to query backfill jobs")


@router.get("/backfill/{job_id}", response_model=BackfillJobResponse)
async def get_backfill_job(job_id: UUID):
    """
    Get specific backfill job with caching.
    
    Args:
        job_id: Job UUID
    
    Returns:
        Backfill job details
    
    Raises:
        HTTPException: If job not found or query fails
    """
    try:
        # Try cache first
        async with CacheService() as cache:
            cached_job = await cache.get_backfill_job(str(job_id))
            if cached_job:
                logger.debug(f"Cache hit for backfill job {job_id}")
                return cached_job
        
        # Query database
        async with DatabaseService() as db:
            job = await db.get_backfill_job(job_id)
            
            if not job:
                raise HTTPException(status_code=404, detail=f"Backfill job {job_id} not found")
            
            # Cache the result
            async with CacheService() as cache:
                await cache.cache_backfill_job(str(job_id), job)
            
            logger.debug(f"Retrieved backfill job {job_id} from database")
            return job
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error retrieving backfill job: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve backfill job")


@router.post("/metrics", response_model=MetricResponse)
async def record_metric(metric_data: MetricCreate):
    """
    Record a system metric in database.
    
    Args:
        metric_data: Metric creation data
    
    Returns:
        Created metric
    
    Raises:
        HTTPException: If recording fails
    """
    try:
        async with DatabaseService() as db:
            metric = await db.record_metric(metric_data)
            logger.debug(f"Recorded metric {metric_data.metric_type} for {metric_data.service_name}")
            return metric
    except ValidationError as e:
        logger.error(f"Validation error recording metric: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error recording metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metric")


@router.post("/metrics/batch", response_model=List[MetricResponse])
async def record_metrics_batch(metrics_data: List[MetricCreate]):
    """
    Record multiple system metrics in a batch.
    
    Args:
        metrics_data: List of metric creation data
    
    Returns:
        List of created metrics
    
    Raises:
        HTTPException: If batch recording fails
    """
    try:
        async with DatabaseService() as db:
            metrics = await db.record_metrics_batch(metrics_data)
            logger.info(f"Recorded batch of {len(metrics)} metrics")
            return metrics
    except ValidationError as e:
        logger.error(f"Validation error recording metrics batch: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error recording metrics batch: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metrics batch")


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    service_name: Optional[str] = Query(None),
    metric_type: Optional[str] = Query(None),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0)
):
    """
    Query metrics with time range filters.
    
    Args:
        service_name: Filter by service name (optional)
        metric_type: Filter by metric type (optional)
        start_time: Start of time range
        end_time: End of time range
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        List of metrics
    
    Raises:
        HTTPException: If query fails
    """
    try:
        # Try cache for recent metrics (last 1 hour)
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        if service_name and metric_type and start_time >= one_hour_ago:
            async with CacheService() as cache:
                cached_metrics = await cache.get_recent_metrics(service_name, metric_type)
                if cached_metrics:
                    logger.debug(f"Cache hit for recent metrics: {service_name}/{metric_type}")
                    # Filter cached metrics by time range
                    filtered = [
                        m for m in cached_metrics
                        if start_time <= datetime.fromisoformat(m['timestamp']) <= end_time
                    ]
                    return filtered[:limit]
        
        # Query database
        async with DatabaseService() as db:
            metrics = await db.get_metrics(
                service_name=service_name,
                metric_type=metric_type,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset
            )
            
            # Cache recent metrics if applicable
            if service_name and metric_type and start_time >= one_hour_ago:
                async with CacheService() as cache:
                    await cache.cache_recent_metrics(service_name, metric_type, metrics)
            
            logger.debug(f"Retrieved {len(metrics)} metrics from database")
            return metrics
    except DatabaseError as e:
        logger.error(f"Database error querying metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to query metrics")


@router.get("/metrics/aggregate")
async def get_aggregated_metrics(
    service_name: str = Query(...),
    metric_type: str = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    interval: str = Query("hour", pattern="^(hour|day)$")
):
    """
    Get aggregated metrics for hourly or daily rollups.
    
    Args:
        service_name: Service name to aggregate
        metric_type: Metric type to aggregate
        start_time: Aggregation start time
        end_time: Aggregation end time
        interval: Aggregation interval ('hour' or 'day')
    
    Returns:
        List of aggregated metric data points
    
    Raises:
        HTTPException: If aggregation fails
    """
    try:
        # Try cache first
        async with CacheService() as cache:
            cached_agg = await cache.get_aggregated_metrics(
                service_name, metric_type, interval, start_time, end_time
            )
            if cached_agg:
                logger.debug(f"Cache hit for aggregated metrics: {service_name}/{metric_type}/{interval}")
                return {
                    "service_name": service_name,
                    "metric_type": metric_type,
                    "interval": interval,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "data": cached_agg
                }
        
        # Query database
        async with DatabaseService() as db:
            aggregated_data = await db.aggregate_metrics(
                service_name=service_name,
                metric_type=metric_type,
                start_time=start_time,
                end_time=end_time,
                interval=interval
            )
        
        # Cache the result
        async with CacheService() as cache:
            await cache.cache_aggregated_metrics(
                service_name, metric_type, interval, start_time, end_time, aggregated_data
            )
        
        logger.debug(f"Retrieved {len(aggregated_data)} aggregated data points from database")
        return {
            "service_name": service_name,
            "metric_type": metric_type,
            "interval": interval,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data": aggregated_data
        }
    except ValidationError as e:
        logger.error(f"Validation error aggregating metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error aggregating metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to aggregate metrics")


@router.get("/metrics/processing", response_model=ProcessingMetrics)
async def get_processing_metrics(
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get real-time processing metrics.
    
    Requires admin role.
    """
    # TODO: Query from BigQuery/Redis
    return ProcessingMetrics(
        blocks_processed_24h=144,
        insights_generated_24h=42,
        signals_computed_24h=156,
        avg_block_processing_time_ms=2500.0,
        avg_insight_generation_time_ms=8500.0,
        current_block_height=870000,
        last_processed_block=869998,
        blocks_behind=2
    )


@router.get("/metrics/signals")
async def get_signal_metrics(
    hours: int = Query(24, ge=1, le=168)
):
    """
    Get signal generation metrics over time
    
    Args:
        hours: Number of hours to look back
    """
    # TODO: Query from BigQuery
    return {
        "period_hours": hours,
        "signals_by_category": {
            "mempool": 45,
            "exchange": 38,
            "miner": 42,
            "whale": 31
        },
        "signals_by_confidence": {
            "high": 67,
            "medium": 58,
            "low": 31
        },
        "total_signals": 156
    }


@router.get("/metrics/insights")
async def get_insight_metrics(
    hours: int = Query(24, ge=1, le=168)
):
    """
    Get insight generation metrics over time
    """
    # TODO: Query from BigQuery
    return {
        "period_hours": hours,
        "insights_generated": 42,
        "insights_by_category": {
            "mempool": 12,
            "exchange": 10,
            "miner": 11,
            "whale": 9
        },
        "avg_confidence": 0.78,
        "insights_posted_to_x": 8
    }


@router.post("/retention/run")
async def run_retention_policies():
    """
    Execute all data retention policies.
    
    This endpoint is designed to be called by Cloud Scheduler daily at 02:00 UTC.
    It archives and deletes old records according to retention policies:
    - Backfill jobs: Archive and delete after 180 days
    - Feedback: Archive and delete after 2 years
    - Metrics: Archive after 90 days, delete after 1 year
    
    Returns:
        Dictionary with results from all retention operations
    
    Raises:
        HTTPException: If retention execution fails
    """
    try:
        logger.info("Starting scheduled retention policy execution")
        
        async with RetentionService(settings.gcp_project_id) as retention:
            results = await retention.run_all_retention_policies()
        
        logger.info(f"Completed retention policy execution: {results}")
        
        return {
            "status": "success",
            "message": "Retention policies executed successfully",
            "results": results
        }
    except DatabaseError as e:
        logger.error(f"Database error during retention execution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute retention policies: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during retention execution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during retention execution: {str(e)}"
        )


@router.get("/database/pool")
async def get_database_pool_metrics(
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get current database connection pool metrics.
    
    Requires admin role.
    
    Returns:
        Dictionary containing pool metrics:
        - size: Pool size
        - checked_in: Available connections
        - checked_out: Active connections
        - overflow: Overflow connections
        - total_connections: Total connections
    
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        monitor = get_database_monitor()
        metrics = await monitor.get_pool_metrics(engine.pool)
        
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error retrieving pool metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve pool metrics: {str(e)}"
        )


@router.get("/database/queries")
async def get_database_query_metrics(
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get database query performance metrics.
    
    Requires admin role.
    
    Returns:
        Dictionary containing query metrics:
        - total_queries: Total number of queries executed
        - slow_queries: Number of slow queries (>200ms)
        - slow_query_percentage: Percentage of slow queries
        - average_query_time: Average query execution time
        - slow_query_threshold: Threshold for slow queries (200ms)
    
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        monitor = get_database_monitor()
        metrics = await monitor.get_query_metrics()
        
        # Check for high slow query rate
        if metrics["slow_query_percentage"] > 5.0:
            logger.warning(
                f"High slow query rate detected: {metrics['slow_query_percentage']:.2f}%"
            )
        
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error retrieving query metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve query metrics: {str(e)}"
        )


@router.post("/database/publish-metrics")
async def publish_database_metrics():
    """
    Publish database metrics to Cloud Monitoring.
    
    This endpoint publishes both connection pool and query performance metrics
    to Google Cloud Monitoring for dashboard visualization and alerting.
    
    Should be called periodically (e.g., every 60 seconds) by a cron job.
    
    Returns:
        Success status
    
    Raises:
        HTTPException: If metric publishing fails
    """
    try:
        monitor = get_database_monitor()
        
        # Publish pool metrics
        await monitor.publish_pool_metrics(engine.pool)
        
        # Publish query metrics
        await monitor.publish_query_metrics()
        
        logger.info("Successfully published database metrics to Cloud Monitoring")
        
        return {
            "status": "success",
            "message": "Database metrics published to Cloud Monitoring"
        }
    except Exception as e:
        logger.error(f"Error publishing database metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish database metrics: {str(e)}"
        )


# Alert Configuration Endpoints

@router.post("/alerts", response_model=AlertConfigResponse, status_code=201)
async def create_alert_configuration(
    alert_data: AlertConfigCreate,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Create a new alert configuration.
    
    Args:
        alert_data: Alert configuration data
        user: Authenticated user
    
    Returns:
        Created alert configuration
    
    Raises:
        HTTPException: If creation fails
    """
    try:
        async with DatabaseService() as db:
            from src.models.monitoring import AlertConfiguration
            from sqlalchemy import select
            
            # Create alert configuration
            alert_config = AlertConfiguration(
                name=alert_data.name,
                service_name=alert_data.service_name,
                metric_type=alert_data.metric_type,
                threshold_type=alert_data.threshold_type,
                threshold_value=alert_data.threshold_value,
                comparison_operator=alert_data.comparison_operator,
                severity=alert_data.severity,
                evaluation_window_seconds=alert_data.evaluation_window_seconds,
                notification_channels=alert_data.notification_channels,
                suppression_enabled=alert_data.suppression_enabled,
                suppression_start=alert_data.suppression_start,
                suppression_end=alert_data.suppression_end,
                created_by=user.id,
                enabled=alert_data.enabled
            )
            
            db.session.add(alert_config)
            await db.session.commit()
            await db.session.refresh(alert_config)
            
            logger.info(f"Created alert configuration {alert_config.id} for user {user.id}")
            return AlertConfigResponse.model_validate(alert_config)
    except ValidationError as e:
        logger.error(f"Validation error creating alert configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error creating alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert configuration")


@router.get("/alerts", response_model=AlertConfigListResponse)
async def list_alert_configurations(
    service_name: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None, pattern="^(info|warning|critical)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    List alert configurations for the authenticated user.
    
    Args:
        service_name: Filter by service name (optional)
        enabled: Filter by enabled status (optional)
        severity: Filter by severity level (optional)
        page: Page number
        page_size: Number of items per page
        user: Authenticated user
    
    Returns:
        List of alert configurations
    
    Raises:
        HTTPException: If query fails
    """
    try:
        async with DatabaseService() as db:
            from src.models.monitoring import AlertConfiguration
            from sqlalchemy import select, func
            
            # Build query
            query = select(AlertConfiguration).where(AlertConfiguration.created_by == user.id)
            
            if service_name:
                query = query.where(AlertConfiguration.service_name == service_name)
            if enabled is not None:
                query = query.where(AlertConfiguration.enabled == enabled)
            if severity:
                query = query.where(AlertConfiguration.severity == severity)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            result = await db.session.execute(count_query)
            total = result.scalar()
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.order_by(AlertConfiguration.created_at.desc()).offset(offset).limit(page_size)
            
            # Execute query
            result = await db.session.execute(query)
            alerts = result.scalars().all()
            
            logger.debug(f"Retrieved {len(alerts)} alert configurations for user {user.id}")
            
            return AlertConfigListResponse(
                alerts=[AlertConfigResponse.model_validate(alert) for alert in alerts],
                total=total,
                page=page,
                page_size=page_size
            )
    except DatabaseError as e:
        logger.error(f"Database error listing alert configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list alert configurations")


@router.get("/alerts/{alert_id}", response_model=AlertConfigResponse)
async def get_alert_configuration(
    alert_id: UUID,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get a specific alert configuration.
    
    Args:
        alert_id: Alert configuration ID
        user: Authenticated user
    
    Returns:
        Alert configuration
    
    Raises:
        HTTPException: If alert not found or access denied
    """
    try:
        async with DatabaseService() as db:
            from src.models.monitoring import AlertConfiguration
            from sqlalchemy import select
            
            query = select(AlertConfiguration).where(
                AlertConfiguration.id == alert_id,
                AlertConfiguration.created_by == user.id
            )
            result = await db.session.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert configuration not found")
            
            return AlertConfigResponse.model_validate(alert)
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error retrieving alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert configuration")


@router.patch("/alerts/{alert_id}", response_model=AlertConfigResponse)
async def update_alert_configuration(
    alert_id: UUID,
    alert_data: AlertConfigUpdate,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Update an alert configuration.
    
    Args:
        alert_id: Alert configuration ID
        alert_data: Alert configuration update data
        user: Authenticated user
    
    Returns:
        Updated alert configuration
    
    Raises:
        HTTPException: If alert not found or update fails
    """
    try:
        async with DatabaseService() as db:
            from src.models.monitoring import AlertConfiguration
            from sqlalchemy import select
            
            # Get existing alert
            query = select(AlertConfiguration).where(
                AlertConfiguration.id == alert_id,
                AlertConfiguration.created_by == user.id
            )
            result = await db.session.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert configuration not found")
            
            # Update fields
            update_data = alert_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(alert, field, value)
            
            alert.updated_at = datetime.utcnow()
            
            await db.session.commit()
            await db.session.refresh(alert)
            
            logger.info(f"Updated alert configuration {alert_id}")
            return AlertConfigResponse.model_validate(alert)
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error updating alert configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error updating alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert configuration")


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert_configuration(
    alert_id: UUID,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Delete an alert configuration.
    
    Args:
        alert_id: Alert configuration ID
        user: Authenticated user
    
    Raises:
        HTTPException: If alert not found or deletion fails
    """
    try:
        async with DatabaseService() as db:
            from src.models.monitoring import AlertConfiguration
            from sqlalchemy import select, delete
            
            # Verify ownership
            query = select(AlertConfiguration).where(
                AlertConfiguration.id == alert_id,
                AlertConfiguration.created_by == user.id
            )
            result = await db.session.execute(query)
            alert = result.scalar_one_or_none()
            
            if not alert:
                raise HTTPException(status_code=404, detail="Alert configuration not found")
            
            # Delete alert (cascade will delete history)
            delete_query = delete(AlertConfiguration).where(AlertConfiguration.id == alert_id)
            await db.session.execute(delete_query)
            await db.session.commit()
            
            logger.info(f"Deleted alert configuration {alert_id}")
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error deleting alert configuration: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert configuration")


# Alert History Endpoints

@router.get("/alerts/history", response_model=AlertHistoryListResponse)
async def get_alert_history(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    severity: Optional[str] = Query(None, pattern="^(info|warning|critical)$", description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get alert history with filtering and pagination.
    
    Retrieves historical alert records for alerts created by the authenticated user.
    Supports filtering by service, severity, date range, and resolution status.
    
    Args:
        service_name: Filter by service name (optional)
        severity: Filter by severity level (optional)
        start_date: Filter alerts triggered after this date (optional)
        end_date: Filter alerts triggered before this date (optional)
        resolved: Filter by resolution status - True for resolved, False for active (optional)
        page: Page number for pagination
        page_size: Number of items per page
        user: Authenticated user
    
    Returns:
        Paginated list of alert history records
    
    Raises:
        HTTPException: If query fails
    """
    try:
        async with DatabaseService() as db:
            from src.models.monitoring import AlertHistory, AlertConfiguration
            from sqlalchemy import select, func, and_
            
            # Build base query - join with alert configurations to filter by user
            query = select(AlertHistory).join(
                AlertConfiguration,
                AlertHistory.alert_config_id == AlertConfiguration.id
            ).where(AlertConfiguration.created_by == user.id)
            
            # Apply filters
            filters = []
            
            if service_name:
                filters.append(AlertConfiguration.service_name == service_name)
            
            if severity:
                filters.append(AlertHistory.severity == severity)
            
            if start_date:
                filters.append(AlertHistory.triggered_at >= start_date)
            
            if end_date:
                filters.append(AlertHistory.triggered_at <= end_date)
            
            if resolved is not None:
                if resolved:
                    filters.append(AlertHistory.resolved_at.isnot(None))
                else:
                    filters.append(AlertHistory.resolved_at.is_(None))
            
            if filters:
                query = query.where(and_(*filters))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            result = await db.session.execute(count_query)
            total = result.scalar()
            
            # Apply pagination and ordering
            offset = (page - 1) * page_size
            query = query.order_by(AlertHistory.triggered_at.desc()).offset(offset).limit(page_size)
            
            # Execute query
            result = await db.session.execute(query)
            history_records = result.scalars().all()
            
            logger.debug(
                f"Retrieved {len(history_records)} alert history records for user {user.id} "
                f"(page {page}, total {total})"
            )
            
            return AlertHistoryListResponse(
                history=[AlertHistoryResponse.model_validate(record) for record in history_records],
                total=total,
                page=page,
                page_size=page_size
            )
    except DatabaseError as e:
        logger.error(f"Database error retrieving alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert history")



@router.get("/alerts/history/analytics", response_model=AlertAnalyticsResponse)
async def get_alert_analytics(
    start_date: Optional[datetime] = Query(None, description="Analytics period start date"),
    end_date: Optional[datetime] = Query(None, description="Analytics period end date"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get alert history analytics and statistics.
    
    Provides comprehensive analytics including:
    - Mean time to resolution (MTTR)
    - Alert frequency per service
    - Most common alert types
    - Alert trend reports over time
    
    Args:
        start_date: Start of analytics period (defaults to 30 days ago)
        end_date: End of analytics period (defaults to now)
        service_name: Filter analytics by service name (optional)
        user: Authenticated user
    
    Returns:
        Alert analytics data
    
    Raises:
        HTTPException: If analytics calculation fails
    """
    try:
        # Default to last 30 days if not specified
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        async with DatabaseService() as db:
            from src.models.monitoring import AlertHistory, AlertConfiguration
            from sqlalchemy import select, func, and_, case, cast, Date
            
            # Build base query - join with alert configurations to filter by user
            base_query = select(AlertHistory).join(
                AlertConfiguration,
                AlertHistory.alert_config_id == AlertConfiguration.id
            ).where(
                and_(
                    AlertConfiguration.created_by == user.id,
                    AlertHistory.triggered_at >= start_date,
                    AlertHistory.triggered_at <= end_date
                )
            )
            
            # Apply service filter if specified
            if service_name:
                base_query = base_query.where(AlertConfiguration.service_name == service_name)
            
            # Get total counts
            total_query = select(func.count()).select_from(base_query.subquery())
            result = await db.session.execute(total_query)
            total_alerts = result.scalar() or 0
            
            # Get active vs resolved counts
            active_query = select(func.count()).select_from(
                base_query.where(AlertHistory.resolved_at.is_(None)).subquery()
            )
            result = await db.session.execute(active_query)
            active_alerts = result.scalar() or 0
            
            resolved_alerts = total_alerts - active_alerts
            
            # Calculate mean time to resolution (MTTR)
            mttr_query = select(
                func.avg(
                    func.extract('epoch', AlertHistory.resolved_at - AlertHistory.triggered_at) / 60
                )
            ).select_from(
                base_query.where(AlertHistory.resolved_at.isnot(None)).subquery()
            )
            result = await db.session.execute(mttr_query)
            mttr_minutes = result.scalar()
            
            # Get alert frequency by service
            frequency_query = select(
                AlertConfiguration.service_name,
                func.count(AlertHistory.id).label('total_alerts'),
                func.sum(case((AlertHistory.severity == 'critical', 1), else_=0)).label('critical_alerts'),
                func.sum(case((AlertHistory.severity == 'warning', 1), else_=0)).label('warning_alerts'),
                func.sum(case((AlertHistory.severity == 'info', 1), else_=0)).label('info_alerts')
            ).select_from(AlertHistory).join(
                AlertConfiguration,
                AlertHistory.alert_config_id == AlertConfiguration.id
            ).where(
                and_(
                    AlertConfiguration.created_by == user.id,
                    AlertHistory.triggered_at >= start_date,
                    AlertHistory.triggered_at <= end_date
                )
            )
            
            if service_name:
                frequency_query = frequency_query.where(AlertConfiguration.service_name == service_name)
            
            frequency_query = frequency_query.group_by(AlertConfiguration.service_name)
            
            result = await db.session.execute(frequency_query)
            frequency_rows = result.all()
            
            # Calculate days in period for avg alerts per day
            days_in_period = (end_date - start_date).days or 1
            
            alert_frequency_by_service = [
                AlertFrequencyByService(
                    service_name=row.service_name,
                    total_alerts=row.total_alerts,
                    critical_alerts=row.critical_alerts or 0,
                    warning_alerts=row.warning_alerts or 0,
                    info_alerts=row.info_alerts or 0,
                    avg_alerts_per_day=round(row.total_alerts / days_in_period, 2)
                )
                for row in frequency_rows
            ]
            
            # Get most common alert types
            alert_types_query = select(
                AlertConfiguration.metric_type,
                AlertConfiguration.service_name,
                func.count(AlertHistory.id).label('alert_count'),
                func.avg(AlertHistory.metric_value).label('avg_metric_value')
            ).select_from(AlertHistory).join(
                AlertConfiguration,
                AlertHistory.alert_config_id == AlertConfiguration.id
            ).where(
                and_(
                    AlertConfiguration.created_by == user.id,
                    AlertHistory.triggered_at >= start_date,
                    AlertHistory.triggered_at <= end_date
                )
            )
            
            if service_name:
                alert_types_query = alert_types_query.where(AlertConfiguration.service_name == service_name)
            
            alert_types_query = alert_types_query.group_by(
                AlertConfiguration.metric_type,
                AlertConfiguration.service_name
            ).order_by(func.count(AlertHistory.id).desc()).limit(10)
            
            result = await db.session.execute(alert_types_query)
            alert_types_rows = result.all()
            
            most_common_alert_types = [
                AlertTypeFrequency(
                    metric_type=row.metric_type,
                    service_name=row.service_name,
                    alert_count=row.alert_count,
                    avg_metric_value=round(float(row.avg_metric_value), 2)
                )
                for row in alert_types_rows
            ]
            
            # Get alert trends (daily aggregation)
            trends_query = select(
                cast(AlertHistory.triggered_at, Date).label('date'),
                func.count(AlertHistory.id).label('total_alerts'),
                func.sum(case((AlertHistory.severity == 'critical', 1), else_=0)).label('critical_alerts'),
                func.sum(case((AlertHistory.severity == 'warning', 1), else_=0)).label('warning_alerts'),
                func.sum(case((AlertHistory.severity == 'info', 1), else_=0)).label('info_alerts')
            ).select_from(AlertHistory).join(
                AlertConfiguration,
                AlertHistory.alert_config_id == AlertConfiguration.id
            ).where(
                and_(
                    AlertConfiguration.created_by == user.id,
                    AlertHistory.triggered_at >= start_date,
                    AlertHistory.triggered_at <= end_date
                )
            )
            
            if service_name:
                trends_query = trends_query.where(AlertConfiguration.service_name == service_name)
            
            trends_query = trends_query.group_by('date').order_by('date')
            
            result = await db.session.execute(trends_query)
            trends_rows = result.all()
            
            alert_trends = [
                AlertTrendData(
                    date=row.date.isoformat(),
                    total_alerts=row.total_alerts,
                    critical_alerts=row.critical_alerts or 0,
                    warning_alerts=row.warning_alerts or 0,
                    info_alerts=row.info_alerts or 0
                )
                for row in trends_rows
            ]
            
            logger.info(
                f"Generated alert analytics for user {user.id}: "
                f"{total_alerts} total alerts, MTTR={mttr_minutes:.2f}min" if mttr_minutes else
                f"{total_alerts} total alerts, MTTR=N/A"
            )
            
            return AlertAnalyticsResponse(
                period_start=start_date,
                period_end=end_date,
                total_alerts=total_alerts,
                active_alerts=active_alerts,
                resolved_alerts=resolved_alerts,
                mean_time_to_resolution_minutes=round(mttr_minutes, 2) if mttr_minutes else None,
                alert_frequency_by_service=alert_frequency_by_service,
                most_common_alert_types=most_common_alert_types,
                alert_trends=alert_trends
            )
    except DatabaseError as e:
        logger.error(f"Database error calculating alert analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate alert analytics")



# Distributed Tracing Endpoints

class TraceSpanResponse(BaseModel):
    """Trace span data"""
    span_id: str
    name: str
    start_time: Optional[str]
    end_time: Optional[str]
    parent_span_id: Optional[str]
    attributes: Dict[str, str]
    status: Optional[Dict[str, Any]]


class TraceResponse(BaseModel):
    """Trace data with spans"""
    trace_id: str
    project_id: str
    spans: List[TraceSpanResponse]
    span_count: int


class TraceSummaryResponse(BaseModel):
    """Trace summary for list view"""
    trace_id: str
    project_id: str
    span_count: int


@router.get("/traces/{trace_id}", response_model=TraceResponse)
async def get_trace(
    trace_id: str,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get detailed trace information by trace ID.
    
    Retrieves a complete trace with all spans, including:
    - Span hierarchy and timing
    - Request metadata (method, path, status code)
    - Custom attributes added during execution
    - Error information if applicable
    
    Args:
        trace_id: The Cloud Trace ID to retrieve
        user: Authenticated user
    
    Returns:
        Complete trace data with all spans
    
    Raises:
        HTTPException: If trace not found or retrieval fails
    """
    try:
        # Get tracing service from app state
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest
        
        # Access the app instance to get tracing service
        # Note: In production, this should be injected via dependency
        tracing_service = TracingService(
            project_id=settings.gcp_project_id,
            service_name="web-api"
        )
        
        # Retrieve trace data
        trace_data = await tracing_service.get_trace(trace_id)
        
        logger.info(f"Retrieved trace {trace_id} for user {user.id}")
        
        # Format response
        return TraceResponse(
            trace_id=trace_data["trace_id"],
            project_id=trace_data["project_id"],
            spans=[
                TraceSpanResponse(
                    span_id=span["span_id"],
                    name=span["name"],
                    start_time=span["start_time"],
                    end_time=span["end_time"],
                    parent_span_id=span["parent_span_id"],
                    attributes=span["attributes"],
                    status=span["status"]
                )
                for span in trace_data["spans"]
            ],
            span_count=trace_data["span_count"]
        )
    except Exception as e:
        logger.error(f"Error retrieving trace {trace_id}: {e}")
        if "not found" in str(e).lower() or "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trace: {str(e)}")


@router.get("/traces", response_model=List[TraceSummaryResponse])
async def list_traces(
    start_time: datetime = Query(..., description="Start of time range"),
    end_time: datetime = Query(..., description="End of time range"),
    filter_str: Optional[str] = Query(None, description="Optional filter string"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of traces to return"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    List traces within a time range.
    
    Retrieves trace summaries for the specified time period. Useful for:
    - Finding traces related to specific requests
    - Analyzing request patterns over time
    - Identifying performance issues
    
    Args:
        start_time: Start of time range
        end_time: End of time range
        filter_str: Optional Cloud Trace filter string
        page_size: Number of traces to return (max 1000)
        user: Authenticated user
    
    Returns:
        List of trace summaries
    
    Raises:
        HTTPException: If listing fails
    """
    try:
        # Get tracing service
        tracing_service = TracingService(
            project_id=settings.gcp_project_id,
            service_name="web-api"
        )
        
        # List traces
        traces = await tracing_service.list_traces(
            start_time=start_time,
            end_time=end_time,
            filter_str=filter_str,
            page_size=page_size
        )
        
        logger.info(
            f"Listed {len(traces)} traces for user {user.id} "
            f"(period: {start_time} to {end_time})"
        )
        
        # Format response
        return [
            TraceSummaryResponse(
                trace_id=trace["trace_id"],
                project_id=trace["project_id"],
                span_count=trace["span_count"]
            )
            for trace in traces
        ]
    except Exception as e:
        logger.error(f"Error listing traces: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list traces: {str(e)}")



# Log Aggregation Endpoints

class LogEntryResponse(BaseModel):
    """Log entry data"""
    log_id: str
    timestamp: Optional[str]
    severity: str
    message: Optional[str]
    resource: Dict[str, Any]
    labels: Dict[str, str]
    trace: Optional[str]
    span_id: Optional[str]
    json_payload: Optional[Dict[str, Any]] = None
    http_request: Optional[Dict[str, Any]] = None
    is_target: Optional[bool] = False


class LogSearchResponse(BaseModel):
    """Log search results"""
    logs: List[LogEntryResponse]
    next_page_token: Optional[str]
    total_count: int
    filter: Optional[str]


class LogContextResponse(BaseModel):
    """Log context with surrounding entries"""
    before: List[LogEntryResponse]
    target: Optional[LogEntryResponse]
    after: List[LogEntryResponse]
    context_lines: int


class LogStatisticsResponse(BaseModel):
    """Log statistics"""
    total_count: int
    severity_counts: Dict[str, int]
    time_range: Dict[str, str]
    service: Optional[str]


@router.post("/logs/search", response_model=LogSearchResponse)
async def search_logs(
    query: Optional[str] = Query(None, description="Full-text search query"),
    start_time: Optional[datetime] = Query(None, description="Start of time range"),
    end_time: Optional[datetime] = Query(None, description="End of time range"),
    severity: Optional[str] = Query(
        None,
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Log severity level"
    ),
    service: Optional[str] = Query(None, description="Service name to filter by"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Search logs with filters.
    
    Provides centralized log search across all services with support for:
    - Full-text search across log messages
    - Filtering by service, severity, and time range
    - Pagination for large result sets
    
    Args:
        query: Full-text search query (optional)
        start_time: Start of time range (optional)
        end_time: End of time range (optional)
        severity: Log severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (optional)
        service: Service name to filter by (optional)
        limit: Maximum number of results (1-1000)
        page_token: Token for pagination (optional)
        user: Authenticated user
    
    Returns:
        Log search results with pagination
    
    Raises:
        HTTPException: If search fails
    """
    try:
        # Initialize log aggregation service
        log_service = LogAggregationService(project_id=settings.gcp_project_id)
        
        # Execute search
        results = await log_service.search_logs(
            query=query,
            start_time=start_time,
            end_time=end_time,
            severity=severity,
            service=service,
            limit=limit,
            page_token=page_token
        )
        
        logger.info(
            f"Log search by user {user.id}: found {results['total_count']} logs "
            f"(query={query}, service={service}, severity={severity})"
        )
        
        # Format response
        return LogSearchResponse(
            logs=[LogEntryResponse(**log) for log in results["logs"]],
            next_page_token=results.get("next_page_token"),
            total_count=results["total_count"],
            filter=results.get("filter")
        )
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search logs: {str(e)}")


@router.get("/logs/{log_id}/context", response_model=LogContextResponse)
async def get_log_context(
    log_id: str,
    timestamp: datetime = Query(..., description="Timestamp of the target log"),
    context_lines: int = Query(10, ge=1, le=50, description="Number of lines before and after"),
    service: Optional[str] = Query(None, description="Service name to filter by"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get log context with surrounding entries.
    
    Retrieves log entries before and after a target log to provide context.
    Useful for understanding the sequence of events leading to an error or issue.
    
    Args:
        log_id: ID of the target log entry
        timestamp: Timestamp of the target log
        context_lines: Number of lines before and after (1-50, default: 10)
        service: Optional service name to filter by
        user: Authenticated user
    
    Returns:
        Log context with before, target, and after entries
    
    Raises:
        HTTPException: If context retrieval fails
    """
    try:
        # Initialize log aggregation service
        log_service = LogAggregationService(project_id=settings.gcp_project_id)
        
        # Get log context
        context = await log_service.get_log_context(
            target_log_id=log_id,
            target_timestamp=timestamp,
            context_lines=context_lines,
            service=service
        )
        
        logger.info(
            f"Retrieved log context for {log_id} by user {user.id}: "
            f"{len(context['before'])} before, {len(context['after'])} after"
        )
        
        # Format response
        return LogContextResponse(
            before=[LogEntryResponse(**log) for log in context["before"]],
            target=LogEntryResponse(**context["target"]) if context["target"] else None,
            after=[LogEntryResponse(**log) for log in context["after"]],
            context_lines=context["context_lines"]
        )
    except Exception as e:
        logger.error(f"Error retrieving log context for {log_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve log context: {str(e)}")


@router.get("/logs/statistics", response_model=LogStatisticsResponse)
async def get_log_statistics(
    start_time: datetime = Query(..., description="Start of time range"),
    end_time: datetime = Query(..., description="End of time range"),
    service: Optional[str] = Query(None, description="Service name to filter by"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get log statistics for a time range.
    
    Provides aggregate statistics about logs including:
    - Total log count
    - Breakdown by severity level
    - Time range covered
    
    Args:
        start_time: Start of time range
        end_time: End of time range
        service: Optional service name to filter by
        user: Authenticated user
    
    Returns:
        Log statistics
    
    Raises:
        HTTPException: If statistics calculation fails
    """
    try:
        # Initialize log aggregation service
        log_service = LogAggregationService(project_id=settings.gcp_project_id)
        
        # Get statistics
        stats = await log_service.get_log_statistics(
            start_time=start_time,
            end_time=end_time,
            service=service
        )
        
        logger.info(
            f"Retrieved log statistics by user {user.id}: "
            f"{stats['total_count']} logs from {start_time} to {end_time}"
        )
        
        # Format response
        return LogStatisticsResponse(
            total_count=stats["total_count"],
            severity_counts=stats["severity_counts"],
            time_range=stats["time_range"],
            service=stats.get("service")
        )
    except Exception as e:
        logger.error(f"Error retrieving log statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve log statistics: {str(e)}")


# Error Tracking Endpoints

class ErrorGroupResponse(BaseModel):
    """Error group data"""
    group_id: str
    group_name: str
    count: int
    affected_users_count: int
    first_seen_time: Optional[str]
    last_seen_time: Optional[str]
    representative: Optional[Dict[str, Any]]
    num_affected_services: int
    service_contexts: List[Dict[str, str]]


class ErrorGroupListResponse(BaseModel):
    """Error group list with pagination"""
    error_groups: List[ErrorGroupResponse]
    next_page_token: Optional[str]
    total_count: int


class ErrorGroupDetailResponse(BaseModel):
    """Detailed error group information"""
    group_id: str
    name: str
    tracking_issues: List[Dict[str, str]]
    recent_events: List[Dict[str, Any]]


class ErrorEventResponse(BaseModel):
    """Error event data"""
    event_time: Optional[str]
    message: Optional[str]
    service_context: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]


class ErrorStatisticsResponse(BaseModel):
    """Error statistics and trends"""
    period_start: str
    period_end: str
    total_errors: int
    unique_error_groups: int
    affected_users: int
    error_rate_trend: str
    top_errors: List[ErrorGroupResponse]
    service_filter: Optional[str]


@router.get("/errors", response_model=ErrorGroupListResponse)
async def list_errors(
    service: Optional[str] = Query(None, description="Filter by service name"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (defaults to 24h ago)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (defaults to now)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of results per page"),
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    List error groups with filtering.
    
    Retrieves error groups from Cloud Error Reporting with support for:
    - Filtering by service name
    - Time range filtering
    - Pagination for large result sets
    - Error frequency and affected user counts
    
    Args:
        service: Filter by service name (optional)
        start_time: Start of time range (optional, defaults to 24h ago)
        end_time: End of time range (optional, defaults to now)
        page_size: Number of results per page (1-1000)
        page_token: Token for pagination (optional)
        user: Authenticated user
    
    Returns:
        List of error groups with pagination
    
    Raises:
        HTTPException: If listing fails
    """
    try:
        from src.services.error_tracking_service import ErrorTrackingService
        
        # Initialize error tracking service
        async with ErrorTrackingService(project_id=settings.gcp_project_id) as error_service:
            # List error groups
            results = await error_service.list_error_groups(
                service=service,
                start_time=start_time,
                end_time=end_time,
                page_size=page_size,
                page_token=page_token
            )
        
        logger.info(
            f"Listed {results['total_count']} error groups for user {user.id} "
            f"(service={service}, period={start_time} to {end_time})"
        )
        
        # Format response
        return ErrorGroupListResponse(
            error_groups=[ErrorGroupResponse(**group) for group in results["error_groups"]],
            next_page_token=results.get("next_page_token"),
            total_count=results["total_count"]
        )
    except Exception as e:
        logger.error(f"Error listing error groups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list error groups: {str(e)}")


@router.get("/errors/{group_id}", response_model=ErrorGroupDetailResponse)
async def get_error_group(
    group_id: str,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get detailed information about a specific error group.
    
    Retrieves comprehensive details including:
    - Error group metadata
    - Tracking issues (if linked to issue tracker)
    - Recent error events
    - Stack traces and context
    
    Args:
        group_id: Error group ID
        user: Authenticated user
    
    Returns:
        Detailed error group information
    
    Raises:
        HTTPException: If error group not found or retrieval fails
    """
    try:
        from src.services.error_tracking_service import ErrorTrackingService
        
        # Initialize error tracking service
        async with ErrorTrackingService(project_id=settings.gcp_project_id) as error_service:
            # Get error group details
            error_group = await error_service.get_error_group(group_id=group_id)
        
        logger.info(f"Retrieved error group {group_id} for user {user.id}")
        
        # Format response
        return ErrorGroupDetailResponse(**error_group)
    except Exception as e:
        logger.error(f"Error retrieving error group {group_id}: {e}")
        if "not found" in str(e).lower() or "404" in str(e):
            raise HTTPException(status_code=404, detail=f"Error group {group_id} not found")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve error group: {str(e)}")


@router.get("/errors/{group_id}/events", response_model=List[ErrorEventResponse])
async def list_error_events(
    group_id: str,
    page_size: int = Query(100, ge=1, le=1000, description="Number of results per page"),
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    List error events for a specific error group.
    
    Retrieves individual error occurrences for an error group, including:
    - Stack traces
    - HTTP request context
    - User information
    - Source code references
    
    Args:
        group_id: Error group ID
        page_size: Number of results per page (1-1000)
        page_token: Token for pagination (optional)
        user: Authenticated user
    
    Returns:
        List of error events
    
    Raises:
        HTTPException: If listing fails
    """
    try:
        from src.services.error_tracking_service import ErrorTrackingService
        
        # Initialize error tracking service
        async with ErrorTrackingService(project_id=settings.gcp_project_id) as error_service:
            # List error events
            results = await error_service.list_error_events(
                group_id=group_id,
                page_size=page_size,
                page_token=page_token
            )
        
        logger.info(
            f"Listed {len(results['error_events'])} error events for group {group_id} "
            f"by user {user.id}"
        )
        
        # Format response
        return [ErrorEventResponse(**event) for event in results["error_events"]]
    except Exception as e:
        logger.error(f"Error listing error events for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list error events: {str(e)}")


@router.get("/errors/statistics", response_model=ErrorStatisticsResponse)
async def get_error_statistics(
    service: Optional[str] = Query(None, description="Filter by service name"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (defaults to 7 days ago)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (defaults to now)"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get error statistics and trends.
    
    Provides comprehensive error analytics including:
    - Total error count
    - Number of unique error groups
    - Affected user count
    - Error rate trends
    - Top errors by frequency
    
    Args:
        service: Filter by service name (optional)
        start_time: Start of time range (optional, defaults to 7 days ago)
        end_time: End of time range (optional, defaults to now)
        user: Authenticated user
    
    Returns:
        Error statistics and trends
    
    Raises:
        HTTPException: If statistics calculation fails
    """
    try:
        from src.services.error_tracking_service import ErrorTrackingService
        
        # Initialize error tracking service
        async with ErrorTrackingService(project_id=settings.gcp_project_id) as error_service:
            # Get error statistics
            stats = await error_service.get_error_statistics(
                service=service,
                start_time=start_time,
                end_time=end_time
            )
        
        logger.info(
            f"Retrieved error statistics for user {user.id}: "
            f"{stats['total_errors']} total errors, "
            f"{stats['unique_error_groups']} unique groups, "
            f"{stats['affected_users']} affected users"
        )
        
        # Format response
        return ErrorStatisticsResponse(
            period_start=stats["period_start"],
            period_end=stats["period_end"],
            total_errors=stats["total_errors"],
            unique_error_groups=stats["unique_error_groups"],
            affected_users=stats["affected_users"],
            error_rate_trend=stats["error_rate_trend"],
            top_errors=[ErrorGroupResponse(**error) for error in stats["top_errors"]],
            service_filter=stats.get("service_filter")
        )
    except Exception as e:
        logger.error(f"Error retrieving error statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve error statistics: {str(e)}")


# Service Dependency Visualization Endpoints

class ServiceNodeResponse(BaseModel):
    """Service node in dependency graph"""
    service_name: str
    call_count: int
    error_count: int
    avg_duration_ms: float
    health_status: str
    last_seen: Optional[str]


class ServiceEdgeResponse(BaseModel):
    """Service dependency edge in graph"""
    source: str
    target: str
    call_count: int
    error_count: int
    avg_duration_ms: float
    failed: bool


class DependencyGraphMetadata(BaseModel):
    """Metadata about dependency graph"""
    start_time: str
    end_time: str
    traces_analyzed: int
    total_services: int
    total_dependencies: int


class DependencyGraphResponse(BaseModel):
    """Service dependency graph"""
    nodes: List[ServiceNodeResponse]
    edges: List[ServiceEdgeResponse]
    metadata: DependencyGraphMetadata


@router.get("/dependencies", response_model=DependencyGraphResponse)
async def get_service_dependencies(
    start_time: Optional[datetime] = Query(
        None,
        description="Start of time range (defaults to 1 hour ago)"
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End of time range (defaults to now)"
    ),
    max_traces: int = Query(
        1000,
        ge=100,
        le=5000,
        description="Maximum number of traces to analyze"
    ),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get service dependency graph visualization.
    
    Analyzes distributed traces to build a dependency graph showing:
    - All services and their connections
    - Real-time health status for each service
    - Request flow direction with arrows
    - Failed dependencies highlighted
    - Call counts and average durations
    
    The graph is built by analyzing trace data within the specified time range.
    Services are represented as nodes, and service-to-service calls as edges.
    
    Health status is determined by recent error rates:
    - healthy: <5% error rate
    - degraded: 5-10% error rate
    - unhealthy: >10% error rate
    - unknown: no recent metrics available
    
    Args:
        start_time: Start of time range (optional, defaults to 1 hour ago)
        end_time: End of time range (optional, defaults to now)
        max_traces: Maximum number of traces to analyze (100-5000)
        user: Authenticated user
    
    Returns:
        Service dependency graph with nodes and edges
    
    Raises:
        HTTPException: If graph construction fails
    """
    try:
        from src.services.dependency_visualization_service import DependencyVisualizationService
        
        # Default to last hour if not specified
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(hours=1)
        
        # Validate time range
        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="start_time must be before end_time"
            )
        
        # Limit time range to 24 hours
        max_range = timedelta(hours=24)
        if end_time - start_time > max_range:
            raise HTTPException(
                status_code=400,
                detail="Time range cannot exceed 24 hours"
            )
        
        # Initialize dependency visualization service
        dep_service = DependencyVisualizationService(
            project_id=settings.gcp_project_id
        )
        
        # Build dependency graph
        graph = await dep_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time,
            max_traces=max_traces
        )
        
        logger.info(
            f"Built dependency graph for user {user.id}: "
            f"{graph['metadata']['total_services']} services, "
            f"{graph['metadata']['total_dependencies']} dependencies "
            f"from {graph['metadata']['traces_analyzed']} traces"
        )
        
        # Format response
        return DependencyGraphResponse(
            nodes=[ServiceNodeResponse(**node) for node in graph["nodes"]],
            edges=[ServiceEdgeResponse(**edge) for edge in graph["edges"]],
            metadata=DependencyGraphMetadata(**graph["metadata"])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building dependency graph: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build dependency graph: {str(e)}"
        )


# Performance Profiling Endpoints

class ProfilingSessionResponse(BaseModel):
    """Profiling session response"""
    session_id: str
    service_name: str
    pid: Optional[int]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: int
    flame_graph_url: Optional[str]
    raw_data_url: Optional[str]
    error_message: Optional[str]
    sample_rate_hz: int
    overhead_percent: Optional[float]


class ProfilingSessionListResponse(BaseModel):
    """List of profiling sessions"""
    sessions: List[ProfilingSessionResponse]
    total_count: int


class StartProfilingRequest(BaseModel):
    """Request to start profiling session"""
    service_name: str
    duration_seconds: int = 60
    pid: Optional[int] = None


@router.post("/profile/start", response_model=ProfilingSessionResponse, status_code=201)
async def start_profiling_session(
    request: StartProfilingRequest,
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Start a new on-demand profiling session.
    
    Initiates CPU profiling using py-spy at 100 Hz sampling rate.
    The profiling session runs for the specified duration (default 60 seconds)
    and generates flame graphs for visual analysis.
    
    Requirements:
    - py-spy must be installed: pip install py-spy
    - Requires admin role for security
    - Duration must be between 10 and 300 seconds
    - Profiling overhead is typically <5%
    
    Args:
        request: Profiling session configuration
        user: Authenticated admin user
    
    Returns:
        Created profiling session with session_id
    
    Raises:
        HTTPException: If profiling cannot be started
    """
    try:
        from src.services.profiling_service import ProfilingService
        
        # Initialize profiling service
        profiling_service = ProfilingService(
            project_id=settings.gcp_project_id
        )
        
        # Start profiling session
        session = await profiling_service.start_profiling_session(
            service_name=request.service_name,
            duration_seconds=request.duration_seconds,
            pid=request.pid
        )
        
        logger.info(
            f"Started profiling session {session.session_id} for {request.service_name} "
            f"by user {user.id} (duration: {request.duration_seconds}s)"
        )
        
        return ProfilingSessionResponse(
            session_id=session.session_id,
            service_name=session.service_name,
            pid=session.pid,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            duration_seconds=session.duration_seconds,
            flame_graph_url=session.flame_graph_url,
            raw_data_url=session.raw_data_url,
            error_message=session.error_message,
            sample_rate_hz=session.sample_rate_hz,
            overhead_percent=session.overhead_percent
        )
    except ValueError as e:
        logger.error(f"Validation error starting profiling session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting profiling session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start profiling session: {str(e)}"
        )


@router.get("/profile/{session_id}", response_model=ProfilingSessionResponse)
async def get_profiling_session(
    session_id: str,
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get profiling session details by session ID.
    
    Retrieves the status and results of a profiling session, including:
    - Session status (running, completed, failed)
    - Flame graph URL (when completed)
    - Raw profiling data URL (when completed)
    - Performance overhead metrics
    - Error information (if failed)
    
    The flame graph can be viewed directly in a browser, and the raw data
    can be downloaded and analyzed with tools like speedscope.app.
    
    Args:
        session_id: Profiling session ID
        user: Authenticated admin user
    
    Returns:
        Profiling session details
    
    Raises:
        HTTPException: If session not found or retrieval fails
    """
    try:
        from src.services.profiling_service import ProfilingService
        
        # Initialize profiling service
        profiling_service = ProfilingService(
            project_id=settings.gcp_project_id
        )
        
        # Get profiling session
        session = await profiling_service.get_profiling_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Profiling session {session_id} not found"
            )
        
        logger.info(
            f"Retrieved profiling session {session_id} for user {user.id} "
            f"(status: {session.status})"
        )
        
        return ProfilingSessionResponse(
            session_id=session.session_id,
            service_name=session.service_name,
            pid=session.pid,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            duration_seconds=session.duration_seconds,
            flame_graph_url=session.flame_graph_url,
            raw_data_url=session.raw_data_url,
            error_message=session.error_message,
            sample_rate_hz=session.sample_rate_hz,
            overhead_percent=session.overhead_percent
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profiling session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve profiling session: {str(e)}"
        )


@router.get("/profile", response_model=ProfilingSessionListResponse)
async def list_profiling_sessions(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status: Optional[str] = Query(
        None,
        pattern="^(running|completed|failed)$",
        description="Filter by status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    user: User = Depends(require_role(Role.ADMIN)),
    _: None = Depends(rate_limit_dependency)
):
    """
    List profiling sessions with optional filters.
    
    Retrieves a list of profiling sessions, optionally filtered by:
    - Service name
    - Status (running, completed, failed)
    
    Sessions are returned in reverse chronological order (most recent first).
    
    Args:
        service_name: Filter by service name (optional)
        status: Filter by status (optional)
        limit: Maximum number of results (1-100)
        user: Authenticated admin user
    
    Returns:
        List of profiling sessions
    
    Raises:
        HTTPException: If listing fails
    """
    try:
        from src.services.profiling_service import ProfilingService
        
        # Initialize profiling service
        profiling_service = ProfilingService(
            project_id=settings.gcp_project_id
        )
        
        # List profiling sessions
        sessions = await profiling_service.list_profiling_sessions(
            service_name=service_name,
            status=status,
            limit=limit
        )
        
        logger.info(
            f"Listed {len(sessions)} profiling sessions for user {user.id} "
            f"(service={service_name}, status={status})"
        )
        
        return ProfilingSessionListResponse(
            sessions=[
                ProfilingSessionResponse(
                    session_id=session.session_id,
                    service_name=session.service_name,
                    pid=session.pid,
                    status=session.status,
                    started_at=session.started_at,
                    completed_at=session.completed_at,
                    duration_seconds=session.duration_seconds,
                    flame_graph_url=session.flame_graph_url,
                    raw_data_url=session.raw_data_url,
                    error_message=session.error_message,
                    sample_rate_hz=session.sample_rate_hz,
                    overhead_percent=session.overhead_percent
                )
                for session in sessions
            ],
            total_count=len(sessions)
        )
    except Exception as e:
        logger.error(f"Error listing profiling sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list profiling sessions: {str(e)}"
        )



# Custom Dashboard Endpoints

@router.post("/dashboards", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Create a new custom monitoring dashboard.
    
    Allows users to create personalized dashboards with custom widgets for monitoring
    specific metrics. Supports multiple widget types:
    - line_chart: Time series line charts
    - bar_chart: Bar charts for comparisons
    - gauge: Gauge charts for single values
    - stat_card: Simple stat cards with numbers
    
    Each widget can be configured with:
    - Data source (metric type, service, aggregation, time range)
    - Display options (colors, labels, thresholds)
    - Position and size in the dashboard grid
    
    Args:
        dashboard_data: Dashboard creation data
        user: Authenticated user
    
    Returns:
        Created dashboard configuration
    
    Raises:
        HTTPException: If creation fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            dashboard = await dashboard_service.create_dashboard(
                user_id=user.id,
                dashboard_data=dashboard_data
            )
            
            logger.info(f"Created dashboard {dashboard.id} for user {user.id}")
            
            return DashboardResponse.model_validate(dashboard)
    except ValidationError as e:
        logger.error(f"Validation error creating dashboard: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create dashboard")


@router.get("/dashboards", response_model=DashboardListResponse)
async def list_dashboards(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    List all dashboards for the authenticated user.
    
    Returns a paginated list of dashboards owned by the user, ordered by
    most recently updated first.
    
    Args:
        page: Page number for pagination
        page_size: Number of items per page (1-100)
        user: Authenticated user
    
    Returns:
        Paginated list of dashboards
    
    Raises:
        HTTPException: If listing fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            dashboards, total = await dashboard_service.list_dashboards(
                user_id=user.id,
                page=page,
                page_size=page_size
            )
            
            logger.debug(
                f"Listed {len(dashboards)} dashboards for user {user.id} "
                f"(page {page}, total {total})"
            )
            
            return DashboardListResponse(
                dashboards=[DashboardResponse.model_validate(d) for d in dashboards],
                total=total,
                page=page,
                page_size=page_size
            )
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to list dashboards")


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get a specific dashboard by ID.
    
    Retrieves a dashboard owned by the user or a public dashboard.
    
    Args:
        dashboard_id: Dashboard ID
        user: Authenticated user
    
    Returns:
        Dashboard configuration
    
    Raises:
        HTTPException: If dashboard not found or access denied
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            dashboard = await dashboard_service.get_dashboard(
                dashboard_id=dashboard_id,
                user_id=user.id
            )
            
            if not dashboard:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found"
                )
            
            return DashboardResponse.model_validate(dashboard)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")


@router.patch("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: UUID,
    dashboard_data: DashboardUpdate,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Update a dashboard.
    
    Allows updating dashboard properties including:
    - Name and description
    - Layout configuration
    - Widget configurations
    - Public/private status
    
    Only the dashboard owner can update it.
    
    Args:
        dashboard_id: Dashboard ID
        dashboard_data: Dashboard update data
        user: Authenticated user
    
    Returns:
        Updated dashboard configuration
    
    Raises:
        HTTPException: If dashboard not found or update fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            dashboard = await dashboard_service.update_dashboard(
                dashboard_id=dashboard_id,
                user_id=user.id,
                dashboard_data=dashboard_data
            )
            
            if not dashboard:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found"
                )
            
            logger.info(f"Updated dashboard {dashboard_id}")
            
            return DashboardResponse.model_validate(dashboard)
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error updating dashboard: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update dashboard")


@router.delete("/dashboards/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: UUID,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Delete a dashboard.
    
    Permanently deletes a dashboard. Only the dashboard owner can delete it.
    
    Args:
        dashboard_id: Dashboard ID
        user: Authenticated user
    
    Raises:
        HTTPException: If dashboard not found or deletion fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            deleted = await dashboard_service.delete_dashboard(
                dashboard_id=dashboard_id,
                user_id=user.id
            )
            
            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found"
                )
            
            logger.info(f"Deleted dashboard {dashboard_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete dashboard")


@router.post("/dashboards/{dashboard_id}/share", response_model=DashboardShareResponse)
async def share_dashboard(
    dashboard_id: UUID,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Generate a share token for a dashboard.
    
    Makes the dashboard publicly accessible via a unique share token.
    The dashboard will be accessible to anyone with the share URL,
    even without authentication.
    
    If the dashboard already has a share token, this endpoint will
    regenerate it, invalidating the old token.
    
    Args:
        dashboard_id: Dashboard ID
        user: Authenticated user
    
    Returns:
        Share token and URL
    
    Raises:
        HTTPException: If dashboard not found or sharing fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            share_token = await dashboard_service.generate_share_token(
                dashboard_id=dashboard_id,
                user_id=user.id
            )
            
            if not share_token:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found"
                )
            
            # Construct share URL
            share_url = f"{settings.api_base_url}/api/v1/monitoring/dashboards/public/{share_token}"
            
            logger.info(f"Generated share token for dashboard {dashboard_id}")
            
            return DashboardShareResponse(
                dashboard_id=dashboard_id,
                share_token=share_token,
                share_url=share_url,
                is_public=True
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to share dashboard")


@router.get("/dashboards/public/{share_token}", response_model=DashboardResponse)
async def get_public_dashboard(
    share_token: str,
    _: None = Depends(rate_limit_dependency)
):
    """
    Get a public dashboard by share token.
    
    Retrieves a dashboard using its public share token. No authentication required.
    This endpoint allows anyone with the share URL to view the dashboard.
    
    Args:
        share_token: Dashboard share token
    
    Returns:
        Dashboard configuration
    
    Raises:
        HTTPException: If dashboard not found or not public
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            dashboard = await dashboard_service.get_dashboard_by_share_token(
                share_token=share_token
            )
            
            if not dashboard:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found or not public"
                )
            
            logger.debug(f"Retrieved public dashboard via share token")
            
            return DashboardResponse.model_validate(dashboard)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving public dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")


@router.post("/dashboards/copy", response_model=DashboardResponse, status_code=201)
async def copy_dashboard(
    copy_request: DashboardCopyRequest,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Copy a dashboard to the user's account.
    
    Creates a copy of an existing dashboard (either owned by the user or public).
    The copied dashboard will be private by default and owned by the requesting user.
    
    This is useful for:
    - Creating variations of existing dashboards
    - Copying shared dashboards from other users
    - Creating templates from public dashboards
    
    Args:
        copy_request: Copy request with source dashboard ID and new name
        user: Authenticated user
    
    Returns:
        Copied dashboard configuration
    
    Raises:
        HTTPException: If source dashboard not found or copying fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            copied_dashboard = await dashboard_service.copy_dashboard(
                source_dashboard_id=copy_request.source_dashboard_id,
                user_id=user.id,
                new_name=copy_request.new_name
            )
            
            if not copied_dashboard:
                raise HTTPException(
                    status_code=404,
                    detail="Source dashboard not found or not accessible"
                )
            
            logger.info(
                f"Copied dashboard {copy_request.source_dashboard_id} to "
                f"{copied_dashboard.id} for user {user.id}"
            )
            
            return DashboardResponse.model_validate(copied_dashboard)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error copying dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to copy dashboard")


@router.post("/dashboards/{dashboard_id}/widget-data", response_model=WidgetDataResponse)
async def get_widget_data(
    dashboard_id: UUID,
    widget_request: WidgetDataRequest,
    user: User = Depends(require_role(Role.USER)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Fetch data for a specific widget.
    
    Retrieves time series data for a widget based on its data source configuration.
    The data is fetched from Cloud Monitoring and cached for performance.
    
    Cache TTL varies based on time range:
    - 1 hour range: 1 minute cache
    - Up to 6 hours: 5 minutes cache
    - Longer ranges: 10-30 minutes cache
    
    Supports custom time ranges per widget:
    - '1h': Last 1 hour
    - '6h': Last 6 hours
    - '24h': Last 24 hours
    - '7d': Last 7 days
    - '30d': Last 30 days
    
    Args:
        dashboard_id: Dashboard ID (for access control)
        widget_request: Widget data request with data source configuration
        user: Authenticated user
    
    Returns:
        Widget data with time series points
    
    Raises:
        HTTPException: If dashboard not found or data fetch fails
    """
    try:
        async with DatabaseService() as db:
            from src.services.dashboard_service import DashboardService
            
            dashboard_service = DashboardService(
                db_session=db.session,
                project_id=settings.gcp_project_id
            )
            
            # Verify dashboard access
            dashboard = await dashboard_service.get_dashboard(
                dashboard_id=dashboard_id,
                user_id=user.id
            )
            
            if not dashboard:
                raise HTTPException(
                    status_code=404,
                    detail="Dashboard not found"
                )
            
            # Fetch widget data
            data_points = await dashboard_service.get_widget_data(
                data_source=widget_request.data_source
            )
            
            logger.debug(
                f"Fetched {len(data_points)} data points for widget {widget_request.widget_id} "
                f"in dashboard {dashboard_id}"
            )
            
            return WidgetDataResponse(
                widget_id=widget_request.widget_id,
                data=data_points,
                metadata={
                    "metric_type": widget_request.data_source.metric_type,
                    "service_name": widget_request.data_source.service_name,
                    "aggregation": widget_request.data_source.aggregation,
                    "time_range": widget_request.data_source.time_range
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching widget data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch widget data")
