"""Tests for alert configuration endpoints."""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from src.models.monitoring import AlertConfiguration, AlertHistory
from src.database import AsyncSessionLocal


@pytest.fixture
async def test_alert_config(test_user):
    """Create a test alert configuration."""
    alert = AlertConfiguration(
        id=uuid4(),
        name="Test CPU Alert",
        service_name="web-api",
        metric_type="cpu_usage",
        threshold_type="absolute",
        threshold_value=80.0,
        comparison_operator=">",
        severity="warning",
        evaluation_window_seconds=300,
        notification_channels=["email", "slack"],
        suppression_enabled=False,
        created_by=test_user.id,
        enabled=True
    )
    
    async with AsyncSessionLocal() as session:
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
    
    return alert


@pytest.fixture
async def multiple_alert_configs(test_user):
    """Create multiple test alert configurations."""
    alerts = [
        AlertConfiguration(
            id=uuid4(),
            name=f"Alert {i}",
            service_name="web-api" if i % 2 == 0 else "insight-generator",
            metric_type="cpu_usage",
            threshold_type="absolute",
            threshold_value=float(70 + i * 5),
            comparison_operator=">",
            severity="warning" if i % 2 == 0 else "critical",
            evaluation_window_seconds=300,
            notification_channels=["email"],
            suppression_enabled=False,
            created_by=test_user.id,
            enabled=i % 3 != 0  # Some disabled
        )
        for i in range(5)
    ]
    
    async with AsyncSessionLocal() as session:
        for alert in alerts:
            session.add(alert)
        await session.commit()
        for alert in alerts:
            await session.refresh(alert)
    
    return alerts


