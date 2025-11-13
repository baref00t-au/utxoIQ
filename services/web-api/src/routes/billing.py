"""Billing and subscription API routes."""
import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..models import SubscriptionResponse, User
from ..middleware import verify_firebase_token, rate_limit_dependency
from ..services.billing_service import BillingService
from ..services.user_service import UserService
from ..database import get_db
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


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


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events for subscription management.
    
    This endpoint receives webhook events from Stripe and automatically updates
    user subscription tiers based on payment events. Supported events:
    - subscription.created: New subscription created
    - subscription.updated: Subscription tier changed
    - subscription.deleted: Subscription cancelled
    - customer.subscription.trial_will_end: Trial ending soon
    
    Args:
        request: FastAPI request object with webhook payload
        stripe_signature: Stripe signature header for verification
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 400 if signature verification fails
    """
    if not stripe_signature:
        logger.warning("Stripe webhook received without signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    # Get raw request body
    payload = await request.body()
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid Stripe webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe webhook signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Handle the event
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Received Stripe webhook event: {event_type}")
    
    try:
        if event_type == "customer.subscription.created":
            await handle_subscription_created(db, event_data)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(db, event_data)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(db, event_data)
        elif event_type == "customer.subscription.trial_will_end":
            logger.info(f"Trial ending soon for customer {event_data.get('customer')}")
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
    
    except Exception as e:
        logger.error(f"Error processing Stripe webhook {event_type}: {e}", exc_info=True)
        # Return 200 to acknowledge receipt even if processing fails
        # Stripe will retry failed webhooks
    
    return {"status": "success"}


async def handle_subscription_created(db: AsyncSession, subscription_data: dict):
    """
    Handle subscription.created event.
    
    Updates user subscription tier when a new subscription is created.
    Supports trial periods by checking subscription status.
    
    Args:
        db: Database session
        subscription_data: Stripe subscription object data
    """
    customer_id = subscription_data.get("customer")
    status_value = subscription_data.get("status")
    
    # Get subscription tier from metadata or price
    metadata = subscription_data.get("metadata", {})
    tier = metadata.get("tier", "pro")  # Default to pro if not specified
    
    # Find user by Stripe customer ID
    from sqlalchemy import select
    from ..models.db_models import User as DBUser
    
    result = await db.execute(
        select(DBUser).where(DBUser.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User not found for Stripe customer {customer_id}")
        return
    
    # Update subscription tier if subscription is active or in trial
    if status_value in ["active", "trialing"]:
        await UserService.update_subscription_tier(
            db=db,
            user=user,
            tier=tier,
            reason="stripe_subscription_created"
        )
        logger.info(f"Updated user {user.id} to {tier} tier (subscription created, status: {status_value})")


async def handle_subscription_updated(db: AsyncSession, subscription_data: dict):
    """
    Handle subscription.updated event.
    
    Updates user subscription tier when subscription changes, including:
    - Tier upgrades/downgrades
    - Trial period transitions to active
    - Subscription cancellations
    
    Args:
        db: Database session
        subscription_data: Stripe subscription object data
    """
    customer_id = subscription_data.get("customer")
    status_value = subscription_data.get("status")
    
    # Get subscription tier from metadata or price
    metadata = subscription_data.get("metadata", {})
    tier = metadata.get("tier", "pro")
    
    # Find user by Stripe customer ID
    from sqlalchemy import select
    from ..models.db_models import User as DBUser
    
    result = await db.execute(
        select(DBUser).where(DBUser.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User not found for Stripe customer {customer_id}")
        return
    
    # Update subscription tier based on status
    if status_value in ["active", "trialing"]:
        # Active subscription or trial period - upgrade to paid tier
        await UserService.update_subscription_tier(
            db=db,
            user=user,
            tier=tier,
            reason="stripe_subscription_updated"
        )
        logger.info(f"Updated user {user.id} to {tier} tier (subscription updated, status: {status_value})")
    elif status_value in ["canceled", "unpaid", "past_due"]:
        # Subscription cancelled or payment failed - downgrade to free tier
        await UserService.update_subscription_tier(
            db=db,
            user=user,
            tier="free",
            reason=f"stripe_subscription_{status_value}"
        )
        logger.info(f"Downgraded user {user.id} to free tier (subscription {status_value})")


async def handle_subscription_deleted(db: AsyncSession, subscription_data: dict):
    """
    Handle subscription.deleted event.
    
    Downgrades user to free tier when subscription is cancelled.
    
    Args:
        db: Database session
        subscription_data: Stripe subscription object data
    """
    customer_id = subscription_data.get("customer")
    
    # Find user by Stripe customer ID
    from sqlalchemy import select
    from ..models.db_models import User as DBUser
    
    result = await db.execute(
        select(DBUser).where(DBUser.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User not found for Stripe customer {customer_id}")
        return
    
    # Downgrade to free tier on subscription cancellation
    await UserService.update_subscription_tier(
        db=db,
        user=user,
        tier="free",
        reason="stripe_subscription_deleted"
    )
    logger.info(f"Downgraded user {user.id} to free tier (subscription deleted)")
