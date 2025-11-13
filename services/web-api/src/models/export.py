"""Export data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ExportFormat(str, Enum):
    """Export format enumeration."""
    CSV = "csv"
    JSON = "json"


class ExportRequest(BaseModel):
    """Export request model."""
    format: ExportFormat
    filters: Optional[dict] = Field(
        None,
        description="Filter criteria applied to the export"
    )
    limit: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Maximum number of records to export"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "format": "csv",
                "filters": {
                    "signal_type": "mempool",
                    "min_confidence": 0.7,
                    "date_range": {
                        "start": "2025-11-01T00:00:00Z",
                        "end": "2025-11-07T23:59:59Z"
                    }
                },
                "limit": 1000
            }
        }


class ExportResponse(BaseModel):
    """Export response model."""
    filename: str
    content: str
    content_type: str
    record_count: int
    generated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "insights_mempool_2025-11-07.csv",
                "content": "id,signal_type,headline,confidence...",
                "content_type": "text/csv",
                "record_count": 150,
                "generated_at": "2025-11-07T10:30:00Z"
            }
        }
