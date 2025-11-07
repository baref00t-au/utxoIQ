"""Data models for utxoIQ SDK."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Evidence citation for an insight."""
    type: str
    id: str
    description: str
    url: str


class ExplainabilitySummary(BaseModel):
    """Explainability information for confidence scores."""
    confidence_factors: Dict[str, float]
    explanation: str
    supporting_evidence: List[str]


class Insight(BaseModel):
    """Bitcoin blockchain insight."""
    id: str
    signal_type: str
    headline: str
    summary: str
    confidence: float
    timestamp: datetime
    block_height: int
    evidence: List[Citation]
    chart_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    explainability: Optional[ExplainabilitySummary] = None
    accuracy_rating: Optional[float] = None
    is_predictive: bool = False


class Alert(BaseModel):
    """User alert configuration."""
    id: str
    user_id: str
    signal_type: str
    threshold: float
    operator: str
    is_active: bool
    created_at: datetime
    notification_channel: Optional[str] = None


class DailyBrief(BaseModel):
    """Daily brief summary."""
    date: str
    insights: List[Insight]
    summary: str
    created_at: datetime


class ChatResponse(BaseModel):
    """AI chat query response."""
    answer: str
    citations: List[Citation]
    confidence: float
    timestamp: datetime


class UserFeedback(BaseModel):
    """User feedback on insight."""
    insight_id: str
    user_id: str
    rating: str
    timestamp: datetime
    comment: Optional[str] = None


class AccuracyLeaderboard(BaseModel):
    """Model accuracy leaderboard entry."""
    model_version: str
    accuracy_rating: float
    total_ratings: int
    useful_count: int
    not_useful_count: int


class Subscription(BaseModel):
    """User subscription information."""
    user_id: str
    tier: str
    status: str
    current_period_end: datetime
    cancel_at_period_end: bool


class EmailPreferences(BaseModel):
    """User email preferences."""
    user_id: str
    daily_brief_enabled: bool
    frequency: str
    signal_filters: List[str]
    quiet_hours: Optional[Dict[str, str]] = None
