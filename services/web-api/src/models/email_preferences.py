"""Email preferences models."""
from pydantic import BaseModel
from typing import List, Optional
from .insights import SignalType


class EmailFrequency(str):
    """Email frequency type."""
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class QuietHours(BaseModel):
    """Quiet hours configuration."""
    start: str  # HH:MM format
    end: str    # HH:MM format


class EmailPreferences(BaseModel):
    """Email preferences model."""
    user_id: str
    daily_brief_enabled: bool = True
    frequency: str = "daily"
    signal_filters: List[SignalType] = []
    quiet_hours: Optional[QuietHours] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_abc123",
                "daily_brief_enabled": True,
                "frequency": "daily",
                "signal_filters": ["mempool", "exchange"],
                "quiet_hours": {
                    "start": "22:00",
                    "end": "08:00"
                }
            }
        }


class EmailPreferencesUpdate(BaseModel):
    """Email preferences update request."""
    daily_brief_enabled: Optional[bool] = None
    frequency: Optional[str] = None
    signal_filters: Optional[List[SignalType]] = None
    quiet_hours: Optional[QuietHours] = None
