"""Monitoring and alerting database models."""
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Index, Boolean, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import secrets

from src.database import Base


class AlertConfiguration(Base):
    """Alert configuration model for monitoring thresholds and notifications."""
    
    __tablename__ = "alert_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    service_name = Column(String(100), nullable=False)
    metric_type = Column(String(100), nullable=False)
    threshold_type = Column(String(20), nullable=False)  # 'absolute', 'percentage', 'rate'
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # '>', '<', '>=', '<=', '=='
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'critical'
    evaluation_window_seconds = Column(Integer, default=300, nullable=False)
    notification_channels = Column(ARRAY(String), default=list, nullable=False)  # ['email', 'slack', 'sms']
    suppression_enabled = Column(Boolean, default=False, nullable=False)
    suppression_start = Column(DateTime, nullable=True)
    suppression_end = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    history = relationship("AlertHistory", back_populates="alert_config", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_alert_service', 'service_name'),
        Index('idx_alert_enabled', 'enabled'),
        Index('idx_alert_created_by', 'created_by'),
    )
    
    def __repr__(self):
        return f"<AlertConfiguration(id={self.id}, name={self.name}, service={self.service_name})>"


class AlertHistory(Base):
    """Alert history model to track triggered alerts and their resolutions."""
    
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
    resolution_method = Column(String(50), nullable=True)  # 'auto', 'manual', 'suppressed'
    
    # Relationships
    alert_config = relationship("AlertConfiguration", back_populates="history")
    
    __table_args__ = (
        Index('idx_alert_history_triggered', 'triggered_at'),
        Index('idx_alert_history_config', 'alert_config_id'),
        Index('idx_alert_history_resolved', 'resolved_at'),
    )
    
    def __repr__(self):
        return f"<AlertHistory(id={self.id}, config_id={self.alert_config_id}, triggered={self.triggered_at})>"


class DashboardConfiguration(Base):
    """Dashboard configuration model for custom monitoring dashboards."""
    
    __tablename__ = "dashboard_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    layout = Column(JSONB, nullable=False, default=dict)  # Widget positions and sizes
    widgets = Column(JSONB, nullable=False, default=list)  # Widget configurations
    is_public = Column(Boolean, default=False, nullable=False)
    share_token = Column(String(64), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_dashboard_user', 'user_id'),
        Index('idx_dashboard_share_token', 'share_token'),
        Index('idx_dashboard_public', 'is_public'),
    )
    
    def generate_share_token(self):
        """Generate a unique share token for public dashboards."""
        self.share_token = secrets.token_urlsafe(48)
        return self.share_token
    
    def __repr__(self):
        return f"<DashboardConfiguration(id={self.id}, name={self.name}, user_id={self.user_id})>"
