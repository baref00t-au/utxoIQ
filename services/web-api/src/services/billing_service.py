"""Billing service."""
import logging
from typing import Optional
from ..models import SubscriptionInfo, UserSubscriptionTier

logger = logging.getLogger(__name__)


class BillingService:
    """Service for managing billing and subscriptions."""
    
    async def get_subscription(self, user_id: str) -> Optional[SubscriptionInfo]:
        """Get subscription information for a user."""
        # TODO: Implement database query and Stripe integration
        logger.info(f"Fetching subscription for user {user_id}")
        return SubscriptionInfo(
            user_id=user_id,
            tier=UserSubscriptionTier.FREE
        )
