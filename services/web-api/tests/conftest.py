"""Pytest configuration and fixtures."""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime
from uuid import uuid4

# Set test environment BEFORE importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["FIREBASE_PROJECT_ID"] = "test-project"
os.environ["FIREBASE_CREDENTIALS_PATH"] = "./test-firebase-credentials.json"
os.environ["GCP_PROJECT_ID"] = "utxoiq-test"
os.environ["CLOUD_SQL_CONNECTION_NAME"] = "local:test:instance"
os.environ["DB_USER"] = "utxoiq"
os.environ["DB_PASSWORD"] = "utxoiq_dev_password"
os.environ["DB_NAME"] = "utxoiq_db"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5433"  # Test database on different port
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6380"  # Test Redis on different port
os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock_key"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_mock_secret"
os.environ["VERTEX_AI_LOCATION"] = "us-central1"
os.environ["RATE_LIMIT_FREE_TIER"] = "100"
os.environ["RATE_LIMIT_PRO_TIER"] = "1000"
os.environ["RATE_LIMIT_POWER_TIER"] = "10000"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["ARCHIVE_BUCKET_NAME"] = "utxoiq-test-archives"

from src.main import app
from src.models.db_models import Base, User, APIKey
from src.models.monitoring import AlertConfiguration, AlertHistory  # Import to register with Base
from src.models.auth import UserSubscriptionTier, Role
from src.database import AsyncSessionLocal, engine as app_engine


@pytest.fixture
def client():
    """Create a synchronous test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase Auth token for testing."""
    return "mock_firebase_jwt_token"


@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "uid": "test_user_123",
        "email": "test@example.com",
        "subscription_tier": "pro"
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_test_database():
    """Set up test database schema once per test session."""
    # Create all tables
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop all tables after tests
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def clean_database(setup_test_database):
    """Clean database before each test."""
    # Truncate all tables before each test
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Get all table names
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
        await session.commit()
    
    yield
    
    # Clean up after test
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
        await session.commit()


@pytest.fixture
async def test_user(clean_database):
    """Create a test user in the database."""
    user = User(
        id=uuid4(),
        firebase_uid="test_user_123",
        email="test@example.com",
        display_name="Test User",
        role=Role.USER.value,
        subscription_tier=UserSubscriptionTier.FREE.value,
        created_at=datetime.utcnow(),
        last_login_at=datetime.utcnow()
    )
    
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


@pytest.fixture
async def pro_user(clean_database):
    """Create a Pro tier test user in the database."""
    user = User(
        id=uuid4(),
        firebase_uid="pro_user_123",
        email="pro@example.com",
        display_name="Pro User",
        role=Role.USER.value,
        subscription_tier=UserSubscriptionTier.PRO.value,
        created_at=datetime.utcnow(),
        last_login_at=datetime.utcnow()
    )
    
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


@pytest.fixture
async def power_user(clean_database):
    """Create a Power tier test user in the database."""
    user = User(
        id=uuid4(),
        firebase_uid="power_user_123",
        email="power@example.com",
        display_name="Power User",
        role=Role.USER.value,
        subscription_tier=UserSubscriptionTier.POWER.value,
        created_at=datetime.utcnow(),
        last_login_at=datetime.utcnow()
    )
    
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


@pytest.fixture
async def admin_user(clean_database):
    """Create an admin test user in the database."""
    user = User(
        id=uuid4(),
        firebase_uid="admin_user_123",
        email="admin@example.com",
        display_name="Admin User",
        role=Role.ADMIN.value,
        subscription_tier=UserSubscriptionTier.PRO.value,
        created_at=datetime.utcnow(),
        last_login_at=datetime.utcnow()
    )
    
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


@pytest.fixture
def mock_firebase_service():
    """Mock Firebase Auth service for testing."""
    with patch('src.middleware.auth.firebase_service') as mock:
        mock.is_initialized.return_value = True
        mock.verify_token = AsyncMock(return_value={
            "uid": "test_user_123",
            "email": "test@example.com"
        })
        yield mock


@pytest.fixture
def auth_headers(mock_firebase_token):
    """Create authentication headers with Bearer token."""
    return {"Authorization": f"Bearer {mock_firebase_token}"}


@pytest.fixture
def free_tier_headers(mock_firebase_token):
    """Create authentication headers for free tier user."""
    return {"Authorization": f"Bearer {mock_firebase_token}"}


@pytest.fixture
def pro_tier_headers():
    """Create authentication headers for Pro tier user."""
    return {"Authorization": "Bearer mock_pro_tier_token"}


@pytest.fixture
def power_tier_headers():
    """Create authentication headers for Power tier user."""
    return {"Authorization": "Bearer mock_power_tier_token"}


@pytest.fixture
def admin_headers():
    """Create authentication headers for admin user."""
    return {"Authorization": "Bearer mock_admin_token"}


@pytest.fixture
def api_key_headers():
    """Create API key headers for testing."""
    return {"X-API-Key": "test_api_key_12345"}


@pytest.fixture(autouse=True)
def mock_rate_limiter():
    """Mock rate limiter to avoid Redis dependency in tests."""
    with patch('src.middleware.rate_limit.get_rate_limiter') as mock:
        mock_limiter = AsyncMock()
        mock_limiter.check_rate_limit = AsyncMock(return_value=(True, 100, 3600))
        mock_limiter._get_limit_for_tier = Mock(return_value=100)
        mock.return_value = mock_limiter
        yield mock


@pytest.fixture(autouse=True)
def mock_audit_service():
    """Mock audit service to avoid database writes in tests."""
    with patch('src.middleware.auth.AuditService') as mock:
        mock.log_successful_login = AsyncMock()
        mock.log_failed_login = AsyncMock()
        mock.log_authorization_failure = AsyncMock()
        yield mock
