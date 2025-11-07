"""Data models for email service."""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EmailFrequency(str, Enum):
    """Email frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class SignalType(str, Enum):
    """Signal types for filtering."""
    MEMPOOL = "mempool"
    EXCHANGE = "exchange"
    MINER = "miner"
    WHALE = "whale"


class QuietHours(BaseModel):
    """Quiet hours configuration."""
    start: str = Field(..., description="Start time in HH:MM format (UTC)")
    end: str = Field(..., description="End time in HH:MM format (UTC)")


class EmailPreferences(BaseModel):
    """User email preferences."""
    user_id: str
    email: EmailStr
    daily_brief_enabled: bool = True
    frequency: EmailFrequency = EmailFrequency.DAILY
    signal_filters: List[SignalType] = Field(default_factory=list)
    quiet_hours: Optional[QuietHours] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmailPreferencesUpdate(BaseModel):
    """Update email preferences request."""
    daily_brief_enabled: Optional[bool] = None
    frequency: Optional[EmailFrequency] = None
    signal_filters: Optional[List[SignalType]] = None
    quiet_hours: Optional[QuietHours] = None


class Citation(BaseModel):
    """Evidence citation."""
    type: str
    id: str
    description: str
    url: str


class Insight(BaseModel):
    """Insight data model."""
    id: str
    signal_type: str
    headline: str
    summary: str
    confidence: float
    timestamp: datetime
    block_height: int
    evidence: List[Citation] = Field(default_factory=list)
    chart_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DailyBrief(BaseModel):
    """Daily brief data model."""
    date: str
    insights: List[Insight]
    summary: Optional[str] = None


class EmailEvent(str, Enum):
    """Email engagement event types."""
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class EmailEngagement(BaseModel):
    """Email engagement tracking."""
    email_id: str
    user_id: str
    event: EmailEvent
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class UnsubscribeRequest(BaseModel):
    """Unsubscribe request."""
    user_id: str
    reason: Optional[str] = None
