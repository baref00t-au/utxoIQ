"""API routes for bookmark management."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from src.database import get_db
from src.services.bookmark_service import BookmarkService
from src.middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])


# Request/Response models

class BookmarkCreate(BaseModel):
    """Request model for creating a bookmark."""
    insight_id: str = Field(..., description="ID of the insight to bookmark")
    folder_id: Optional[UUID] = Field(None, description="Optional folder ID to organize bookmark")
    note: Optional[str] = Field(None, max_length=1000, description="Optional note about the bookmark")


class BookmarkUpdate(BaseModel):
    """Request model for updating a bookmark."""
    folder_id: Optional[UUID] = Field(None, description="Folder ID to move bookmark to")
    note: Optional[str] = Field(None, max_length=1000, description="Note about the bookmark")


class BookmarkResponse(BaseModel):
    """Response model for a bookmark."""
    id: UUID
    user_id: UUID
    insight_id: str
    folder_id: Optional[UUID]
    note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookmarkCheckResponse(BaseModel):
    """Response model for bookmark existence check."""
    exists: bool
    bookmark_id: Optional[UUID] = None


class FolderCreate(BaseModel):
    """Request model for creating a folder."""
    name: str = Field(..., min_length=1, max_length=100, description="Folder name")


class FolderUpdate(BaseModel):
    """Request model for updating a folder."""
    name: str = Field(..., min_length=1, max_length=100, description="New folder name")


class FolderResponse(BaseModel):
    """Response model for a folder."""
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    bookmark_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Bookmark endpoints

@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bookmark for an insight."""
    service = BookmarkService(db)
    bookmark = service.create_bookmark(
        user_id=UUID(current_user["uid"]),
        insight_id=bookmark_data.insight_id,
        folder_id=bookmark_data.folder_id,
        note=bookmark_data.note
    )
    return bookmark


@router.get("", response_model=List[BookmarkResponse])
async def get_bookmarks(
    folder_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookmarks for the current user, optionally filtered by folder."""
    service = BookmarkService(db)
    bookmarks = service.get_user_bookmarks(
        user_id=UUID(current_user["uid"]),
        folder_id=folder_id,
        limit=limit,
        offset=offset
    )
    return bookmarks


@router.get("/check/{insight_id}", response_model=BookmarkCheckResponse)
async def check_bookmark(
    insight_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a bookmark exists for an insight."""
    from src.models.db_models import Bookmark
    
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == UUID(current_user["uid"]),
        Bookmark.insight_id == insight_id
    ).first()
    
    exists = bookmark is not None
    bookmark_id = bookmark.id if bookmark else None
    
    return BookmarkCheckResponse(exists=exists, bookmark_id=bookmark_id)


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific bookmark by ID."""
    service = BookmarkService(db)
    bookmark = service.get_bookmark(bookmark_id, UUID(current_user["uid"]))
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    return bookmark


@router.patch("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: UUID,
    bookmark_data: BookmarkUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a bookmark's folder or note."""
    service = BookmarkService(db)
    bookmark = service.update_bookmark(
        bookmark_id=bookmark_id,
        user_id=UUID(current_user["uid"]),
        folder_id=bookmark_data.folder_id,
        note=bookmark_data.note
    )
    return bookmark


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bookmark."""
    service = BookmarkService(db)
    service.delete_bookmark(bookmark_id, UUID(current_user["uid"]))
    return None


# Folder endpoints

@router.post("/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    folder_data: FolderCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bookmark folder."""
    service = BookmarkService(db)
    folder = service.create_folder(
        user_id=UUID(current_user["uid"]),
        name=folder_data.name
    )
    return folder


@router.get("/folders", response_model=List[FolderResponse])
async def get_folders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all folders for the current user."""
    service = BookmarkService(db)
    folders = service.get_user_folders(UUID(current_user["uid"]))
    
    # Add bookmark count to each folder
    folder_responses = []
    for folder in folders:
        count = service.get_folder_bookmark_count(folder.id, UUID(current_user["uid"]))
        folder_dict = {
            "id": folder.id,
            "user_id": folder.user_id,
            "name": folder.name,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "bookmark_count": count
        }
        folder_responses.append(FolderResponse(**folder_dict))
    
    return folder_responses


@router.get("/folders/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific folder by ID."""
    service = BookmarkService(db)
    folder = service.get_folder(folder_id, UUID(current_user["uid"]))
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    count = service.get_folder_bookmark_count(folder.id, UUID(current_user["uid"]))
    folder_dict = {
        "id": folder.id,
        "user_id": folder.user_id,
        "name": folder.name,
        "created_at": folder.created_at,
        "updated_at": folder.updated_at,
        "bookmark_count": count
    }
    return FolderResponse(**folder_dict)


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    folder_data: FolderUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a folder's name."""
    service = BookmarkService(db)
    folder = service.update_folder(
        folder_id=folder_id,
        user_id=UUID(current_user["uid"]),
        name=folder_data.name
    )
    
    count = service.get_folder_bookmark_count(folder.id, UUID(current_user["uid"]))
    folder_dict = {
        "id": folder.id,
        "user_id": folder.user_id,
        "name": folder.name,
        "created_at": folder.created_at,
        "updated_at": folder.updated_at,
        "bookmark_count": count
    }
    return FolderResponse(**folder_dict)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a folder. Bookmarks in the folder will be moved to no folder."""
    service = BookmarkService(db)
    service.delete_folder(folder_id, UUID(current_user["uid"]))
    return None
