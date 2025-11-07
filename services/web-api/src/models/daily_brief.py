"""Daily brief models."""
from pydantic import BaseModel
from typing import List
from datetime import date
from .insights import Insight


class DailyBrief(BaseModel):
    """Daily brief model."""
    date: date
    top_insights: List[Insight]
    summary: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-07",
                "top_insights": [],
                "summary": "Top 3 blockchain events from the past 24 hours"
            }
        }


class DailyBriefResponse(BaseModel):
    """Daily brief response."""
    brief: DailyBrief
