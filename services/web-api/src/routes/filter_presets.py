"""API routes for filter preset management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from src.database import get_db
from src.middleware.auth import get_current_user, get_optional_user
from src.models.auth import User
from src.models.filter_presets import (
    FilterPresetCreate,
    FilterPresetUpdate,
    FilterPresetResponse,
    FilterPresetListResponse
)
from src.services.filter_presets_service import FilterPresetService


router = APIRouter(prefix="/api/v1/filters/presets", tags=["filter-presets"])


@router.post(
    "",
    response_model=FilterPresetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new filter preset"
)
async def create_filter_preset(
    preset_data: FilterPresetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new filter preset for the authenticated user.
    
    Maximum of 10 presets allowed per user.
    """
    try:
        preset = await FilterPresetService.create_preset(
            db=db,
            user_id=current_user.id,
            preset_data=preset_data
        )
        return FilterPresetResponse.model_validate(preset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=FilterPresetListResponse,
    summary="Get all filter presets for current user"
)
async def get_filter_presets(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all filter presets for the authenticated user.
    Returns empty list if not authenticated.
    """
    if not current_user:
        return FilterPresetListResponse(presets=[], total=0)
    
    presets = await FilterPresetService.get_user_presets(
        db=db,
        user_id=current_user.id
    )
    
    return FilterPresetListResponse(
        presets=[FilterPresetResponse.model_validate(p) for p in presets],
        total=len(presets)
    )


@router.get(
    "/{preset_id}",
    response_model=FilterPresetResponse,
    summary="Get a specific filter preset"
)
async def get_filter_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific filter preset by ID.
    """
    preset = await FilterPresetService.get_preset_by_id(
        db=db,
        preset_id=preset_id,
        user_id=current_user.id
    )
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter preset not found"
        )
    
    return FilterPresetResponse.model_validate(preset)


@router.patch(
    "/{preset_id}",
    response_model=FilterPresetResponse,
    summary="Update a filter preset"
)
async def update_filter_preset(
    preset_id: UUID,
    preset_data: FilterPresetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a filter preset's name or filters.
    """
    preset = await FilterPresetService.update_preset(
        db=db,
        preset_id=preset_id,
        user_id=current_user.id,
        preset_data=preset_data
    )
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter preset not found"
        )
    
    return FilterPresetResponse.model_validate(preset)


@router.delete(
    "/{preset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a filter preset"
)
async def delete_filter_preset(
    preset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a filter preset.
    """
    deleted = await FilterPresetService.delete_preset(
        db=db,
        preset_id=preset_id,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter preset not found"
        )
    
    return None
