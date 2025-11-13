"""Tests for bookmark service."""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.services.bookmark_service import BookmarkService
from src.models.db_models import Bookmark, BookmarkFolder, User


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        id=uuid4(),
        firebase_uid="test_firebase_uid",
        email="test@example.com",
        display_name="Test User",
        role="user",
        subscription_tier="free"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_folder(db_session: Session, test_user: User):
    """Create a test folder."""
    folder = BookmarkFolder(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Folder"
    )
    db_session.add(folder)
    db_session.commit()
    return folder


@pytest.fixture
def bookmark_service(db_session: Session):
    """Create bookmark service instance."""
    return BookmarkService(db_session)


def test_create_bookmark(bookmark_service: BookmarkService, test_user: User):
    """Test creating a bookmark."""
    bookmark = bookmark_service.create_bookmark(
        user_id=test_user.id,
        insight_id="insight_123",
        note="Test note"
    )
    
    assert bookmark.id is not None
    assert bookmark.user_id == test_user.id
    assert bookmark.insight_id == "insight_123"
    assert bookmark.note == "Test note"
    assert bookmark.folder_id is None


def test_create_bookmark_with_folder(
    bookmark_service: BookmarkService,
    test_user: User,
    test_folder: BookmarkFolder
):
    """Test creating a bookmark in a folder."""
    bookmark = bookmark_service.create_bookmark(
        user_id=test_user.id,
        insight_id="insight_123",
        folder_id=test_folder.id,
        note="Test note"
    )
    
    assert bookmark.folder_id == test_folder.id


def test_create_duplicate_bookmark(
    bookmark_service: BookmarkService,
    test_user: User
):
    """Test creating a duplicate bookmark raises error."""
    bookmark_service.create_bookmark(
        user_id=test_user.id,
        insight_id="insight_123"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        bookmark_service.create_bookmark(
            user_id=test_user.id,
            insight_id="insight_123"
        )
    
    assert exc_info.value.status_code == 409


def test_get_user_bookmarks(
    bookmark_service: BookmarkService,
    test_user: User
):
    """Test getting user bookmarks."""
    # Create multiple bookmarks
    bookmark_service.create_bookmark(test_user.id, "insight_1")
    bookmark_service.create_bookmark(test_user.id, "insight_2")
    bookmark_service.create_bookmark(test_user.id, "insight_3")
    
    bookmarks = bookmark_service.get_user_bookmarks(test_user.id)
    
    assert len(bookmarks) == 3


def test_get_user_bookmarks_by_folder(
    bookmark_service: BookmarkService,
    test_user: User,
    test_folder: BookmarkFolder
):
    """Test getting bookmarks filtered by folder."""
    bookmark_service.create_bookmark(
        test_user.id,
        "insight_1",
        folder_id=test_folder.id
    )
    bookmark_service.create_bookmark(test_user.id, "insight_2")
    
    bookmarks = bookmark_service.get_user_bookmarks(
        test_user.id,
        folder_id=test_folder.id
    )
    
    assert len(bookmarks) == 1
    assert bookmarks[0].folder_id == test_folder.id


def test_update_bookmark(
    bookmark_service: BookmarkService,
    test_user: User,
    test_folder: BookmarkFolder
):
    """Test updating a bookmark."""
    bookmark = bookmark_service.create_bookmark(
        test_user.id,
        "insight_123"
    )
    
    updated = bookmark_service.update_bookmark(
        bookmark_id=bookmark.id,
        user_id=test_user.id,
        folder_id=test_folder.id,
        note="Updated note"
    )
    
    assert updated.folder_id == test_folder.id
    assert updated.note == "Updated note"


def test_delete_bookmark(
    bookmark_service: BookmarkService,
    test_user: User
):
    """Test deleting a bookmark."""
    bookmark = bookmark_service.create_bookmark(
        test_user.id,
        "insight_123"
    )
    
    result = bookmark_service.delete_bookmark(bookmark.id, test_user.id)
    assert result is True
    
    # Verify bookmark is deleted
    deleted = bookmark_service.get_bookmark(bookmark.id, test_user.id)
    assert deleted is None


def test_check_bookmark_exists(
    bookmark_service: BookmarkService,
    test_user: User
):
    """Test checking if bookmark exists."""
    exists = bookmark_service.check_bookmark_exists(
        test_user.id,
        "insight_123"
    )
    assert exists is False
    
    bookmark_service.create_bookmark(test_user.id, "insight_123")
    
    exists = bookmark_service.check_bookmark_exists(
        test_user.id,
        "insight_123"
    )
    assert exists is True


def test_create_folder(bookmark_service: BookmarkService, test_user: User):
    """Test creating a folder."""
    folder = bookmark_service.create_folder(test_user.id, "My Folder")
    
    assert folder.id is not None
    assert folder.user_id == test_user.id
    assert folder.name == "My Folder"


def test_get_user_folders(
    bookmark_service: BookmarkService,
    test_user: User
):
    """Test getting user folders."""
    bookmark_service.create_folder(test_user.id, "Folder 1")
    bookmark_service.create_folder(test_user.id, "Folder 2")
    
    folders = bookmark_service.get_user_folders(test_user.id)
    
    assert len(folders) == 2


def test_update_folder(
    bookmark_service: BookmarkService,
    test_user: User,
    test_folder: BookmarkFolder
):
    """Test updating a folder."""
    updated = bookmark_service.update_folder(
        folder_id=test_folder.id,
        user_id=test_user.id,
        name="Updated Folder"
    )
    
    assert updated.name == "Updated Folder"


def test_delete_folder(
    bookmark_service: BookmarkService,
    test_user: User,
    test_folder: BookmarkFolder
):
    """Test deleting a folder."""
    # Create bookmark in folder
    bookmark_service.create_bookmark(
        test_user.id,
        "insight_123",
        folder_id=test_folder.id
    )
    
    result = bookmark_service.delete_folder(test_folder.id, test_user.id)
    assert result is True
    
    # Verify folder is deleted
    deleted = bookmark_service.get_folder(test_folder.id, test_user.id)
    assert deleted is None
    
    # Verify bookmark still exists but folder_id is None
    bookmarks = bookmark_service.get_user_bookmarks(test_user.id)
    assert len(bookmarks) == 1
    assert bookmarks[0].folder_id is None


def test_get_folder_bookmark_count(
    bookmark_service: BookmarkService,
    test_user: User,
    test_folder: BookmarkFolder
):
    """Test getting bookmark count for a folder."""
    bookmark_service.create_bookmark(
        test_user.id,
        "insight_1",
        folder_id=test_folder.id
    )
    bookmark_service.create_bookmark(
        test_user.id,
        "insight_2",
        folder_id=test_folder.id
    )
    
    count = bookmark_service.get_folder_bookmark_count(
        test_folder.id,
        test_user.id
    )
    
    assert count == 2
