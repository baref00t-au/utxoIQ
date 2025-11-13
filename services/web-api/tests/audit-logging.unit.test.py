"""Tests for audit logging service."""
import pytest
import logging
from unittest.mock import patch, MagicMock, call
from uuid import uuid4
from datetime import datetime

from src.services.audit_service import AuditService


@pytest.fixture
def mock_audit_logger():
    """Mock the audit logger for testing."""
    with patch("src.services.audit_service.audit_logger") as mock_logger:
        yield mock_logger


class TestSuccessfulLoginLogging:
    """Tests for successful login event logging."""
    
    @pytest.mark.asyncio
    async def test_log_successful_login_with_jwt(self, mock_audit_logger):
        """Test logging successful login with JWT authentication."""
        user_id = uuid4()
        user_email = "test@example.com"
        ip_address = "192.168.1.1"
        
        await AuditService.log_successful_login(
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            auth_method="firebase_jwt"
        )
        
        # Verify logger was called
        assert mock_audit_logger.info.called
        call_args = mock_audit_logger.info.call_args
        
        # Check message
        assert call_args[0][0] == "SUCCESSFUL_LOGIN"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "successful_login"
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["ip_address"] == ip_address
        assert extra["auth_method"] == "firebase_jwt"
        assert "timestamp" in extra
    
    @pytest.mark.asyncio
    async def test_log_successful_login_with_api_key(self, mock_audit_logger):
        """Test logging successful login with API key authentication."""
        user_id = uuid4()
        user_email = "api@example.com"
        ip_address = "10.0.0.1"
        
        await AuditService.log_successful_login(
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            auth_method="api_key"
        )
        
        # Verify logger was called with correct auth method
        call_args = mock_audit_logger.info.call_args
        extra = call_args[1]["extra"]
        assert extra["auth_method"] == "api_key"


