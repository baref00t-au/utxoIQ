"""Authentication and user models."""
from pydantic import BaseModel, EmailStr, ConfigDict
from enum import Enum
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class UserSubscriptionTier(str, Enum):
    """User subscription tier enumeration."""
    FREE = "free"
    PRO = "pro"
    POWER = "power"
    WHITE_LABEL = "white_label"


class Role(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    SERVICE = "service"


class User(BaseModel):
    """User model (legacy - for backward compatibility)."""
    uid: str
    email: str
    subscription_tier: UserSubscriptionTier = UserSubscriptionTier.FREE
    api_key: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "uid": "user_abc123",
                "email": "user@example.com",
                "subscription_tier": "pro",
                "api_key": "sk_live_abc123"
            }
        }
    )


class UserProfile(BaseModel):
    """User profile response model."""
    id: UUID
    email: EmailStr
    display_name: Optional[str] = None
    role: str
    subscription_tier: str
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "display_name": "John Doe",
                "role": "user",
                "subscription_tier": "pro",
                "created_at": "2024-01-10T10:00:00Z",
                "last_login_at": "2024-01-10T12:00:00Z"
            }
        }
    )


class UserUpdate(BaseModel):
    """User profile update request model."""
    display_name: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "John Doe"
            }
        }
    )


class SubscriptionTierUpdate(BaseModel):
    """Subscription tier update request model (admin only)."""
    subscription_tier: UserSubscriptionTier
    reason: Optional[str] = "manual_update"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subscription_tier": "pro",
                "reason": "admin_override"
            }
        }
    )


class APIKeyCreate(BaseModel):
    """API key creation request model."""
    name: str
    scopes: List[str] = []
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Production API Key",
                "scopes": ["insights:read", "alerts:write"]
            }
        }
    )


class APIKeyResponse(BaseModel):
    """API key response model (without secret)."""
    id: UUID
    key_prefix: str
    name: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "key_prefix": "sk_live_",
                "name": "Production API Key",
                "scopes": ["insights:read", "alerts:write"],
                "created_at": "2024-01-10T10:00:00Z",
                "last_used_at": "2024-01-10T12:00:00Z"
            }
        }
    )


class APIKeyWithSecret(APIKeyResponse):
    """API key response model with secret (only returned on creation)."""
    key: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "key_prefix": "sk_live_",
                "name": "Production API Key",
                "scopes": ["insights:read", "alerts:write"],
                "created_at": "2024-01-10T10:00:00Z",
                "last_used_at": None,
                "key": "sk_live_abc123def456ghi789"
            }
        }
    )
