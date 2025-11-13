"""Integration tests for authentication middleware."""
import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.auth import (
    get_current_user,
    get_current_user_from_api_key,
    get_optional_user
)
from src.models.db_models import User, APIKey
from src.models.errors import AuthenticationError
from src.services.user_service import UserService
from src.database import AsyncSessionLocal


@pytest.mark.asyncio
class TestJWTAuthentication:
    """Test JWT token authentication."""
    
    async def test_successful_jwt_authentication(self, clean_database):
        """Test successful JWT authentication creates user on first login."""
        # Mock Firebase token verification
        mock_decoded_token = {
            "uid": "firebase_user_123",
            "email": "user@example.com",
            "name": "Test User",
            "email_verified": True
        }
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token_123"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            # Call the middleware function directly
            async with AsyncSessionLocal() as db:
                user = await get_current_user(mock_credentials, db)
                
                # Verify user was created
                assert user is not None
                assert user.email == "user@example.com"
                assert user.firebase_uid == "firebase_user_123"
                assert user.role == "user"
                assert user.subscription_tier == "free"
                assert user.last_login_at is not None
    
    async def test_jwt_authentication_updates_last_login(self, clean_database):
        """Test JWT authentication updates last_login_at on subsequent logins."""
        # Create existing user
        async with AsyncSessionLocal() as db:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "firebase_user_456",
                    "email": "existing@example.com",
                    "name": "Existing User"
                }
            )
            original_login_time = user.last_login_at
            await db.commit()
        
        # Wait a moment to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)
        
        # Mock Firebase token verification
        mock_decoded_token = {
            "uid": "firebase_user_456",
            "email": "existing@example.com",
            "name": "Existing User"
        }
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token_456"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            # Call middleware function
            async with AsyncSessionLocal() as db:
                user = await get_current_user(mock_credentials, db)
                
                # Verify last_login_at was updated
                assert user.last_login_at > original_login_time
    
    async def test_expired_token_rejection(self, clean_database):
        """Test expired JWT token is rejected with HTTPException."""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="expired_token"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(
                side_effect=AuthenticationError("Authentication token has expired")
            )
            
            # Call middleware function - should raise HTTPException
            async with AsyncSessionLocal() as db:
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials, db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_invalid_token_rejection(self, clean_database):
        """Test invalid JWT token is rejected with HTTPException."""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(
                side_effect=AuthenticationError("Invalid authentication token")
            )
            
            # Call middleware function - should raise HTTPException
            async with AsyncSessionLocal() as db:
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials, db)
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_missing_authentication_rejection(self, clean_database):
        """Test request without authentication credentials is rejected."""
        # Call middleware with None credentials
        async with AsyncSessionLocal() as db:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(None, db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestAPIKeyAuthentication:
    """Test API key authentication."""
    
    async def test_successful_api_key_authentication(self, clean_database):
        """Test successful API key authentication."""
        # Create user and API key
        async with AsyncSessionLocal() as db:
            # Create user
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "api_user_123",
                    "email": "apiuser@example.com",
                    "name": "API User"
                }
            )
            
            # Create API key
            api_key_value = "sk_test_abc123def456ghi789"
            key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
            
            api_key = APIKey(
                user_id=user.id,
                key_hash=key_hash,
                key_prefix="sk_test_",
                name="Test API Key",
                scopes=["insights:read"]
            )
            db.add(api_key)
            await db.commit()
        
        # Call middleware function directly
        async with AsyncSessionLocal() as db:
            authenticated_user = await get_current_user_from_api_key(api_key_value, db)
            
            # Verify user was returned
            assert authenticated_user is not None
            assert authenticated_user.email == "apiuser@example.com"
            
            # Verify last_used_at was updated
            from sqlalchemy import select
            result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
            updated_key = result.scalar_one()
            assert updated_key.last_used_at is not None
    
    async def test_invalid_api_key_rejection(self, clean_database):
        """Test invalid API key is rejected with HTTPException."""
        # Call middleware with invalid API key
        async with AsyncSessionLocal() as db:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_api_key("sk_invalid_key", db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_revoked_api_key_rejection(self, clean_database):
        """Test revoked API key is rejected."""
        # Create user and revoked API key
        async with AsyncSessionLocal() as db:
            # Create user
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "revoked_user_123",
                    "email": "revoked@example.com",
                    "name": "Revoked User"
                }
            )
            
            # Create revoked API key
            api_key_value = "sk_test_revoked123"
            key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
            
            api_key = APIKey(
                user_id=user.id,
                key_hash=key_hash,
                key_prefix="sk_test_",
                name="Revoked API Key",
                scopes=["insights:read"],
                revoked_at=datetime.utcnow()
            )
            db.add(api_key)
            await db.commit()
        
        # Call middleware with revoked API key
        async with AsyncSessionLocal() as db:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_api_key(api_key_value, db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_missing_api_key_rejection(self, clean_database):
        """Test request without API key is rejected."""
        # Call middleware with None API key
        async with AsyncSessionLocal() as db:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_api_key(None, db)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestOptionalAuthentication:
    """Test optional authentication for public endpoints."""
    
    async def test_optional_auth_with_valid_token(self, clean_database):
        """Test optional authentication returns user when valid token provided."""
        mock_decoded_token = {
            "uid": "optional_user_123",
            "email": "optional@example.com",
            "name": "Optional User"
        }
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(return_value=mock_decoded_token)
            
            # Call optional auth middleware
            async with AsyncSessionLocal() as db:
                user = await get_optional_user(mock_credentials, db)
                
                # Should return user
                assert user is not None
                assert user.email == "optional@example.com"
    
    async def test_optional_auth_without_token(self, clean_database):
        """Test optional authentication returns None without token."""
        # Call optional auth middleware with None credentials
        async with AsyncSessionLocal() as db:
            user = await get_optional_user(None, db)
            
            # Should return None
            assert user is None
    
    async def test_optional_auth_with_invalid_token(self, clean_database):
        """Test optional authentication returns None with invalid token."""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            mock_firebase.is_initialized.return_value = True
            mock_firebase.verify_token = AsyncMock(
                side_effect=AuthenticationError("Invalid token")
            )
            
            # Call optional auth middleware
            async with AsyncSessionLocal() as db:
                user = await get_optional_user(mock_credentials, db)
                
                # Should return None (not raise exception)
                assert user is None


@pytest.mark.asyncio
class TestAuthenticationErrorHandling:
    """Test authentication error handling and logging."""
    
    async def test_authentication_failure_logging(self, clean_database):
        """Test authentication failures are logged with details."""
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="bad_token"
        )
        
        with patch("src.middleware.auth.firebase_service") as mock_firebase:
            with patch("src.middleware.auth.logger") as mock_logger:
                mock_firebase.is_initialized.return_value = True
                mock_firebase.verify_token = AsyncMock(
                    side_effect=AuthenticationError("Test auth failure")
                )
                
                # Call middleware - should raise and log
                async with AsyncSessionLocal() as db:
                    with pytest.raises(HTTPException):
                        await get_current_user(mock_credentials, db)
                    
                    # Verify logging was called
                    assert mock_logger.warning.called or mock_logger.error.called
