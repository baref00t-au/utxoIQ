"""SQLAlchemy database models for persistent storage."""
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Index, 
    UniqueConstraint, TIMESTAMP, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4

from src.database import Base


class User(Base):
    """User profile model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # user, admin, service
    subscription_tier = Column(String(20), default="free", nullable=False)  # free, pro, power
    stripe_customer_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationship to API keys
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_firebase_uid', 'firebase_uid'),
        Index('idx_user_email', 'email'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class APIKey(Base):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)  # SHA256 hash
    key_prefix = Column(String(20), nullable=False)  # First 8 chars for display
    name = Column(String(100), nullable=False)
    scopes = Column(ARRAY(String), default=list, nullable=False)  # ['insights:read', 'alerts:write']
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_apikey_hash', 'key_hash'),
        Index('idx_apikey_user', 'user_id'),
    )
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id})>"


class BackfillJob(Base):
    """Backfill job tracking model."""
    
    __tablename__ = "backfill_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type = Column(String(50), nullable=False)  # 'blocks', 'transactions', etc.
    start_block = Column(Integer, nullable=False)
    end_block = Column(Integer, nullable=False)
    current_block = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # 'running', 'completed', 'failed', 'paused'
    progress_percentage = Column(Float, default=0.0)
    estimated_completion = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_backfill_status', 'status'),
        Index('idx_backfill_started', 'started_at'),
        Index('idx_backfill_job_type', 'job_type'),
    )
    
    def __repr__(self):
        return f"<BackfillJob(id={self.id}, type={self.job_type}, status={self.status})>"


class InsightFeedback(Base):
    """User feedback on insights model."""
    
    __tablename__ = "insight_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    insight_id = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    comment = Column(Text, nullable=True)
    flag_type = Column(String(50), nullable=True)  # 'inaccurate', 'misleading', 'spam'
    flag_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    __table_args__ = (
        Index('idx_feedback_insight', 'insight_id'),
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_created', 'created_at'),
        UniqueConstraint('insight_id', 'user_id', name='uq_insight_user_feedback'),
    )
    
    def __repr__(self):
        return f"<InsightFeedback(id={self.id}, insight={self.insight_id}, rating={self.rating})>"


class SystemMetric(Base):
    """System metrics for monitoring and observability."""
    
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    service_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'cpu', 'memory', 'latency', etc.
    metric_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # 'percent', 'ms', 'bytes'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metric_metadata = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_metrics_service_time', 'service_name', 'timestamp'),
        Index('idx_metrics_type_time', 'metric_type', 'timestamp'),
        Index('idx_metrics_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SystemMetric(service={self.service_name}, type={self.metric_type}, value={self.metric_value})>"


class FilterPreset(Base):
    """User-saved filter presets for quick access to common filter combinations."""
    
    __tablename__ = "filter_presets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    filters = Column(JSONB, nullable=False)  # Stores FilterState as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationship to user
    user = relationship("User", backref="filter_presets")
    
    __table_args__ = (
        Index('idx_filter_preset_user', 'user_id'),
        Index('idx_filter_preset_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<FilterPreset(id={self.id}, name={self.name}, user_id={self.user_id})>"


class BookmarkFolder(Base):
    """Bookmark folder model for organizing bookmarks."""
    
    __tablename__ = "bookmark_folders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationship to user and bookmarks
    user = relationship("User", backref="bookmark_folders")
    bookmarks = relationship("Bookmark", back_populates="folder", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_bookmark_folder_user', 'user_id'),
        Index('idx_bookmark_folder_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BookmarkFolder(id={self.id}, name={self.name}, user_id={self.user_id})>"


class Bookmark(Base):
    """Bookmark model for saving insights for quick access."""
    
    __tablename__ = "bookmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    insight_id = Column(String(100), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey('bookmark_folders.id'), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("User", backref="bookmarks")
    folder = relationship("BookmarkFolder", back_populates="bookmarks")
    
    __table_args__ = (
        Index('idx_bookmark_user', 'user_id'),
        Index('idx_bookmark_insight', 'insight_id'),
        Index('idx_bookmark_folder', 'folder_id'),
        Index('idx_bookmark_created', 'created_at'),
        UniqueConstraint('user_id', 'insight_id', name='uq_user_insight_bookmark'),
    )
    
    def __repr__(self):
        return f"<Bookmark(id={self.id}, insight_id={self.insight_id}, user_id={self.user_id})>"
