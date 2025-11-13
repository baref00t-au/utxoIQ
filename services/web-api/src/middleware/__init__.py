"""Middleware modules."""
from .auth import (
    get_current_user,
    get_current_user_from_api_key,
    get_optional_user,
    require_subscription_tier
)
from .rate_limit import rate_limit_dependency, check_rate_limit

# Backward compatibility alias
verify_firebase_token = get_current_user

__all__ = [
    "get_current_user",
    "get_current_user_from_api_key",
    "get_optional_user",
    "require_subscription_tier",
    "verify_firebase_token",  # Backward compatibility
    "rate_limit_dependency",
    "check_rate_limit",
]
