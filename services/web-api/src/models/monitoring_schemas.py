"""Pydantic schemas for monitoring and alerting API."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID


class AlertConfigCreate(BaseModel):
    """Schema for creating an alert configuration."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Alert name")
    service_name: str = Field(..., min_length=1, max_length=100, description="Service to monitor")
    metric_type: str = Field(..., min_length=1, max_length=100, description="Metric type to monitor")
    threshold_type: Literal['absolute', 'percentage', 'rate'] = Field(..., description="Type of threshold")
    threshold_value: float = Field(..., gt=0, description="Threshold value (must be positive)")
    comparison_operator: Literal['>', '<', '>=', '<=', '=='] = Field(..., description="Comparison operator")
    severity: Literal['info', 'warning', 'critical'] = Field(..., description="Alert severity level")
    evaluation_window_seconds: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Evaluation window in seconds (60-3600)"
    )
    notification_channels: List[Literal['email', 'slack', 'sms']] = Field(
        default_factory=list,
        description="Notification channels"
    )
    suppression_enabled: bool = Field(default=False, description="Enable alert suppression")
    suppression_start: Optional[datetime] = Field(None, description="Suppression start time")
    suppression_end: Optional[datetime] = Field(None, description="Suppression end time")
    enabled: bool = Field(default=True, description="Enable alert")
    
    @field_validator('notification_channels')
    @classmethod
    def validate_channels(cls, v):
        """Validate notification channels are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Notification channels must be unique")
        return v
    
    @field_validator('suppression_end')
    @classmethod
    def validate_suppression_window(cls, v, info):
        """Validate suppression end is after start."""
        if v is not None and info.data.get('suppression_start') is not None:
            if v <= info.data['suppression_start']:
                raise ValueError("Suppression end must be after suppression start")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "High CPU Alert",
                "service_name": "web-api",
                "metric_type": "cpu_usage",
                "threshold_type": "absolute",
                "threshold_value": 80.0,
                "comparison_operator": ">",
                "severity": "warning",
                "evaluation_window_seconds": 300,
                "notification_channels": ["email", "slack"],
                "enabled": True
            }
        }


class AlertConfigUpdate(BaseModel):
    """Schema for updating an alert configuration."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    threshold_value: Optional[float] = Field(None, gt=0)
    comparison_operator: Optional[Literal['>', '<', '>=', '<=', '==']] = None
    severity: Optional[Literal['info', 'warning', 'critical']] = None
    evaluation_window_seconds: Optional[int] = Field(None, ge=60, le=3600)
    notification_channels: Optional[List[Literal['email', 'slack', 'sms']]] = None
    suppression_enabled: Optional[bool] = None
    suppression_start: Optional[datetime] = None
    suppression_end: Optional[datetime] = None
    enabled: Optional[bool] = None
    
    @field_validator('notification_channels')
    @classmethod
    def validate_channels(cls, v):
        """Validate notification channels are unique."""
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Notification channels must be unique")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "threshold_value": 90.0,
                "severity": "critical",
                "enabled": True
            }
        }


class AlertConfigResponse(BaseModel):
    """Schema for alert configuration response."""
    
    id: UUID
    name: str
    service_name: str
    metric_type: str
    threshold_type: str
    threshold_value: float
    comparison_operator: str
    severity: str
    evaluation_window_seconds: int
    notification_channels: List[str]
    suppression_enabled: bool
    suppression_start: Optional[datetime]
    suppression_end: Optional[datetime]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    enabled: bool
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "High CPU Alert",
                "service_name": "web-api",
                "metric_type": "cpu_usage",
                "threshold_type": "absolute",
                "threshold_value": 80.0,
                "comparison_operator": ">",
                "severity": "warning",
                "evaluation_window_seconds": 300,
                "notification_channels": ["email", "slack"],
                "suppression_enabled": False,
                "suppression_start": None,
                "suppression_end": None,
                "created_by": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
                "enabled": True
            }
        }


class AlertHistoryResponse(BaseModel):
    """Schema for alert history response."""
    
    id: UUID
    alert_config_id: UUID
    triggered_at: datetime
    resolved_at: Optional[datetime]
    severity: str
    metric_value: float
    threshold_value: float
    message: str
    notification_sent: bool
    notification_channels: List[str]
    resolution_method: Optional[str]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "alert_config_id": "123e4567-e89b-12d3-a456-426614174000",
                "triggered_at": "2024-01-15T10:30:00Z",
                "resolved_at": "2024-01-15T10:45:00Z",
                "severity": "warning",
                "metric_value": 85.5,
                "threshold_value": 80.0,
                "message": "CPU usage exceeded threshold: 85.5% > 80.0%",
                "notification_sent": True,
                "notification_channels": ["email", "slack"],
                "resolution_method": "auto"
            }
        }


