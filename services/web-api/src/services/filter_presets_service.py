"""Service layer for filter preset operations."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.db_models import FilterPreset
from src.models.filter_presets import FilterPresetCreate, FilterPresetUpdate


class FilterPresetService:
    """Service for managing filter presets."""
    
    MAX_PRESETS_PER_USER = 10
    
    @staticmethod
    async def create_preset(
        db: Session,
        user_id: UUID,
        preset_data: FilterPresetCreate
    ) -> FilterPreset:
        """Create a new filter preset for a user.
        
        Args:
            db: Database session
            user_id: User ID
            preset_data: Preset creation data
            
        Returns:
            Created FilterPreset instance
            
        Raises:
            ValueError: If user has reached maximum preset limit
        """
        # Check if user has reached the limit
        preset_count = db.query(func.count(FilterPreset.id)).filter(
            FilterPreset.user_id == user_id
        ).scalar()
        
        if preset_count >= FilterPresetService.MAX_PRESETS_PER_USER:
            raise ValueError(
                f"Maximum of {FilterPresetService.MAX_PRESETS_PER_USER} presets allowed per user"
            )
        
        # Create new preset
        preset = FilterPreset(
            user_id=user_id,
            name=preset_data.name,
            filters=preset_data.filters.model_dump()
        )
        
        db.add(preset)
        db.commit()
        db.refresh(preset)
        
        return preset
    
    @staticmethod
    async def get_user_presets(
        db: Session,
        user_id: UUID
    ) -> List[FilterPreset]:
        """Get all filter presets for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of FilterPreset instances
        """
        return db.query(FilterPreset).filter(
            FilterPreset.user_id == user_id
        ).order_by(FilterPreset.created_at.desc()).all()
    
    @staticmethod
    async def get_preset_by_id(
        db: Session,
        preset_id: UUID,
        user_id: UUID
    ) -> Optional[FilterPreset]:
        """Get a specific filter preset by ID.
        
        Args:
            db: Database session
            preset_id: Preset ID
            user_id: User ID (for authorization)
            
        Returns:
            FilterPreset instance or None if not found
        """
        return db.query(FilterPreset).filter(
            FilterPreset.id == preset_id,
            FilterPreset.user_id == user_id
        ).first()
    
    @staticmethod
    async def update_preset(
        db: Session,
        preset_id: UUID,
        user_id: UUID,
        preset_data: FilterPresetUpdate
    ) -> Optional[FilterPreset]:
        """Update a filter preset.
        
        Args:
            db: Database session
            preset_id: Preset ID
            user_id: User ID (for authorization)
            preset_data: Preset update data
            
        Returns:
            Updated FilterPreset instance or None if not found
        """
        preset = await FilterPresetService.get_preset_by_id(db, preset_id, user_id)
        
        if not preset:
            return None
        
        # Update fields if provided
        if preset_data.name is not None:
            preset.name = preset_data.name
        
        if preset_data.filters is not None:
            preset.filters = preset_data.filters.model_dump()
        
        db.commit()
        db.refresh(preset)
        
        return preset
    
    @staticmethod
    async def delete_preset(
        db: Session,
        preset_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a filter preset.
        
        Args:
            db: Database session
            preset_id: Preset ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        preset = await FilterPresetService.get_preset_by_id(db, preset_id, user_id)
        
        if not preset:
            return False
        
        db.delete(preset)
        db.commit()
        
        return True
