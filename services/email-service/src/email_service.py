"""Core email service for sending daily briefs."""
import logging
from typing import List, Optional
from datetime import datetime, time

from .models import EmailPreferences, DailyBrief, SignalType
from .bigquery_client import BigQueryClient
from .sendgrid_client import SendGridClient
from .email_templates import EmailTemplates
from .api_client import APIClient

logger = logging.getLogger(__name__)


class EmailService:
    """Service for managing email operations."""
    
    def __init__(self):
        """Initialize email service."""
        self.bq_client = BigQueryClient()
        self.sendgrid_client = SendGridClient()
        self.templates = EmailTemplates()
        self.api_client = APIClient()
    
    def _is_in_quiet_hours(self, preferences: EmailPreferences) -> bool:
        """Check if current time is within user's quiet hours."""
        if not preferences.quiet_hours:
            return False
        
        current_time = datetime.utcnow().time()
        start = time.fromisoformat(preferences.quiet_hours.start)
        end = time.fromisoformat(preferences.quiet_hours.end)
        
        # Handle quiet hours that span midnight
        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end
    
    def _filter_insights(
        self,
        insights: List,
        signal_filters: List[SignalType]
    ) -> List:
        """Filter insights based on user preferences."""
        if not signal_filters:
            return insights
        
        filter_values = [f.value for f in signal_filters]
        return [i for i in insights if i.signal_type in filter_values]
    
    async def send_daily_brief_to_user(
        self,
        preferences: EmailPreferences,
        brief: DailyBrief
    ) -> bool:
        """
        Send daily brief to a single user.
        
        Args:
            preferences: User email preferences
            brief: Daily brief to send
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Check if in quiet hours
            if self._is_in_quiet_hours(preferences):
                logger.info(f"Skipping user {preferences.user_id} - in quiet hours")
                return False
            
            # Filter insights based on preferences
            filtered_insights = self._filter_insights(
                brief.insights,
                preferences.signal_filters
            )
            
            if not filtered_insights:
                logger.info(f"No insights match filters for user {preferences.user_id}")
                return False
            
            # Create filtered brief
            filtered_brief = DailyBrief(
                date=brief.date,
                insights=filtered_insights,
                summary=brief.summary
            )
            
            # Generate email content
            html_content = self.templates.render_daily_brief(
                filtered_brief,
                preferences.user_id
            )
            plain_text = self.templates.render_plain_text(
                filtered_brief,
                preferences.user_id
            )
            
            # Send email
            subject = f"utxoIQ Daily Brief — {brief.date}"
            self.sendgrid_client.send_email(
                to_email=preferences.email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text,
                user_id=preferences.user_id
            )
            
            logger.info(f"Sent daily brief to {preferences.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily brief to {preferences.email}: {str(e)}")
            return False
    
    async def send_daily_briefs(self, date: Optional[str] = None) -> dict:
        """
        Send daily briefs to all subscribed users.
        
        Args:
            date: Date in YYYY-MM-DD format. Defaults to yesterday.
        
        Returns:
            Dictionary with send statistics
        """
        try:
            # Fetch daily brief
            brief = await self.api_client.get_daily_brief(date)
            if not brief:
                logger.error(f"No daily brief found for date: {date}")
                return {
                    "success": False,
                    "error": "Daily brief not found",
                    "sent": 0,
                    "failed": 0,
                    "skipped": 0
                }
            
            # Get users who should receive daily brief
            users = self.bq_client.get_users_for_daily_brief()
            logger.info(f"Found {len(users)} users subscribed to daily briefs")
            
            # Send to each user
            sent = 0
            failed = 0
            skipped = 0
            
            for user_prefs in users:
                try:
                    result = await self.send_daily_brief_to_user(user_prefs, brief)
                    if result:
                        sent += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.error(f"Failed to send to {user_prefs.email}: {str(e)}")
                    failed += 1
            
            logger.info(f"Daily brief send complete: {sent} sent, {failed} failed, {skipped} skipped")
            
            return {
                "success": True,
                "date": brief.date,
                "sent": sent,
                "failed": failed,
                "skipped": skipped,
                "total_users": len(users)
            }
            
        except Exception as e:
            logger.error(f"Error in send_daily_briefs: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sent": 0,
                "failed": 0,
                "skipped": 0
            }
