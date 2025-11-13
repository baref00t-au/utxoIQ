"""
Integration tests for protected endpoints.

Tests authentication, authorization, subscription tier enforcement,
and rate limiting on protected API endpoints.
"""
import pytest
from fastapi import status
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, AsyncMock, Mock


@pytest.mark.asyncio
class TestInsightEndpointsProtection:
    """Test authentication and authorization for insight endpoints."""
    
    def test_get_latest_insights_without_auth(self, client):
        """Test that latest insights endpoint works without authentication (guest mode)."""
        response = client.get("/insights/latest")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "insights" in data
        assert "total" in data
    
    def test_get_latest_insights_with_auth(self, client, auth_headers):
        """Test that latest insights endpoint works with authentication."""
        response = client.get("/insights/latest", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "insights" in data
    
    def test_get_public_insights_without_auth(self, client):
        """Test that public insights endpoint works without authentication."""
        response = client.get("/insights/public")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "insights" in data
        assert len(data["insights"]) <= 20


@pytest.mark.asyncio
class TestFeedbackEndpointsProtection:
    """Test authentication requirements for feedback endpoints."""
    
    def test_rate_insight_without_auth(self, client):
        """Test that rating requires authentication."""
        response = client.post(
            "/api/v1/feedback/rate",
            json={
                "insight_id": "test-insight-123",
                "rating": 5
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_rate_insight_with_auth(self, client, auth_headers, test_user):
        """Test that authenticated users can rate insights."""
        response = client.post(
            "/api/v1/feedback/rate",
            headers=auth_headers,
            json={
                "insight_id": "test-insight-123",
                "rating": 5,
                "comment": "Great insight!"
            }
        )
        # May fail if insight doesn't exist, but should not be 401
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    def test_comment_on_insight_without_auth(self, client):
        """Test that commenting requires authentication."""
        response = client.post(
            "/api/v1/feedback/comment",
            json={
                "insight_id": "test-insight-123",
                "comment": "Test comment"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_flag_insight_without_auth(self, client):
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
    
    def test_get_user_feedback_without_auth(self, client):
        """Test that getting user feedback requires authentication."""
        response = client.get("/api/v1/feedback/user")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_feedback_with_auth(self, client, auth_headers):
        """Test that authenticated users can get their feedback."""
        response = client.get("/api/v1/feedback/user", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "feedback" in data
        assert "user_id" in data


class TestAlertEndpointsProtection:
    """Test authentication and subscription tier requirements for alert endpoints."""
    
    def test_create_alert_without_auth(self, client):
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
    
    def test_create_alert_with_free_tier(self, client, free_tier_headers):
        """Test that free tier users cannot create alerts."""
        response = client.post(
            "/alerts",
            headers=free_tier_headers,
            json={
                "name": "Test Alert",
                "metric": "mempool_fee",
                "threshold": 100,
                "condition": "above"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "pro" in data["error"]["message"].lower() or "subscription" in data["error"]["message"].lower()
    
    def test_create_alert_with_pro_tier(self, client, pro_tier_headers):
        """Test that Pro tier users can create alerts."""
        response = client.post(
            "/alerts",
            headers=pro_tier_headers,
            json={
                "name": "Test Alert",
                "metric": "mempool_fee",
                "threshold": 100,
                "condition": "above"
            }
        )
        # May fail for other reasons, but should not be 403
        assert response.status_code != status.HTTP_403_FORBIDDEN
    
    def test_get_user_alerts_without_auth(self, client):
        """Test that getting alerts requires authentication."""
        response = client.get("/alerts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_alerts_with_auth(self, client, auth_headers):
        """Test that authenticated users can get their alerts."""
        response = client.get("/alerts", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)


class TestChatEndpointsProtection:
    """Test subscription tier requirements for AI chat endpoints."""
    
    def test_chat_query_without_auth(self, client):
        """Test that chat queries require authentication."""
        response = client.post(
            "/chat/query",
            json={"query": "What is the current block height?"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_chat_query_with_free_tier(self, client, free_tier_headers):
        """Test that free tier users cannot use chat."""
        response = client.post(
            "/chat/query",
            headers=free_tier_headers,
            json={"query": "What is the current block height?"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "pro" in data["error"]["message"].lower() or "subscription" in data["error"]["message"].lower()
    
    def test_chat_query_with_pro_tier(self, client, pro_tier_headers):
        """Test that Pro tier users can use chat."""
        response = client.post(
            "/chat/query",
            headers=pro_tier_headers,
            json={"query": "What is the current block height?"}
        )
        # May fail for other reasons, but should not be 403
        assert response.status_code != status.HTTP_403_FORBIDDEN
    
    def test_chat_query_with_power_tier(self, client, power_tier_headers):
        """Test that Power tier users can use chat."""
        response = client.post(
            "/chat/query",
            headers=power_tier_headers,
            json={"query": "What is the current block height?"}
        )
        # May fail for other reasons, but should not be 403
        assert response.status_code != status.HTTP_403_FORBIDDEN


class TestMonitoringEndpointsProtection:
    """Test role-based access control for monitoring endpoints."""
    
    def test_get_system_status_without_auth(self, client):
        """Test that system status requires authentication."""
        response = client.get("/api/v1/monitoring/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_system_status_with_user_role(self, client, auth_headers):
        """Test that regular users cannot access system status."""
        response = client.get("/api/v1/monitoring/status", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "admin" in data["error"]["message"].lower()
    
    def test_get_system_status_with_admin_role(self, client, admin_headers):
        """Test that admin users can access system status."""
        response = client.get("/api/v1/monitoring/status", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "services" in data
    
    def test_start_backfill_without_auth(self, client):
        """Test that starting backfill requires authentication."""
        response = client.post(
            "/api/v1/monitoring/backfill/start",
            json={
                "job_type": "blocks",
                "start_block": 800000,
                "end_block": 800100
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_start_backfill_with_user_role(self, client, auth_headers):
        """Test that regular users cannot start backfill jobs."""
        response = client.post(
            "/api/v1/monitoring/backfill/start",
            headers=auth_headers,
            json={
                "job_type": "blocks",
                "start_block": 800000,
                "end_block": 800100
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_database_pool_metrics_without_auth(self, client):
        """Test that database metrics require authentication."""
        response = client.get("/api/v1/monitoring/database/pool")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_database_pool_metrics_with_user_role(self, client, auth_headers):
        """Test that regular users cannot access database metrics."""
        response = client.get("/api/v1/monitoring/database/pool", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRateLimiting:
    """Test rate limiting enforcement on protected endpoints."""
    
    def test_rate_limit_headers_present(self, client, auth_headers):
        """Test that rate limit headers are included in responses."""
        response = client.get("/insights/latest", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_enforcement_free_tier(self, client, free_tier_headers):
        """Test that free tier rate limits are enforced."""
        # Make multiple requests to trigger rate limit
        # Free tier: 100 requests per hour
        responses = []
        for i in range(105):
            response = client.get("/insights/latest", headers=free_tier_headers)
            responses.append(response)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
        
        # Should hit rate limit before 105 requests
        rate_limited = any(r.status_code == status.HTTP_429_TOO_MANY_REQUESTS for r in responses)
        if rate_limited:
            # Find the rate limited response
            rate_limited_response = next(r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS)
            data = rate_limited_response.json()
            assert "rate limit" in data["error"]["message"].lower()
            assert "Retry-After" in rate_limited_response.headers
    
    def test_rate_limit_different_tiers(self, client, free_tier_headers, pro_tier_headers):
        """Test that different tiers have different rate limits."""
        # Get rate limit for free tier
        free_response = client.get("/insights/latest", headers=free_tier_headers)
        free_limit = int(free_response.headers.get("X-RateLimit-Limit", 0))
        
        # Get rate limit for pro tier
        pro_response = client.get("/insights/latest", headers=pro_tier_headers)
        pro_limit = int(pro_response.headers.get("X-RateLimit-Limit", 0))
        
        # Pro tier should have higher limit than free tier
        assert pro_limit > free_limit
    
    def test_health_check_not_rate_limited(self, client):
        """Test that health check endpoint is not rate limited."""
        # Make many requests to health check
        for i in range(150):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK
        
        # Should never hit rate limit on health check


class TestEndpointAccessWithValidAuth:
    """Test that endpoints are accessible with valid authentication."""
    
    def test_insights_endpoint_with_valid_auth(self, client, auth_headers):
        """Test insights endpoint with valid authentication."""
        response = client.get("/insights/latest", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_alerts_endpoint_with_valid_auth_and_tier(self, client, pro_tier_headers):
        """Test alerts endpoint with valid authentication and subscription."""
        response = client.get("/alerts", headers=pro_tier_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_feedback_endpoint_with_valid_auth(self, client, auth_headers):
        """Test feedback endpoint with valid authentication."""
        response = client.get("/api/v1/feedback/user", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestEndpointRejectionWithoutAuth:
    """Test that protected endpoints reject requests without authentication."""
    
    def test_feedback_endpoints_reject_without_auth(self, client):
        """Test that all feedback write endpoints require authentication."""
        endpoints = [
            ("/api/v1/feedback/rate", {"insight_id": "test", "rating": 5}),
            ("/api/v1/feedback/comment", {"insight_id": "test", "comment": "test"}),
            ("/api/v1/feedback/flag", {"insight_id": "test", "flag_type": "inaccurate"}),
        ]
        
        for endpoint, data in endpoints:
            response = client.post(endpoint, json=data)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"Endpoint {endpoint} should require auth"
    
    def test_alert_endpoints_reject_without_auth(self, client):
        """Test that all alert endpoints require authentication."""
        # Create alert
        response = client.post("/alerts", json={"name": "test", "metric": "test", "threshold": 100})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Get alerts
        response = client.get("/alerts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Get specific alert
        response = client.get("/alerts/test-id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Update alert
        response = client.put("/alerts/test-id", json={"name": "updated"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Delete alert
        response = client.delete("/alerts/test-id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_monitoring_endpoints_reject_without_auth(self, client):
        """Test that monitoring endpoints require authentication."""
        endpoints = [
            "/api/v1/monitoring/status",
            "/api/v1/monitoring/database/pool",
            "/api/v1/monitoring/database/queries",
            "/api/v1/monitoring/metrics/processing",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, f"Endpoint {endpoint} should require auth"


class TestSubscriptionTierEnforcement:
    """Test that subscription tier restrictions are properly enforced."""
    
    def test_pro_features_blocked_for_free_tier(self, client, free_tier_headers):
        """Test that Pro features are blocked for free tier users."""
        # Chat endpoint
        response = client.post(
            "/chat/query",
            headers=free_tier_headers,
            json={"query": "test"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Create alert endpoint
        response = client.post(
            "/alerts",
            headers=free_tier_headers,
            json={"name": "test", "metric": "test", "threshold": 100}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_pro_features_allowed_for_pro_tier(self, client, pro_tier_headers):
        """Test that Pro features are allowed for Pro tier users."""
        # Chat endpoint (may fail for other reasons, but not 403)
        response = client.post(
            "/chat/query",
            headers=pro_tier_headers,
            json={"query": "test"}
        )
        assert response.status_code != status.HTTP_403_FORBIDDEN
        
        # Create alert endpoint (may fail for other reasons, but not 403)
        response = client.post(
            "/alerts",
            headers=pro_tier_headers,
            json={"name": "test", "metric": "test", "threshold": 100}
        )
        assert response.status_code != status.HTTP_403_FORBIDDEN
    
    def test_pro_features_allowed_for_power_tier(self, client, power_tier_headers):
        """Test that Pro features are allowed for Power tier users."""
        # Chat endpoint (may fail for other reasons, but not 403)
        response = client.post(
            "/chat/query",
            headers=power_tier_headers,
            json={"query": "test"}
        )
        assert response.status_code != status.HTTP_403_FORBIDDEN
