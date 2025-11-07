"""Error response models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Error code enumeration."""
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: ErrorDetail
    request_id: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "API rate limit exceeded. Try again in 60 seconds.",
                    "details": {
                        "limit": 100,
                        "window": "1h",
                        "retry_after": 60
                    }
                },
                "request_id": "req_abc123",
                "timestamp": "2025-11-07T10:30:00Z"
            }
        }
