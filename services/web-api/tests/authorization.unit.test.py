"""Tests for role-based access control and authorization."""
import pytest
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import (
    require_role,
    require_subscription,
    require_scope
)
from src.models.auth import Role, UserSubscriptionTier
from src.models.db_models import User, APIKey
from src.services.user_service import UserService
from src.database import AsyncSessionLocal


@pytest.mark.asyncio
class TestRoleBasedAccessControl:
    """Test role-based access control."""
    
    async def test_admin_role_required_success(self, clean_database):
        """Test admin role requirement allows admin users."""
        # Create admin user
        async with AsyncSessionLocal() as db:
            admin_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "admin_user_123",
                    "email": "admin@example.com",
                    "name": "Admin User"
                }
            )
            await UserService.update_user_role(db, admin_user, "admin")
            await db.commit()
            await db.refresh(admin_user)
        
        # Test require_role decorator
        check_admin = require_role(Role.ADMIN)
        
        async with AsyncSessionLocal() as db:
            # Should not raise exception
            result = await check_admin(admin_user)
            assert result.role == "admin"
    
    async def test_admin_role_required_failure(self, clean_database):
        """Test admin role requirement rejects regular users."""
        # Create regular user
        async with AsyncSessionLocal() as db:
            regular_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "regular_user_123",
                    "email": "user@example.com",
                    "name": "Regular User"
                }
            )
            await db.commit()
            await db.refresh(regular_user)
        
        # Test require_role decorator
        check_admin = require_role(Role.ADMIN)
        
        async with AsyncSessionLocal() as db:
            # Should raise HTTPException with 403
            with pytest.raises(HTTPException) as exc_info:
                await check_admin(regular_user)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "admin" in exc_info.value.detail.lower()
    
    async def test_service_role_required(self, clean_database):
        """Test service role requirement."""
        # Create service user
        async with AsyncSessionLocal() as db:
            service_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "service_user_123",
                    "email": "service@example.com",
                    "name": "Service User"
                }
            )
            await UserService.update_user_role(db, service_user, "service")
            await db.commit()
            await db.refresh(service_user)
        
        # Test require_role decorator
        check_service = require_role(Role.SERVICE)
        
        async with AsyncSessionLocal() as db:
            # Should not raise exception
            result = await check_service(service_user)
            assert result.role == "service"
    
    async def test_role_check_logs_failure(self, clean_database):
        """Test role check failures are logged."""
        # Create regular user
        async with AsyncSessionLocal() as db:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "log_test_user",
                    "email": "logtest@example.com",
                    "name": "Log Test User"
                }
            )
            await db.commit()
            await db.refresh(user)
        
        # Mock the audit service
        with patch("src.middleware.auth.AuditService.log_authorization_failure") as mock_log:
            check_admin = require_role(Role.ADMIN)
            
            async with AsyncSessionLocal() as db:
                with pytest.raises(HTTPException):
                    await check_admin(user)
                
                # Verify audit logging was called
                assert mock_log.called
                call_args = mock_log.call_args[1]
                assert call_args["user_id"] == user.id
                assert call_args["user_email"] == user.email
                assert call_args["user_role"] == "user"
                assert "admin" in call_args["required_permission"]


