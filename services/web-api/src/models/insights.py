"""Insight data models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """Signal type enumeration."""
    MEMPOOL = "mempool"
    EXCHANGE = "exchange"
    MINER = "miner"
    WHALE = "whale"
    PREDICTIVE = "predictive"


class CitationType(str, Enum):
    """Citation type enumeration."""
    BLOCK = "block"
    TRANSACTION = "transaction"
    ADDRESS = "address"


class Citation(BaseModel):
    """Evidence citation model."""
    type: CitationType
    id: str
    description: str
    url: str


class ExplainabilitySummary(BaseModel):
    """Explainability summary for confidence scores."""
    confidence_factors: dict = Field(
        description="Breakdown of confidence score factors",
        example={
            "signal_strength": 0.85,
            "historical_accuracy": 0.78,
            "data_quality": 0.92
        }
    )
    explanation: str = Field(
        description="Human-readable explanation of confidence score"
    )
    supporting_evidence: List[str] = Field(
        description="List of supporting evidence points"
    )


class Insight(BaseModel):
    """Insight data model."""
    id: str
    signal_type: SignalType
    headline: str = Field(max_length=280)
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    block_height: int
    evidence: List[Citation]
    chart_url: Optional[str] = None
    tags: List[str] = []
    explainability: Optional[ExplainabilitySummary] = None
    accuracy_rating: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_predictive: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "insight_abc123",
                "signal_type": "mempool",
                "headline": "Mempool fees spike to 50 sat/vB as demand surges",
                "summary": "Transaction fees have increased significantly...",
                "confidence": 0.85,
                "timestamp": "2025-11-07T10:30:00Z",
                "block_height": 820000,
                "evidence": [
                    {
                        "type": "block",
                        "id": "820000",
                        "description": "Block 820000",
                        "url": "https://blockstream.info/block/820000"
                    }
                ],
                "chart_url": "https://storage.googleapis.com/charts/insight_abc123.png",
                "tags": ["fees", "mempool"],
                "explainability": {
                    "confidence_factors": {
                        "signal_strength": 0.85,
                        "historical_accuracy": 0.78,
                        "data_quality": 0.92
                    },
                    "explanation": "High confidence due to strong signal...",
                    "supporting_evidence": ["Historical pattern match", "Data quality verified"]
                },
                "accuracy_rating": 0.82,
                "is_predictive": False
            }
        }


class InsightResponse(BaseModel):
    """Single insight response."""
    insight: Insight


class InsightListResponse(BaseModel):
    """List of insights response."""
    insights: List[Insight]
    total: int
    page: int
    page_size: int
    has_more: bool
