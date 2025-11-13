"""
Tests for notification service.

Tests cover:
- Email notification formatting and sending
- Slack notification formatting and sending
- SMS notification for critical alerts only
- Retry logic for failed notifications
- Delivery status tracking
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from src.services.notification_service import (
    NotificationService,
    NotificationError,
    EmailNotificationError,
    SlackNotificationError,
    SMSNotificationError
)
from src.models.monitoring import AlertConfiguration, AlertHistory


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


@pytest.fixture
def sample_critical_alert_config():
    """Create sample critical alert configuration."""
    return AlertConfiguration(
        id=uuid4(),
        name="Critical CPU Alert",
        service_name="web-api",
        metric_type="cpu_usage",
        threshold_type="absolute",
        threshold_value=95.0,
        comparison_operator=">",
        severity="critical",
        evaluation_window_seconds=300,
        notification_channels=["email", "slack", "sms"],
        suppression_enabled=False,
        suppression_start=None,
        suppression_end=None,
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        enabled=True
    )


@pytest.fixture
def sample_alert_history():
    """Create sample alert history."""
    return AlertHistory(
        id=uuid4(),
        alert_config_id=uuid4(),
        triggered_at=datetime.utcnow(),
        resolved_at=None,
        severity="warning",
        metric_value=85.5,
        threshold_value=80.0,
        message="web-api - cpu_usage: 85.50 > 80.00",
        notification_sent=False,
        notification_channels=["email", "slack"]
    )


@pytest.fixture
def sample_resolved_alert_history():
    """Create sample resolved alert history."""
    triggered_at = datetime.utcnow() - timedelta(minutes=15)
    resolved_at = datetime.utcnow()
    
    return AlertHistory(
        id=uuid4(),
        alert_config_id=uuid4(),
        triggered_at=triggered_at,
        resolved_at=resolved_at,
        severity="warning",
        metric_value=85.5,
        threshold_value=80.0,
        message="web-api - cpu_usage: 85.50 > 80.00",
        notification_sent=True,
        notification_channels=["email", "slack"],
        resolution_method="auto"
    )


@pytest.fixture
def notification_service():
    """Create notification service with mock credentials."""
    return NotificationService(
        sendgrid_api_key="test_sendgrid_key",
        slack_webhook_url="https://hooks.slack.com/services/test",
        twilio_account_sid="test_account_sid",
        twilio_auth_token="test_auth_token",
        twilio_from_number="+15555551234",
        alert_email_recipients=["ops@utxoiq.com", "alerts@utxoiq.com"],
        alert_sms_recipients=["+15555555555", "+15555555556"],
        dashboard_base_url="https://utxoiq.com",
        max_retries=3
    )


class TestEmailNotifications:
    """Test email notification functionality."""
    
    @pytest.mark.asyncio
    async def test_send_email_alert_success(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test successful email alert sending."""
        # Mock SendGrid client
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(
            notification_service.sendgrid_client,
            'send',
            return_value=mock_response
        ):
            result = await notification_service.send_email_alert(
                sample_alert_config,
                sample_alert_history
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email_alert_with_retry(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test email sending with retry on failure."""
        # Mock SendGrid client to fail twice then succeed
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(
            notification_service.sendgrid_client,
            'send',
            side_effect=[Exception("Network error"), Exception("Network error"), mock_response]
        ):
            result = await notification_service.send_email_alert(
                sample_alert_config,
                sample_alert_history
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_email_alert_max_retries_exceeded(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test email sending fails after max retries."""
        # Mock SendGrid client to always fail
        with patch.object(
            notification_service.sendgrid_client,
            'send',
            side_effect=Exception("Network error")
        ):
            with pytest.raises(EmailNotificationError):
                await notification_service.send_email_alert(
                    sample_alert_config,
                    sample_alert_history
                )
    
    @pytest.mark.asyncio
    async def test_email_alert_formatting(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test email alert HTML formatting."""
        html = notification_service._format_email_body(
            sample_alert_config,
            sample_alert_history
        )
        
        # Verify key elements are present
        assert "High CPU Alert" in html
        assert "web-api" in html
        assert "cpu_usage" in html
        assert "85.5" in html or "85.50" in html
        assert "80.0" in html or "80.00" in html
        assert "WARNING" in html.upper()
        assert "View in Dashboard" in html
        assert sample_alert_history.message in html
    
    @pytest.mark.asyncio
    async def test_email_alert_severity_colors(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test email uses correct colors for severity levels."""
        # Test warning severity
        sample_alert_history.severity = "warning"
        html_warning = notification_service._format_email_body(
            sample_alert_config,
            sample_alert_history
        )
        assert "#ff9900" in html_warning
        
        # Test critical severity
        sample_alert_history.severity = "critical"
        html_critical = notification_service._format_email_body(
            sample_alert_config,
            sample_alert_history
        )
        assert "#ff0000" in html_critical
        
        # Test info severity
        sample_alert_history.severity = "info"
        html_info = notification_service._format_email_body(
            sample_alert_config,
            sample_alert_history
        )
        assert "#36a64f" in html_info
    
    @pytest.mark.asyncio
    async def test_send_email_resolution(
        self,
        notification_service,
        sample_alert_config,
        sample_resolved_alert_history
    ):
        """Test sending email resolution notification."""
        mock_response = Mock()
        mock_response.status_code = 202
        
        with patch.object(
            notification_service.sendgrid_client,
            'send',
            return_value=mock_response
        ):
            result = await notification_service.send_email_resolution(
                sample_alert_config,
                sample_resolved_alert_history
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_email_resolution_formatting(
        self,
        notification_service,
        sample_alert_config,
        sample_resolved_alert_history
    ):
        """Test email resolution HTML formatting."""
        html = notification_service._format_resolution_email_body(
            sample_alert_config,
            sample_resolved_alert_history
        )
        
        # Verify key elements are present
        assert "RESOLVED" in html.upper()
        assert "High CPU Alert" in html
        assert "web-api" in html
        assert "cpu_usage" in html
        assert "Duration" in html
        assert "#36a64f" in html  # Green color for resolved
    
    @pytest.mark.asyncio
    async def test_email_no_recipients(
        self,
        sample_alert_config,
        sample_alert_history
    ):
        """Test email sending with no recipients configured."""
        service = NotificationService(
            sendgrid_api_key="test_key",
            alert_email_recipients=[]
        )
        
        result = await service.send_email_alert(
            sample_alert_config,
            sample_alert_history
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_email_no_sendgrid_client(
        self,
        sample_alert_config,
        sample_alert_history
    ):
        """Test email sending when SendGrid is not configured."""
        service = NotificationService(
            sendgrid_api_key=None
        )
        
        result = await service.send_email_alert(
            sample_alert_config,
            sample_alert_history
        )
        
        assert result is False


class TestSlackNotifications:
    """Test Slack notification functionality."""
    
    @pytest.mark.asyncio
    async def test_send_slack_alert_success(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test successful Slack alert sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await notification_service.send_slack_alert(
                sample_alert_config,
                sample_alert_history
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_slack_alert_with_retry(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test Slack sending with retry on failure."""
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[
                    mock_response_fail,
                    mock_response_fail,
                    mock_response_success
                ]
            )
            
            result = await notification_service.send_slack_alert(
                sample_alert_config,
                sample_alert_history
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_slack_alert_max_retries_exceeded(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test Slack sending fails after max retries."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )
            
            with pytest.raises(SlackNotificationError):
                await notification_service.send_slack_alert(
                    sample_alert_config,
                    sample_alert_history
                )
    
    @pytest.mark.asyncio
    async def test_slack_alert_payload_structure(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test Slack alert payload has correct structure."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        captured_payload = None
        
        async def capture_post(url, json=None, **kwargs):
            nonlocal captured_payload
            captured_payload = json
            return mock_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = capture_post
            
            await notification_service.send_slack_alert(
                sample_alert_config,
                sample_alert_history
            )
        
        # Verify payload structure
        assert captured_payload is not None
        assert "attachments" in captured_payload
        assert len(captured_payload["attachments"]) == 1
        
        attachment = captured_payload["attachments"][0]
        assert "color" in attachment
        assert "title" in attachment
        assert "text" in attachment
        assert "fields" in attachment
        assert "footer" in attachment
        assert "ts" in attachment
        
        # Verify fields
        fields = attachment["fields"]
        field_titles = [f["title"] for f in fields]
        assert "Service" in field_titles
        assert "Metric" in field_titles
        assert "Current Value" in field_titles
        assert "Threshold" in field_titles
    
    @pytest.mark.asyncio
    async def test_slack_alert_severity_colors(
        self,
        notification_service,
        sample_alert_config,
        sample_alert_history
    ):
        """Test Slack uses correct colors for severity levels."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        captured_payloads = []
        
        async def capture_post(url, json=None, **kwargs):
            captured_payloads.append(json)
            return mock_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = capture_post
            
            # Test warning
            sample_alert_history.severity = "warning"
            await notification_service.send_slack_alert(
                sample_alert_config,
                sample_alert_history
            )
            assert captured_payloads[-1]["attachments"][0]["color"] == "#ff9900"
            
            # Test critical
            sample_alert_history.severity = "critical"
            await notification_service.send_slack_alert(
                sample_alert_config,
                sample_alert_history
            )
            assert captured_payloads[-1]["attachments"][0]["color"] == "#ff0000"
            
            # Test info
            sample_alert_history.severity = "info"
            await notification_service.send_slack_alert(
                sample_alert_config,
                sample_alert_history
            )
            assert captured_payloads[-1]["attachments"][0]["color"] == "#36a64f"
    
    @pytest.mark.asyncio
    async def test_send_slack_resolution(
        self,
        notification_service,
        sample_alert_config,
        sample_resolved_alert_history
    ):
        """Test sending Slack resolution notification."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await notification_service.send_slack_resolution(
                sample_alert_config,
                sample_resolved_alert_history
            )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_slack_no_webhook_url(
        self,
        sample_alert_config,
        sample_alert_history
    ):
        """Test Slack sending when webhook URL is not configured."""
        service = NotificationService(
            slack_webhook_url=None
        )
        
        result = await service.send_slack_alert(
            sample_alert_config,
            sample_alert_history
        )
        
        assert result is False


class TestSMSNotifications:
    """Test SMS notification functionality."""
    
    @pytest.mark.asyncio
    async def test_send_sms_alert_critical_only(
        self,
        notification_service,
        sample_alert_config,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS is only sent for critical alerts."""
        # Mock Twilio client
        mock_message = Mock()
        mock_message.sid = "SM123456"
        
        with patch.object(
            notification_service.twilio_client.messages,
            'create',
            return_value=mock_message
        ):
            # Test warning severity - should not send
            sample_alert_history.severity = "warning"
            result_warning = await notification_service.send_sms_alert(
                sample_alert_config,
                sample_alert_history
            )
            assert result_warning["sent"] == 0
            assert result_warning["failed"] == 0
            
            # Test critical severity - should send
            sample_alert_history.severity = "critical"
            result_critical = await notification_service.send_sms_alert(
                sample_critical_alert_config,
                sample_alert_history
            )
            assert result_critical["sent"] == 2  # 2 recipients configured
            assert result_critical["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_sms_message_character_limit(
        self,
        notification_service,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS message is limited to 160 characters."""
        # Create a very long message
        sample_alert_history.message = "A" * 200
        
        message = notification_service._format_sms_message(
            sample_critical_alert_config,
            sample_alert_history
        )
        
        assert len(message) <= 160
        assert message.startswith("[CRITICAL]")
    
    @pytest.mark.asyncio
    async def test_sms_recipient_limit(
        self,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS recipients are limited to 5."""
        # Create service with more than 5 recipients
        service = NotificationService(
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            twilio_from_number="+15555551234",
            alert_sms_recipients=[
                "+15555555551",
                "+15555555552",
                "+15555555553",
                "+15555555554",
                "+15555555555",
                "+15555555556",  # 6th recipient should be ignored
                "+15555555557"   # 7th recipient should be ignored
            ]
        )
        
        # Verify only 5 recipients are stored
        assert len(service.alert_sms_recipients) == 5
    
    @pytest.mark.asyncio
    async def test_sms_delivery_status_tracking(
        self,
        notification_service,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS delivery status is tracked per recipient."""
        sample_alert_history.severity = "critical"
        
        # Mock Twilio client with mixed success/failure
        mock_message = Mock()
        mock_message.sid = "SM123456"
        
        with patch.object(
            notification_service.twilio_client.messages,
            'create',
            side_effect=[mock_message, Exception("Failed to send")]
        ):
            result = await notification_service.send_sms_alert(
                sample_critical_alert_config,
                sample_alert_history
            )
        
        assert result["sent"] == 1
        assert result["failed"] == 1
        assert len(result["statuses"]) == 2
        
        # Verify status structure
        assert result["statuses"][0]["status"] == "sent"
        assert result["statuses"][0]["sid"] == "SM123456"
        assert result["statuses"][0]["error"] is None
        
        assert result["statuses"][1]["status"] == "failed"
        assert result["statuses"][1]["sid"] is None
        assert result["statuses"][1]["error"] is not None
    
    @pytest.mark.asyncio
    async def test_sms_retry_logic(
        self,
        notification_service,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS sending retries on failure."""
        sample_alert_history.severity = "critical"
        
        # Mock Twilio to fail once then succeed
        mock_message = Mock()
        mock_message.sid = "SM123456"
        
        from twilio.base.exceptions import TwilioRestException
        
        with patch.object(
            notification_service.twilio_client.messages,
            'create',
            side_effect=[
                TwilioRestException(500, "http://test", msg="Server error", code=500),
                mock_message,
                mock_message
            ]
        ):
            result = await notification_service.send_sms_alert(
                sample_critical_alert_config,
                sample_alert_history
            )
        
        # Should succeed after retry
        assert result["sent"] == 2
        assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_sms_no_recipients(
        self,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS sending with no recipients configured."""
        sample_alert_history.severity = "critical"
        
        service = NotificationService(
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            twilio_from_number="+15555551234",
            alert_sms_recipients=[]
        )
        
        result = await service.send_sms_alert(
            sample_critical_alert_config,
            sample_alert_history
        )
        
        assert result["sent"] == 0
        assert result["failed"] == 0
        assert len(result["statuses"]) == 0
    
    @pytest.mark.asyncio
    async def test_sms_no_twilio_client(
        self,
        sample_critical_alert_config,
        sample_alert_history
    ):
        """Test SMS sending when Twilio is not configured."""
        sample_alert_history.severity = "critical"
        
        service = NotificationService(
            twilio_account_sid=None,
            twilio_auth_token=None
        )
        
        with pytest.raises(SMSNotificationError):
            await service.send_sms_alert(
                sample_critical_alert_config,
                sample_alert_history
            )


class TestNotificationServiceStatus:
    """Test notification service status and configuration."""
    
    def test_get_status_all_enabled(self, notification_service):
        """Test status when all notification channels are enabled."""
        status = notification_service.get_status()
        
        assert status["email_enabled"] is True
        assert status["slack_enabled"] is True
        assert status["sms_enabled"] is True
        assert status["email_recipients"] == 2
        assert status["sms_recipients"] == 2
        assert status["max_retries"] == 3
    
    def test_get_status_partial_enabled(self):
        """Test status when only some channels are enabled."""
        service = NotificationService(
            sendgrid_api_key="test_key",
            slack_webhook_url=None,
            twilio_account_sid=None,
            alert_email_recipients=["test@example.com"]
        )
        
        status = service.get_status()
        
        assert status["email_enabled"] is True
        assert status["slack_enabled"] is False
        assert status["sms_enabled"] is False
        assert status["email_recipients"] == 1
        assert status["sms_recipients"] == 0
    
    def test_get_status_none_enabled(self):
        """Test status when no channels are enabled."""
        service = NotificationService(
            sendgrid_api_key=None,
            slack_webhook_url=None,
            twilio_account_sid=None
        )
        
        status = service.get_status()
        
        assert status["email_enabled"] is False
        assert status["slack_enabled"] is False
        assert status["sms_enabled"] is False
        assert status["email_recipients"] == 0
        assert status["sms_recipients"] == 0


class TestNotificationServiceInitialization:
    """Test notification service initialization and configuration."""
    
    def test_init_with_environment_variables(self):
        """Test initialization from environment variables."""
        with patch.dict('os.environ', {
            'SENDGRID_API_KEY': 'env_sendgrid_key',
            'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/env',
            'TWILIO_ACCOUNT_SID': 'env_account_sid',
            'TWILIO_AUTH_TOKEN': 'env_auth_token',
            'TWILIO_FROM_NUMBER': '+15555559999',
            'ALERT_EMAIL_RECIPIENTS': 'test1@example.com,test2@example.com',
            'ALERT_SMS_RECIPIENTS': '+15555551111,+15555552222',
            'DASHBOARD_BASE_URL': 'https://dashboard.example.com'
        }):
            service = NotificationService()
            
            assert service.sendgrid_api_key == 'env_sendgrid_key'
            assert service.slack_webhook_url == 'https://hooks.slack.com/env'
            assert service.twilio_account_sid == 'env_account_sid'
            assert service.twilio_from_number == '+15555559999'
            assert len(service.alert_email_recipients) == 2
            assert len(service.alert_sms_recipients) == 2
            assert service.dashboard_base_url == 'https://dashboard.example.com'
    
    def test_init_with_explicit_parameters(self):
        """Test initialization with explicit parameters overrides environment."""
        with patch.dict('os.environ', {
            'SENDGRID_API_KEY': 'env_key',
        }):
            service = NotificationService(
                sendgrid_api_key='explicit_key'
            )
            
            # Explicit parameter should override environment
            assert service.sendgrid_api_key == 'explicit_key'
    
    def test_parse_email_recipients(self):
        """Test parsing email recipients from comma-separated string."""
        with patch.dict('os.environ', {
            'ALERT_EMAIL_RECIPIENTS': 'test1@example.com, test2@example.com , test3@example.com'
        }):
            service = NotificationService()
            
            assert len(service.alert_email_recipients) == 3
            assert 'test1@example.com' in service.alert_email_recipients
            assert 'test2@example.com' in service.alert_email_recipients
            assert 'test3@example.com' in service.alert_email_recipients
    
    def test_parse_sms_recipients_with_limit(self):
        """Test parsing SMS recipients with 5 recipient limit."""
        with patch.dict('os.environ', {
            'ALERT_SMS_RECIPIENTS': '+1,+2,+3,+4,+5,+6,+7'
        }):
            service = NotificationService()
            
            # Should be limited to 5
            assert len(service.alert_sms_recipients) == 5