@pytest.mark.asyncio
class TestSubscriptionTierRestrictions:
    """Test subscription tier-based access control."""
    
    async def test_pro_tier_required_success(self, clean_database):
        """Test Pro tier requirement allows Pro users."""
        # Create Pro user
        async with AsyncSessionLocal() as db:
            pro_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "pro_user_123",
                    "email": "pro@example.com",
                    "name": "Pro User"
                }
            )
            await UserService.update_subscription_tier(db, pro_user, "pro")
            await db.commit()
            await db.refresh(pro_user)
        
        # Test require_subscription decorator
        check_pro = require_subscription(UserSubscriptionTier.PRO)
        
        async with AsyncSessionLocal() as db:
            # Should not raise exception
            result = await check_pro(pro_user)
            assert result.subscription_tier == "pro"
    
    async def test_pro_tier_required_allows_power(self, clean_database):
        """Test Pro tier requirement allows Power users (higher tier)."""
        # Create Power user
        async with AsyncSessionLocal() as db:
            power_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "power_user_123",
                    "email": "power@example.com",
                    "name": "Power User"
                }
            )
            await UserService.update_subscription_tier(db, power_user, "power")
            await db.commit()
            await db.refresh(power_user)
        
        # Test require_subscription decorator
        check_pro = require_subscription(UserSubscriptionTier.PRO)
        
        async with AsyncSessionLocal() as db:
            # Should not raise exception (Power > Pro)
            result = await check_pro(power_user)
            assert result.subscription_tier == "power"
    
    async def test_pro_tier_required_rejects_free(self, clean_database):
        """Test Pro tier requirement rejects Free users."""
        # Create Free user
        async with AsyncSessionLocal() as db:
            free_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "free_user_123",
                    "email": "free@example.com",
                    "name": "Free User"
                }
            )
            await db.commit()
            await db.refresh(free_user)
        
        # Test require_subscription decorator
        check_pro = require_subscription(UserSubscriptionTier.PRO)
        
        async with AsyncSessionLocal() as db:
            # Should raise HTTPException with 403
            with pytest.raises(HTTPException) as exc_info:
                await check_pro(free_user)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "pro" in exc_info.value.detail.lower()
    
    async def test_power_tier_required(self, clean_database):
        """Test Power tier requirement."""
        # Create Power user
        async with AsyncSessionLocal() as db:
            power_user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "power_user_456",
                    "email": "power2@example.com",
                    "name": "Power User 2"
                }
            )
            await UserService.update_subscription_tier(db, power_user, "power")
            await db.commit()
            await db.refresh(power_user)
        
        # Test require_subscription decorator
        check_power = require_subscription(UserSubscriptionTier.POWER)
        
        async with AsyncSessionLocal() as db:
            # Should not raise exception
            result = await check_power(power_user)
            assert result.subscription_tier == "power"
    
    async def test_subscription_check_logs_failure(self, clean_database):
        """Test subscription tier check failures are logged."""
        # Create Free user
        async with AsyncSessionLocal() as db:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "sub_log_test",
                    "email": "sublog@example.com",
                    "name": "Sub Log Test"
                }
            )
            await db.commit()
            await db.refresh(user)
        
        # Mock the audit service
        with patch("src.middleware.auth.AuditService.log_authorization_failure") as mock_log:
            check_pro = require_subscription(UserSubscriptionTier.PRO)
            
            async with AsyncSessionLocal() as db:
                with pytest.raises(HTTPException):
                    await check_pro(user)
                
                # Verify audit logging was called
                assert mock_log.called
                call_args = mock_log.call_args[1]
                assert call_args["user_id"] == user.id
                assert call_args["user_email"] == user.email
                assert "pro" in call_args["required_permission"]


