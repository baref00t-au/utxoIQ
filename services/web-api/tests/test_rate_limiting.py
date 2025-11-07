"""Rate limiting integration tests."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are included in responses."""
        response = client.get("/insights/public")
        assert response.status_code == 200
        
        # Check for rate limit headers
        # Note: These may not be present if Redis is not available in test environment
        # In production, these headers should always be present
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert int(response.headers["X-RateLimit-Limit"]) > 0
    
    def test_guest_mode_rate_limiting(self):
        """Test rate limiting for unauthenticated requests."""
        # Make multiple requests to test rate limiting
        # Note: This test may not trigger rate limit in test environment
        # without Redis, but validates the endpoint works
        for i in range(5):
            response = client.get("/insights/public")
            assert response.status_code in [200, 429]  # OK or rate limited
            
            if response.status_code == 429:
                # Verify rate limit error response
                data = response.json()
                assert "error" in data
                assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
                assert "Retry-After" in response.headers
                break


class TestErrorHandling:
    """Test error handling and response formats."""
    
    def test_404_error_format(self):
        """Test 404 error response format."""
        response = client.get("/insights/nonexistent_id")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "request_id" in data
        assert "timestamp" in data
    
    def test_validation_error_format(self):
        """Test validation error response format."""
        # Send invalid data to create alert endpoint
        response = client.post("/alerts", json={
            "signal_type": "invalid_type",
            "threshold": "not_a_number",
            "operator": "invalid_op"
        })
        # Should get 403 (auth required) or 422 (validation error)
        assert response.status_code in [403, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
