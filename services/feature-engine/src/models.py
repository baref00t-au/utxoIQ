"""
Pydantic models for Feature Engine service
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """Signal type enumeration"""
    MEMPOOL = "mempool"
    EXCHANGE = "exchange"
    MINER = "miner"
    WHALE = "whale"
    PREDICTIVE = "predictive"


class PredictiveSignalType(str, Enum):
    """Predictive signal type enumeration"""
    FEE_FORECAST = "fee_forecast"
    LIQUIDITY_PRESSURE = "liquidity_pressure"


class Signal(BaseModel):
    """Signal data model"""
    type: SignalType
    strength: float = Field(ge=0, le=1)
    data: Dict[str, Any]
    block_height: int = Field(gt=0)
    transaction_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    is_predictive: Optional[bool] = False
    prediction_confidence_interval: Optional[Tuple[float, float]] = None


class MempoolData(BaseModel):
    """Mempool snapshot data"""
    block_height: int
    timestamp: datetime
    transaction_count: int
    total_fees: float
    fee_quantiles: Dict[str, float]  # p10, p25, p50, p75, p90
    avg_fee_rate: float
    mempool_size_bytes: int


class ExchangeFlowData(BaseModel):
    """Exchange flow data"""
    block_height: int
    timestamp: datetime
    entity_id: str
    entity_name: str
    inflow_btc: float
    outflow_btc: float
    net_flow_btc: float
    transaction_count: int
    transaction_ids: List[str]


class MinerTreasuryData(BaseModel):
    """Miner treasury data"""
    block_height: int
    timestamp: datetime
    entity_id: str
    entity_name: str
    balance_btc: float
    daily_change_btc: float
    mining_rewards_btc: float
    transaction_ids: List[str]


class WhaleActivityData(BaseModel):
    """Whale activity data"""
    block_height: int
    timestamp: datetime
    address: str
    balance_btc: float
    seven_day_change_btc: float
    accumulation_streak_days: int
    transaction_ids: List[str]


class PredictiveSignal(BaseModel):
    """Predictive signal data model"""
    type: PredictiveSignalType
    prediction: float
    confidence_interval: Tuple[float, float]
    forecast_horizon: str
    model_version: str


class BlockData(BaseModel):
    """Block data for processing"""
    block_hash: str
    height: int
    timestamp: datetime
    size: int
    tx_count: int
    fees_total: float
