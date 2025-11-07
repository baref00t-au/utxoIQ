"""Data models for X Bot service."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """Signal type enumeration."""
    MEMPOOL = "mempool"
    EXCHANGE = "exchange"
    MINER = "miner"
    WHALE = "whale"


class Citation(BaseModel):
    """Evidence citation model."""
    type: str
    id: str
    description: str
    url: str


class Insight(BaseModel):
    """Insight model from Web API."""
    id: str
    signal_type: SignalType
    headline: str
    summary: str
    confidence: float = Field(ge=0, le=1)
    timestamp: datetime
    block_height: int
    evidence: List[Citation] = []
    chart_url: Optional[str] = None
    tags: List[str] = []
    is_predictive: bool = False


class TweetData(BaseModel):
    """Tweet composition data."""
    text: str
    media_ids: List[str] = []
    insight_id: str
    signal_type: SignalType


class PostResult(BaseModel):
    """Result of posting a tweet."""
    success: bool
    tweet_id: Optional[str] = None
    error: Optional[str] = None
    insight_id: str


class DailyBrief(BaseModel):
    """Daily brief summary model."""
    date: str
    top_insights: List[Insight]
    summary: str
