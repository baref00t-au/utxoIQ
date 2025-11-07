"""
Pydantic models for Chart Renderer Service
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """Signal type enumeration"""
    MEMPOOL = "mempool"
    EXCHANGE = "exchange"
    MINER = "miner"
    WHALE = "whale"
    PREDICTIVE = "predictive"


class ChartSize(str, Enum):
    """Chart size enumeration"""
    MOBILE = "mobile"
    DESKTOP = "desktop"


class MempoolChartRequest(BaseModel):
    """Request model for mempool chart generation"""
    block_height: int = Field(gt=0)
    timestamp: datetime
    fee_quantiles: Dict[str, float] = Field(
        description="Fee quantiles: p10, p25, p50, p75, p90"
    )
    avg_fee_rate: float = Field(gt=0)
    transaction_count: int = Field(gt=0)
    size: ChartSize = ChartSize.DESKTOP


class ExchangeChartRequest(BaseModel):
    """Request model for exchange flow chart generation"""
    entity_name: str
    timestamps: List[datetime] = Field(min_length=1)
    inflows: List[float] = Field(min_length=1)
    outflows: List[float] = Field(min_length=1)
    net_flows: List[float] = Field(min_length=1)
    spike_threshold: Optional[float] = None
    size: ChartSize = ChartSize.DESKTOP


class MinerChartRequest(BaseModel):
    """Request model for miner treasury chart generation"""
    entity_name: str
    timestamps: List[datetime] = Field(min_length=1)
    balances: List[float] = Field(min_length=1)
    daily_changes: List[float] = Field(min_length=1)
    size: ChartSize = ChartSize.DESKTOP


class WhaleChartRequest(BaseModel):
    """Request model for whale accumulation chart generation"""
    address: str
    timestamps: List[datetime] = Field(min_length=1)
    balances: List[float] = Field(min_length=1)
    seven_day_changes: List[float] = Field(min_length=1)
    accumulation_streak_days: int = Field(ge=0)
    size: ChartSize = ChartSize.DESKTOP


class PredictiveChartRequest(BaseModel):
    """Request model for predictive signal chart generation"""
    signal_type: str
    timestamps: List[datetime] = Field(min_length=1)
    historical_values: List[float] = Field(min_length=1)
    predicted_values: List[float] = Field(min_length=1)
    confidence_intervals: List[Tuple[float, float]] = Field(min_length=1)
    forecast_horizon: str
    size: ChartSize = ChartSize.DESKTOP


class ChartResponse(BaseModel):
    """Response model for chart generation"""
    chart_url: str = Field(description="GCS signed URL for the chart image")
    chart_path: str = Field(description="GCS path to the chart")
    width: int
    height: int
    size_bytes: int
