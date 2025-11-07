"""SendGrid client for sending emails."""
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
import base64
from typing import Optional
import logging

from .config import settings
from .models import EmailEngagement, EmailEvent
from .bigquery_client import BigQueryClient

logger = logging.getLogger(__name__)


class SendGridClient:
    """Client for SendGrid email operations."""
    
    def __init__(self):
        """Initialize SendGrid client."""
        self.client = SendGridAPIClient(settings.sendgrid_api_key)
        self.from_email = Email(settings.sendgrid_from_email, settings.sendgrid_from_name)
        self.bq_client = BigQueryClient()
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
        user_id: str,
        email_id: Optional[str] = None
    ) -> str:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            plain_text_content: Plain text email content
            user_id: User ID for tracking
            email_id: Optional email ID for tracking
        
        Returns:
            Email ID for tracking
        """
        try:
            # Generate email ID if not provided
            if not email_id:
                from datetime import datetime
                email_id = f"email_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Create message
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", plain_text_content),
                html_content=Content("text/html", html_content)
            )
            
            # Add custom args for tracking
            message.custom_arg = [
                {"key": "user_id", "value": user_id},
                {"key": "email_id", "value": email_id}
            ]
            
            # Send email
            response = self.client.send(message)
            
            # Track delivery
            if response.status_code in [200, 202]:
                self.bq_client.track_engagement(EmailEngagement(
                    email_id=email_id,
                    user_id=user_id,
                    event=EmailEvent.DELIVERED
                ))
                logger.info(f"Email sent successfully to {to_email} (ID: {email_id})")
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.body}")
            
            return email_id
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            raise
    
    def handle_webhook_event(self, event_data: dict) -> None:
        """
        Handle SendGrid webhook events for engagement tracking.
        
        Args:
            event_data: Webhook event data from SendGrid
        """
        try:
            event_type = event_data.get("event")
            user_id = event_data.get("user_id")
            email_id = event_data.get("email_id")
            
            if not user_id or not email_id:
                logger.warning(f"Missing user_id or email_id in webhook event: {event_data}")
                return
            
            # Map SendGrid events to our event types
            event_mapping = {
                "open": EmailEvent.OPENED,
                "click": EmailEvent.CLICKED,
                "bounce": EmailEvent.BOUNCED,
                "dropped": EmailEvent.BOUNCED,
                "unsubscribe": EmailEvent.UNSUBSCRIBED
            }
            
            if event_type in event_mapping:
                self.bq_client.track_engagement(EmailEngagement(
                    email_id=email_id,
                    user_id=user_id,
                    event=event_mapping[event_type],
                    metadata=event_data
                ))
                logger.info(f"Tracked {event_type} event for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}")
