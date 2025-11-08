"""
User feedback endpoints for insights and signals
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

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


class FeedbackStats(BaseModel):
    """Aggregated feedback statistics"""
    insight_id: str
    total_ratings: int
    avg_rating: float
    rating_distribution: dict
    total_comments: int
    total_flags: int
    flag_reasons: dict


class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    success: bool
    feedback_id: str
    message: str


@router.post("/insights/{insight_id}/rate", response_model=FeedbackResponse)
async def rate_insight(
    insight_id: str,
    rating: int = Field(..., ge=1, le=5),
    comment: Optional[str] = None,
    # user_id: str = Depends(get_current_user)  # TODO: Add auth
):
    """
    Rate an insight (1-5 stars) with optional comment
    """
    # TODO: Validate insight exists
    # TODO: Store in database
    # TODO: Update insight rating cache
    
    feedback_id = f"fb_{insight_id}_{datetime.utcnow().timestamp()}"
    
    return FeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        message="Thank you for your feedback!"
    )


@router.post("/insights/{insight_id}/comment", response_model=FeedbackResponse)
async def comment_on_insight(
    insight_id: str,
    comment: str = Field(..., min_length=1, max_length=1000),
    # user_id: str = Depends(get_current_user)
):
    """
    Add a comment to an insight
    """
    # TODO: Validate insight exists
    # TODO: Store in database
    # TODO: Moderate content
    
    feedback_id = f"fb_{insight_id}_{datetime.utcnow().timestamp()}"
    
    return FeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        message="Comment added successfully"
    )


@router.post("/insights/{insight_id}/flag", response_model=FeedbackResponse)
async def flag_insight(
    insight_id: str,
    reason: FlagReason,
    details: Optional[str] = Field(None, max_length=500),
    # user_id: str = Depends(get_current_user)
):
    """
    Flag an insight for review
    """
    # TODO: Validate insight exists
    # TODO: Store flag in database
    # TODO: Trigger review workflow if threshold reached
    
    feedback_id = f"flag_{insight_id}_{datetime.utcnow().timestamp()}"
    
    return FeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        message="Thank you for reporting this. We'll review it shortly."
    )


@router.get("/insights/{insight_id}/stats", response_model=FeedbackStats)
async def get_insight_feedback_stats(insight_id: str):
    """
    Get aggregated feedback statistics for an insight
    """
    # TODO: Query from database
    return FeedbackStats(
        insight_id=insight_id,
        total_ratings=42,
        avg_rating=4.2,
        rating_distribution={
            "1": 2,
            "2": 3,
            "3": 8,
            "4": 15,
            "5": 14
        },
        total_comments=12,
        total_flags=1,
        flag_reasons={
            "inaccurate": 1
        }
    )


@router.get("/insights/{insight_id}/comments")
async def get_insight_comments(
    insight_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    Get comments for an insight
    """
    # TODO: Query from database with pagination
    return {
        "insight_id": insight_id,
        "comments": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/user/feedback")
async def get_user_feedback(
    # user_id: str = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    Get user's feedback history
    """
    # TODO: Query from database
    return {
        "feedback": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }
