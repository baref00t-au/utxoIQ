"""Main FastAPI application for X Bot service."""
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List
from datetime import date

from .config import settings
from .posting_service import PostingService
from .daily_brief_service import DailyBriefService
from .models import PostResult

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize services
posting_service = PostingService()
daily_brief_service = DailyBriefService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    logger.info("X Bot service starting up")
    yield
    logger.info("X Bot service shutting down")


# Create FastAPI app
app = FastAPI(
    title="utxoIQ X Bot",
    description="Automated social media posting service for Bitcoin blockchain insights",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "utxoIQ X Bot",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


@app.post("/post/hourly")
async def post_hourly_insights(background_tasks: BackgroundTasks):
    """
    Endpoint for hourly insight posting (triggered by Cloud Scheduler).
    
    This endpoint processes publishable insights and posts them to X.
    """
    if not settings.hourly_check_enabled:
        raise HTTPException(status_code=503, detail="Hourly posting is disabled")
    
    logger.info("Hourly posting endpoint triggered")
    
    # Process insights in background
    results = await posting_service.process_hourly_insights()
    
    # Return summary
    successful = sum(1 for r in results if r.success)
    
    return {
        "status": "completed",
        "total_processed": len(results),
        "successful_posts": successful,
        "failed_posts": len(results) - successful,
        "results": [
            {
                "insight_id": r.insight_id,
                "success": r.success,
                "tweet_id": r.tweet_id,
                "error": r.error
            }
            for r in results
        ]
    }


@app.post("/post/daily-brief")
async def post_daily_brief_endpoint(brief_date: str = None):
    """
    Endpoint for posting daily Bitcoin Pulse thread (triggered by Cloud Scheduler).
    
    Args:
        brief_date: Optional date string (YYYY-MM-DD). Defaults to today.
    """
    logger.info(f"Daily brief posting endpoint triggered for date: {brief_date or 'today'}")
    
    # Parse date if provided
    target_date = None
    if brief_date:
        try:
            target_date = date.fromisoformat(brief_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Post daily brief
    tweet_ids = await daily_brief_service.post_daily_brief(target_date)
    
    if not tweet_ids:
        return {
            "status": "skipped",
            "message": "Daily brief not posted (already posted or not available)"
        }
    
    successful_tweets = sum(1 for tid in tweet_ids if tid is not None)
    
    return {
        "status": "completed",
        "total_tweets": len(tweet_ids),
        "successful_tweets": successful_tweets,
        "failed_tweets": len(tweet_ids) - successful_tweets,
        "tweet_ids": tweet_ids
    }


@app.post("/post/insight/{insight_id}")
async def post_single_insight(insight_id: str):
    """
    Endpoint for posting a single insight manually.
    
    Args:
        insight_id: Unique insight identifier
    """
    logger.info(f"Manual posting endpoint triggered for insight: {insight_id}")
    
    # Fetch the specific insight
    insights = await posting_service.api_client.get_publishable_insights(limit=100)
    
    # Find the requested insight
    target_insight = None
    for insight in insights:
        if insight.id == insight_id:
            target_insight = insight
            break
    
    if not target_insight:
        raise HTTPException(status_code=404, detail=f"Insight {insight_id} not found or not publishable")
    
    # Post the insight
    result = await posting_service.post_insight(target_insight)
    
    if result.success:
        return {
            "status": "success",
            "insight_id": result.insight_id,
            "tweet_id": result.tweet_id
        }
    else:
        raise HTTPException(status_code=400, detail=result.error)


@app.get("/status/recent-posts")
async def get_recent_posts():
    """
    Get status of recent posts.
    
    Returns information about what has been posted recently.
    """
    last_daily_brief = posting_service.redis_client.get_last_daily_brief_date()
    
    return {
        "last_daily_brief_date": last_daily_brief,
        "duplicate_prevention_window": settings.duplicate_prevention_window,
        "confidence_threshold": settings.confidence_threshold
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
