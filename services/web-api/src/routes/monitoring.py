"""
Monitoring and system status endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

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
async def get_system_status():
    """
    Get overall system status including all services and backfill progress
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
    
    # TODO: Query actual backfill progress from database
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


@router.get("/backfill", response_model=List[BackfillProgress])
async def get_backfill_progress(
    status: Optional[BackfillStatus] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get backfill job progress
    
    Args:
        status: Filter by job status
        limit: Maximum number of jobs to return
    """
    # TODO: Query from database
    return []


@router.get("/backfill/{job_id}", response_model=BackfillProgress)
async def get_backfill_job(job_id: str):
    """
    Get specific backfill job progress
    """
    # TODO: Query from database
    raise HTTPException(status_code=404, detail="Job not found")


@router.get("/metrics/processing", response_model=ProcessingMetrics)
async def get_processing_metrics():
    """
    Get real-time processing metrics
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
