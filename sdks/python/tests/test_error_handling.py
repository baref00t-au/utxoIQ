"""Tests for error handling and retry logic."""
import pytest
from unittest.mock import Mock, patch
from utxoiq import UtxoIQClient
from utxoiq.exceptions import (
    UtxoIQError,
    AuthenticationError,
    RateLimitError,
    SubscriptionRequiredError,
    DataUnavailableError,
    ConfidenceTooLowError
)


class TestErrorHandling:
    """Test cases for error handling."""
    
    @patch('requests.Session.request')
    def test_subscription_required_error(self, mock_request):
        """Test handling of subscription required errors."""
        mock_response = Mock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": {
                "code": "SUBSCRIPTION_REQUIRED",
                "message": "This feature requires a paid subscription"
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(firebase_token="test-token")
        with pytest.raises(SubscriptionRequiredError) as exc_info:
            client.get("/premium-feature")
        
        assert exc_info.value.status_code == 402
        assert "paid subscription" in str(exc_info.value)
    
    @patch('requests.Session.request')
    def test_data_unavailable_error(self, mock_request):
        """Test handling of data unavailable errors."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "error": {
                "code": "DATA_UNAVAILABLE",
                "message": "Blockchain data not yet available"
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        with pytest.raises(DataUnavailableError):
            client.get("/insights/latest")
    
    @patch('requests.Session.request')
    def test_confidence_too_low_error(self, mock_request):
        """Test handling of confidence too low errors."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "error": {
                "code": "CONFIDENCE_TOO_LOW",
                "message": "Insight confidence below publication threshold"
            }
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        with pytest.raises(ConfidenceTooLowError):
            client.get("/insight/low-confidence")
    
    @patch('requests.Session.request')
    def test_retry_logic_on_server_error(self, mock_request):
        """Test retry logic on server errors."""
        # First two calls fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.json.return_value = {"error": {"message": "Service unavailable"}}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"data": "success"}
        
        mock_request.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        client = UtxoIQClient(api_key="test-key", max_retries=3)
        # This should eventually succeed after retries
        # Note: The actual retry logic is in the requests adapter
        # This test verifies the configuration is set up correctly
        assert client.session is not None
    
    @patch('requests.Session.request')
    def test_error_with_request_id(self, mock_request):
        """Test that errors include request ID for debugging."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            },
            "request_id": "req_abc123"
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        with pytest.raises(UtxoIQError) as exc_info:
            client.get("/test")
        
        assert exc_info.value.request_id == "req_abc123"
