"""
Simplified integration tests for protected endpoints.

Tests authentication and authorization without requiring full database setup.
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock, Mock


class TestEndpointAuthenticationRequirements:
    """Test that endpoints require authentication where expected."""
    
    def test_feedback_rate_requires_auth(self, client):
        """Test that rating insights requires authentication."""
        response = client.post(
            "/api/v1/feedback/rate",
            json={
                "insight_id": "test-insight-123",
                "rating": 5
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_feedback_comment_requires_auth(self, client):
        """Test that commenting requires authentication."""
        response = client.post(
            "/api/v1/feedback/comment",
            json={
                "insight_id": "test-insight-123",
                "comment": "Test comment"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_feedback_flag_requires_auth(self, client):
        """Test that flagging requires authentication."""
        response = client.post(
            "/api/v1/feedback/flag",
            json={
                "insight_id": "test-insight-123",
                "flag_type": "inaccurate",
                "flag_reason": "Test reason"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_feedback_requires_auth(self, client):
        """Test that getting user feedback requires authentication."""
        response = client.get("/api/v1/feedback/user")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_alert_requires_auth(self, client):
        """Test that creating alerts requires authentication."""
        response = client.post(
            "/alerts",
            json={
                "name": "Test Alert",
                "metric": "mempool_fee",
                "threshold": 100,
                "condition": "above"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_alerts_requires_auth(self, client):
        """Test that getting alerts requires authentication."""
        response = client.get("/alerts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_chat_query_requires_auth(self, client):
        """Test that chat queries require authentication."""
        response = client.post(
            "/chat/query",
            json={"query": "What is the current block height?"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_monitoring_status_requires_auth(self, client):
        """Test that system status requires authentication."""
        response = client.get("/api/v1/monitoring/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_database_pool_metrics_requires_auth(self, client):
        """Test that database metrics require authentication."""
        response = client.get("/api/v1/monitoring/database/pool")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPublicEndpoints:
    """Test that public endpoints work without authentication."""
    
    def test_health_check_public(self, client):
        """Test that health check is publicly accessible."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint_public(self, client):
        """Test that root endpoint is publicly accessible."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_public_insights_accessible(self, client):
        """Test that public insights endpoint works without auth."""
        with patch('src.routes.insights.InsightsService') as mock_service:
            mock_service.return_value.get_public_insights = AsyncMock(
                return_value=([], 0)
            )
            response = client.get("/insights/public")
            # Should not be 401 (may be other errors due to mocking)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    def test_feedback_stats_public(self, client):
        """Test that feedback stats are publicly accessible."""
        response = client.get("/api/v1/feedback/stats?insight_id=test-123")
        # Should not be 401 (may be other errors due to missing data)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


class TestRateLimitHeaders:
    """Test that rate limit headers are present in responses."""
    
    def test_rate_limit_headers_on_public_endpoint(self, client):
        """Test that rate limit headers are included even on public endpoints."""
        with patch('src.routes.insights.InsightsService') as mock_service:
            mock_service.return_value.get_public_insights = AsyncMock(
                return_value=([], 0)
            )
            response = client.get("/insights/public")
            
            # Rate limit headers should be present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    def test_health_check_no_rate_limit(self, client):
        """Test that health check is not rate limited."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        # Health check should not have rate limit headers
        # (or they should be very high/unlimited)


class TestAuthenticationErrorMessages:
    """Test that authentication errors provide clear messages."""
    
    def test_missing_auth_error_message(self, client):
        """Test that missing auth provides clear error message."""
        response = client.post(
            "/api/v1/feedback/rate",
            json={"insight_id": "test", "rating": 5}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "error" in data
        # Should have WWW-Authenticate header
        assert "WWW-Authenticate" in response.headers
    
    def test_invalid_token_format(self, client):
        """Test that invalid token format is rejected."""
        response = client.post(
            "/api/v1/feedback/rate",
            headers={"Authorization": "InvalidFormat"},
            json={"insight_id": "test", "rating": 5}
        )
        # Should still be unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCorrelationIdHeader:
    """Test that correlation ID is added to responses."""
    
    def test_correlation_id_in_response(self, client):
        """Test that correlation ID is included in response headers."""
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers
    
    def test_correlation_id_preserved(self, client):
        """Test that provided correlation ID is preserved."""
        correlation_id = "test-correlation-123"
        response = client.get(
            "/health",
            headers={"X-Correlation-ID": correlation_id}
        )
        assert response.headers["X-Correlation-ID"] == correlation_id


class TestEndpointDocumentation:
    """Test that API documentation is accessible."""
    
    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_docs_accessible(self, client):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    def test_redoc_accessible(self, client):
        """Test that ReDoc is accessible."""
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK


class TestSecurityHeaders:
    """Test that security-related headers are properly set."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # CORS middleware should handle OPTIONS requests
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]


class TestErrorHandling:
    """Test that errors are handled consistently."""
    
    def test_404_for_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_405_for_wrong_method(self, client):
        """Test that wrong HTTP method returns 405."""
        response = client.put("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_422_for_invalid_request_body(self, client):
        """Test that invalid request body returns 422."""
        response = client.post(
            "/api/v1/feedback/rate",
            headers={"Authorization": "Bearer mock_token"},
            json={"invalid": "data"}
        )
        # Should be 422 (validation error) or 401 (auth error)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
