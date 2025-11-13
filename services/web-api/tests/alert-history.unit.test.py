"""Tests for alert history endpoints."""
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
async def test_alert_history(test_alert_config):
    """Create test alert history records."""
    now = datetime.utcnow()
    
    history_records = [
        AlertHistory(
            id=uuid4(),
            alert_config_id=test_alert_config.id,
            triggered_at=now - timedelta(hours=i),
            resolved_at=now - timedelta(hours=i) + timedelta(minutes=15) if i % 2 == 0 else None,
            severity="critical" if i % 3 == 0 else "warning",
            metric_value=85.0 + i,
            threshold_value=80.0,
            message=f"Test alert {i} triggered",
            notification_sent=True,
            notification_channels=["email", "slack"],
            resolution_method="auto" if i % 2 == 0 else None
        )
        for i in range(10)
    ]
    
    async with AsyncSessionLocal() as session:
        for record in history_records:
            session.add(record)
        await session.commit()
        for record in history_records:
            await session.refresh(record)
    
    return history_records


@pytest.fixture
async def multi_service_alert_history(test_user):
    """Create alert history for multiple services."""
    # Create alert configs for different services
    configs = []
    for service in ["web-api", "insight-generator", "feature-engine"]:
        config = AlertConfiguration(
            id=uuid4(),
            name=f"{service} Alert",
            service_name=service,
            metric_type="cpu_usage",
            threshold_type="absolute",
            threshold_value=80.0,
            comparison_operator=">",
            severity="warning",
            evaluation_window_seconds=300,
            notification_channels=["email"],
            suppression_enabled=False,
            created_by=test_user.id,
            enabled=True
        )
        configs.append(config)
    
    async with AsyncSessionLocal() as session:
        for config in configs:
            session.add(config)
        await session.commit()
        for config in configs:
            await session.refresh(config)
    
    # Create history for each config
    now = datetime.utcnow()
    history_records = []
    
    for i, config in enumerate(configs):
        for j in range(5):
            history = AlertHistory(
                id=uuid4(),
                alert_config_id=config.id,
                triggered_at=now - timedelta(days=j),
                resolved_at=now - timedelta(days=j) + timedelta(hours=1) if j % 2 == 0 else None,
                severity="critical" if j == 0 else "warning",
                metric_value=85.0 + j,
                threshold_value=80.0,
                message=f"{config.service_name} alert {j}",
                notification_sent=True,
                notification_channels=["email"],
                resolution_method="auto" if j % 2 == 0 else None
            )
            history_records.append(history)
    
    async with AsyncSessionLocal() as session:
        for record in history_records:
            session.add(record)
        await session.commit()
        for record in history_records:
            await session.refresh(record)
    
    return history_records


