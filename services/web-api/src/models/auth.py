"""Authentication and user models."""
from pydantic import BaseModel
from enum import Enum
from typing import Optional


class UserSubscriptionTier(str, Enum):
    """User subscription tier enumeration."""
    FREE = "free"
    PRO = "pro"
    POWER = "power"
    WHITE_LABEL = "white_label"


class User(BaseModel):
    """User model."""
    uid: str
    email: str
    subscription_tier: UserSubscriptionTier = UserSubscriptionTier.FREE
    api_key: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "uid": "user_abc123",
                "email": "user@example.com",
                "subscription_tier": "pro",
                "api_key": "sk_live_abc123"
            }
        }
