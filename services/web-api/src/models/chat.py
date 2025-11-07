"""Chat query models."""
from pydantic import BaseModel, Field
from typing import List, Optional


class ChatQuery(BaseModel):
    """Chat query request."""
    query: str = Field(min_length=1, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the current mempool fee rate?"
            }
        }


class ChatCitation(BaseModel):
    """Chat response citation."""
    type: str
    id: str
    description: str


class ChatResponse(BaseModel):
    """Chat query response."""
    response: str
    citations: List[ChatCitation] = []
    confidence: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The current mempool fee rate is approximately 25 sat/vB...",
                "citations": [
                    {
                        "type": "block",
                        "id": "820000",
                        "description": "Latest block data"
                    }
                ],
                "confidence": 0.85
            }
        }