class AlertConfigListResponse(BaseModel):
    """Schema for listing alert configurations."""
    
    alerts: List[AlertConfigResponse]
    total: int
    page: int = 1
    page_size: int = 50
    
    class Config:
        json_schema_extra = {
            "example": {
                "alerts": [],
                "total": 0,
                "page": 1,
                "page_size": 50
            }
        }


class AlertHistoryListResponse(BaseModel):
    """Schema for listing alert history."""
    
    history: List[AlertHistoryResponse]
    total: int
    page: int = 1
    page_size: int = 50
    
    class Config:
        json_schema_extra = {
            "example": {
                "history": [],
                "total": 0,
                "page": 1,
                "page_size": 50
            }
        }


class AlertFrequencyByService(BaseModel):
    """Alert frequency statistics per service."""
    
    service_name: str
    total_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    avg_alerts_per_day: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "web-api",
                "total_alerts": 45,
                "critical_alerts": 5,
                "warning_alerts": 30,
                "info_alerts": 10,
                "avg_alerts_per_day": 1.5
            }
        }


class AlertTypeFrequency(BaseModel):
    """Most common alert types."""
    
    metric_type: str
    service_name: str
    alert_count: int
    avg_metric_value: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_type": "cpu_usage",
                "service_name": "web-api",
                "alert_count": 25,
                "avg_metric_value": 85.5
            }
        }


class AlertTrendData(BaseModel):
    """Alert trend data point."""
    
    date: str
    total_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-15",
                "total_alerts": 12,
                "critical_alerts": 2,
                "warning_alerts": 8,
                "info_alerts": 2
            }
        }


class AlertAnalyticsResponse(BaseModel):
    """Schema for alert analytics response."""
    
    period_start: datetime
    period_end: datetime
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    mean_time_to_resolution_minutes: Optional[float]
    alert_frequency_by_service: List[AlertFrequencyByService]
    most_common_alert_types: List[AlertTypeFrequency]
    alert_trends: List[AlertTrendData]
    
    class Config:
        json_schema_extra = {
            "example": {
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z",
                "total_alerts": 150,
                "active_alerts": 5,
                "resolved_alerts": 145,
                "mean_time_to_resolution_minutes": 15.5,
                "alert_frequency_by_service": [],
                "most_common_alert_types": [],
                "alert_trends": []
            }
        }



# Dashboard Configuration Schemas

class WidgetDataSource(BaseModel):
    """Widget data source configuration."""
    
    metric_type: str = Field(..., description="Metric type to display")
    service_name: Optional[str] = Field(None, description="Service name filter")
    aggregation: Literal['ALIGN_MEAN', 'ALIGN_MAX', 'ALIGN_MIN', 'ALIGN_SUM', 'ALIGN_COUNT'] = Field(
        default='ALIGN_MEAN',
        description="Aggregation method"
    )
    time_range: str = Field(default='1h', description="Time range (e.g., '1h', '24h', '7d', '30d')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_type": "custom.googleapis.com/api/response_time",
                "service_name": "web-api",
                "aggregation": "ALIGN_MEAN",
                "time_range": "1h"
            }
        }


class WidgetDisplayOptions(BaseModel):
    """Widget display options."""
    
    show_legend: bool = Field(default=True, description="Show chart legend")
    y_axis_label: Optional[str] = Field(None, description="Y-axis label")
    color: str = Field(default='#FF5A21', description="Primary color")
    threshold_line: Optional[float] = Field(None, description="Threshold line value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "show_legend": True,
                "y_axis_label": "Milliseconds",
                "color": "#FF5A21",
                "threshold_line": 100.0
            }
        }


class WidgetConfig(BaseModel):
    """Widget configuration."""
    
    id: str = Field(..., description="Unique widget ID")
    type: Literal['line_chart', 'bar_chart', 'gauge', 'stat_card'] = Field(
        ...,
        description="Widget type"
    )
    title: str = Field(..., min_length=1, max_length=100, description="Widget title")
    data_source: WidgetDataSource = Field(..., description="Data source configuration")
    display_options: WidgetDisplayOptions = Field(
        default_factory=WidgetDisplayOptions,
        description="Display options"
    )
    position: dict = Field(
        default_factory=dict,
        description="Widget position and size (x, y, w, h)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "widget-1",
                "type": "line_chart",
                "title": "API Response Time",
                "data_source": {
                    "metric_type": "custom.googleapis.com/api/response_time",
                    "aggregation": "ALIGN_MEAN",
                    "time_range": "1h"
                },
                "display_options": {
                    "show_legend": True,
                    "y_axis_label": "Milliseconds",
                    "color": "#FF5A21"
                },
                "position": {"x": 0, "y": 0, "w": 6, "h": 4}
            }
        }


