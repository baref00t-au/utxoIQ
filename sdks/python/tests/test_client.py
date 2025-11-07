"""Tests for utxoIQ client."""
import pytest
from unittest.mock import Mock, patch
from utxoiq import UtxoIQClient
from utxoiq.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError
)


class TestUtxoIQClient:
    """Test cases for UtxoIQClient."""
    
    def test_client_initialization_with_firebase_token(self):
        """Test client initialization with Firebase token."""
        client = UtxoIQClient(firebase_token="test-token")
        assert client.firebase_token == "test-token"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test-token"
    
    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = UtxoIQClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert "X-API-Key" in client.session.headers
        assert client.session.headers["X-API-Key"] == "test-api-key"
    
    def test_client_initialization_without_auth(self):
        """Test client initialization without authentication (Guest Mode)."""
        client = UtxoIQClient()
        assert client.firebase_token is None
        assert client.api_key is None
        assert "Authorization" not in client.session.headers
        assert "X-API-Key" not in client.session.headers
    
    def test_custom_base_url(self):
        """Test client with custom base URL."""
        client = UtxoIQClient(base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
    
    @patch('requests.Session.request')
    def test_authentication_error_handling(self, mock_request):
        """Test handling of authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": "AUTHENTICATION_ERROR",
                "message": "Invalid token"
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="invalid-token")
        with pytest.raises(AuthenticationError) as exc_info:
            client.get("/test")
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value)
    
    @patch('requests.Session.request')
    def test_rate_limit_error_handling(self, mock_request):
        """Test handling of rate limit errors."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded",
                "details": {"retry_after": 60}
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        with pytest.raises(RateLimitError) as exc_info:
            client.get("/test")
        
        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60
    
    @patch('requests.Session.request')
    def test_validation_error_handling(self, mock_request):
        """Test handling of validation errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters"
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        with pytest.raises(ValidationError):
            client.post("/test", json={"invalid": "data"})
    
    @patch('requests.Session.request')
    def test_not_found_error_handling(self, mock_request):
        """Test handling of not found errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource not found"
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        with pytest.raises(NotFoundError):
            client.get("/test/nonexistent")
    
    @patch('requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"data": "test"}
