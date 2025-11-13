"""
Notification service for multi-channel alert delivery.

This service handles sending alert notifications via:
- Email (SendGrid)
- Slack (Webhook)
- SMS (Twilio)

Includes retry logic, HTML templates, and delivery tracking.
"""
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from src.models.monitoring import AlertConfiguration, AlertHistory

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Base exception for notification errors."""
    pass


class EmailNotificationError(NotificationError):
    """Raised when email notification fails."""
    pass


class SlackNotificationError(NotificationError):
    """Raised when Slack notification fails."""
    pass


class SMSNotificationError(NotificationError):
    """Raised when SMS notification fails."""
    pass


class NotificationService:
    """
    Multi-channel notification service for alert delivery.
    
    Supports:
    - Email notifications via SendGrid
    - Slack notifications via webhook
    - SMS notifications via Twilio (critical alerts only)
    
    Features:
    - Retry logic for failed sends
    - HTML email templates
    - Color-coded Slack messages
    - SMS character limit handling
    - Delivery status tracking
    """
    
    def __init__(
        self,
        sendgrid_api_key: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
        twilio_from_number: Optional[str] = None,
        alert_email_recipients: Optional[List[str]] = None,
        alert_sms_recipients: Optional[List[str]] = None,
        dashboard_base_url: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        Initialize notification service.
        
        Args:
            sendgrid_api_key: SendGrid API key for email
            slack_webhook_url: Slack webhook URL
            twilio_account_sid: Twilio account SID for SMS
            twilio_auth_token: Twilio auth token
            twilio_from_number: Twilio phone number to send from
            alert_email_recipients: Default email recipients
            alert_sms_recipients: Default SMS recipients (max 5)
            dashboard_base_url: Base URL for monitoring dashboard links
            max_retries: Maximum retry attempts for failed notifications
        """
        # Email configuration
        self.sendgrid_api_key = sendgrid_api_key or os.getenv('SENDGRID_API_KEY')
        self.sendgrid_client = None
        if self.sendgrid_api_key:
            self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
            logger.info("SendGrid client initialized")
        else:
            logger.warning("SendGrid API key not provided, email notifications disabled")
        
        # Slack configuration
        self.slack_webhook_url = slack_webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        if self.slack_webhook_url:
            logger.info("Slack webhook configured")
        else:
            logger.warning("Slack webhook URL not provided, Slack notifications disabled")
        
        # Twilio configuration
        self.twilio_account_sid = twilio_account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = twilio_auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_from_number = twilio_from_number or os.getenv('TWILIO_FROM_NUMBER')
        self.twilio_client = None
        
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = TwilioClient(
                self.twilio_account_sid,
                self.twilio_auth_token
            )
            logger.info("Twilio client initialized")
        else:
            logger.warning("Twilio credentials not provided, SMS notifications disabled")
        
        # Recipients
        self.alert_email_recipients = alert_email_recipients or self._parse_email_recipients()
        
        # SMS recipients with 5 recipient limit
        sms_recipients = alert_sms_recipients or self._parse_sms_recipients()
        if len(sms_recipients) > 5:
            logger.warning(f"SMS recipients limited to 5, got {len(sms_recipients)}")
            sms_recipients = sms_recipients[:5]
        self.alert_sms_recipients = sms_recipients
        
        # Dashboard URL
        self.dashboard_base_url = dashboard_base_url or os.getenv(
            'DASHBOARD_BASE_URL',
            'https://utxoiq.com'
        )
        
        # Retry configuration
        self.max_retries = max_retries
        
        logger.info(
            f"NotificationService initialized - "
            f"Email: {bool(self.sendgrid_client)}, "
            f"Slack: {bool(self.slack_webhook_url)}, "
            f"SMS: {bool(self.twilio_client)}"
        )
    
    def _parse_email_recipients(self) -> List[str]:
        """Parse email recipients from environment variable."""
        recipients_str = os.getenv('ALERT_EMAIL_RECIPIENTS', '')
        if not recipients_str:
            return []
        return [email.strip() for email in recipients_str.split(',') if email.strip()]
    
    def _parse_sms_recipients(self) -> List[str]:
        """Parse SMS recipients from environment variable (max 5)."""
        recipients_str = os.getenv('ALERT_SMS_RECIPIENTS', '')
        if not recipients_str:
            return []
        recipients = [phone.strip() for phone in recipients_str.split(',') if phone.strip()]
        if len(recipients) > 5:
            logger.warning(f"SMS recipients limited to 5, got {len(recipients)}")
            recipients = recipients[:5]
        return recipients
    
    async def send_email_alert(
        self,
        config: AlertConfiguration,
        alert: AlertHistory,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification for alert.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            recipients: Optional list of email recipients (overrides default)
            
        Returns:
            True if email sent successfully, False otherwise
            
        Raises:
            EmailNotificationError: If email fails after retries
        """
        if not self.sendgrid_client:
            logger.error("SendGrid client not initialized, cannot send email")
            return False
        
        recipients = recipients or self.alert_email_recipients
        if not recipients:
            logger.warning("No email recipients configured")
            return False
        
        logger.info(
            f"Sending email alert for {config.name} to {len(recipients)} recipients"
        )
        
        # Prepare email
        subject = f"[{alert.severity.upper()}] {config.name}"
        html_content = self._format_email_body(config, alert)
        
        message = Mail(
            from_email=Email('alerts@utxoiq.com', 'utxoIQ Monitoring'),
            to_emails=[To(email) for email in recipients],
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        # Send with retry logic
        for attempt in range(self.max_retries):
            try:
                response = self.sendgrid_client.send(message)
                
                if response.status_code in (200, 202):
                    logger.info(
                        f"Email alert sent successfully (attempt {attempt + 1})"
                    )
                    return True
                else:
                    logger.warning(
                        f"Email send returned status {response.status_code} "
                        f"(attempt {attempt + 1})"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Email send failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise EmailNotificationError(
                        f"Failed to send email after {self.max_retries} attempts"
                    ) from e
        
        return False
    
    def _format_email_body(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> str:
        """
        Format HTML email body for alert notification.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            
        Returns:
            HTML email content
        """
        # Severity color mapping
        severity_colors = {
            'info': '#36a64f',
            'warning': '#ff9900',
            'critical': '#ff0000'
        }
        color = severity_colors.get(alert.severity, '#666666')
        
        # Dashboard link
        dashboard_url = f"{self.dashboard_base_url}/monitoring/alerts/{config.id}"
        
        # Format timestamp
        triggered_time = alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alert: {config.name}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">{alert.severity.upper()} ALERT</h1>
        <p style="margin: 10px 0 0 0; font-size: 18px;">{config.name}</p>
    </div>
    
    <div style="background-color: #f5f5f5; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px;">
        <h2 style="margin-top: 0; color: #333;">Alert Details</h2>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Service:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.service_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Metric:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.metric_type}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Current Value:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{alert.metric_value:.2f}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Threshold:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.comparison_operator} {alert.threshold_value:.2f}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Triggered At:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{triggered_time}</td>
            </tr>
        </table>
        
        <div style="margin-top: 20px; padding: 15px; background-color: white; border-left: 4px solid {color};">
            <p style="margin: 0;"><strong>Message:</strong></p>
            <p style="margin: 10px 0 0 0;">{alert.message}</p>
        </div>
        
        <div style="margin-top: 20px; text-align: center;">
            <a href="{dashboard_url}" style="display: inline-block; padding: 12px 24px; background-color: #FF5A21; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                View in Dashboard
            </a>
        </div>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
            <p style="margin: 0;">This is an automated alert from utxoIQ Monitoring.</p>
            <p style="margin: 5px 0 0 0;">Alert ID: {alert.id}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    async def send_email_resolution(
        self,
        config: AlertConfiguration,
        alert: AlertHistory,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification for alert resolution.
        
        Args:
            config: Alert configuration
            alert: Resolved alert history record
            recipients: Optional list of email recipients
            
        Returns:
            True if email sent successfully
        """
        if not self.sendgrid_client:
            return False
        
        recipients = recipients or self.alert_email_recipients
        if not recipients:
            return False
        
        logger.info(f"Sending resolution email for {config.name}")
        
        subject = f"[RESOLVED] {config.name}"
        html_content = self._format_resolution_email_body(config, alert)
        
        message = Mail(
            from_email=Email('alerts@utxoiq.com', 'utxoIQ Monitoring'),
            to_emails=[To(email) for email in recipients],
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.sendgrid_client.send(message)
            return response.status_code in (200, 202)
        except Exception as e:
            logger.error(f"Failed to send resolution email: {e}")
            return False
    
    def _format_resolution_email_body(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> str:
        """Format HTML email body for alert resolution."""
        triggered_time = alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')
        resolved_time = alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC') if alert.resolved_at else 'N/A'
        
        # Calculate duration
        if alert.resolved_at:
            duration = alert.resolved_at - alert.triggered_at
            duration_str = str(duration).split('.')[0]  # Remove microseconds
        else:
            duration_str = 'N/A'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alert Resolved: {config.name}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #36a64f; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">✓ ALERT RESOLVED</h1>
        <p style="margin: 10px 0 0 0; font-size: 18px;">{config.name}</p>
    </div>
    
    <div style="background-color: #f5f5f5; padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px;">
        <p style="margin-top: 0;">The alert condition has cleared and the service has returned to normal.</p>
        
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Service:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.service_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Metric:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{config.metric_type}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Triggered At:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{triggered_time}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Resolved At:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{resolved_time}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; font-weight: bold;">Duration:</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{duration_str}</td>
            </tr>
        </table>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
            <p style="margin: 0;">This is an automated notification from utxoIQ Monitoring.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    
    async def send_slack_alert(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> bool:
        """
        Send Slack notification for alert.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            
        Returns:
            True if Slack message sent successfully
            
        Raises:
            SlackNotificationError: If Slack notification fails after retries
        """
        if not self.slack_webhook_url:
            logger.error("Slack webhook URL not configured, cannot send notification")
            return False
        
        logger.info(f"Sending Slack alert for {config.name}")
        
        # Severity color mapping
        severity_colors = {
            'info': '#36a64f',
            'warning': '#ff9900',
            'critical': '#ff0000'
        }
        color = severity_colors.get(alert.severity, '#666666')
        
        # Format timestamp
        timestamp = int(alert.triggered_at.timestamp())
        
        # Build Slack message payload
        payload = {
            "attachments": [{
                "color": color,
                "title": f"{alert.severity.upper()}: {config.name}",
                "text": alert.message,
                "fields": [
                    {
                        "title": "Service",
                        "value": config.service_name,
                        "short": True
                    },
                    {
                        "title": "Metric",
                        "value": config.metric_type,
                        "short": True
                    },
                    {
                        "title": "Current Value",
                        "value": f"{alert.metric_value:.2f}",
                        "short": True
                    },
                    {
                        "title": "Threshold",
                        "value": f"{config.comparison_operator} {alert.threshold_value:.2f}",
                        "short": True
                    }
                ],
                "footer": "utxoIQ Monitoring",
                "footer_icon": "https://utxoiq.com/favicon.ico",
                "ts": timestamp
            }]
        }
        
        # Send with retry logic
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        self.slack_webhook_url,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        logger.info(
                            f"Slack alert sent successfully (attempt {attempt + 1})"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Slack send returned status {response.status_code} "
                            f"(attempt {attempt + 1}): {response.text}"
                        )
                        
            except Exception as e:
                logger.error(
                    f"Slack send failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise SlackNotificationError(
                        f"Failed to send Slack notification after {self.max_retries} attempts"
                    ) from e
        
        return False
    
    async def send_slack_resolution(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> bool:
        """
        Send Slack notification for alert resolution.
        
        Args:
            config: Alert configuration
            alert: Resolved alert history record
            
        Returns:
            True if Slack message sent successfully
        """
        if not self.slack_webhook_url:
            return False
        
        logger.info(f"Sending Slack resolution for {config.name}")
        
        # Calculate duration
        if alert.resolved_at:
            duration = alert.resolved_at - alert.triggered_at
            duration_str = str(duration).split('.')[0]  # Remove microseconds
        else:
            duration_str = 'N/A'
        
        timestamp = int(alert.resolved_at.timestamp()) if alert.resolved_at else int(datetime.utcnow().timestamp())
        
        payload = {
            "attachments": [{
                "color": "#36a64f",
                "title": f"✓ RESOLVED: {config.name}",
                "text": "Alert condition has cleared",
                "fields": [
                    {
                        "title": "Service",
                        "value": config.service_name,
                        "short": True
                    },
                    {
                        "title": "Metric",
                        "value": config.metric_type,
                        "short": True
                    },
                    {
                        "title": "Duration",
                        "value": duration_str,
                        "short": True
                    },
                    {
                        "title": "Resolution Method",
                        "value": alert.resolution_method or 'auto',
                        "short": True
                    }
                ],
                "footer": "utxoIQ Monitoring",
                "footer_icon": "https://utxoiq.com/favicon.ico",
                "ts": timestamp
            }]
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Slack resolution: {e}")
            return False
    
    async def send_sms_alert(
        self,
        config: AlertConfiguration,
        alert: AlertHistory,
        recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send SMS notification for critical alerts.
        
        SMS notifications are only sent for critical severity alerts.
        Messages are limited to 160 characters.
        Supports up to 5 phone numbers per alert.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            recipients: Optional list of phone numbers (overrides default, max 5)
            
        Returns:
            Dictionary with delivery status:
            - sent: Number of SMS sent successfully
            - failed: Number of SMS that failed
            - statuses: List of delivery statuses per recipient
            
        Raises:
            SMSNotificationError: If SMS service is not configured
        """
        if not self.twilio_client:
            logger.error("Twilio client not initialized, cannot send SMS")
            raise SMSNotificationError("SMS service not configured")
        
        # Only send SMS for critical alerts
        if alert.severity != 'critical':
            logger.debug(
                f"Skipping SMS for non-critical alert {config.name} "
                f"(severity: {alert.severity})"
            )
            return {"sent": 0, "failed": 0, "statuses": []}
        
        recipients = recipients or self.alert_sms_recipients
        if not recipients:
            logger.warning("No SMS recipients configured")
            return {"sent": 0, "failed": 0, "statuses": []}
        
        # Limit to 5 recipients
        if len(recipients) > 5:
            logger.warning(f"SMS recipients limited to 5, got {len(recipients)}")
            recipients = recipients[:5]
        
        logger.info(
            f"Sending SMS alert for {config.name} to {len(recipients)} recipients"
        )
        
        # Format SMS message (160 character limit)
        message_body = self._format_sms_message(config, alert)
        
        # Track delivery status
        result = {
            "sent": 0,
            "failed": 0,
            "statuses": []
        }
        
        # Send to each recipient
        for phone in recipients:
            try:
                # Send SMS with retry (once)
                message = await self._send_sms_with_retry(
                    phone,
                    message_body,
                    max_retries=2
                )
                
                result["sent"] += 1
                result["statuses"].append({
                    "phone": phone,
                    "status": "sent",
                    "sid": message.sid,
                    "error": None
                })
                
                logger.info(f"SMS sent to {phone} (SID: {message.sid})")
                
            except Exception as e:
                result["failed"] += 1
                result["statuses"].append({
                    "phone": phone,
                    "status": "failed",
                    "sid": None,
                    "error": str(e)
                })
                
                logger.error(f"Failed to send SMS to {phone}: {e}")
        
        logger.info(
            f"SMS delivery complete: {result['sent']} sent, {result['failed']} failed"
        )
        
        return result
    
    def _format_sms_message(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> str:
        """
        Format SMS message with 160 character limit.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            
        Returns:
            SMS message text (max 160 characters)
        """
        # Build message components
        prefix = f"[CRITICAL] {config.service_name}: "
        
        # Truncate message to fit 160 character limit
        max_message_length = 160 - len(prefix)
        
        # Try to include metric details
        metric_info = f"{config.metric_type} {alert.metric_value:.1f} {config.comparison_operator} {alert.threshold_value:.1f}"
        
        if len(metric_info) <= max_message_length:
            message = prefix + metric_info
        else:
            # Fallback to shorter message
            short_message = alert.message[:max_message_length]
            message = prefix + short_message
        
        # Ensure we don't exceed 160 characters
        if len(message) > 160:
            message = message[:157] + "..."
        
        return message
    
    async def _send_sms_with_retry(
        self,
        to_phone: str,
        message_body: str,
        max_retries: int = 2
    ) -> Any:
        """
        Send SMS with retry logic.
        
        Args:
            to_phone: Recipient phone number
            message_body: SMS message text
            max_retries: Maximum retry attempts
            
        Returns:
            Twilio message object
            
        Raises:
            SMSNotificationError: If SMS fails after retries
        """
        for attempt in range(max_retries):
            try:
                # Create message using Twilio client
                # Note: Twilio client is synchronous, but we wrap it in async context
                message = self.twilio_client.messages.create(
                    body=message_body,
                    from_=self.twilio_from_number,
                    to=to_phone
                )
                
                return message
                
            except TwilioRestException as e:
                logger.error(
                    f"Twilio error sending SMS (attempt {attempt + 1}/{max_retries}): "
                    f"{e.code} - {e.msg}"
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise SMSNotificationError(
                        f"Failed to send SMS after {max_retries} attempts: {e.msg}"
                    ) from e
                    
            except Exception as e:
                logger.error(
                    f"Unexpected error sending SMS (attempt {attempt + 1}/{max_retries}): {e}"
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise SMSNotificationError(
                        f"Failed to send SMS after {max_retries} attempts"
                    ) from e
        
        raise SMSNotificationError("Failed to send SMS")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get notification service status.
        
        Returns:
            Dictionary with service status:
            - email_enabled: Whether email is configured
            - slack_enabled: Whether Slack is configured
            - sms_enabled: Whether SMS is configured
            - email_recipients: Number of email recipients
            - sms_recipients: Number of SMS recipients
        """
        return {
            "email_enabled": bool(self.sendgrid_client),
            "slack_enabled": bool(self.slack_webhook_url),
            "sms_enabled": bool(self.twilio_client),
            "email_recipients": len(self.alert_email_recipients),
            "sms_recipients": len(self.alert_sms_recipients),
            "max_retries": self.max_retries
        }
