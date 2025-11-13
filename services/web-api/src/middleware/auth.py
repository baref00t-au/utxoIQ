"""Authentication middleware using Firebase Auth and API keys."""
import logging
import hashlib
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, Security, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import settings
from ..models.auth import User as UserSchema, UserSubscriptionTier, Role
from ..models.errors import AuthenticationError
from ..models.db_models import User, APIKey
from ..services.firebase_auth_service import FirebaseAuthService
from ..services.user_service import UserService
from ..services.audit_service import AuditService
from ..database import get_db

logger = logging.getLogger(__name__)

# Initialize Firebase Auth Service
firebase_service: Optional[FirebaseAuthService] = None
try:
    firebase_service = FirebaseAuthService(
        credentials_path=settings.firebase_credentials_path,
        project_id=settings.firebase_project_id
    )
    logger.info("Firebase Auth Service initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Firebase Auth Service: {e}")
    logger.warning("Running in development mode without Firebase authentication")

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract and verify Firebase JWT token, create or update user record.
    
    This is the main authentication dependency for protected endpoints.
    It verifies the Firebase token, creates a user record on first login,
    and updates the last_login_at timestamp.
    
    Args:
        credentials: HTTP authorization credentials with Bearer token
        db: Database session
        
    Returns:
        User: Database user object with full profile
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    # Get IP address from request context (will be set by middleware)
    from starlette.requests import Request
    from contextvars import ContextVar
    
    # Try to get IP from context (set by middleware)
    ip_address = "unknown"
    try:
        from fastapi import Request as FastAPIRequest
        # This is a simplified approach - in production, use proper request context
        ip_address = "0.0.0.0"  # Placeholder - will be enhanced with proper middleware
    except:
        pass
    
    if firebase_service is None or not firebase_service.is_initialized():
        # Development mode: create or get mock user
        logger.warning("Firebase not initialized, using mock user for development")
        user = await UserService.get_user_by_email(db, "dev@utxoiq.local")
        if not user:
            user = await UserService.create_user_from_firebase(
                db,
                {
                    "uid": "dev-user-123",
                    "email": "dev@utxoiq.local",
                    "name": "Dev User"
                }
            )
        return user
    
    if credentials is None:
        logger.warning("Authentication required but no credentials provided")
        await AuditService.log_failed_login(
            email=None,
            ip_address=ip_address,
            reason="no_credentials_provided",
            auth_method="firebase_jwt"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    try:
        # Verify the Firebase ID token
        decoded_token = await firebase_service.verify_token(token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email", "unknown")
        
        # Get or create user in database
        user = await UserService.get_user_by_firebase_uid(db, firebase_uid)
        
        if not user:
            # First-time login: create user record
            logger.info(f"Creating new user for Firebase UID: {firebase_uid}")
            user = await UserService.create_user_from_firebase(db, decoded_token)
        else:
            # Update last login timestamp
            user.last_login_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
        
        # Log successful login
        await AuditService.log_successful_login(
            user_id=user.id,
            user_email=user.email,
            ip_address=ip_address,
            auth_method="firebase_jwt"
        )
        
        logger.debug(f"User authenticated: {user.id} ({user.email})")
        return user
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        
        # Try to extract email from token for logging (even if invalid)
        email = None
        try:
            import jwt
            unverified = jwt.decode(token, options={"verify_signature": False})
            email = unverified.get("email")
        except:
            pass
        
        # Determine failure reason
        reason = "authentication_error"
        if "expired" in str(e).lower():
            reason = "token_expired"
        elif "invalid" in str(e).lower():
            reason = "invalid_token"
        
        await AuditService.log_failed_login(
            email=email,
            ip_address=ip_address,
            reason=reason,
            auth_method="firebase_jwt"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}", exc_info=True)
        
        await AuditService.log_failed_login(
            email=None,
            ip_address=ip_address,
            reason="unexpected_error",
            auth_method="firebase_jwt"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_from_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate API key and return associated user.
    
    This dependency authenticates requests using API keys instead of JWT tokens.
    It hashes the provided key, looks it up in the database, validates it's not
    revoked, updates the last_used_at timestamp, and returns the associated user.
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        User: Database user object associated with the API key
        
    Raises:
        HTTPException: 401 if API key is invalid or revoked
    """
    # Get IP address (placeholder - will be enhanced with proper middleware)
    ip_address = "0.0.0.0"
    
    if not x_api_key:
        logger.warning("API key authentication required but no key provided")
        await AuditService.log_failed_login(
            email=None,
            ip_address=ip_address,
            reason="no_api_key_provided",
            auth_method="api_key"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    try:
        # Hash the provided API key
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        
        # Look up API key in database
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.revoked_at.is_(None)
            )
        )
        api_key_record = result.scalar_one_or_none()
        
        if not api_key_record:
            logger.warning(f"Invalid or revoked API key attempted")
            await AuditService.log_failed_login(
                email=None,
                ip_address=ip_address,
                reason="invalid_or_revoked_api_key",
                auth_method="api_key"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        # Update last used timestamp
        api_key_record.last_used_at = datetime.utcnow()
        await db.commit()
        
        # Get associated user
        user = await UserService.get_user_by_id(db, str(api_key_record.user_id))
        
        if not user:
            logger.error(f"API key {api_key_record.id} has no associated user")
            await AuditService.log_failed_login(
                email=None,
                ip_address=ip_address,
                reason="api_key_no_user",
                auth_method="api_key"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        # Log successful API key authentication
        await AuditService.log_successful_login(
            user_id=user.id,
            user_email=user.email,
            ip_address=ip_address,
            auth_method="api_key"
        )
        
        logger.debug(f"User authenticated via API key: {user.id} ({user.email})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key authentication error: {e}", exc_info=True)
        await AuditService.log_failed_login(
            email=None,
            ip_address=ip_address,
            reason="api_key_error",
            auth_method="api_key"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "ApiKey"}
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get user information if authenticated, otherwise return None.
    Used for endpoints that support both authenticated and guest access.
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_subscription_tier(required_tier: UserSubscriptionTier):
    """
    Dependency to require a specific subscription tier.
    
    Args:
        required_tier: The minimum required subscription tier
        
    Returns:
        Dependency function that checks subscription tier
    """
    tier_hierarchy = {
        UserSubscriptionTier.FREE: 0,
        UserSubscriptionTier.PRO: 1,
        UserSubscriptionTier.POWER: 2,
        UserSubscriptionTier.WHITE_LABEL: 3
    }
    
    async def check_tier(user: User = Depends(get_current_user)) -> User:
        """Check if user has required subscription tier."""
        user_tier_level = tier_hierarchy.get(UserSubscriptionTier(user.subscription_tier), 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)
        
        if user_tier_level < required_tier_level:
            # Log authorization failure
            await AuditService.log_authorization_failure(
                user_id=user.id,
                user_email=user.email,
                user_role=user.role,
                attempted_action=f"access_{required_tier.value}_feature",
                required_permission=f"subscription_tier:{required_tier.value}",
                reason=f"User has {user.subscription_tier} tier, requires {required_tier.value} or higher"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier.value} subscription or higher"
            )
        
        return user
    
    return check_tier


def require_role(required_role: Role):
    """
    Dependency to require a specific user role.
    
    This decorator ensures that only users with the specified role can access
    the endpoint. Commonly used for admin-only endpoints.
    
    Args:
        required_role: The required user role (USER, ADMIN, or SERVICE)
        
    Returns:
        Dependency function that checks user role
        
    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    async def check_role(user: User = Depends(get_current_user)) -> User:
        """Check if user has required role."""
        if user.role != required_role.value:
            # Log authorization failure
            await AuditService.log_authorization_failure(
                user_id=user.id,
                user_email=user.email,
                user_role=user.role,
                attempted_action=f"access_{required_role.value}_endpoint",
                required_permission=f"role:{required_role.value}",
                reason=f"User has {user.role} role, requires {required_role.value}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {required_role.value} role"
            )
        
        logger.debug(f"Role check passed: User {user.id} has {required_role.value} role")
        return user
    
    return check_role


def require_subscription(min_tier: UserSubscriptionTier):
    """
    Decorator to require minimum subscription tier for tiered features.
    
    This is an alias for require_subscription_tier with clearer naming
    for use in route definitions.
    
    Args:
        min_tier: The minimum required subscription tier
        
    Returns:
        Dependency function that checks subscription tier
        
    Raises:
        HTTPException: 403 if user doesn't have required subscription tier
    """
    return require_subscription_tier(min_tier)


def require_scope(required_scope: str):
    """
    Dependency to require a specific API key scope.
    
    This decorator validates that an API key has the required scope to access
    an endpoint. It only works with API key authentication (X-API-Key header).
    
    Args:
        required_scope: The required scope (e.g., 'insights:read', 'alerts:write')
        
    Returns:
        Dependency function that checks API key scope
        
    Raises:
        HTTPException: 401 if no API key provided, 403 if scope insufficient
    """
    async def check_scope(
        x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Check if API key has required scope."""
        if not x_api_key:
            logger.warning("Scope check failed: No API key provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required for this endpoint",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        try:
            # Hash the provided API key
            key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
            
            # Look up API key in database
            result = await db.execute(
                select(APIKey).where(
                    APIKey.key_hash == key_hash,
                    APIKey.revoked_at.is_(None)
                )
            )
            api_key_record = result.scalar_one_or_none()
            
            if not api_key_record:
                logger.warning("Scope check failed: Invalid or revoked API key")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
            
            # Check if API key has required scope
            if required_scope not in api_key_record.scopes:
                # Get user for logging
                user = await UserService.get_user_by_id(db, str(api_key_record.user_id))
                
                # Log API key scope failure
                await AuditService.log_api_key_scope_failure(
                    api_key_id=api_key_record.id,
                    user_id=api_key_record.user_id,
                    user_email=user.email if user else "unknown",
                    required_scope=required_scope,
                    available_scopes=api_key_record.scopes,
                    attempted_endpoint=required_scope
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key missing required scope: {required_scope}"
                )
            
            # Update last used timestamp
            api_key_record.last_used_at = datetime.utcnow()
            await db.commit()
            
            # Get associated user
            user = await UserService.get_user_by_id(db, str(api_key_record.user_id))
            
            if not user:
                logger.error(f"API key {api_key_record.id} has no associated user")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "ApiKey"}
                )
            
            logger.debug(
                f"Scope check passed: API key {api_key_record.id} has scope {required_scope}"
            )
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Scope validation error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "ApiKey"}
            )
    
    return check_scope