class DashboardCreate(BaseModel):
    """Schema for creating a dashboard."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Dashboard name")
    description: Optional[str] = Field(None, max_length=500, description="Dashboard description")
    layout: dict = Field(default_factory=dict, description="Dashboard layout configuration")
    widgets: List[WidgetConfig] = Field(default_factory=list, description="Dashboard widgets")
    is_public: bool = Field(default=False, description="Make dashboard publicly accessible")
    
    @field_validator('widgets')
    @classmethod
    def validate_widget_ids(cls, v):
        """Validate widget IDs are unique."""
        widget_ids = [w.id for w in v]
        if len(widget_ids) != len(set(widget_ids)):
            raise ValueError("Widget IDs must be unique")
        return v
    
    @field_validator('widgets')
    @classmethod
    def validate_widget_types(cls, v):
        """Validate widget types are supported."""
        valid_types = {'line_chart', 'bar_chart', 'gauge', 'stat_card'}
        for widget in v:
            if widget.type not in valid_types:
                raise ValueError(f"Invalid widget type: {widget.type}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "API Performance Dashboard",
                "description": "Monitor API response times and error rates",
                "layout": {"cols": 12, "rowHeight": 100},
                "widgets": [],
                "is_public": False
            }
        }


class DashboardUpdate(BaseModel):
    """Schema for updating a dashboard."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    layout: Optional[dict] = None
    widgets: Optional[List[WidgetConfig]] = None
    is_public: Optional[bool] = None
    
    @field_validator('widgets')
    @classmethod
    def validate_widget_ids(cls, v):
        """Validate widget IDs are unique."""
        if v is not None:
            widget_ids = [w.id for w in v]
            if len(widget_ids) != len(set(widget_ids)):
                raise ValueError("Widget IDs must be unique")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Dashboard Name",
                "is_public": True
            }
        }


class DashboardResponse(BaseModel):
    """Schema for dashboard response."""
    
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    layout: dict
    widgets: List[dict]  # Serialized widget configs
    is_public: bool
    share_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "API Performance Dashboard",
                "description": "Monitor API response times and error rates",
                "layout": {"cols": 12, "rowHeight": 100},
                "widgets": [],
                "is_public": False,
                "share_token": None,
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        }


class DashboardListResponse(BaseModel):
    """Schema for listing dashboards."""
    
    dashboards: List[DashboardResponse]
    total: int
    page: int = 1
    page_size: int = 50
    
    class Config:
        json_schema_extra = {
            "example": {
                "dashboards": [],
                "total": 0,
                "page": 1,
                "page_size": 50
            }
        }


class DashboardShareResponse(BaseModel):
    """Schema for dashboard share response."""
    
    dashboard_id: UUID
    share_token: str
    share_url: str
    is_public: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "dashboard_id": "123e4567-e89b-12d3-a456-426614174000",
                "share_token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
                "share_url": "https://api.utxoiq.com/api/v1/monitoring/dashboards/public/abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
                "is_public": True
            }
        }


class WidgetDataRequest(BaseModel):
    """Request for widget data."""
    
    widget_id: str = Field(..., description="Widget ID")
    data_source: WidgetDataSource = Field(..., description="Data source configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "widget_id": "widget-1",
                "data_source": {
                    "metric_type": "custom.googleapis.com/api/response_time",
                    "aggregation": "ALIGN_MEAN",
                    "time_range": "1h"
                }
            }
        }


class WidgetDataPoint(BaseModel):
    """Widget data point."""
    
    timestamp: str
    value: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:00:00Z",
                "value": 125.5
            }
        }


class WidgetDataResponse(BaseModel):
    """Response for widget data."""
    
    widget_id: str
    data: List[WidgetDataPoint]
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "widget_id": "widget-1",
                "data": [
                    {"timestamp": "2024-01-15T10:00:00Z", "value": 125.5},
                    {"timestamp": "2024-01-15T10:05:00Z", "value": 130.2}
                ],
                "metadata": {
                    "metric_type": "custom.googleapis.com/api/response_time",
                    "time_range": "1h",
                    "aggregation": "ALIGN_MEAN"
                }
            }
        }


class DashboardCopyRequest(BaseModel):
    """Request to copy a dashboard."""
    
    source_dashboard_id: UUID = Field(..., description="Dashboard ID to copy from")
    new_name: str = Field(..., min_length=1, max_length=100, description="Name for the copied dashboard")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_dashboard_id": "123e4567-e89b-12d3-a456-426614174000",
                "new_name": "Copy of API Performance Dashboard"
            }
        }