@pytest.mark.asyncio
class TestAPIKeyScopeValidation:
    """Test API key scope-based access control."""
    
    async def test_scope_validation_success(self, clean_database):
        """Test API key with required scope is allowed."""
        # Create user and API key with scope
        async with AsyncSessionLocal() as db:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "scope_user_123",
                    "email": "scope@example.com",
                    "name": "Scope User"
                }
            )
            
            # Create API key with insights:read scope
            api_key_value = "sk_test_scope123"
            key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
            
            api_key = APIKey(
                user_id=user.id,
                key_hash=key_hash,
                key_prefix="sk_test_",
                name="Scoped API Key",
                scopes=["insights:read", "alerts:write"]
            )
            db.add(api_key)
            await db.commit()
        
        # Test require_scope decorator
        check_scope = require_scope("insights:read")
        
        async with AsyncSessionLocal() as db:
            # Should not raise exception
            result = await check_scope(api_key_value, db)
            assert result.email == "scope@example.com"
    
    async def test_scope_validation_failure(self, clean_database):
        """Test API key without required scope is rejected."""
        # Create user and API key without required scope
        async with AsyncSessionLocal() as db:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "noscope_user_123",
                    "email": "noscope@example.com",
                    "name": "No Scope User"
                }
            )
            
            # Create API key without insights:write scope
            api_key_value = "sk_test_noscope123"
            key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
            
            api_key = APIKey(
                user_id=user.id,
                key_hash=key_hash,
                key_prefix="sk_test_",
                name="Limited API Key",
                scopes=["insights:read"]  # Missing insights:write
            )
            db.add(api_key)
            await db.commit()
        
        # Test require_scope decorator
        check_scope = require_scope("insights:write")
        
        async with AsyncSessionLocal() as db:
            # Should raise HTTPException with 403
            with pytest.raises(HTTPException) as exc_info:
                await check_scope(api_key_value, db)
            
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "scope" in exc_info.value.detail.lower()
    
    async def test_scope_validation_no_api_key(self, clean_database):
        """Test scope validation rejects requests without API key."""
        # Test require_scope decorator without API key
        check_scope = require_scope("insights:read")
        
        async with AsyncSessionLocal() as db:
            # Should raise HTTPException with 401
            with pytest.raises(HTTPException) as exc_info:
                await check_scope(None, db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_scope_validation_invalid_api_key(self, clean_database):
        """Test scope validation rejects invalid API keys."""
        # Test require_scope decorator with invalid API key
        check_scope = require_scope("insights:read")
        
        async with AsyncSessionLocal() as db:
            # Should raise HTTPException with 401
            with pytest.raises(HTTPException) as exc_info:
                await check_scope("sk_invalid_key", db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_scope_validation_logs_failure(self, clean_database):
        """Test scope validation failures are logged."""
        # Create user and API key without required scope
        async with AsyncSessionLocal() as db:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "scope_log_user",
                    "email": "scopelog@example.com",
                    "name": "Scope Log User"
                }
            )
            
            api_key_value = "sk_test_scopelog"
            key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
            
            api_key = APIKey(
                user_id=user.id,
                key_hash=key_hash,
                key_prefix="sk_test_",
                name="Log Test Key",
                scopes=["insights:read"]
            )
            db.add(api_key)
            await db.commit()
        
        # Mock the audit service
        with patch("src.middleware.auth.AuditService.log_api_key_scope_failure") as mock_log:
            check_scope = require_scope("alerts:write")
            
            async with AsyncSessionLocal() as db:
                with pytest.raises(HTTPException):
                    await check_scope(api_key_value, db)
                
                # Verify audit logging was called
                assert mock_log.called
                call_args = mock_log.call_args[1]
                assert call_args["required_scope"] == "alerts:write"
                assert "insights:read" in call_args["available_scopes"]


@pytest.mark.asyncio
class TestAuthorizationLogging:
    """Test authorization event logging."""
    
    async def test_role_change_logging(self, clean_database):
        """Test role changes are logged."""
        # Mock the audit service
        with patch("src.services.audit_service.AuditService.log_role_change") as mock_log:
            # Create user and update role in same session
            async with AsyncSessionLocal() as db:
                user = await UserService.create_user_from_firebase(
                    db,
                    {
                        "uid": "role_change_user",
                        "email": "rolechange@example.com",
                        "name": "Role Change User"
                    }
                )
                await db.commit()
                await db.refresh(user)
                
                # Update role
                await UserService.update_user_role(db, user, "admin")
                
                # Verify logging was called
                assert mock_log.called
                call_args = mock_log.call_args[1]
                assert call_args["user_id"] == user.id
                assert call_args["old_role"] == "user"
                assert call_args["new_role"] == "admin"
    
    async def test_subscription_tier_change_logging(self, clean_database):
        """Test subscription tier changes are logged."""
        # Mock the audit service
        with patch("src.services.audit_service.AuditService.log_subscription_tier_change") as mock_log:
            # Create user and update tier in same session
            async with AsyncSessionLocal() as db:
                user = await UserService.create_user_from_firebase(
                    db,
                    {
                        "uid": "tier_change_user",
                        "email": "tierchange@example.com",
                        "name": "Tier Change User"
                    }
                )
                await db.commit()
                await db.refresh(user)
                
                # Update subscription tier
                await UserService.update_subscription_tier(
                    db, user, "pro", reason="stripe_payment"
                )
                
                # Verify logging was called
                assert mock_log.called
                call_args = mock_log.call_args[1]
                assert call_args["user_id"] == user.id
                assert call_args["old_tier"] == "free"
                assert call_args["new_tier"] == "pro"
                assert call_args["reason"] == "stripe_payment"
