"""Pydantic models for filter preset API requests and responses."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class FilterState(BaseModel):
    """Filter state structure matching frontend FilterState."""
    search: str = ""
    categories: List[str] = Field(default_factory=list)
    minConfidence: float = Field(ge=0, le=1, default=0)
    dateRange: Optional[dict] = None  # {start: ISO string, end: ISO string}
    
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v):
        """Validate that categories are valid signal types."""
        valid_categories = {'mempool', 'exchange', 'miner', 'whale'}
        for category in v:
            if category not in valid_categories:
                raise ValueError(f"Invalid category: {category}")
        return v


class FilterPresetCreate(BaseModel):
    """Request model for creating a filter preset."""
    name: str = Field(..., min_length=1, max_length=100)
    filters: FilterState


class FilterPresetUpdate(BaseModel):
    """Request model for updating a filter preset."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filters: Optional[FilterState] = None


class FilterPresetResponse(BaseModel):
    """Response model for filter preset."""
    id: UUID
    user_id: UUID
    name: str
    filters: FilterState
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FilterPresetListResponse(BaseModel):
    """Response model for list of filter presets."""
    presets: List[FilterPresetResponse]
    total: int
