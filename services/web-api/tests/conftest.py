"""Pytest configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


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
