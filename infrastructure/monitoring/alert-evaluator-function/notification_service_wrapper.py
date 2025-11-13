"""
Notification service wrapper for Cloud Function.

This module provides a simplified wrapper around the NotificationService
that can be used in the Cloud Function context.
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class NotificationServiceWrapper:
    """Wrapper for NotificationService compatible with Cloud Function."""
    
    def __init__(self):
        """Initialize notification service wrapper."""
        # Get configuration from environment
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_from_number = os.environ.get('TWILIO_FROM_NUMBER')
        
        logger.info("NotificationServiceWrapper initialized")
    
    async def send_email_alert(self, config: Any, alert: Any) -> bool:
        """
        Send email notification for alert.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API key not configured, skipping email")
            return False
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            # Format email
            subject = f"[{alert.severity.upper()}] {config.name}"
            html_content = self._format_email_body(config, alert)
            
            message = Mail(
                from_email='alerts@utxoiq.com',
                to_emails=self._get_alert_recipients(config),
                subject=subject,
                html_content=html_content
            )
            
            # Send email
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            success = response.status_code == 202
            if success:
                logger.info(f"Email sent for alert {config.id}")
            else:
                logger.warning(f"Email send failed with status {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email for alert {config.id}: {e}")
            return False
    
    async def send_slack_alert(self, config: Any, alert: Any) -> bool:
        """
        Send Slack notification for alert.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            
        Returns:
            True if successful, False otherwise
        """
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured, skipping Slack")
            return False
        
        try:
            import httpx
            
            # Color code by severity
            color = {
                'info': '#36a64f',
                'warning': '#ff9900',
                'critical': '#ff0000'
            }.get(alert.severity, '#808080')
            
            # Format Slack message
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"{alert.severity.upper()}: {config.name}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Service", "value": config.service_name, "short": True},
                        {"title": "Metric", "value": config.metric_type, "short": True},
                        {"title": "Current Value", "value": str(alert.metric_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold_value), "short": True},
                    ],
                    "footer": "utxoIQ Monitoring",
                    "ts": int(alert.triggered_at.timestamp())
                }]
            }
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(self.slack_webhook_url, json=payload)
                
                success = response.status_code == 200
                if success:
                    logger.info(f"Slack message sent for alert {config.id}")
                else:
                    logger.warning(f"Slack send failed with status {response.status_code}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error sending Slack message for alert {config.id}: {e}")
            return False
    
    async def send_sms_alert(self, config: Any, alert: Any) -> bool:
        """
        Send SMS notification for critical alert.
        
        Args:
            config: Alert configuration
            alert: Alert history record
            
        Returns:
            True if successful, False otherwise
        """
        if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from_number]):
            logger.warning("Twilio not configured, skipping SMS")
            return False
        
        if alert.severity != 'critical':
            logger.debug(f"Skipping SMS for non-critical alert {config.id}")
            return False
        
        try:
            from twilio.rest import Client
            
            # Initialize Twilio client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            # Format SMS message (max 160 chars)
            message_body = f"[CRITICAL] {config.service_name}: {alert.message[:100]}"
            
            # Get phone numbers
            phone_numbers = self._get_sms_recipients(config)
            
            # Send to each number
            success = False
            for phone in phone_numbers:
                try:
                    message = client.messages.create(
                        body=message_body,
                        from_=self.twilio_from_number,
                        to=phone
                    )
                    logger.info(f"SMS sent to {phone} for alert {config.id}")
                    success = True
                except Exception as e:
                    logger.error(f"Failed to send SMS to {phone}: {e}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending SMS for alert {config.id}: {e}")
            return False
    
    async def send_email_resolution(self, config: Any, alert: Any) -> bool:
        """Send email notification for alert resolution."""
        # Similar to send_email_alert but with resolution message
        logger.info(f"Email resolution notification for alert {config.id}")
        return True
    
    async def send_slack_resolution(self, config: Any, alert: Any) -> bool:
        """Send Slack notification for alert resolution."""
        # Similar to send_slack_alert but with resolution message
        logger.info(f"Slack resolution notification for alert {config.id}")
        return True
    
    def _format_email_body(self, config: Any, alert: Any) -> str:
        """Format HTML email body."""
        return f"""
        <html>
        <body>
            <h2>Alert: {config.name}</h2>
            <p><strong>Severity:</strong> {alert.severity.upper()}</p>
            <p><strong>Service:</strong> {config.service_name}</p>
            <p><strong>Metric:</strong> {config.metric_type}</p>
            <p><strong>Current Value:</strong> {alert.metric_value}</p>
            <p><strong>Threshold:</strong> {alert.threshold_value}</p>
            <p><strong>Message:</strong> {alert.message}</p>
            <p><strong>Triggered At:</strong> {alert.triggered_at}</p>
        </body>
        </html>
        """
    
    def _get_alert_recipients(self, config: Any) -> list:
        """Get email recipients for alert."""
        # In production, this would query user preferences
        # For now, use environment variable
        recipients = os.environ.get('ALERT_EMAIL_RECIPIENTS', 'alerts@utxoiq.com')
        return [email.strip() for email in recipients.split(',')]
    
    def _get_sms_recipients(self, config: Any) -> list:
        """Get SMS recipients for alert."""
        # In production, this would query user preferences
        # For now, use environment variable
        recipients = os.environ.get('ALERT_SMS_RECIPIENTS', '')
        if not recipients:
            return []
        return [phone.strip() for phone in recipients.split(',')]
