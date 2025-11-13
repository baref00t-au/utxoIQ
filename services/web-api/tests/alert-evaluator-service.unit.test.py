"""
Tests for alert evaluation engine.

Tests cover:
- Threshold evaluation for all operators
- Alert triggering and history creation
- Alert resolution detection
- Suppression logic
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.alert_evaluator_service import (
    AlertEvaluator,
    AlertEvaluationError,
    MetricNotFoundError
)
from src.models.monitoring import AlertConfiguration, AlertHistory


@pytest.fixture
def mock_metrics_service():
    """Create mock metrics service."""
    service = AsyncMock()
    service.get_time_series = AsyncMock()
    return service


@pytest.fixture
def mock_notification_service():
    """Create mock notification service."""
    service = AsyncMock()
    service.send_email_alert = AsyncMock()
    service.send_slack_alert = AsyncMock()
    service.send_sms_alert = AsyncMock()
    service.send_email_resolution = AsyncMock()
    service.send_slack_resolution = AsyncMock()
    return service


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def alert_evaluator(mock_metrics_service, mock_db_session, mock_notification_service):
    """Create alert evaluator instance."""
    return AlertEvaluator(
        metrics_service=mock_metrics_service,
        db=mock_db_session,
        notification_service=mock_notification_service
    )


@pytest.fixture
def sample_alert_config():
    """Create sample alert configuration."""
    return AlertConfiguration(
        id=uuid4(),
        name="High CPU Alert",
        service_name="web-api",
        metric_type="cpu_usage",
        threshold_type="absolute",
        threshold_value=80.0,
        comparison_operator=">",
        severity="warning",
        evaluation_window_seconds=300,
        notification_channels=["email", "slack"],
        suppression_enabled=False,
        suppression_start=None,
        suppression_end=None,
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        enabled=True
    )


class TestThresholdEvaluation:
    """Test threshold evaluation logic for all operators."""
    
    def test_greater_than_operator(self, alert_evaluator):
        """Test > operator."""
        assert alert_evaluator._evaluate_threshold(85.0, 80.0, '>') is True
        assert alert_evaluator._evaluate_threshold(75.0, 80.0, '>') is False
        assert alert_evaluator._evaluate_threshold(80.0, 80.0, '>') is False
    
    def test_less_than_operator(self, alert_evaluator):
        """Test < operator."""
        assert alert_evaluator._evaluate_threshold(75.0, 80.0, '<') is True
        assert alert_evaluator._evaluate_threshold(85.0, 80.0, '<') is False
        assert alert_evaluator._evaluate_threshold(80.0, 80.0, '<') is False
    
    def test_greater_than_or_equal_operator(self, alert_evaluator):
        """Test >= operator."""
        assert alert_evaluator._evaluate_threshold(85.0, 80.0, '>=') is True
        assert alert_evaluator._evaluate_threshold(80.0, 80.0, '>=') is True
        assert alert_evaluator._evaluate_threshold(75.0, 80.0, '>=') is False
    
    def test_less_than_or_equal_operator(self, alert_evaluator):
        """Test <= operator."""
        assert alert_evaluator._evaluate_threshold(75.0, 80.0, '<=') is True
        assert alert_evaluator._evaluate_threshold(80.0, 80.0, '<=') is True
        assert alert_evaluator._evaluate_threshold(85.0, 80.0, '<=') is False
    
    def test_equal_operator(self, alert_evaluator):
        """Test == operator with floating point tolerance."""
        assert alert_evaluator._evaluate_threshold(80.0, 80.0, '==') is True
        assert alert_evaluator._evaluate_threshold(80.0001, 80.0, '==') is True
        assert alert_evaluator._evaluate_threshold(80.5, 80.0, '==') is False
    
    def test_invalid_operator(self, alert_evaluator):
        """Test invalid operator returns False."""
        assert alert_evaluator._evaluate_threshold(85.0, 80.0, '!=') is False
        assert alert_evaluator._evaluate_threshold(85.0, 80.0, 'invalid') is False


class TestAlertTriggering:
    """Test alert triggering and history creation."""
    
    @pytest.mark.asyncio
    async def test_trigger_new_alert(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_notification_service
    ):
        """Test triggering a new alert creates history record."""
        # Mock no existing active alert
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Trigger alert
        was_triggered = await alert_evaluator._handle_alert_triggered(
            sample_alert_config,
            85.5
        )
        
        assert was_triggered is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()
        
        # Verify alert history was created
        added_alert = mock_db_session.add.call_args[0][0]
        assert isinstance(added_alert, AlertHistory)
        assert added_alert.alert_config_id == sample_alert_config.id
        assert added_alert.metric_value == 85.5
        assert added_alert.threshold_value == 80.0
        assert added_alert.severity == "warning"
        assert added_alert.resolved_at is None
    
    @pytest.mark.asyncio
    async def test_trigger_existing_alert_skipped(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session
    ):
        """Test triggering an already active alert is skipped."""
        # Mock existing active alert
        existing_alert = AlertHistory(
            id=uuid4(),
            alert_config_id=sample_alert_config.id,
            triggered_at=datetime.utcnow(),
            resolved_at=None,
            severity="warning",
            metric_value=85.0,
            threshold_value=80.0,
            message="Test alert"
        )
        
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = existing_alert
        mock_db_session.execute.return_value = mock_result
        
        # Try to trigger alert
        was_triggered = await alert_evaluator._handle_alert_triggered(
            sample_alert_config,
            90.0
        )
        
        assert was_triggered is False
        mock_db_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_alert_message_formatting(
        self,
        alert_evaluator,
        sample_alert_config
    ):
        """Test alert message is properly formatted."""
        message = alert_evaluator._format_alert_message(
            sample_alert_config,
            85.5
        )
        
        assert "web-api" in message
        assert "cpu_usage" in message
        assert "85.5" in message or "85.50" in message
        assert ">" in message
        assert "80.0" in message or "80.00" in message
    
    @pytest.mark.asyncio
    async def test_notifications_sent_on_trigger(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_notification_service
    ):
        """Test notifications are sent when alert is triggered."""
        # Mock no existing active alert
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Trigger alert
        await alert_evaluator._handle_alert_triggered(
            sample_alert_config,
            85.5
        )
        
        # Verify notifications were sent
        mock_notification_service.send_email_alert.assert_called_once()
        mock_notification_service.send_slack_alert.assert_called_once()
        # SMS should not be sent for warning severity
        mock_notification_service.send_sms_alert.assert_not_called()


class TestAlertResolution:
    """Test alert resolution detection and handling."""
    
    @pytest.mark.asyncio
    async def test_resolve_active_alert(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_notification_service
    ):
        """Test resolving an active alert."""
        # Mock existing active alert
        active_alert = AlertHistory(
            id=uuid4(),
            alert_config_id=sample_alert_config.id,
            triggered_at=datetime.utcnow() - timedelta(minutes=10),
            resolved_at=None,
            severity="warning",
            metric_value=85.0,
            threshold_value=80.0,
            message="Test alert"
        )
        
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = active_alert
        mock_db_session.execute.return_value = mock_result
        
        # Resolve alert
        was_resolved = await alert_evaluator._handle_alert_resolved(
            sample_alert_config
        )
        
        assert was_resolved is True
        assert active_alert.resolved_at is not None
        assert active_alert.resolution_method == 'auto'
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_resolve_no_active_alert(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session
    ):
        """Test resolving when no active alert exists."""
        # Mock no active alert
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Try to resolve
        was_resolved = await alert_evaluator._handle_alert_resolved(
            sample_alert_config
        )
        
        assert was_resolved is False
    
    @pytest.mark.asyncio
    async def test_resolution_notification_sent(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_notification_service
    ):
        """Test resolution notification is sent."""
        # Mock existing active alert
        active_alert = AlertHistory(
            id=uuid4(),
            alert_config_id=sample_alert_config.id,
            triggered_at=datetime.utcnow() - timedelta(minutes=10),
            resolved_at=None,
            severity="warning",
            metric_value=85.0,
            threshold_value=80.0,
            message="Test alert"
        )
        
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = active_alert
        mock_db_session.execute.return_value = mock_result
        
        # Resolve alert
        await alert_evaluator._handle_alert_resolved(sample_alert_config)
        
        # Verify resolution notifications were sent
        mock_notification_service.send_email_resolution.assert_called_once()
        mock_notification_service.send_slack_resolution.assert_called_once()


class TestAlertSuppression:
    """Test alert suppression logic."""
    
    def test_suppression_disabled(self, alert_evaluator, sample_alert_config):
        """Test alert is not suppressed when suppression is disabled."""
        sample_alert_config.suppression_enabled = False
        
        is_suppressed = alert_evaluator._is_suppressed(sample_alert_config)
        
        assert is_suppressed is False
    
    def test_suppression_enabled_within_window(self, alert_evaluator, sample_alert_config):
        """Test alert is suppressed within suppression window."""
        now = datetime.utcnow()
        sample_alert_config.suppression_enabled = True
        sample_alert_config.suppression_start = now - timedelta(hours=1)
        sample_alert_config.suppression_end = now + timedelta(hours=1)
        
        is_suppressed = alert_evaluator._is_suppressed(sample_alert_config)
        
        assert is_suppressed is True
    
    def test_suppression_enabled_before_window(self, alert_evaluator, sample_alert_config):
        """Test alert is not suppressed before suppression window."""
        now = datetime.utcnow()
        sample_alert_config.suppression_enabled = True
        sample_alert_config.suppression_start = now + timedelta(hours=1)
        sample_alert_config.suppression_end = now + timedelta(hours=2)
        
        is_suppressed = alert_evaluator._is_suppressed(sample_alert_config)
        
        assert is_suppressed is False
    
    def test_suppression_enabled_after_window(self, alert_evaluator, sample_alert_config):
        """Test alert is not suppressed after suppression window."""
        now = datetime.utcnow()
        sample_alert_config.suppression_enabled = True
        sample_alert_config.suppression_start = now - timedelta(hours=2)
        sample_alert_config.suppression_end = now - timedelta(hours=1)
        
        is_suppressed = alert_evaluator._is_suppressed(sample_alert_config)
        
        assert is_suppressed is False
    
    def test_suppression_no_window_defined(self, alert_evaluator, sample_alert_config):
        """Test alert is not suppressed when window is not defined."""
        sample_alert_config.suppression_enabled = True
        sample_alert_config.suppression_start = None
        sample_alert_config.suppression_end = None
        
        is_suppressed = alert_evaluator._is_suppressed(sample_alert_config)
        
        assert is_suppressed is False
    
    @pytest.mark.asyncio
    async def test_suppressed_alert_logged(
        self,
        alert_evaluator,
        sample_alert_config,
        caplog
    ):
        """Test suppressed alerts are logged for audit."""
        now = datetime.utcnow()
        sample_alert_config.suppression_enabled = True
        sample_alert_config.suppression_start = now - timedelta(hours=1)
        sample_alert_config.suppression_end = now + timedelta(hours=1)
        
        await alert_evaluator._log_suppressed_alert(sample_alert_config)
        
        assert "suppressed" in caplog.text.lower()
        assert str(sample_alert_config.id) in caplog.text


class TestAlertEvaluation:
    """Test complete alert evaluation flow."""
    
    @pytest.mark.asyncio
    async def test_evaluate_alert_triggers(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_metrics_service,
        mock_db_session
    ):
        """Test evaluating an alert that should trigger."""
        # Mock metric value above threshold
        mock_metrics_service.get_time_series.return_value = [{
            'points': [{'value': 85.0, 'timestamp': datetime.utcnow().isoformat()}]
        }]
        
        # Mock no existing active alert
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Evaluate alert
        result = await alert_evaluator.evaluate_alert(sample_alert_config)
        
        assert result['triggered'] is True
        assert result['suppressed'] is False
        assert result['resolved'] is False
        assert result['metric_value'] == 85.0
    
    @pytest.mark.asyncio
    async def test_evaluate_alert_resolves(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_metrics_service,
        mock_db_session
    ):
        """Test evaluating an alert that should resolve."""
        # Mock metric value below threshold
        mock_metrics_service.get_time_series.return_value = [{
            'points': [{'value': 75.0, 'timestamp': datetime.utcnow().isoformat()}]
        }]
        
        # Mock existing active alert
        active_alert = AlertHistory(
            id=uuid4(),
            alert_config_id=sample_alert_config.id,
            triggered_at=datetime.utcnow() - timedelta(minutes=10),
            resolved_at=None,
            severity="warning",
            metric_value=85.0,
            threshold_value=80.0,
            message="Test alert"
        )
        
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = active_alert
        mock_db_session.execute.return_value = mock_result
        
        # Evaluate alert
        result = await alert_evaluator.evaluate_alert(sample_alert_config)
        
        assert result['triggered'] is False
        assert result['suppressed'] is False
        assert result['resolved'] is True
        assert result['metric_value'] == 75.0
    
    @pytest.mark.asyncio
    async def test_evaluate_suppressed_alert(
        self,
        alert_evaluator,
        sample_alert_config
    ):
        """Test evaluating a suppressed alert."""
        # Enable suppression
        now = datetime.utcnow()
        sample_alert_config.suppression_enabled = True
        sample_alert_config.suppression_start = now - timedelta(hours=1)
        sample_alert_config.suppression_end = now + timedelta(hours=1)
        
        # Evaluate alert
        result = await alert_evaluator.evaluate_alert(sample_alert_config)
        
        assert result['suppressed'] is True
        assert result['triggered'] is False
        assert result['resolved'] is False
    
    @pytest.mark.asyncio
    async def test_evaluate_all_alerts(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_metrics_service
    ):
        """Test evaluating all enabled alerts."""
        # Mock enabled alerts - first call returns list of configs
        mock_result_configs = MagicMock()
        mock_result_configs.scalars().all.return_value = [sample_alert_config]
        
        # Mock no existing active alert - second call returns None
        mock_result_active = MagicMock()
        mock_result_active.scalars().first.return_value = None
        
        # Set up execute to return different results on consecutive calls
        mock_db_session.execute.side_effect = [mock_result_configs, mock_result_active]
        
        # Mock metric value
        mock_metrics_service.get_time_series.return_value = [{
            'points': [{'value': 85.0, 'timestamp': datetime.utcnow().isoformat()}]
        }]
        
        # Evaluate all alerts
        summary = await alert_evaluator.evaluate_all_alerts()
        
        assert summary['total_evaluated'] == 1
        assert summary['triggered'] >= 0
        assert summary['errors'] == 0


class TestSMSNotifications:
    """Test SMS notification logic for critical alerts."""
    
    @pytest.mark.asyncio
    async def test_sms_sent_for_critical_alert(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_notification_service
    ):
        """Test SMS is sent for critical severity alerts."""
        # Set critical severity
        sample_alert_config.severity = "critical"
        sample_alert_config.notification_channels = ["email", "slack", "sms"]
        
        # Mock no existing active alert
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Trigger alert
        await alert_evaluator._handle_alert_triggered(
            sample_alert_config,
            95.0
        )
        
        # Verify SMS was sent
        mock_notification_service.send_sms_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sms_not_sent_for_warning_alert(
        self,
        alert_evaluator,
        sample_alert_config,
        mock_db_session,
        mock_notification_service
    ):
        """Test SMS is not sent for warning severity alerts."""
        # Set warning severity
        sample_alert_config.severity = "warning"
        sample_alert_config.notification_channels = ["email", "slack", "sms"]
        
        # Mock no existing active alert
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Trigger alert
        await alert_evaluator._handle_alert_triggered(
            sample_alert_config,
            85.0
        )
        
        # Verify SMS was not sent
        mock_notification_service.send_sms_alert.assert_not_called()
