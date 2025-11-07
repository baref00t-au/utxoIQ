"""Authentication middleware using Firebase Auth."""
import logging
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from ..config import settings
from ..models.auth import User, UserSubscriptionTier

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(settings.firebase_credentials_path)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """
    Verify Firebase Auth token and return user information.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User object with authentication details
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email", "")
        
        # TODO: Fetch subscription tier from database
        # For now, default to FREE tier
        subscription_tier = UserSubscriptionTier.FREE
        
        return User(
            uid=uid,
            email=email,
            subscription_tier=subscription_tier
        )
        
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)
) -> Optional[User]:
    """
    Get user information if authenticated, otherwise return None.
    Used for endpoints that support both authenticated and guest access.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return await verify_firebase_token(credentials)
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
    
    async def check_tier(user: User = Security(verify_firebase_token)) -> User:
        """Check if user has required subscription tier."""
        user_tier_level = tier_hierarchy.get(user.subscription_tier, 0)
        required_tier_level = tier_hierarchy.get(required_tier, 0)
        
        if user_tier_level < required_tier_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires {required_tier.value} subscription or higher"
            )
        
        return user
    
    return check_tier
