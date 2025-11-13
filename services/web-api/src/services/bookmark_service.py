"""Bookmark service for managing user bookmarks and folders."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.models.db_models import Bookmark, BookmarkFolder


class BookmarkService:
    """Service for managing bookmarks and bookmark folders."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Bookmark operations
    
    def create_bookmark(
        self,
        user_id: UUID,
        insight_id: str,
        folder_id: Optional[UUID] = None,
        note: Optional[str] = None
    ) -> Bookmark:
        """Create a new bookmark for an insight."""
        # Validate folder belongs to user if provided
        if folder_id:
            folder = self.db.query(BookmarkFolder).filter(
                BookmarkFolder.id == folder_id,
                BookmarkFolder.user_id == user_id
            ).first()
            if not folder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Folder not found or does not belong to user"
                )
        
        bookmark = Bookmark(
            user_id=user_id,
            insight_id=insight_id,
            folder_id=folder_id,
            note=note
        )
        
        try:
            self.db.add(bookmark)
            self.db.commit()
            self.db.refresh(bookmark)
            return bookmark
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bookmark already exists for this insight"
            )
    
    def get_bookmark(self, bookmark_id: UUID, user_id: UUID) -> Optional[Bookmark]:
        """Get a bookmark by ID for a specific user."""
        return self.db.query(Bookmark).filter(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == user_id
        ).first()
    
    def get_user_bookmarks(
        self,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Bookmark]:
        """Get all bookmarks for a user, optionally filtered by folder."""
        query = self.db.query(Bookmark).filter(Bookmark.user_id == user_id)
        
        if folder_id:
            query = query.filter(Bookmark.folder_id == folder_id)
        
        return query.order_by(Bookmark.created_at.desc()).limit(limit).offset(offset).all()
    
    def update_bookmark(
        self,
        bookmark_id: UUID,
        user_id: UUID,
        folder_id: Optional[UUID] = None,
        note: Optional[str] = None
    ) -> Optional[Bookmark]:
        """Update a bookmark's folder or note."""
        bookmark = self.get_bookmark(bookmark_id, user_id)
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        # Validate folder belongs to user if provided
        if folder_id:
            folder = self.db.query(BookmarkFolder).filter(
                BookmarkFolder.id == folder_id,
                BookmarkFolder.user_id == user_id
            ).first()
            if not folder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Folder not found or does not belong to user"
                )
            bookmark.folder_id = folder_id
        
        if note is not None:
            bookmark.note = note
        
        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark
    
    def delete_bookmark(self, bookmark_id: UUID, user_id: UUID) -> bool:
        """Delete a bookmark."""
        bookmark = self.get_bookmark(bookmark_id, user_id)
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        self.db.delete(bookmark)
        self.db.commit()
        return True
    
    def check_bookmark_exists(self, user_id: UUID, insight_id: str) -> bool:
        """Check if a bookmark exists for a user and insight."""
        return self.db.query(Bookmark).filter(
            Bookmark.user_id == user_id,
            Bookmark.insight_id == insight_id
        ).first() is not None
    
    # Folder operations
    
    def create_folder(self, user_id: UUID, name: str) -> BookmarkFolder:
        """Create a new bookmark folder."""
        folder = BookmarkFolder(
            user_id=user_id,
            name=name
        )
        
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return folder
    
    def get_folder(self, folder_id: UUID, user_id: UUID) -> Optional[BookmarkFolder]:
        """Get a folder by ID for a specific user."""
        return self.db.query(BookmarkFolder).filter(
            BookmarkFolder.id == folder_id,
            BookmarkFolder.user_id == user_id
        ).first()
    
    def get_user_folders(self, user_id: UUID) -> List[BookmarkFolder]:
        """Get all folders for a user."""
        return self.db.query(BookmarkFolder).filter(
            BookmarkFolder.user_id == user_id
        ).order_by(BookmarkFolder.created_at.desc()).all()
    
    def update_folder(
        self,
        folder_id: UUID,
        user_id: UUID,
        name: str
    ) -> Optional[BookmarkFolder]:
        """Update a folder's name."""
        folder = self.get_folder(folder_id, user_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        
        folder.name = name
        self.db.commit()
        self.db.refresh(folder)
        return folder
    
    def delete_folder(self, folder_id: UUID, user_id: UUID) -> bool:
        """Delete a folder and set all bookmarks in it to no folder."""
        folder = self.get_folder(folder_id, user_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        
        # Bookmarks will have folder_id set to NULL due to ON DELETE SET NULL
        self.db.delete(folder)
        self.db.commit()
        return True
    
    def get_folder_bookmark_count(self, folder_id: UUID, user_id: UUID) -> int:
        """Get the count of bookmarks in a folder."""
        return self.db.query(Bookmark).filter(
            Bookmark.folder_id == folder_id,
            Bookmark.user_id == user_id
        ).count()
