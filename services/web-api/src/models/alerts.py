"""Alert data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .insights import SignalType


class AlertOperator(str):
    """Alert operator type."""
    GT = "gt"
    LT = "lt"
    EQ = "eq"


class AlertCreate(BaseModel):
    """Alert creation request."""
    signal_type: SignalType
    threshold: float
    operator: str = Field(pattern="^(gt|lt|eq)$")
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "signal_type": "mempool",
                "threshold": 50.0,
                "operator": "gt",
                "is_active": True
            }
        }


class AlertUpdate(BaseModel):
    """Alert update request."""
    threshold: Optional[float] = None
    operator: Optional[str] = Field(None, pattern="^(gt|lt|eq)$")
    is_active: Optional[bool] = None


class Alert(BaseModel):
    """Alert data model."""
    id: str
    user_id: str
    signal_type: SignalType
    threshold: float
    operator: str
    is_active: bool
    created_at: datetime
    last_triggered: Optional[datetime] = None


class AlertResponse(BaseModel):
    """Alert response."""
    alert: Alert
