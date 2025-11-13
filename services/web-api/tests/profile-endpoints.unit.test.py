"""Tests for user profile endpoints."""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from src.models.db_models import User
from src.database import AsyncSessionLocal


@pytest.fixture
async def test_user(clean_database):
    """Create a test user."""
    async with AsyncSessionLocal() as session:
        user = User(
            firebase_uid="test_user_123",
            email="test@example.com",
            display_name="Test User",
            role="user",
            subscription_tier="pro"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def test_admin_user(clean_database):
    """Create a test admin user."""
    async with AsyncSessionLocal() as session:
        user = User(
            firebase_uid="admin_user_123",
            email="admin@example.com",
            display_name="Admin User",
            role="admin",
            subscription_tier="power"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
async def test_target_user(clean_database):
    """Create a target user for admin operations."""
    async with AsyncSessionLocal() as session:
        user = User(
            firebase_uid="target_user_123",
            email="target@example.com",
            display_name="Target User",
            role="user",
            subscription_tier="free"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture
def mock_auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer mock_firebase_token"}


class TestGetProfile:
    """Tests for GET /api/v1/auth/profile endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test successful profile retrieval."""
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.get(
                "/api/v1/auth/profile",
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify profile structure
            assert data["email"] == test_user.email
            assert data["display_name"] == test_user.display_name
            assert data["role"] == test_user.role
            assert data["subscription_tier"] == test_user.subscription_tier
            assert "id" in data
            assert "created_at" in data
            assert "last_login_at" in data
            
            # Verify sensitive fields are excluded
            assert "firebase_uid" not in data
            assert "stripe_customer_id" not in data
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(self, async_client: AsyncClient):
        """Test profile retrieval without authentication."""
        response = await async_client.get("/api/v1/auth/profile")
        
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_profile_invalid_token(self, async_client: AsyncClient, mock_auth_headers):
        """Test profile retrieval with invalid token."""
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(
                side_effect=Exception("Invalid token")
            )
            
            response = await async_client.get(
                "/api/v1/auth/profile",
                headers=mock_auth_headers
            )
            
            assert response.status_code == 401


class TestUpdateProfile:
    """Tests for PATCH /api/v1/auth/profile endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_profile_display_name(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test updating user display name."""
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.patch(
                "/api/v1/auth/profile",
                json={"display_name": "Updated Name"},
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["display_name"] == "Updated Name"
            assert data["email"] == test_user.email
            
            # Verify database was updated
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    User.__table__.select().where(User.id == test_user.id)
                )
                updated_user = result.first()
                assert updated_user.display_name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_profile_empty_update(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test updating profile with no changes."""
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.patch(
                "/api/v1/auth/profile",
                json={},
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Profile should remain unchanged
            assert data["display_name"] == test_user.display_name
    
    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self, async_client: AsyncClient):
        """Test profile update without authentication."""
        response = await async_client.patch(
            "/api/v1/auth/profile",
            json={"display_name": "New Name"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_profile_cannot_change_role(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test that users cannot change their own role via profile update."""
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            # Try to update with role field (should be ignored)
            response = await async_client.patch(
                "/api/v1/auth/profile",
                json={
                    "display_name": "New Name",
                    "role": "admin"  # This should be ignored
                },
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Role should remain unchanged
            assert data["role"] == "user"
            assert data["display_name"] == "New Name"
    
    @pytest.mark.asyncio
    async def test_update_profile_cannot_change_subscription_tier(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test that users cannot change their own subscription tier via profile update."""
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            # Try to update with subscription_tier field (should be ignored)
            response = await async_client.patch(
                "/api/v1/auth/profile",
                json={
                    "display_name": "New Name",
                    "subscription_tier": "power"  # This should be ignored
                },
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Subscription tier should remain unchanged
            assert data["subscription_tier"] == "pro"
            assert data["display_name"] == "New Name"


class TestUpdateSubscriptionTier:
    """Tests for PATCH /api/v1/auth/users/{user_id}/subscription-tier endpoint."""
    
    @pytest.mark.asyncio
    async def test_admin_update_subscription_tier(self, async_client: AsyncClient, test_admin_user, test_target_user, mock_auth_headers):
        """Test admin successfully updating user subscription tier."""
        mock_decoded_token = {
            "uid": test_admin_user.firebase_uid,
            "email": test_admin_user.email,
            "name": test_admin_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.patch(
                f"/api/v1/auth/users/{test_target_user.id}/subscription-tier",
                json={
                    "subscription_tier": "pro",
                    "reason": "admin_upgrade"
                },
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["subscription_tier"] == "pro"
            assert data["id"] == str(test_target_user.id)
            
            # Verify database was updated
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    User.__table__.select().where(User.id == test_target_user.id)
                )
                updated_user = result.first()
                assert updated_user.subscription_tier == "pro"
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_update_subscription_tier(self, async_client: AsyncClient, test_user, test_target_user, mock_auth_headers):
        """Test that non-admin users cannot update subscription tiers."""
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.patch(
                f"/api/v1/auth/users/{test_target_user.id}/subscription-tier",
                json={
                    "subscription_tier": "power",
                    "reason": "unauthorized_attempt"
                },
                headers=mock_auth_headers
            )
            
            assert response.status_code == 403
            assert "admin" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_subscription_tier_invalid_user(self, async_client: AsyncClient, test_admin_user, mock_auth_headers):
        """Test updating subscription tier for non-existent user."""
        mock_decoded_token = {
            "uid": test_admin_user.firebase_uid,
            "email": test_admin_user.email,
            "name": test_admin_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            fake_user_id = uuid4()
            response = await async_client.patch(
                f"/api/v1/auth/users/{fake_user_id}/subscription-tier",
                json={
                    "subscription_tier": "pro",
                    "reason": "test"
                },
                headers=mock_auth_headers
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_subscription_tier_all_tiers(self, async_client: AsyncClient, test_admin_user, test_target_user, mock_auth_headers):
        """Test updating to all valid subscription tiers."""
        mock_decoded_token = {
            "uid": test_admin_user.firebase_uid,
            "email": test_admin_user.email,
            "name": test_admin_user.display_name
        }
        
        valid_tiers = ["free", "pro", "power"]
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            for tier in valid_tiers:
                response = await async_client.patch(
                    f"/api/v1/auth/users/{test_target_user.id}/subscription-tier",
                    json={
                        "subscription_tier": tier,
                        "reason": f"test_{tier}"
                    },
                    headers=mock_auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["subscription_tier"] == tier
    
    @pytest.mark.asyncio
    async def test_update_subscription_tier_with_reason(self, async_client: AsyncClient, test_admin_user, test_target_user, mock_auth_headers):
        """Test that tier update reason is logged."""
        mock_decoded_token = {
            "uid": test_admin_user.firebase_uid,
            "email": test_admin_user.email,
            "name": test_admin_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            with patch("src.services.audit_service.AuditService.log_subscription_tier_change") as mock_audit:
                response = await async_client.patch(
                    f"/api/v1/auth/users/{test_target_user.id}/subscription-tier",
                    json={
                        "subscription_tier": "pro",
                        "reason": "customer_request"
                    },
                    headers=mock_auth_headers
                )
                
                assert response.status_code == 200
                
                # Verify audit log was called
                mock_audit.assert_called_once()
                call_args = mock_audit.call_args[1]
                assert call_args["reason"] == "customer_request"
                assert call_args["old_tier"] == "free"
                assert call_args["new_tier"] == "pro"


class TestUnauthorizedProfileAccess:
    """Tests for preventing unauthorized profile access."""
    
    @pytest.mark.asyncio
    async def test_cannot_view_other_user_profile(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test that users can only view their own profile."""
        # The /profile endpoint always returns the authenticated user's profile
        # There's no way to view another user's profile through this endpoint
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.get(
                "/api/v1/auth/profile",
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should only return authenticated user's profile
            assert data["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_cannot_update_other_user_profile(self, async_client: AsyncClient, test_user, mock_auth_headers):
        """Test that users can only update their own profile."""
        # The /profile endpoint always updates the authenticated user's profile
        # There's no way to update another user's profile through this endpoint
        mock_decoded_token = {
            "uid": test_user.firebase_uid,
            "email": test_user.email,
            "name": test_user.display_name
        }
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            response = await async_client.patch(
                "/api/v1/auth/profile",
                json={"display_name": "Hacker Name"},
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should only update authenticated user's profile
            assert data["email"] == test_user.email
            assert data["display_name"] == "Hacker Name"
            
            # Verify only the authenticated user was updated
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    User.__table__.select().where(User.id == test_user.id)
                )
                updated_user = result.first()
                assert updated_user.display_name == "Hacker Name"
