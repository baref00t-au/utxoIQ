"""Unit tests for Firebase Auth Service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from firebase_admin import auth
from src.services.firebase_auth_service import FirebaseAuthService
from src.models.errors import AuthenticationError


@pytest.fixture
def mock_credentials_path(tmp_path):
    """Create a temporary credentials file."""
    creds_file = tmp_path / "firebase-credentials.json"
    creds_file.write_text('{"type": "service_account", "project_id": "test-project"}')
    return str(creds_file)


@pytest.fixture
def firebase_service(mock_credentials_path):
    """Create a FirebaseAuthService instance with mocked initialization."""
    with patch('firebase_admin.initialize_app'):
        with patch('firebase_admin.credentials.Certificate'):
            service = FirebaseAuthService(
                credentials_path=mock_credentials_path,
                project_id="test-project"
            )
            service._initialized = True  # Force initialized state for testing
            return service


class TestFirebaseAuthServiceInitialization:
    """Test Firebase Auth Service initialization."""
    
    def test_initialization_success(self, mock_credentials_path):
        """Test successful Firebase initialization."""
        with patch('firebase_admin.initialize_app') as mock_init:
            with patch('firebase_admin.credentials.Certificate') as mock_cert:
                service = FirebaseAuthService(
                    credentials_path=mock_credentials_path,
                    project_id="test-project"
                )
                
                assert service.is_initialized()
                assert service.project_id == "test-project"
                mock_cert.assert_called_once_with(mock_credentials_path)
                mock_init.assert_called_once()
    
    def test_initialization_failure(self, mock_credentials_path):
        """Test Firebase initialization failure."""
        with patch('firebase_admin.initialize_app', side_effect=Exception("Init failed")):
            with patch('firebase_admin.credentials.Certificate'):
                with pytest.raises(Exception, match="Init failed"):
                    FirebaseAuthService(
                        credentials_path=mock_credentials_path,
                        project_id="test-project"
                    )


class TestTokenVerification:
    """Test token verification methods."""
    
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, firebase_service):
        """Test verification of a valid Firebase token."""
        mock_decoded_token = {
            "uid": "user123",
            "email": "test@example.com",
            "email_verified": True,
            "auth_time": 1234567890,
            "exp": 9999999999
        }
        
        with patch('firebase_admin.auth.verify_id_token', return_value=mock_decoded_token):
            result = await firebase_service.verify_token("valid_token")
            
            assert result == mock_decoded_token
            assert result["uid"] == "user123"
            assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_verify_expired_token(self, firebase_service):
        """Test verification of an expired token."""
        with patch('firebase_admin.auth.verify_id_token', side_effect=auth.ExpiredIdTokenError("Token expired", cause=None)):
            with pytest.raises(AuthenticationError, match="Authentication token has expired"):
                await firebase_service.verify_token("expired_token")
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, firebase_service):
        """Test verification of an invalid token."""
        with patch('firebase_admin.auth.verify_id_token', side_effect=auth.InvalidIdTokenError("Invalid token")):
            with pytest.raises(AuthenticationError, match="Invalid authentication token"):
                await firebase_service.verify_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_verify_revoked_token(self, firebase_service):
        """Test verification of a revoked token."""
        # RevokedIdTokenError is a subclass of InvalidIdTokenError
        with patch('firebase_admin.auth.verify_id_token', side_effect=auth.InvalidIdTokenError("Token revoked", cause=None)):
            with pytest.raises(AuthenticationError, match="Invalid authentication token"):
                await firebase_service.verify_token("revoked_token")
    
    @pytest.mark.asyncio
    async def test_verify_token_certificate_fetch_error(self, firebase_service):
        """Test verification when certificate fetch fails."""
        with patch('firebase_admin.auth.verify_id_token', side_effect=auth.CertificateFetchError("Cert fetch failed", cause=None)):
            with pytest.raises(AuthenticationError, match="Authentication service temporarily unavailable"):
                await firebase_service.verify_token("some_token")
    
    @pytest.mark.asyncio
    async def test_verify_token_unexpected_error(self, firebase_service):
        """Test verification with unexpected error."""
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Unexpected error")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                await firebase_service.verify_token("some_token")
    
    @pytest.mark.asyncio
    async def test_verify_token_when_not_initialized(self, mock_credentials_path):
        """Test token verification when service is not initialized."""
        with patch('firebase_admin.initialize_app'):
            with patch('firebase_admin.credentials.Certificate'):
                service = FirebaseAuthService(
                    credentials_path=mock_credentials_path,
                    project_id="test-project"
                )
                service._initialized = False
                
                with pytest.raises(AuthenticationError, match="Firebase Auth service not initialized"):
                    await service.verify_token("some_token")


class TestUserManagement:
    """Test user management methods."""
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, firebase_service):
        """Test successful user retrieval."""
        mock_user = Mock()
        mock_user.uid = "user123"
        mock_user.email = "test@example.com"
        
        with patch('firebase_admin.auth.get_user', return_value=mock_user):
            result = await firebase_service.get_user("user123")
            
            assert result.uid == "user123"
            assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, firebase_service):
        """Test user retrieval when user doesn't exist."""
        with patch('firebase_admin.auth.get_user', side_effect=auth.UserNotFoundError("User not found")):
            with pytest.raises(AuthenticationError, match="User not found: user123"):
                await firebase_service.get_user("user123")
    
    @pytest.mark.asyncio
    async def test_get_user_error(self, firebase_service):
        """Test user retrieval with unexpected error."""
        with patch('firebase_admin.auth.get_user', side_effect=Exception("Unexpected error")):
            with pytest.raises(AuthenticationError, match="Failed to retrieve user information"):
                await firebase_service.get_user("user123")
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, firebase_service):
        """Test successful user retrieval by email."""
        mock_user = Mock()
        mock_user.uid = "user123"
        mock_user.email = "test@example.com"
        
        with patch('firebase_admin.auth.get_user_by_email', return_value=mock_user):
            result = await firebase_service.get_user_by_email("test@example.com")
            
            assert result.uid == "user123"
            assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, firebase_service):
        """Test user retrieval by email when user doesn't exist."""
        with patch('firebase_admin.auth.get_user_by_email', side_effect=auth.UserNotFoundError("User not found")):
            with pytest.raises(AuthenticationError, match="User not found: test@example.com"):
                await firebase_service.get_user_by_email("test@example.com")


