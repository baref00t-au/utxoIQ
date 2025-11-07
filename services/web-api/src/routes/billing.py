"""Billing and subscription API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ..models import SubscriptionResponse, User
from ..middleware import verify_firebase_token, rate_limit_dependency
from ..services.billing_service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get(
    "/subscription",
    response_model=SubscriptionResponse,
    summary="Get subscription info",
    description="Retrieve current subscription information for the authenticated user"
)
async def get_subscription(
    user: User = Depends(verify_firebase_token),
    _: None = Depends(rate_limit_dependency)
):
    """Get subscription information for the authenticated user."""
    try:
        service = BillingService()
        subscription = await service.get_subscription(user.uid)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        return SubscriptionResponse(subscription=subscription)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription"
        )
