"""Authentication and API key management routes."""
import logging
import secrets
import hashlib
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..middleware.auth import get_current_user, require_role
from ..models.auth import (
    UserProfile,
    UserUpdate,
    SubscriptionTierUpdate,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
    Role
)
from ..models.db_models import User, APIKey
from ..services.user_service import UserService
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile.
    
    Returns the authenticated user's profile information including
    email, display name, role, and subscription tier.
    
    Returns:
        UserProfile: Current user's profile data
    """
    return UserProfile.from_orm(current_user)


@router.patch("/profile", response_model=UserProfile)
async def update_profile(
    update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile.
    
    Allows users to update their display name and other profile preferences.
    Users can only update their own profile.
    
    Args:
        update: Profile update data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        UserProfile: Updated user profile
    """
    updated_user = await UserService.update_user_profile(db, current_user, update)
    return UserProfile.from_orm(updated_user)


@router.patch("/users/{user_id}/subscription-tier", response_model=UserProfile)
async def update_user_subscription_tier(
    user_id: UUID,
    tier_update: SubscriptionTierUpdate,
    admin_user: User = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's subscription tier (admin only).
    
    This endpoint allows administrators to manually update a user's subscription tier.
    All tier changes are logged for audit purposes. This endpoint is typically used
    for manual overrides or corrections, while Stripe webhooks handle automatic
    tier updates based on payments.
    
    Args:
        user_id: UUID of the user to update
        tier_update: Subscription tier update data
        admin_user: Authenticated admin user
        db: Database session
        
    Returns:
        UserProfile: Updated user profile
        
    Raises:
        HTTPException: 404 if user not found, 400 if tier is invalid
    """
    # Get the target user
    target_user = await UserService.get_user_by_id(db, str(user_id))
    
    if not target_user:
        logger.warning(f"Admin {admin_user.id} attempted to update non-existent user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate tier value
    try:
        tier_value = tier_update.subscription_tier.value
    except Exception as e:
        logger.error(f"Invalid subscription tier: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subscription tier"
        )
    
    # Update subscription tier
    updated_user = await UserService.update_subscription_tier(
        db=db,
        user=target_user,
        tier=tier_value,
        reason=tier_update.reason or "admin_update",
        changed_by=admin_user.id,
        changed_by_email=admin_user.email
    )
    
    logger.info(
        f"Admin {admin_user.id} ({admin_user.email}) updated user {user_id} "
        f"subscription tier to {tier_value}"
    )
    
    return UserProfile.from_orm(updated_user)


@router.post("/api-keys", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key for programmatic access.
    
    Generates a secure random API key and stores its hash in the database.
    Users can create up to 5 active API keys. The full API key is only
    returned once during creation and cannot be retrieved later.
    
    Args:
        key_data: API key creation data (name and scopes)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        APIKeyWithSecret: Created API key with the secret key
        
    Raises:
        HTTPException: 400 if user has reached the 5 key limit
    """
    # Check if user has reached the limit of 5 API keys
    existing_keys_count = await UserService.count_user_api_keys(db, str(current_user.id))
    
    if existing_keys_count >= 5:
        logger.warning(
            f"User {current_user.id} ({current_user.email}) attempted to create "
            f"API key but has reached limit of 5 keys"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 API keys allowed per user"
        )
    
    # Generate secure random API key (32 bytes = 43 characters in base64)
    key = secrets.token_urlsafe(32)
    
    # Hash the key for storage (SHA256)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    # Extract prefix for display (first 8 characters)
    key_prefix = key[:8]
    
    # Create API key record
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        scopes=key_data.scopes
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    # Log API key creation
    await AuditService.log_api_key_creation(
        api_key_id=api_key.id,
        user_id=current_user.id,
        user_email=current_user.email,
        key_name=key_data.name,
        scopes=key_data.scopes
    )
    
    logger.info(
        f"Created API key {api_key.id} for user {current_user.id} ({current_user.email})"
    )
    
    # Return the API key with the secret (only time it's shown)
    return APIKeyWithSecret(
        id=api_key.id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        scopes=api_key.scopes,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        key=key  # Full key only returned on creation
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys for the current user.
    
    Returns a list of the user's API keys with metadata but without
    the actual key values. Only non-revoked keys are returned by default.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List[APIKeyResponse]: List of user's API keys
    """
    # Query all non-revoked API keys for the user
    result = await db.execute(
        select(APIKey)
        .where(
            APIKey.user_id == current_user.id,
            APIKey.revoked_at.is_(None)
        )
        .order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()
    
    logger.debug(f"Retrieved {len(api_keys)} API keys for user {current_user.id}")
    
    return [
        APIKeyResponse(
            id=key.id,
            key_prefix=key.key_prefix,
            name=key.name,
            scopes=key.scopes,
            created_at=key.created_at,
            last_used_at=key.last_used_at
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke an API key.
    
    Sets the revoked_at timestamp on the API key, effectively disabling it.
    The key record is not deleted to maintain audit history. Users can only
    revoke their own API keys.
    
    Args:
        key_id: UUID of the API key to revoke
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if key not found or doesn't belong to user
    """
    # Look up the API key
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    
    # Check if key exists and belongs to the current user
    if not api_key or api_key.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to revoke non-existent "
            f"or unauthorized API key {key_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Check if already revoked
    if api_key.revoked_at is not None:
        logger.info(f"API key {key_id} already revoked")
        return {"message": "API key already revoked"}
    
    # Set revoked timestamp
    from datetime import datetime
    api_key.revoked_at = datetime.utcnow()
    
    await db.commit()
    
    # Log API key revocation
    await AuditService.log_api_key_revocation(
        api_key_id=api_key.id,
        user_id=current_user.id,
        user_email=current_user.email,
        key_name=api_key.name
    )
    
    logger.info(
        f"Revoked API key {api_key.id} for user {current_user.id} ({current_user.email})"
    )
    
    return {"message": "API key revoked successfully"}