class TestTokenRevocation:
    """Test token revocation methods."""
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_tokens_success(self, firebase_service):
        """Test successful token revocation."""
        with patch('firebase_admin.auth.revoke_refresh_tokens') as mock_revoke:
            await firebase_service.revoke_refresh_tokens("user123")
            
            mock_revoke.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_tokens_user_not_found(self, firebase_service):
        """Test token revocation when user doesn't exist."""
        with patch('firebase_admin.auth.revoke_refresh_tokens', side_effect=auth.UserNotFoundError("User not found")):
            with pytest.raises(AuthenticationError, match="User not found: user123"):
                await firebase_service.revoke_refresh_tokens("user123")
    
    @pytest.mark.asyncio
    async def test_revoke_refresh_tokens_error(self, firebase_service):
        """Test token revocation with unexpected error."""
        with patch('firebase_admin.auth.revoke_refresh_tokens', side_effect=Exception("Unexpected error")):
            with pytest.raises(AuthenticationError, match="Failed to revoke user sessions"):
                await firebase_service.revoke_refresh_tokens("user123")


class TestCustomClaims:
    """Test custom claims management."""
    
    @pytest.mark.asyncio
    async def test_set_custom_claims_success(self, firebase_service):
        """Test successful custom claims setting."""
        claims = {"role": "admin", "subscription": "pro"}
        
        with patch('firebase_admin.auth.set_custom_user_claims') as mock_set_claims:
            await firebase_service.set_custom_claims("user123", claims)
            
            mock_set_claims.assert_called_once_with("user123", claims)
    
    @pytest.mark.asyncio
    async def test_set_custom_claims_user_not_found(self, firebase_service):
        """Test setting custom claims when user doesn't exist."""
        with patch('firebase_admin.auth.set_custom_user_claims', side_effect=auth.UserNotFoundError("User not found")):
            with pytest.raises(AuthenticationError, match="User not found: user123"):
                await firebase_service.set_custom_claims("user123", {"role": "admin"})
    
    @pytest.mark.asyncio
    async def test_set_custom_claims_error(self, firebase_service):
        """Test setting custom claims with unexpected error."""
        with patch('firebase_admin.auth.set_custom_user_claims', side_effect=Exception("Unexpected error")):
            with pytest.raises(AuthenticationError, match="Failed to update user permissions"):
                await firebase_service.set_custom_claims("user123", {"role": "admin"})


class TestUserDeletion:
    """Test user deletion methods."""
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, firebase_service):
        """Test successful user deletion."""
        with patch('firebase_admin.auth.delete_user') as mock_delete:
            await firebase_service.delete_user("user123")
            
            mock_delete.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, firebase_service):
        """Test user deletion when user doesn't exist."""
        with patch('firebase_admin.auth.delete_user', side_effect=auth.UserNotFoundError("User not found")):
            with pytest.raises(AuthenticationError, match="User not found: user123"):
                await firebase_service.delete_user("user123")
    
    @pytest.mark.asyncio
    async def test_delete_user_error(self, firebase_service):
        """Test user deletion with unexpected error."""
        with patch('firebase_admin.auth.delete_user', side_effect=Exception("Unexpected error")):
            with pytest.raises(AuthenticationError, match="Failed to delete user"):
                await firebase_service.delete_user("user123")


class TestServiceState:
    """Test service state management."""
    
    def test_is_initialized_true(self, firebase_service):
        """Test is_initialized returns True when initialized."""
        assert firebase_service.is_initialized() is True
    
    def test_is_initialized_false(self, mock_credentials_path):
        """Test is_initialized returns False when not initialized."""
        with patch('firebase_admin.initialize_app'):
            with patch('firebase_admin.credentials.Certificate'):
                service = FirebaseAuthService(
                    credentials_path=mock_credentials_path,
                    project_id="test-project"
                )
                service._initialized = False
                
                assert service.is_initialized() is False
