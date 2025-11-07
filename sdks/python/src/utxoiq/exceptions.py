"""Exception classes for utxoIQ SDK."""
from typing import Optional, Dict, Any


class UtxoIQError(Exception):
    """Base exception for all utxoIQ SDK errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id


class AuthenticationError(UtxoIQError):
    """Raised when authentication fails."""
    pass


class RateLimitError(UtxoIQError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(UtxoIQError):
    """Raised when request validation fails."""
    pass


class NotFoundError(UtxoIQError):
    """Raised when requested resource is not found."""
    pass


class SubscriptionRequiredError(UtxoIQError):
    """Raised when feature requires paid subscription."""
    pass


class DataUnavailableError(UtxoIQError):
    """Raised when blockchain data is not yet available."""
    pass


class ConfidenceTooLowError(UtxoIQError):
    """Raised when insight confidence is below publication threshold."""
    pass
