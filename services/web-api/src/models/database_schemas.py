"""Pydantic schemas for database models."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Backfill Job Schemas
class BackfillJobCreate(BaseModel):
    """Schema for creating a backfill job."""
    job_type: str = Field(..., max_length=50)
    start_block: int = Field(..., ge=0)
    end_block: int = Field(..., ge=0)
    created_by: Optional[str] = Field(None, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_type": "blocks",
                "start_block": 800000,
                "end_block": 810000,
                "created_by": "admin@utxoiq.com"
            }
        }
    )


class BackfillJobUpdate(BaseModel):
    """Schema for updating backfill job progress."""
    current_block: int = Field(..., ge=0)
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    estimated_completion: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(running|completed|failed|paused)$")
    error_message: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_block": 805000,
                "progress_percentage": 50.0,
                "status": "running"
            }
        }
    )


class BackfillJobResponse(BaseModel):
    """Schema for backfill job response."""
    id: UUID
    job_type: str
    start_block: int
    end_block: int
    current_block: int
    status: str
    progress_percentage: float
    estimated_completion: Optional[datetime]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_by: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# Insight Feedback Schemas
class FeedbackCreate(BaseModel):
    """Schema for creating insight feedback."""
    insight_id: str = Field(..., max_length=100)
    user_id: str = Field(..., max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    flag_type: Optional[str] = Field(None, pattern="^(inaccurate|misleading|spam)$")
    flag_reason: Optional[str] = Field(None, max_length=500)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "insight_id": "insight_123",
                "user_id": "user_456",
                "rating": 5,
                "comment": "Very insightful analysis"
            }
        }
    )


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: UUID
    insight_id: str
    user_id: str
    rating: Optional[int]
    comment: Optional[str]
    flag_type: Optional[str]
    flag_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FeedbackStats(BaseModel):
    """Schema for aggregated feedback statistics."""
    insight_id: str
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[int, int]
    total_comments: int
    total_flags: int
    flag_types: Dict[str, int]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "insight_id": "insight_123",
                "total_ratings": 42,
                "average_rating": 4.5,
                "rating_distribution": {1: 1, 2: 2, 3: 5, 4: 14, 5: 20},
                "total_comments": 15,
                "total_flags": 2,
                "flag_types": {"inaccurate": 1, "spam": 1}
            }
        }
    )


# System Metric Schemas
class MetricCreate(BaseModel):
    """Schema for creating a system metric."""
    service_name: str = Field(..., max_length=100)
    metric_type: str = Field(..., max_length=50)
    metric_value: float
    unit: str = Field(..., max_length=20)
    metric_metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service_name": "web-api",
                "metric_type": "cpu",
                "metric_value": 45.5,
                "unit": "percent",
                "metric_metadata": {"host": "server-01"}
            }
        }
    )


class MetricResponse(BaseModel):
    """Schema for metric response."""
    id: UUID
    service_name: str
    metric_type: str
    metric_value: float
    unit: str
    timestamp: datetime
    metric_metadata: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)


class MetricQuery(BaseModel):
    """Schema for querying metrics."""
    service_name: Optional[str] = None
    metric_type: Optional[str] = None
    start_time: datetime
    end_time: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service_name": "web-api",
                "metric_type": "cpu",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z"
            }
        }
    )
