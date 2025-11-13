"""Error response models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class AuthenticationError(Exception):
    """Base exception raised for authentication failures."""
    pass


class TokenExpiredError(AuthenticationError):
    """Exception raised when authentication token has expired."""
    pass


class InvalidTokenError(AuthenticationError):
    """Exception raised when authentication token is invalid."""
    pass


class RevokedTokenError(AuthenticationError):
    """Exception raised when authentication token has been revoked."""
    pass


class InvalidAPIKeyError(AuthenticationError):
    """Exception raised when API key is invalid or revoked."""
    pass


class InsufficientPermissionsError(Exception):
    """Exception raised when user lacks required permissions."""
    pass


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 3600,
        limit: int = 100,
        remaining: int = 0
    ):
        """
        Initialize rate limit exceeded error.
        
        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
            limit: Rate limit value
            remaining: Remaining requests
        """
        self.message = message
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        super().__init__(self.message)


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
