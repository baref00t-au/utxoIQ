"""Unit tests for user models and user service."""
import pytest
from datetime import datetime
from uuid import uuid4

from src.models.db_models import User, APIKey
from src.services.user_service import UserService
from src.models.auth import UserUpdate
from src.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_create_user_with_valid_data(clean_database):
    """Test creating a user with valid data."""
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            firebase_uid="test_firebase_uid_123",
            email="test@example.com",
            display_name="Test User",
            role="user",
            subscription_tier="free"
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Verify user was created
        assert user.id is not None
        assert user.firebase_uid == "test_firebase_uid_123"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.role == "user"
        assert user.subscription_tier == "free"
        assert user.created_at is not None
        assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_unique_constraint_firebase_uid(clean_database):
    """Test that firebase_uid must be unique."""
    async with AsyncSessionLocal() as session:
        # Create first user
        user1 = User(
            firebase_uid="duplicate_uid",
            email="user1@example.com"
        )
        session.add(user1)
        await session.commit()
        
        # Try to create second user with same firebase_uid
        user2 = User(
            firebase_uid="duplicate_uid",
            email="user2@example.com"
        )
        session.add(user2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            await session.commit()


@pytest.mark.asyncio
async def test_user_unique_constraint_email(clean_database):
    """Test that email must be unique."""
    async with AsyncSessionLocal() as session:
        # Create first user
        user1 = User(
            firebase_uid="uid_1",
            email="duplicate@example.com"
        )
        session.add(user1)
        await session.commit()
        
        # Try to create second user with same email
        user2 = User(
            firebase_uid="uid_2",
            email="duplicate@example.com"
        )
        session.add(user2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            await session.commit()


@pytest.mark.asyncio
async def test_user_default_values(clean_database):
    """Test that default values are set correctly."""
    async with AsyncSessionLocal() as session:
        # Create user with minimal data
        user = User(
            firebase_uid="test_uid",
            email="test@example.com"
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Verify default values
        assert user.role == "user"
        assert user.subscription_tier == "free"
        assert user.display_name is None
        assert user.stripe_customer_id is None
        assert user.last_login_at is None


@pytest.mark.asyncio
async def test_create_user_from_firebase(clean_database):
    """Test creating user from Firebase data."""
    async with AsyncSessionLocal() as session:
        firebase_data = {
            'uid': 'firebase_uid_123',
            'email': 'firebase@example.com',
            'name': 'Firebase User'
        }
        
        user = await UserService.create_user_from_firebase(session, firebase_data)
        
        assert user.id is not None
        assert user.firebase_uid == 'firebase_uid_123'
        assert user.email == 'firebase@example.com'
        assert user.display_name == 'Firebase User'
        assert user.role == 'user'
        assert user.subscription_tier == 'free'
        assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_get_user_by_firebase_uid(clean_database):
    """Test retrieving user by Firebase UID."""
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            firebase_uid="lookup_uid",
            email="lookup@example.com"
        )
        session.add(user)
        await session.commit()
        
        # Retrieve user
        found_user = await UserService.get_user_by_firebase_uid(session, "lookup_uid")
        
        assert found_user is not None
        assert found_user.firebase_uid == "lookup_uid"
        assert found_user.email == "lookup@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email(clean_database):
    """Test retrieving user by email."""
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            firebase_uid="email_lookup_uid",
            email="email_lookup@example.com"
        )
        session.add(user)
        await session.commit()
        
        # Retrieve user
        found_user = await UserService.get_user_by_email(session, "email_lookup@example.com")
        
        assert found_user is not None
        assert found_user.email == "email_lookup@example.com"


@pytest.mark.asyncio
async def test_update_user_profile(clean_database):
    """Test updating user profile."""
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            firebase_uid="update_uid",
            email="update@example.com",
            display_name="Old Name"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Update user
        update_data = UserUpdate(display_name="New Name")
        updated_user = await UserService.update_user_profile(session, user, update_data)
        
        assert updated_user.display_name == "New Name"


@pytest.mark.asyncio
async def test_api_key_relationship(clean_database):
    """Test relationship between User and APIKey."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    async with AsyncSessionLocal() as session:
        # Create user
        user = User(
            firebase_uid="api_key_user",
            email="apikey@example.com"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create API key
        api_key = APIKey(
            user_id=user.id,
            key_hash="hash123",
            key_prefix="sk_test_",
            name="Test Key",
            scopes=["insights:read"]
        )
        session.add(api_key)
        await session.commit()
        
        # Reload user with api_keys relationship
        result = await session.execute(
            select(User).where(User.id == user.id).options(selectinload(User.api_keys))
        )
        user = result.scalar_one()
        
        # Verify relationship
        assert len(user.api_keys) == 1
        assert user.api_keys[0].name == "Test Key"
        assert user.api_keys[0].user_id == user.id


@pytest.mark.asyncio
async def test_api_key_cascade_delete(clean_database):
    """Test that API keys are deleted when user is deleted."""
    async with AsyncSessionLocal() as session:
        # Create user with API key
        user = User(
            firebase_uid="cascade_user",
            email="cascade@example.com"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        api_key = APIKey(
            user_id=user.id,
            key_hash="cascade_hash",
            key_prefix="sk_test_",
            name="Cascade Key"
        )
        session.add(api_key)
        await session.commit()
        
        # Delete user
        await session.delete(user)
        await session.commit()
        
        # Verify API key was also deleted
        from sqlalchemy import select
        result = await session.execute(
            select(APIKey).where(APIKey.key_hash == "cascade_hash")
        )
        deleted_key = result.scalar_one_or_none()
        assert deleted_key is None
