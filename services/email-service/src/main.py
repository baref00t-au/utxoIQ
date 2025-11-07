"""Main FastAPI application for email service."""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Optional

from .config import settings
from .models import (
    EmailPreferences,
    EmailPreferencesUpdate,
    UnsubscribeRequest,
    EmailFrequency
)
from .bigquery_client import BigQueryClient
from .sendgrid_client import SendGridClient
from .email_service import EmailService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="utxoIQ Email Service",
    description="Email service for Daily Brief delivery and preference management",
    version="1.0.0"
)

# Initialize clients
bq_client = BigQueryClient()
sendgrid_client = SendGridClient()
email_service = EmailService()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "email-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/preferences/{user_id}")
async def update_preferences(
    user_id: str,
    email: str,
    updates: EmailPreferencesUpdate
):
    """
    Update email preferences for a user.
    
    Args:
        user_id: User ID
        email: User email address
        updates: Preference updates
    
    Returns:
        Updated preferences
    """
    try:
        # Get existing preferences or create new
        existing = bq_client.get_preferences(user_id)
        
        if existing:
            # Update existing preferences
            if updates.daily_brief_enabled is not None:
                existing.daily_brief_enabled = updates.daily_brief_enabled
            if updates.frequency is not None:
                existing.frequency = updates.frequency
            if updates.signal_filters is not None:
                existing.signal_filters = updates.signal_filters
            if updates.quiet_hours is not None:
                existing.quiet_hours = updates.quiet_hours
            existing.updated_at = datetime.utcnow()
            preferences = existing
        else:
            # Create new preferences
            preferences = EmailPreferences(
                user_id=user_id,
                email=email,
                daily_brief_enabled=updates.daily_brief_enabled if updates.daily_brief_enabled is not None else True,
                frequency=updates.frequency if updates.frequency is not None else EmailFrequency.DAILY,
                signal_filters=updates.signal_filters if updates.signal_filters is not None else [],
                quiet_hours=updates.quiet_hours
            )
        
        # Save to BigQuery
        bq_client.save_preferences(preferences)
        
        logger.info(f"Updated preferences for user {user_id}")
        return preferences
        
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """
    Get email preferences for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        User preferences or 404 if not found
    """
    try:
        preferences = bq_client.get_preferences(user_id)
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/unsubscribe")
async def unsubscribe(request: UnsubscribeRequest):
    """
    Unsubscribe a user from all emails.
    
    Args:
        request: Unsubscribe request with user_id
    
    Returns:
        Success message
    """
    try:
        preferences = bq_client.get_preferences(request.user_id)
        
        if not preferences:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Disable all emails
        preferences.daily_brief_enabled = False
        preferences.frequency = EmailFrequency.NEVER
        preferences.updated_at = datetime.utcnow()
        
        bq_client.save_preferences(preferences)
        
        logger.info(f"User {request.user_id} unsubscribed")
        return {"message": "Successfully unsubscribed", "user_id": request.user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-daily-brief")
async def send_daily_brief(
    background_tasks: BackgroundTasks,
    date: Optional[str] = None
):
    """
    Trigger sending of daily briefs to all subscribed users.
    This endpoint is typically called by Cloud Scheduler at 07:00 UTC.
    
    Args:
        date: Optional date in YYYY-MM-DD format. Defaults to yesterday.
    
    Returns:
        Job status
    """
    try:
        # Add task to background
        background_tasks.add_task(email_service.send_daily_briefs, date)
        
        return {
            "message": "Daily brief send job started",
            "date": date or "yesterday",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting daily brief job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-daily-brief/sync")
async def send_daily_brief_sync(date: Optional[str] = None):
    """
    Synchronously send daily briefs (for testing).
    
    Args:
        date: Optional date in YYYY-MM-DD format. Defaults to yesterday.
    
    Returns:
        Send statistics
    """
    try:
        result = await email_service.send_daily_briefs(date)
        return result
        
    except Exception as e:
        logger.error(f"Error sending daily briefs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/sendgrid")
async def sendgrid_webhook(request: Request):
    """
    Handle SendGrid webhook events for engagement tracking.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Success response
    """
    try:
        events = await request.json()
        
        # SendGrid sends an array of events
        if isinstance(events, list):
            for event in events:
                sendgrid_client.handle_webhook_event(event)
        else:
            sendgrid_client.handle_webhook_event(events)
        
        return {"message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Return 200 to prevent SendGrid from retrying
        return JSONResponse(
            status_code=200,
            content={"message": "Error logged", "error": str(e)}
        )


@app.get("/stats/engagement")
async def get_engagement_stats(user_id: Optional[str] = None, days: int = 30):
    """
    Get email engagement statistics.
    
    Args:
        user_id: Optional user ID to filter by
        days: Number of days to look back (default 30)
    
    Returns:
        Engagement statistics
    """
    try:
        stats = bq_client.get_engagement_stats(user_id, days)
        return {
            "user_id": user_id,
            "days": days,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching engagement stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.service_port)
