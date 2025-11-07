"""User feedback API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ..models import FeedbackCreate, FeedbackResponse, User
from ..middleware import verify_firebase_token, rate_limit_dependency
from ..services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["feedback"])


@router.post(
    "/{insight_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback",
    description="Submit user feedback (useful/not useful) for an insight"
)
async def submit_feedback(
    insight_id: str,
    feedback_data: FeedbackCreate,
    user: User = Depends(verify_firebase_token),
    _: None = Depends(rate_limit_dependency)
):
    """Submit feedback for an insight."""
    try:
        service = FeedbackService()
        feedback = await service.create_feedback(insight_id, user.uid, feedback_data)
        return FeedbackResponse(feedback=feedback)
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )
