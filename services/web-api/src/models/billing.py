"""Billing and subscription models."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .auth import UserSubscriptionTier


class SubscriptionInfo(BaseModel):
    """Subscription information."""
    user_id: str
    tier: UserSubscriptionTier
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    subscription: SubscriptionInfo
    
    class Config:
        json_schema_extra = {
            "example": {
                "subscription": {
                    "user_id": "user_abc123",
                    "tier": "pro",
                    "stripe_customer_id": "cus_abc123",
                    "stripe_subscription_id": "sub_abc123",
                    "current_period_end": "2025-12-07T10:30:00Z",
                    "cancel_at_period_end": False
                }
            }
        }
