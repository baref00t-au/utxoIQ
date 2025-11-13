"""AI chat API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ..models import ChatQuery, ChatResponse, User, UserSubscriptionTier
from ..middleware import get_current_user, require_subscription_tier, rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/query",
    response_model=ChatResponse,
    summary="Submit chat query",
    description="Ask natural language questions about Bitcoin blockchain data (Pro/Power tier required)"
)
async def submit_chat_query(
    query: ChatQuery,
    user: User = Depends(require_subscription_tier(UserSubscriptionTier.PRO)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Submit a natural language query about blockchain data.
    
    Requires Pro or Power subscription tier.
    Power tier users get unlimited queries.
    """
    try:
        # TODO: Implement Vertex AI integration for chat
        logger.info(f"Chat query from {user.uid}: {query.query}")
        
        # Placeholder response
        return ChatResponse(
            response="Chat functionality coming soon",
            citations=[],
            confidence=None
        )
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )
