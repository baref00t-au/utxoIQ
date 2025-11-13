"""User management service for authentication and user profiles."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import logging

from src.models.db_models import User, APIKey
from src.models.auth import UserProfile, UserUpdate
from src.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user profiles and authentication."""
    
    @staticmethod
    async def create_user_from_firebase(
        db: AsyncSession,
        firebase_data: Dict[str, Any]
    ) -> User:
        """
        Create a new user from Firebase authentication data.
        
        Args:
            db: Database session
            firebase_data: Decoded Firebase token data containing uid, email, etc.
            
        Returns:
            User: Created user object
            
        Raises:
            ValueError: If required fields are missing
        """
        firebase_uid = firebase_data.get('uid')
        email = firebase_data.get('email')
        
        if not firebase_uid or not email:
            raise ValueError("Firebase UID and email are required")
        
        # Extract optional fields
        display_name = firebase_data.get('name') or firebase_data.get('display_name')
        
        # Create new user with default values
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            role="user",  # Default role
            subscription_tier="free",  # Default tier
            last_login_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Created new user: {user.id} ({user.email})")
        return user
    
    @staticmethod
    async def get_user_by_firebase_uid(
        db: AsyncSession,
        firebase_uid: str
    ) -> Optional[User]:
        """
        Get user by Firebase UID.
        
        Args:
            db: Database session
            firebase_uid: Firebase user ID
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        result = await db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: str
    ) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user_profile(
        db: AsyncSession,
        user: User,
        update_data: UserUpdate
    ) -> User:
        """
        Update user profile information.
        
        Args:
            db: Database session
            user: User object to update
            update_data: Update data
            
        Returns:
            User: Updated user object
        """
        # Update only provided fields
        if update_data.display_name is not None:
            user.display_name = update_data.display_name
        
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"Updated user profile: {user.id}")
        return user
    
    @staticmethod
    async def update_last_login(
        db: AsyncSession,
        user: User
    ) -> User:
        """
        Update user's last login timestamp.
        
        Args:
            db: Database session
            user: User object to update
            
        Returns:
            User: Updated user object
        """
        user.last_login_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update_subscription_tier(
        db: AsyncSession,
        user: User,
        tier: str,
        reason: str = "manual_update",
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None
    ) -> User:
        """
        Update user's subscription tier.
        
        Args:
            db: Database session
            user: User object to update
            tier: New subscription tier (free, pro, power)
            reason: Reason for tier change (e.g., 'stripe_payment', 'admin_override')
            changed_by: ID of user who made the change (if manual)
            changed_by_email: Email of user who made the change (if manual)
            
        Returns:
            User: Updated user object
            
        Raises:
            ValueError: If tier is invalid
        """
        valid_tiers = ["free", "pro", "power", "white_label"]
        if tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {valid_tiers}")
        
        old_tier = user.subscription_tier
        user.subscription_tier = tier
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        # Log subscription tier change
        await AuditService.log_subscription_tier_change(
            user_id=user.id,
            user_email=user.email,
            old_tier=old_tier,
            new_tier=tier,
            reason=reason,
            changed_by=changed_by,
            changed_by_email=changed_by_email
        )
        
        logger.info(f"Updated user {user.id} subscription tier from {old_tier} to {tier}")
        return user
    
    @staticmethod
    async def update_user_role(
        db: AsyncSession,
        user: User,
        role: str,
        changed_by: Optional[UUID] = None,
        changed_by_email: Optional[str] = None
    ) -> User:
        """
        Update user's role.
        
        Args:
            db: Database session
            user: User object to update
            role: New role (user, admin, service)
            changed_by: ID of user who made the change
            changed_by_email: Email of user who made the change
            
        Returns:
            User: Updated user object
            
        Raises:
            ValueError: If role is invalid
        """
        valid_roles = ["user", "admin", "service"]
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
        
        old_role = user.role
        user.role = role
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(user)
        
        # Log role change
        await AuditService.log_role_change(
            user_id=user.id,
            user_email=user.email,
            old_role=old_role,
            new_role=role,
            changed_by=changed_by,
            changed_by_email=changed_by_email
        )
        
        logger.info(f"Updated user {user.id} role from {old_role} to {role}")
        return user
    
    @staticmethod
    async def count_user_api_keys(
        db: AsyncSession,
        user_id: str
    ) -> int:
        """
        Count active (non-revoked) API keys for a user.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            int: Number of active API keys
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.revoked_at.is_(None)
            )
        )
        keys = result.scalars().all()
        return len(keys)
