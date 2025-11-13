"""Audit logging service for security and compliance events."""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

# Configure structured logging for audit events
logger = logging.getLogger(__name__)

# Create a separate logger for audit events that can be configured
# with specific handlers and formatters for Cloud Logging
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)


class AuditService:
    """Service for logging security and authorization events."""
    
    @staticmethod
    async def log_successful_login(
        user_id: UUID,
        user_email: str,
        ip_address: str,
        auth_method: str = "firebase_jwt"
    ) -> None:
        """
        Log successful login attempts.
        
        Args:
            user_id: User's unique identifier
            user_email: User's email address
            ip_address: IP address of the login request
            auth_method: Authentication method used (firebase_jwt, api_key)
        """
        audit_logger.info(
            "SUCCESSFUL_LOGIN",
            extra={
                "event_type": "successful_login",
                "user_id": str(user_id),
                "user_email": user_email,
                "ip_address": ip_address,
                "auth_method": auth_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_failed_login(
        email: Optional[str],
        ip_address: str,
        reason: str,
        auth_method: str = "firebase_jwt"
    ) -> None:
        """
        Log failed login attempts.
        
        Args:
            email: Email address attempted (if available)
            ip_address: IP address of the failed login attempt
            reason: Reason for login failure (e.g., 'invalid_token', 'expired_token')
            auth_method: Authentication method attempted
        """
        audit_logger.warning(
            "FAILED_LOGIN",
            extra={
                "event_type": "failed_login",
                "email": email or "unknown",
                "ip_address": ip_address,
                "reason": reason,
                "auth_method": auth_method,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_authorization_failure(
        user_id: UUID,
        user_email: str,
        user_role: str,
        attempted_action: str,
        required_permission: str,
        reason: str
    ) -> None:
        """
        Log authorization failure events.
        
        Args:
            user_id: User's unique identifier
            user_email: User's email address
            user_role: User's current role
            attempted_action: The action user attempted to perform
            required_permission: The permission that was required
            reason: Reason for authorization failure
        """
        audit_logger.warning(
            "AUTHORIZATION_FAILURE",
            extra={
                "event_type": "authorization_failure",
                "user_id": str(user_id),
                "user_email": user_email,
                "user_role": user_role,
                "attempted_action": attempted_action,
                "required_permission": required_permission,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_role_change(
        user_id: UUID,
        user_email: str,
        old_role: str,
        new_role: str,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None
    ) -> None:
        """
        Log role assignment changes.
        
        Args:
            user_id: User whose role was changed
            user_email: User's email address
            old_role: Previous role
            new_role: New role
            changed_by: ID of user who made the change
            changed_by_email: Email of user who made the change
        """
        audit_logger.info(
            "ROLE_CHANGE",
            extra={
                "event_type": "role_change",
                "user_id": str(user_id),
                "user_email": user_email,
                "old_role": old_role,
                "new_role": new_role,
                "changed_by": str(changed_by) if changed_by else None,
                "changed_by_email": changed_by_email,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_subscription_tier_change(
        user_id: UUID,
        user_email: str,
        old_tier: str,
        new_tier: str,
        reason: str,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None
    ) -> None:
        """
        Log subscription tier changes.
        
        Args:
            user_id: User whose tier was changed
            user_email: User's email address
            old_tier: Previous subscription tier
            new_tier: New subscription tier
            reason: Reason for tier change (e.g., 'stripe_payment', 'admin_override')
            changed_by: ID of user who made the change (if manual)
            changed_by_email: Email of user who made the change (if manual)
        """
        audit_logger.info(
            "SUBSCRIPTION_TIER_CHANGE",
            extra={
                "event_type": "subscription_tier_change",
                "user_id": str(user_id),
                "user_email": user_email,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "reason": reason,
                "changed_by": str(changed_by) if changed_by else None,
                "changed_by_email": changed_by_email,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_api_key_scope_failure(
        api_key_id: UUID,
        user_id: UUID,
        user_email: str,
        required_scope: str,
        available_scopes: list[str],
        attempted_endpoint: str
    ) -> None:
        """
        Log API key scope validation failures.
        
        Args:
            api_key_id: API key identifier
            user_id: User who owns the API key
            user_email: User's email address
            required_scope: The scope that was required
            available_scopes: Scopes available on the API key
            attempted_endpoint: The endpoint that was attempted
        """
        audit_logger.warning(
            "API_KEY_SCOPE_FAILURE",
            extra={
                "event_type": "api_key_scope_failure",
                "api_key_id": str(api_key_id),
                "user_id": str(user_id),
                "user_email": user_email,
                "required_scope": required_scope,
                "available_scopes": available_scopes,
                "attempted_endpoint": attempted_endpoint,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_api_key_creation(
        api_key_id: UUID,
        user_id: UUID,
        user_email: str,
        key_name: str,
        scopes: list[str]
    ) -> None:
        """
        Log API key creation events.
        
        Args:
            api_key_id: Created API key identifier
            user_id: User who created the key
            user_email: User's email address
            key_name: Name given to the API key
            scopes: Scopes assigned to the API key
        """
        audit_logger.info(
            "API_KEY_CREATED",
            extra={
                "event_type": "api_key_created",
                "api_key_id": str(api_key_id),
                "user_id": str(user_id),
                "user_email": user_email,
                "key_name": key_name,
                "scopes": scopes,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    async def log_api_key_revocation(
        api_key_id: UUID,
        user_id: UUID,
        user_email: str,
        key_name: str
    ) -> None:
        """
        Log API key revocation events.
        
        Args:
            api_key_id: Revoked API key identifier
            user_id: User who revoked the key
            user_email: User's email address
            key_name: Name of the revoked API key
        """
        audit_logger.info(
            "API_KEY_REVOKED",
            extra={
                "event_type": "api_key_revoked",
                "api_key_id": str(api_key_id),
                "user_id": str(user_id),
                "user_email": user_email,
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
