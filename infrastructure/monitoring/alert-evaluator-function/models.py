"""
Database models for alert evaluator Cloud Function.

This module contains the SQLAlchemy models needed for alert evaluation.
"""
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Index, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from uuid import uuid4

Base = declarative_base()


class AlertConfiguration(Base):
    """Alert configuration model."""
    
    __tablename__ = "alert_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    service_name = Column(String(100), nullable=False)
    metric_type = Column(String(100), nullable=False)
    threshold_type = Column(String(20), nullable=False)
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)
    severity = Column(String(20), nullable=False)
    evaluation_window_seconds = Column(Integer, default=300, nullable=False)
    notification_channels = Column(ARRAY(String), default=list, nullable=False)
    suppression_enabled = Column(Boolean, default=False, nullable=False)
    suppression_start = Column(DateTime, nullable=True)
    suppression_end = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    history = relationship("AlertHistory", back_populates="alert_config")
    
    __table_args__ = (
        Index('idx_alert_service', 'service_name'),
        Index('idx_alert_enabled', 'enabled'),
    )


class AlertHistory(Base):
    """Alert history model."""
    
    __tablename__ = "alert_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_config_id = Column(UUID(as_uuid=True), ForeignKey('alert_configurations.id'), nullable=False)
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    severity = Column(String(20), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_channels = Column(ARRAY(String), default=list, nullable=False)
    resolution_method = Column(String(50), nullable=True)
    
    # Relationships
    alert_config = relationship("AlertConfiguration", back_populates="history")
    
    __table_args__ = (
        Index('idx_alert_history_triggered', 'triggered_at'),
        Index('idx_alert_history_config', 'alert_config_id'),
        Index('idx_alert_history_resolved', 'resolved_at'),
    )