class TestCreateAlertConfiguration:
    """Tests for creating alert configurations."""
    
    @pytest.mark.asyncio
    async def test_create_alert_valid_data(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test creating an alert with valid data."""
        alert_data = {
            "name": "High CPU Alert",
            "service_name": "web-api",
            "metric_type": "cpu_usage",
            "threshold_type": "absolute",
            "threshold_value": 85.0,
            "comparison_operator": ">",
            "severity": "critical",
            "evaluation_window_seconds": 300,
            "notification_channels": ["email", "slack"],
            "enabled": True
        }
        
        response = await async_client.post(
            "/api/v1/monitoring/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == alert_data["name"]
        assert data["service_name"] == alert_data["service_name"]
        assert data["threshold_value"] == alert_data["threshold_value"]
        assert data["enabled"] is True
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_alert_invalid_threshold(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test creating an alert with invalid threshold (negative)."""
        alert_data = {
            "name": "Invalid Alert",
            "service_name": "web-api",
            "metric_type": "cpu_usage",
            "threshold_type": "absolute",
            "threshold_value": -10.0,  # Invalid: negative
            "comparison_operator": ">",
            "severity": "warning",
            "evaluation_window_seconds": 300,
            "notification_channels": ["email"]
        }
        
        response = await async_client.post(
            "/api/v1/monitoring/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_alert_invalid_operator(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test creating an alert with invalid comparison operator."""
        alert_data = {
            "name": "Invalid Alert",
            "service_name": "web-api",
            "metric_type": "cpu_usage",
            "threshold_type": "absolute",
            "threshold_value": 80.0,
            "comparison_operator": "!=",  # Invalid operator
            "severity": "warning",
            "evaluation_window_seconds": 300,
            "notification_channels": ["email"]
        }
        
        response = await async_client.post(
            "/api/v1/monitoring/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_alert_invalid_channel(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test creating an alert with invalid notification channel."""
        alert_data = {
            "name": "Invalid Alert",
            "service_name": "web-api",
            "metric_type": "cpu_usage",
            "threshold_type": "absolute",
            "threshold_value": 80.0,
            "comparison_operator": ">",
            "severity": "warning",
            "evaluation_window_seconds": 300,
            "notification_channels": ["email", "telegram"]  # Invalid: telegram
        }
        
        response = await async_client.post(
            "/api/v1/monitoring/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_alert_invalid_evaluation_window(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test creating an alert with invalid evaluation window."""
        # Test too short
        alert_data = {
            "name": "Invalid Alert",
            "service_name": "web-api",
            "metric_type": "cpu_usage",
            "threshold_type": "absolute",
            "threshold_value": 80.0,
            "comparison_operator": ">",
            "severity": "warning",
            "evaluation_window_seconds": 30,  # Invalid: < 60
            "notification_channels": ["email"]
        }
        
        response = await async_client.post(
            "/api/v1/monitoring/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test too long
        alert_data["evaluation_window_seconds"] = 4000  # Invalid: > 3600
        
        response = await async_client.post(
            "/api/v1/monitoring/alerts",
            json=alert_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestListAlertConfigurations:
    """Tests for listing alert configurations."""
    
    @pytest.mark.asyncio
    async def test_list_alerts_empty(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test listing alerts when none exist."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["alerts"]) == 0
    
    @pytest.mark.asyncio
    async def test_list_alerts_with_data(
        self,
        async_client,
        test_user,
        multiple_alert_configs,
        mock_firebase_service,
        auth_headers
    ):
        """Test listing alerts with existing data."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["alerts"]) == 5
    
    @pytest.mark.asyncio
    async def test_list_alerts_filter_by_service(
        self,
        async_client,
        test_user,
        multiple_alert_configs,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alerts by service name."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts?service_name=web-api",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # 3 web-api alerts
        for alert in data["alerts"]:
            assert alert["service_name"] == "web-api"
    
    @pytest.mark.asyncio
    async def test_list_alerts_filter_by_enabled(
        self,
        async_client,
        test_user,
        multiple_alert_configs,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alerts by enabled status."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts?enabled=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # 4 enabled alerts (indices 1, 2, 4 are enabled)
        assert data["total"] >= 3
        for alert in data["alerts"]:
            assert alert["enabled"] is True
    
    @pytest.mark.asyncio
    async def test_list_alerts_filter_by_severity(
        self,
        async_client,
        test_user,
        multiple_alert_configs,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alerts by severity."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts?severity=critical",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        for alert in data["alerts"]:
            assert alert["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_list_alerts_pagination(
        self,
        async_client,
        test_user,
        multiple_alert_configs,
        mock_firebase_service,
        auth_headers
    ):
        """Test alert listing pagination."""
        # Get first page
        response = await async_client.get(
            "/api/v1/monitoring/alerts?page=1&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["alerts"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        
        # Get second page
        response = await async_client.get(
            "/api/v1/monitoring/alerts?page=2&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["alerts"]) == 2
        assert data["page"] == 2


class TestUpdateAlertConfiguration:
    """Tests for updating alert configurations."""
    
    @pytest.mark.asyncio
    async def test_update_alert_threshold(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test updating alert threshold value."""
        update_data = {
            "threshold_value": 90.0
        }
        
        response = await async_client.patch(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["threshold_value"] == 90.0
        assert data["name"] == test_alert_config.name  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_alert_severity(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test updating alert severity."""
        update_data = {
            "severity": "critical"
        }
        
        response = await async_client.patch(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_update_alert_enabled_status(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test enabling/disabling an alert."""
        update_data = {
            "enabled": False
        }
        
        response = await async_client.patch(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_update_alert_not_found(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test updating non-existent alert."""
        fake_id = uuid4()
        update_data = {
            "threshold_value": 90.0
        }
        
        response = await async_client.patch(
            f"/api/v1/monitoring/alerts/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_alert_invalid_threshold(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test updating alert with invalid threshold."""
        update_data = {
            "threshold_value": -50.0  # Invalid: negative
        }
        
        response = await async_client.patch(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestDeleteAlertConfiguration:
    """Tests for deleting alert configurations."""
    
    @pytest.mark.asyncio
    async def test_delete_alert_success(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test successfully deleting an alert."""
        response = await async_client.delete(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify alert is deleted
        response = await async_client.get(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_alert_not_found(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test deleting non-existent alert."""
        fake_id = uuid4()
        
        response = await async_client.delete(
            f"/api/v1/monitoring/alerts/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_alert_cascades_history(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test that deleting an alert cascades to history."""
        # Create alert history
        history = AlertHistory(
            id=uuid4(),
            alert_config_id=test_alert_config.id,
            triggered_at=datetime.utcnow(),
            severity="warning",
            metric_value=85.0,
            threshold_value=80.0,
            message="Test alert triggered",
            notification_sent=True,
            notification_channels=["email"]
        )
        
        async with AsyncSessionLocal() as session:
            session.add(history)
            await session.commit()
        
        # Delete alert
        response = await async_client.delete(
            f"/api/v1/monitoring/alerts/{test_alert_config.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify history is also deleted (cascade)
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AlertHistory).where(AlertHistory.id == history.id)
            )
            deleted_history = result.scalar_one_or_none()
            assert deleted_history is None
