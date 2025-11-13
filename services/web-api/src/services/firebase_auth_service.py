"""Firebase Authentication Service for token verification and user management."""
import logging
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import auth, credentials
from ..models.errors import AuthenticationError

logger = logging.getLogger(__name__)


class FirebaseAuthService:
    """Service for Firebase Auth operations including token verification and user management."""
    
    def __init__(self, credentials_path: str, project_id: str):
        """
        Initialize Firebase Admin SDK.
        
        Args:
            credentials_path: Path to Firebase service account credentials JSON
            project_id: Firebase project ID
            
        Raises:
            Exception: If Firebase initialization fails
        """
        self.project_id = project_id
        self._initialized = False
        
        try:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred, {
                'projectId': project_id
            })
            self._initialized = True
            logger.info(f"Firebase Admin SDK initialized successfully for project: {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise
    
    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded claims.
        
        Args:
            id_token: Firebase ID token from client
            
        Returns:
            Dictionary containing decoded token claims including:
                - uid: User's Firebase UID
                - email: User's email address
                - email_verified: Whether email is verified
                - auth_time: Authentication timestamp
                - exp: Token expiration timestamp
                
        Raises:
            AuthenticationError: If token is invalid, expired, or verification fails
        """
        if not self._initialized:
            raise AuthenticationError("Firebase Auth service not initialized")
        
        try:
            decoded_token = auth.verify_id_token(id_token, check_revoked=True)
            logger.debug(f"Token verified successfully for user: {decoded_token.get('uid')}")
            return decoded_token
            
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired ID token: {e}")
            raise AuthenticationError("Authentication token has expired")
            
        except auth.RevokedIdTokenError as e:
            logger.warning(f"Revoked ID token: {e}")
            raise AuthenticationError("Authentication token has been revoked")
            
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid ID token: {e}")
            raise AuthenticationError("Invalid authentication token")
            
        except auth.CertificateFetchError as e:
            logger.error(f"Failed to fetch Firebase certificates: {e}")
            raise AuthenticationError("Authentication service temporarily unavailable")
            
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise AuthenticationError("Authentication failed")
    
    async def get_user(self, uid: str) -> auth.UserRecord:
        """
        Get user record from Firebase by UID.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            Firebase UserRecord object containing user information
            
        Raises:
            AuthenticationError: If user not found or retrieval fails
        """
        if not self._initialized:
            raise AuthenticationError("Firebase Auth service not initialized")
        
        try:
            user_record = auth.get_user(uid)
            logger.debug(f"Retrieved user record for UID: {uid}")
            return user_record
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found: {uid}")
            raise AuthenticationError(f"User not found: {uid}")
            
        except Exception as e:
            logger.error(f"Failed to retrieve user {uid}: {e}")
            raise AuthenticationError("Failed to retrieve user information")
    
    async def get_user_by_email(self, email: str) -> auth.UserRecord:
        """
        Get user record from Firebase by email address.
        
        Args:
            email: User's email address
            
        Returns:
            Firebase UserRecord object containing user information
            
        Raises:
            AuthenticationError: If user not found or retrieval fails
        """
        if not self._initialized:
            raise AuthenticationError("Firebase Auth service not initialized")
        
        try:
            user_record = auth.get_user_by_email(email)
            logger.debug(f"Retrieved user record for email: {email}")
            return user_record
            
        except auth.UserNotFoundError:
            logger.warning(f"User not found with email: {email}")
            raise AuthenticationError(f"User not found: {email}")
            
        except Exception as e:
            logger.error(f"Failed to retrieve user by email {email}: {e}")
            raise AuthenticationError("Failed to retrieve user information")
    
    async def revoke_refresh_tokens(self, uid: str) -> None:
        """
        Revoke all refresh tokens for a user (logout from all devices).
        
        This invalidates all existing refresh tokens and ID tokens for the user.
        The user will need to sign in again on all devices.
        
        Args:
            uid: Firebase user ID
            
        Raises:
            AuthenticationError: If revocation fails
        """
        if not self._initialized:
            raise AuthenticationError("Firebase Auth service not initialized")
        
        try:
            auth.revoke_refresh_tokens(uid)
            logger.info(f"Revoked all refresh tokens for user: {uid}")
            
        except auth.UserNotFoundError:
            logger.warning(f"Cannot revoke tokens - user not found: {uid}")
            raise AuthenticationError(f"User not found: {uid}")
            
        except Exception as e:
            logger.error(f"Failed to revoke refresh tokens for user {uid}: {e}")
            raise AuthenticationError("Failed to revoke user sessions")
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> None:
        """
        Set custom claims on a user's token (for roles, permissions, etc.).
        
        Custom claims will be included in the user's ID token and can be used
        for authorization. Claims are limited to 1000 bytes.
        
        Args:
            uid: Firebase user ID
            claims: Dictionary of custom claims to set (e.g., {'role': 'admin'})
            
        Raises:
            AuthenticationError: If setting claims fails
        """
        if not self._initialized:
            raise AuthenticationError("Firebase Auth service not initialized")
        
        try:
            auth.set_custom_user_claims(uid, claims)
            logger.info(f"Set custom claims for user {uid}: {claims}")
            
        except auth.UserNotFoundError:
            logger.warning(f"Cannot set claims - user not found: {uid}")
            raise AuthenticationError(f"User not found: {uid}")
            
        except Exception as e:
            logger.error(f"Failed to set custom claims for user {uid}: {e}")
            raise AuthenticationError("Failed to update user permissions")
    
    async def delete_user(self, uid: str) -> None:
        """
        Delete a user from Firebase Auth.
        
        Args:
            uid: Firebase user ID
            
        Raises:
            AuthenticationError: If deletion fails
        """
        if not self._initialized:
            raise AuthenticationError("Firebase Auth service not initialized")
        
        try:
            auth.delete_user(uid)
            logger.info(f"Deleted user: {uid}")
            
        except auth.UserNotFoundError:
            logger.warning(f"Cannot delete - user not found: {uid}")
            raise AuthenticationError(f"User not found: {uid}")
            
        except Exception as e:
            logger.error(f"Failed to delete user {uid}: {e}")
            raise AuthenticationError("Failed to delete user")
    
    def is_initialized(self) -> bool:
        """Check if Firebase Auth service is initialized."""
        return self._initialized