class TestFailedLoginLogging:
    """Tests for failed login event logging."""
    
    @pytest.mark.asyncio
    async def test_log_failed_login_with_email(self, mock_audit_logger):
        """Test logging failed login attempt with email."""
        email = "test@example.com"
        ip_address = "192.168.1.1"
        reason = "invalid_token"
        
        await AuditService.log_failed_login(
            email=email,
            ip_address=ip_address,
            reason=reason,
            auth_method="firebase_jwt"
        )
        
        # Verify logger was called with warning level
        assert mock_audit_logger.warning.called
        call_args = mock_audit_logger.warning.call_args
        
        # Check message
        assert call_args[0][0] == "FAILED_LOGIN"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "failed_login"
        assert extra["email"] == email
        assert extra["ip_address"] == ip_address
        assert extra["reason"] == reason
        assert extra["auth_method"] == "firebase_jwt"
        assert "timestamp" in extra
    
    @pytest.mark.asyncio
    async def test_log_failed_login_without_email(self, mock_audit_logger):
        """Test logging failed login attempt without email."""
        ip_address = "192.168.1.1"
        reason = "no_credentials_provided"
        
        await AuditService.log_failed_login(
            email=None,
            ip_address=ip_address,
            reason=reason,
            auth_method="firebase_jwt"
        )
        
        # Verify email defaults to "unknown"
        call_args = mock_audit_logger.warning.call_args
        extra = call_args[1]["extra"]
        assert extra["email"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_log_failed_login_expired_token(self, mock_audit_logger):
        """Test logging failed login with expired token."""
        email = "test@example.com"
        ip_address = "192.168.1.1"
        
        await AuditService.log_failed_login(
            email=email,
            ip_address=ip_address,
            reason="token_expired",
            auth_method="firebase_jwt"
        )
        
        call_args = mock_audit_logger.warning.call_args
        extra = call_args[1]["extra"]
        assert extra["reason"] == "token_expired"
    
    @pytest.mark.asyncio
    async def test_log_failed_login_invalid_api_key(self, mock_audit_logger):
        """Test logging failed login with invalid API key."""
        ip_address = "10.0.0.1"
        
        await AuditService.log_failed_login(
            email=None,
            ip_address=ip_address,
            reason="invalid_or_revoked_api_key",
            auth_method="api_key"
        )
        
        call_args = mock_audit_logger.warning.call_args
        extra = call_args[1]["extra"]
        assert extra["auth_method"] == "api_key"
        assert extra["reason"] == "invalid_or_revoked_api_key"


class TestAPIKeyEventLogging:
    """Tests for API key creation and revocation logging."""
    
    @pytest.mark.asyncio
    async def test_log_api_key_creation(self, mock_audit_logger):
        """Test logging API key creation event."""
        api_key_id = uuid4()
        user_id = uuid4()
        user_email = "test@example.com"
        key_name = "Production API Key"
        scopes = ["insights:read", "alerts:write"]
        
        await AuditService.log_api_key_creation(
            api_key_id=api_key_id,
            user_id=user_id,
            user_email=user_email,
            key_name=key_name,
            scopes=scopes
        )
        
        # Verify logger was called
        assert mock_audit_logger.info.called
        call_args = mock_audit_logger.info.call_args
        
        # Check message
        assert call_args[0][0] == "API_KEY_CREATED"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "api_key_created"
        assert extra["api_key_id"] == str(api_key_id)
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["key_name"] == key_name
        assert extra["scopes"] == scopes
        assert "timestamp" in extra
    
    @pytest.mark.asyncio
    async def test_log_api_key_revocation(self, mock_audit_logger):
        """Test logging API key revocation event."""
        api_key_id = uuid4()
        user_id = uuid4()
        user_email = "test@example.com"
        key_name = "Old API Key"
        
        await AuditService.log_api_key_revocation(
            api_key_id=api_key_id,
            user_id=user_id,
            user_email=user_email,
            key_name=key_name
        )
        
        # Verify logger was called
        assert mock_audit_logger.info.called
        call_args = mock_audit_logger.info.call_args
        
        # Check message
        assert call_args[0][0] == "API_KEY_REVOKED"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "api_key_revoked"
        assert extra["api_key_id"] == str(api_key_id)
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["key_name"] == key_name
        assert "timestamp" in extra


class TestAuthorizationEventLogging:
    """Tests for authorization failure logging."""
    
    @pytest.mark.asyncio
    async def test_log_authorization_failure(self, mock_audit_logger):
        """Test logging authorization failure event."""
        user_id = uuid4()
        user_email = "test@example.com"
        user_role = "user"
        attempted_action = "access_admin_endpoint"
        required_permission = "role:admin"
        reason = "User has user role, requires admin"
        
        await AuditService.log_authorization_failure(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            attempted_action=attempted_action,
            required_permission=required_permission,
            reason=reason
        )
        
        # Verify logger was called with warning level
        assert mock_audit_logger.warning.called
        call_args = mock_audit_logger.warning.call_args
        
        # Check message
        assert call_args[0][0] == "AUTHORIZATION_FAILURE"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "authorization_failure"
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["user_role"] == user_role
        assert extra["attempted_action"] == attempted_action
        assert extra["required_permission"] == required_permission
        assert extra["reason"] == reason
        assert "timestamp" in extra
    
    @pytest.mark.asyncio
    async def test_log_api_key_scope_failure(self, mock_audit_logger):
        """Test logging API key scope validation failure."""
        api_key_id = uuid4()
        user_id = uuid4()
        user_email = "test@example.com"
        required_scope = "alerts:write"
        available_scopes = ["insights:read"]
        attempted_endpoint = "/api/v1/alerts"
        
        await AuditService.log_api_key_scope_failure(
            api_key_id=api_key_id,
            user_id=user_id,
            user_email=user_email,
            required_scope=required_scope,
            available_scopes=available_scopes,
            attempted_endpoint=attempted_endpoint
        )
        
        # Verify logger was called with warning level
        assert mock_audit_logger.warning.called
        call_args = mock_audit_logger.warning.call_args
        
        # Check message
        assert call_args[0][0] == "API_KEY_SCOPE_FAILURE"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "api_key_scope_failure"
        assert extra["api_key_id"] == str(api_key_id)
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["required_scope"] == required_scope
        assert extra["available_scopes"] == available_scopes
        assert extra["attempted_endpoint"] == attempted_endpoint
        assert "timestamp" in extra


class TestRoleAndTierChangeLogging:
    """Tests for role and subscription tier change logging."""
    
    @pytest.mark.asyncio
    async def test_log_role_change(self, mock_audit_logger):
        """Test logging role change event."""
        user_id = uuid4()
        user_email = "test@example.com"
        old_role = "user"
        new_role = "admin"
        changed_by = uuid4()
        changed_by_email = "admin@example.com"
        
        await AuditService.log_role_change(
            user_id=user_id,
            user_email=user_email,
            old_role=old_role,
            new_role=new_role,
            changed_by=changed_by,
            changed_by_email=changed_by_email
        )
        
        # Verify logger was called
        assert mock_audit_logger.info.called
        call_args = mock_audit_logger.info.call_args
        
        # Check message
        assert call_args[0][0] == "ROLE_CHANGE"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "role_change"
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["old_role"] == old_role
        assert extra["new_role"] == new_role
        assert extra["changed_by"] == str(changed_by)
        assert extra["changed_by_email"] == changed_by_email
        assert "timestamp" in extra
    
    @pytest.mark.asyncio
    async def test_log_subscription_tier_change(self, mock_audit_logger):
        """Test logging subscription tier change event."""
        user_id = uuid4()
        user_email = "test@example.com"
        old_tier = "free"
        new_tier = "pro"
        reason = "stripe_payment"
        changed_by = uuid4()
        changed_by_email = "admin@example.com"
        
        await AuditService.log_subscription_tier_change(
            user_id=user_id,
            user_email=user_email,
            old_tier=old_tier,
            new_tier=new_tier,
            reason=reason,
            changed_by=changed_by,
            changed_by_email=changed_by_email
        )
        
        # Verify logger was called
        assert mock_audit_logger.info.called
        call_args = mock_audit_logger.info.call_args
        
        # Check message
        assert call_args[0][0] == "SUBSCRIPTION_TIER_CHANGE"
        
        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "subscription_tier_change"
        assert extra["user_id"] == str(user_id)
        assert extra["user_email"] == user_email
        assert extra["old_tier"] == old_tier
        assert extra["new_tier"] == new_tier
        assert extra["reason"] == reason
        assert extra["changed_by"] == str(changed_by)
        assert extra["changed_by_email"] == changed_by_email
        assert "timestamp" in extra
    
    @pytest.mark.asyncio
    async def test_log_subscription_tier_change_without_admin(self, mock_audit_logger):
        """Test logging subscription tier change without admin (e.g., Stripe webhook)."""
        user_id = uuid4()
        user_email = "test@example.com"
        old_tier = "free"
        new_tier = "pro"
        reason = "stripe_payment"
        
        await AuditService.log_subscription_tier_change(
            user_id=user_id,
            user_email=user_email,
            old_tier=old_tier,
            new_tier=new_tier,
            reason=reason,
            changed_by=None,
            changed_by_email=None
        )
        
        # Verify logger was called
        call_args = mock_audit_logger.info.call_args
        extra = call_args[1]["extra"]
        
        # Check that changed_by fields are None
        assert extra["changed_by"] is None
        assert extra["changed_by_email"] is None


class TestTimestampFormat:
    """Tests for timestamp formatting in audit logs."""
    
    @pytest.mark.asyncio
    async def test_timestamp_is_iso_format(self, mock_audit_logger):
        """Test that timestamps are in ISO 8601 format."""
        user_id = uuid4()
        
        await AuditService.log_successful_login(
            user_id=user_id,
            user_email="test@example.com",
            ip_address="192.168.1.1",
            auth_method="firebase_jwt"
        )
        
        call_args = mock_audit_logger.info.call_args
        extra = call_args[1]["extra"]
        timestamp = extra["timestamp"]
        
        # Verify timestamp is ISO 8601 format
        # Should be parseable by datetime
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)
    
    @pytest.mark.asyncio
    async def test_all_events_have_timestamps(self, mock_audit_logger):
        """Test that all audit events include timestamps."""
        user_id = uuid4()
        api_key_id = uuid4()
        
        # Test various event types
        events = [
            AuditService.log_successful_login(
                user_id=user_id,
                user_email="test@example.com",
                ip_address="192.168.1.1"
            ),
            AuditService.log_failed_login(
                email="test@example.com",
                ip_address="192.168.1.1",
                reason="invalid_token"
            ),
            AuditService.log_api_key_creation(
                api_key_id=api_key_id,
                user_id=user_id,
                user_email="test@example.com",
                key_name="Test Key",
                scopes=[]
            ),
            AuditService.log_authorization_failure(
                user_id=user_id,
                user_email="test@example.com",
                user_role="user",
                attempted_action="test",
                required_permission="admin",
                reason="insufficient_permissions"
            )
        ]
        
        # Execute all events
        for event in events:
            await event
        
        # Verify all calls have timestamps
        for call in mock_audit_logger.info.call_args_list + mock_audit_logger.warning.call_args_list:
            if "extra" in call[1]:
                assert "timestamp" in call[1]["extra"]
