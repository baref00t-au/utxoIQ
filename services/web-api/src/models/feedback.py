"""User feedback models."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FeedbackRating(str):
    """Feedback rating type."""
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"


class FeedbackCreate(BaseModel):
    """Feedback creation request."""
    rating: str = Field(pattern="^(useful|not_useful)$")
    comment: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": "useful",
                "comment": "Very accurate prediction"
            }
        }


class UserFeedback(BaseModel):
    """User feedback model."""
    id: str
    insight_id: str
    user_id: str
    rating: str
    timestamp: datetime
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""
    feedback: UserFeedback
    message: str = "Feedback submitted successfully"