class TestGetAlertHistory:
    """Tests for retrieving alert history."""
    
    @pytest.mark.asyncio
    async def test_get_history_empty(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test getting alert history when none exists."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["history"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_history_with_data(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test getting alert history with existing records."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["history"]) == 10
        
        # Verify records are ordered by triggered_at desc
        timestamps = [record["triggered_at"] for record in data["history"]]
        assert timestamps == sorted(timestamps, reverse=True)
    
    @pytest.mark.asyncio
    async def test_get_history_filter_by_service(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alert history by service name."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?service_name=web-api",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # 5 records for web-api
        assert len(data["history"]) == 5
    
    @pytest.mark.asyncio
    async def test_get_history_filter_by_severity(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alert history by severity."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?severity=critical",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Every 3rd record is critical (indices 0, 3, 6, 9)
        assert data["total"] >= 3
        for record in data["history"]:
            assert record["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_get_history_filter_by_date_range(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alert history by date range."""
        now = datetime.utcnow()
        start_date = (now - timedelta(hours=5)).isoformat()
        end_date = now.isoformat()
        
        response = await async_client.get(
            f"/api/v1/monitoring/alerts/history?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should get records from last 5 hours (indices 0-4)
        assert data["total"] >= 5
    
    @pytest.mark.asyncio
    async def test_get_history_filter_by_resolved_status(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test filtering alert history by resolution status."""
        # Get resolved alerts
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?resolved=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # Even indices are resolved
        for record in data["history"]:
            assert record["resolved_at"] is not None
        
        # Get active (unresolved) alerts
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?resolved=false",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # Odd indices are unresolved
        for record in data["history"]:
            assert record["resolved_at"] is None
    
    @pytest.mark.asyncio
    async def test_get_history_pagination(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test alert history pagination."""
        # Get first page
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?page=1&page_size=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["history"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
        
        # Get second page
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?page=2&page_size=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["history"]) == 3
        assert data["page"] == 2
    
    @pytest.mark.asyncio
    async def test_get_history_combined_filters(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test combining multiple filters."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?service_name=web-api&severity=critical&resolved=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should get resolved critical alerts from web-api
        for record in data["history"]:
            assert record["severity"] == "critical"
            assert record["resolved_at"] is not None


class TestGetAlertAnalytics:
    """Tests for alert analytics endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_analytics_empty(
        self,
        async_client,
        test_user,
        mock_firebase_service,
        auth_headers
    ):
        """Test getting analytics when no alerts exist."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_alerts"] == 0
        assert data["active_alerts"] == 0
        assert data["resolved_alerts"] == 0
        assert data["mean_time_to_resolution_minutes"] is None
        assert len(data["alert_frequency_by_service"]) == 0
        assert len(data["most_common_alert_types"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_analytics_with_data(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test getting analytics with existing alert history."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_alerts"] == 10
        assert data["active_alerts"] == 5  # Odd indices
        assert data["resolved_alerts"] == 5  # Even indices
        assert data["mean_time_to_resolution_minutes"] is not None
        assert data["mean_time_to_resolution_minutes"] == 15.0  # 15 minutes resolution time
        assert "period_start" in data
        assert "period_end" in data
    
    @pytest.mark.asyncio
    async def test_get_analytics_frequency_by_service(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test alert frequency by service calculation."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have 3 services
        assert len(data["alert_frequency_by_service"]) == 3
        
        # Each service should have 5 alerts
        for service_stats in data["alert_frequency_by_service"]:
            assert service_stats["total_alerts"] == 5
            assert service_stats["critical_alerts"] >= 1
            assert service_stats["warning_alerts"] >= 1
            assert "avg_alerts_per_day" in service_stats
    
    @pytest.mark.asyncio
    async def test_get_analytics_most_common_types(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test most common alert types calculation."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have alert types
        assert len(data["most_common_alert_types"]) > 0
        
        # Each type should have required fields
        for alert_type in data["most_common_alert_types"]:
            assert "metric_type" in alert_type
            assert "service_name" in alert_type
            assert "alert_count" in alert_type
            assert "avg_metric_value" in alert_type
            assert alert_type["alert_count"] > 0
    
    @pytest.mark.asyncio
    async def test_get_analytics_trends(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test alert trend data calculation."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have trend data
        assert len(data["alert_trends"]) > 0
        
        # Each trend point should have required fields
        for trend in data["alert_trends"]:
            assert "date" in trend
            assert "total_alerts" in trend
            assert "critical_alerts" in trend
            assert "warning_alerts" in trend
            assert "info_alerts" in trend
    
    @pytest.mark.asyncio
    async def test_get_analytics_custom_date_range(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test analytics with custom date range."""
        now = datetime.utcnow()
        start_date = (now - timedelta(days=7)).isoformat()
        end_date = now.isoformat()
        
        response = await async_client.get(
            f"/api/v1/monitoring/alerts/history/analytics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == start_date
        assert data["period_end"] == end_date
    
    @pytest.mark.asyncio
    async def test_get_analytics_filter_by_service(
        self,
        async_client,
        test_user,
        multi_service_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test analytics filtered by service."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics?service_name=web-api",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only have web-api in frequency data
        assert len(data["alert_frequency_by_service"]) == 1
        assert data["alert_frequency_by_service"][0]["service_name"] == "web-api"
        
        # Total alerts should be only from web-api
        assert data["total_alerts"] == 5
    
    @pytest.mark.asyncio
    async def test_get_analytics_mttr_calculation(
        self,
        async_client,
        test_user,
        test_alert_config,
        mock_firebase_service,
        auth_headers
    ):
        """Test mean time to resolution calculation."""
        # Create alerts with known resolution times
        now = datetime.utcnow()
        history_records = [
            AlertHistory(
                id=uuid4(),
                alert_config_id=test_alert_config.id,
                triggered_at=now - timedelta(hours=i),
                resolved_at=now - timedelta(hours=i) + timedelta(minutes=10 * (i + 1)),
                severity="warning",
                metric_value=85.0,
                threshold_value=80.0,
                message=f"Test alert {i}",
                notification_sent=True,
                notification_channels=["email"],
                resolution_method="auto"
            )
            for i in range(3)
        ]
        
        async with AsyncSessionLocal() as session:
            for record in history_records:
                session.add(record)
            await session.commit()
        
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # MTTR should be average of 10, 20, 30 minutes = 20 minutes
        assert data["mean_time_to_resolution_minutes"] == 20.0


class TestAlertHistoryPagination:
    """Tests for alert history pagination edge cases."""
    
    @pytest.mark.asyncio
    async def test_pagination_last_page_partial(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test last page with partial results."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?page=4&page_size=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["history"]) == 1  # Only 1 record on last page
        assert data["page"] == 4
    
    @pytest.mark.asyncio
    async def test_pagination_beyond_last_page(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test requesting page beyond available data."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?page=100&page_size=10",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["history"]) == 0  # No records on this page
    
    @pytest.mark.asyncio
    async def test_pagination_max_page_size(
        self,
        async_client,
        test_user,
        test_alert_history,
        mock_firebase_service,
        auth_headers
    ):
        """Test maximum page size limit."""
        response = await async_client.get(
            "/api/v1/monitoring/alerts/history?page=1&page_size=100",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 100
        assert len(data["history"]) == 10  # All records fit in one page
