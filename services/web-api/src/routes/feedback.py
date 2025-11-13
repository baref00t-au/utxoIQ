"""
User feedback endpoints for insights and signals
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import logging

from src.services.database_service import DatabaseService
from src.services.cache_service import CacheService
from src.models.database_schemas import FeedbackCreate, FeedbackResponse, FeedbackStats
from src.services.database_exceptions import ValidationError, DatabaseError
from src.middleware import get_current_user, rate_limit_dependency
from src.models.db_models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


class FeedbackType(str, Enum):
    """Type of feedback"""
    RATING = "rating"
    COMMENT = "comment"
    FLAG = "flag"


class FlagReason(str, Enum):
    """Reason for flagging content"""
    INACCURATE = "inaccurate"
    MISLEADING = "misleading"
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    OTHER = "other"


class InsightFeedback(BaseModel):
    """Feedback on an insight"""
    insight_id: str
    user_id: str
    feedback_type: FeedbackType
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    flag_reason: Optional[FlagReason] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


@router.post("/rate", response_model=FeedbackResponse)
async def rate_insight(
    insight_id: str = Body(...),
    rating: int = Body(..., ge=1, le=5),
    comment: Optional[str] = Body(None, max_length=1000),
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """
    Rate an insight (1-5 stars) with optional comment.
    Stores in database and invalidates cache.
    
    Requires authentication.
    
    Args:
        insight_id: Insight identifier
        rating: Rating value (1-5)
        comment: Optional comment text
        user: Authenticated user (from token)
    
    Returns:
        Created or updated feedback
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        feedback_data = FeedbackCreate(
            insight_id=insight_id,
            user_id=str(user.id),
            rating=rating,
            comment=comment
        )
        
        async with DatabaseService() as db:
            feedback = await db.create_feedback(feedback_data)
        
        # Invalidate feedback stats cache
        async with CacheService() as cache:
            await cache.invalidate_feedback_cache(insight_id)
        
        logger.info(f"User {user.id} rated insight {insight_id} with {rating} stars")
        return feedback
    except ValidationError as e:
        logger.error(f"Validation error rating insight: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error rating insight: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit rating")


@router.post("/comment", response_model=FeedbackResponse)
async def comment_on_insight(
    insight_id: str = Body(...),
    comment: str = Body(..., min_length=1, max_length=1000),
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """
    Add a comment to an insight.
    Stores in database.
    
    Requires authentication.
    
    Args:
        insight_id: Insight identifier
        comment: Comment text
        user: Authenticated user (from token)
    
    Returns:
        Created or updated feedback
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        feedback_data = FeedbackCreate(
            insight_id=insight_id,
            user_id=str(user.id),
            comment=comment
        )
        
        async with DatabaseService() as db:
            feedback = await db.create_feedback(feedback_data)
        
        # Invalidate feedback stats cache (comment count changed)
        async with CacheService() as cache:
            await cache.invalidate_feedback_cache(insight_id)
        
        logger.info(f"User {user.id} commented on insight {insight_id}")
        return feedback
    except ValidationError as e:
        logger.error(f"Validation error adding comment: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error adding comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.post("/flag", response_model=FeedbackResponse)
async def flag_insight(
    insight_id: str = Body(...),
    flag_type: str = Body(..., pattern="^(inaccurate|misleading|spam)$"),
    flag_reason: Optional[str] = Body(None, max_length=500),
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """
    Flag an insight for review.
    Stores flag in database.
    
    Requires authentication.
    
    Args:
        insight_id: Insight identifier
        flag_type: Type of flag
        flag_reason: Optional reason details
        user: Authenticated user (from token)
    
    Returns:
        Created or updated feedback
    
    Raises:
        HTTPException: If operation fails
    """
    try:
        feedback_data = FeedbackCreate(
            insight_id=insight_id,
            user_id=str(user.id),
            flag_type=flag_type,
            flag_reason=flag_reason
        )
        
        async with DatabaseService() as db:
            feedback = await db.create_feedback(feedback_data)
        
        # Invalidate feedback stats cache (flag count changed)
        async with CacheService() as cache:
            await cache.invalidate_feedback_cache(insight_id)
        
        logger.warning(f"User {user.id} flagged insight {insight_id} as {flag_type}")
        return feedback
    except ValidationError as e:
        logger.error(f"Validation error flagging insight: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error flagging insight: {e}")
        raise HTTPException(status_code=500, detail="Failed to flag insight")


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(insight_id: str = Query(...)):
    """
    Get aggregated feedback statistics for an insight.
    Uses cached aggregations with 1-hour TTL.
    
    Args:
        insight_id: Insight identifier
    
    Returns:
        Aggregated feedback statistics
    
    Raises:
        HTTPException: If query fails
    """
    try:
        # Try cache first
        async with CacheService() as cache:
            cached_stats = await cache.get_feedback_stats(insight_id)
            if cached_stats:
                logger.debug(f"Cache hit for feedback stats: {insight_id}")
                return cached_stats
        
        # Query database
        async with DatabaseService() as db:
            stats = await db.get_feedback_stats(insight_id)
        
        # Cache the result
        async with CacheService() as cache:
            await cache.cache_feedback_stats(insight_id, stats)
        
        logger.debug(f"Retrieved feedback stats for insight {insight_id} from database")
        return stats
    except DatabaseError as e:
        logger.error(f"Database error retrieving feedback stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback statistics")


@router.get("/comments")
async def get_insight_comments(
    insight_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get comments for an insight with pagination.
    
    Args:
        insight_id: Insight identifier
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        List of comments with pagination info
    
    Raises:
        HTTPException: If query fails
    """
    try:
        async with DatabaseService() as db:
            feedbacks = await db.list_feedback(
                insight_id=insight_id,
                limit=limit,
                offset=offset
            )
            
            # Filter to only comments
            comments = [
                {
                    "id": str(fb.id),
                    "user_id": fb.user_id,
                    "comment": fb.comment,
                    "created_at": fb.created_at.isoformat(),
                    "updated_at": fb.updated_at.isoformat()
                }
                for fb in feedbacks if fb.comment
            ]
            
            return {
                "insight_id": insight_id,
                "comments": comments,
                "total": len(comments),
                "limit": limit,
                "offset": offset
            }
    except DatabaseError as e:
        logger.error(f"Database error retrieving comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comments")


@router.get("/user")
async def get_user_feedback(
    user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get user's feedback history with pagination.
    
    Requires authentication. Users can only view their own feedback.
    
    Args:
        user: Authenticated user (from token)
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        List of user's feedback with pagination info
    
    Raises:
        HTTPException: If query fails
    """
    try:
        async with DatabaseService() as db:
            feedbacks = await db.list_feedback(
                user_id=str(user.id),
                limit=limit,
                offset=offset
            )
            
            return {
                "user_id": str(user.id),
                "feedback": [
                    {
                        "id": str(fb.id),
                        "insight_id": fb.insight_id,
                        "rating": fb.rating,
                        "comment": fb.comment,
                        "flag_type": fb.flag_type,
                        "created_at": fb.created_at.isoformat(),
                        "updated_at": fb.updated_at.isoformat()
                    }
                    for fb in feedbacks
                ],
                "total": len(feedbacks),
                "limit": limit,
                "offset": offset
            }
    except DatabaseError as e:
        logger.error(f"Database error retrieving user feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user feedback")
