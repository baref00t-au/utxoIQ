# Design Document

## Overview

This design implements a comprehensive monitoring and observability platform using Google Cloud's native monitoring services (Cloud Monitoring, Cloud Logging, Cloud Trace) integrated with custom alerting logic and visualization dashboards. The system provides historical trend analysis, customizable alerts with multi-channel notifications, distributed tracing, and centralized log aggregation.

## Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Frontend Dashboard                   │
│         (React + Recharts/ECharts + TanStack Query)  │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ REST API
                     │
┌────────────────────▼─────────────────────────────────┐
│              Monitoring API Service                   │
│                   (FastAPI)                           │
└─┬──────────┬──────────┬──────────┬────────────┬──────┘
  │          │          │          │            │
  │          │          │          │            │
┌─▼────┐ ┌──▼────┐ ┌───▼────┐ ┌──▼──────┐ ┌───▼────┐
│Cloud │ │Cloud  │ │Cloud   │ │Cloud SQL│ │ Redis  │
│Monitor│ │Logging│ │Trace   │ │(Alerts) │ │(Cache) │
└──────┘ └───────┘ └────────┘ └─────────┘ └────────┘
                                    │
                                    │
                          ┌─────────▼──────────┐
                          │  Alert Dispatcher  │
                          └─┬────────┬────────┬┘
                            │        │        │
                      ┌─────▼──┐ ┌──▼───┐ ┌──▼───┐
                      │ Email  │ │Slack │ │ SMS  │
                      └────────┘ └──────┘ └──────┘
```

### Data Flow

1. **Metrics Collection**: Services → Cloud Monitoring → API → Dashboard
2. **Log Aggregation**: Services → Cloud Logging → API → Search UI
3. **Distributed Tracing**: Services → Cloud Trace → API → Trace Viewer
4. **Alerting**: Cloud Monitoring → Alert Evaluator → Dispatcher → Channels

## Components and Interfaces

### 1. Metrics Collection Service

#### Cloud Monitoring Integration
```python
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import query

class MetricsService:
    def __init__(self, project_id: str):
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        self.query_client = monitoring_v3.QueryServiceClient()
    
    async def get_time_series(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: str = "ALIGN_MEAN",
        interval_seconds: int = 300
    ) -> List[Dict]:
        """Query time series data from Cloud Monitoring"""
        interval = monitoring_v3.TimeInterval({
            "start_time": start_time,
            "end_time": end_time
        })
        
        aggregation = monitoring_v3.Aggregation({
            "alignment_period": {"seconds": interval_seconds},
            "per_series_aligner": aggregation,
        })
        
        results = self.client.list_time_series(
            request={
                "name": self.project_name,
                "filter": f'metric.type = "{metric_type}"',
                "interval": interval,
                "aggregation": aggregation,
            }
        )
        
        return [self._format_time_series(ts) for ts in results]
    
    async def get_service_metrics(
        self,
        service_name: str,
        metrics: List[str],
        time_range: str = "1h"
    ) -> Dict[str, List[Dict]]:
        """Get multiple metrics for a service"""
        end_time = datetime.utcnow()
        start_time = end_time - self._parse_time_range(time_range)
        
        results = {}
        for metric in metrics:
            metric_type = f"custom.googleapis.com/{service_name}/{metric}"
            results[metric] = await self.get_time_series(
                metric_type, start_time, end_time
            )
        
        return results
    
    async def calculate_baseline(
        self,
        metric_type: str,
        days: int = 7
    ) -> Dict[str, float]:
        """Calculate baseline statistics for a metric"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        data = await self.get_time_series(metric_type, start_time, end_time)
        values = [point['value'] for point in data]
        
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99),
        }
```

### 2. Alert Configuration Models

#### Database Models
```python
class AlertConfiguration(Base):
    __tablename__ = "alert_configurations"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    service_name = Column(String(100), nullable=False)
    metric_type = Column(String(100), nullable=False)
    threshold_type = Column(String(20), nullable=False)  # 'absolute', 'percentage', 'rate'
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # '>', '<', '>=', '<=', '=='
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'critical'
    evaluation_window_seconds = Column(Integer, default=300)
    notification_channels = Column(ARRAY(String), default=[])  # ['email', 'slack', 'sms']
    suppression_enabled = Column(Boolean, default=False)
    suppression_start = Column(DateTime, nullable=True)
    suppression_end = Column(DateTime, nullable=True)
    created_by = Column(UUID, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    enabled = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_alert_service', 'service_name'),
        Index('idx_alert_enabled', 'enabled'),
    )

class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    alert_config_id = Column(UUID, ForeignKey('alert_configurations.id'))
    triggered_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    severity = Column(String(20), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    message = Column(Text, nullable=False)
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(ARRAY(String), default=[])
    resolution_method = Column(String(50), nullable=True)  # 'auto', 'manual', 'suppressed'
    
    alert_config = relationship("AlertConfiguration", backref="history")
    
    __table_args__ = (
        Index('idx_alert_history_triggered', 'triggered_at'),
        Index('idx_alert_history_config', 'alert_config_id'),
    )
```

#### Pydantic Schemas
```python
class AlertConfigCreate(BaseModel):
    name: str
    service_name: str
    metric_type: str
    threshold_type: Literal['absolute', 'percentage', 'rate']
    threshold_value: float
    comparison_operator: Literal['>', '<', '>=', '<=', '==']
    severity: Literal['info', 'warning', 'critical']
    evaluation_window_seconds: int = 300
    notification_channels: List[Literal['email', 'slack', 'sms']] = []

class AlertConfigResponse(BaseModel):
    id: UUID
    name: str
    service_name: str
    metric_type: str
    threshold_type: str
    threshold_value: float
    comparison_operator: str
    severity: str
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertHistoryResponse(BaseModel):
    id: UUID
    triggered_at: datetime
    resolved_at: Optional[datetime]
    severity: str
    metric_value: float
    threshold_value: float
    message: str
    notification_sent: bool
    
    class Config:
        from_attributes = True
```

### 3. Alert Evaluation Engine

```python
class AlertEvaluator:
    def __init__(
        self,
        metrics_service: MetricsService,
        db: AsyncSession,
        notification_service: NotificationService
    ):
        self.metrics = metrics_service
        self.db = db
        self.notifications = notification_service
    
    async def evaluate_all_alerts(self):
        """Evaluate all enabled alert configurations"""
        configs = await self._get_enabled_alerts()
        
        for config in configs:
            try:
                await self.evaluate_alert(config)
            except Exception as e:
                logger.error(f"Error evaluating alert {config.id}: {e}")
    
    async def evaluate_alert(self, config: AlertConfiguration):
        """Evaluate a single alert configuration"""
        # Check if suppressed
        if self._is_suppressed(config):
            return
        
        # Get current metric value
        metric_value = await self._get_current_metric_value(
            config.service_name,
            config.metric_type,
            config.evaluation_window_seconds
        )
        
        # Evaluate threshold
        triggered = self._evaluate_threshold(
            metric_value,
            config.threshold_value,
            config.comparison_operator
        )
        
        if triggered:
            await self._handle_alert_triggered(config, metric_value)
        else:
            await self._handle_alert_resolved(config)
    
    def _evaluate_threshold(
        self,
        value: float,
        threshold: float,
        operator: str
    ) -> bool:
        """Evaluate if value crosses threshold"""
        operators = {
            '>': lambda v, t: v > t,
            '<': lambda v, t: v < t,
            '>=': lambda v, t: v >= t,
            '<=': lambda v, t: v <= t,
            '==': lambda v, t: abs(v - t) < 0.001,
        }
        return operators[operator](value, threshold)
    
    async def _handle_alert_triggered(
        self,
        config: AlertConfiguration,
        metric_value: float
    ):
        """Handle alert trigger"""
        # Check if already triggered
        existing = await self._get_active_alert(config.id)
        if existing:
            return  # Already triggered
        
        # Create alert history record
        alert = AlertHistory(
            alert_config_id=config.id,
            triggered_at=datetime.utcnow(),
            severity=config.severity,
            metric_value=metric_value,
            threshold_value=config.threshold_value,
            message=self._format_alert_message(config, metric_value)
        )
        self.db.add(alert)
        await self.db.commit()
        
        # Send notifications
        await self._send_notifications(config, alert)
    
    async def _send_notifications(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ):
        """Send alert notifications to configured channels"""
        for channel in config.notification_channels:
            try:
                if channel == 'email':
                    await self.notifications.send_email_alert(config, alert)
                elif channel == 'slack':
                    await self.notifications.send_slack_alert(config, alert)
                elif channel == 'sms' and config.severity == 'critical':
                    await self.notifications.send_sms_alert(config, alert)
                
                alert.notification_sent = True
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
        
        await self.db.commit()
```

### 4. Notification Service

```python
class NotificationService:
    def __init__(
        self,
        sendgrid_api_key: str,
        slack_webhook_url: str,
        twilio_client: TwilioClient
    ):
        self.sendgrid = SendGridAPIClient(sendgrid_api_key)
        self.slack_webhook = slack_webhook_url
        self.twilio = twilio_client
    
    async def send_email_alert(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ):
        """Send email notification"""
        message = Mail(
            from_email='alerts@utxoiq.com',
            to_emails=self._get_alert_recipients(config),
            subject=f"[{alert.severity.upper()}] {config.name}",
            html_content=self._format_email_body(config, alert)
        )
        
        response = await self.sendgrid.send(message)
        return response.status_code == 202
    
    async def send_slack_alert(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ):
        """Send Slack notification"""
        color = {
            'info': '#36a64f',
            'warning': '#ff9900',
            'critical': '#ff0000'
        }[alert.severity]
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"{alert.severity.upper()}: {config.name}",
                "text": alert.message,
                "fields": [
                    {"title": "Service", "value": config.service_name, "short": True},
                    {"title": "Metric", "value": config.metric_type, "short": True},
                    {"title": "Current Value", "value": str(alert.metric_value), "short": True},
                    {"title": "Threshold", "value": str(alert.threshold_value), "short": True},
                ],
                "footer": "utxoIQ Monitoring",
                "ts": int(alert.triggered_at.timestamp())
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.slack_webhook, json=payload)
            return response.status_code == 200
    
    async def send_sms_alert(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ):
        """Send SMS notification (critical only)"""
        message_body = f"[CRITICAL] {config.service_name}: {alert.message[:100]}"
        
        phone_numbers = self._get_sms_recipients(config)
        for phone in phone_numbers:
            try:
                await self.twilio.messages.create(
                    body=message_body,
                    from_='+1234567890',  # Twilio number
                    to=phone
                )
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone}: {e}")
```

### 5. Distributed Tracing Integration

```python
from google.cloud import trace_v2
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

class TracingService:
    def __init__(self, project_id: str):
        # Set up OpenTelemetry with Cloud Trace exporter
        trace.set_tracer_provider(TracerProvider())
        cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(cloud_trace_exporter)
        )
        self.tracer = trace.get_tracer(__name__)
    
    def trace_request(self, func):
        """Decorator to trace function execution"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with self.tracer.start_as_current_span(func.__name__) as span:
                span.set_attribute("function", func.__name__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.message", str(e))
                    raise
        return wrapper
    
    async def get_trace(self, trace_id: str) -> Dict:
        """Retrieve trace details from Cloud Trace"""
        client = trace_v2.TraceServiceClient()
        project_name = f"projects/{self.project_id}"
        trace_name = f"{project_name}/traces/{trace_id}"
        
        trace = client.get_trace(name=trace_name)
        return self._format_trace(trace)
```

### 6. Log Aggregation Service

```python
from google.cloud import logging

class LogAggregationService:
    def __init__(self, project_id: str):
        self.client = logging.Client(project=project_id)
    
    async def search_logs(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        severity: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Search logs with filters"""
        filter_parts = [
            f'timestamp >= "{start_time.isoformat()}"',
            f'timestamp <= "{end_time.isoformat()}"'
        ]
        
        if severity:
            filter_parts.append(f'severity = "{severity}"')
        
        if service:
            filter_parts.append(f'resource.labels.service_name = "{service}"')
        
        if query:
            filter_parts.append(f'textPayload =~ "{query}"')
        
        filter_str = " AND ".join(filter_parts)
        
        entries = self.client.list_entries(
            filter_=filter_str,
            max_results=limit,
            order_by=logging.DESCENDING
        )
        
        return [self._format_log_entry(entry) for entry in entries]
    
    async def get_log_context(
        self,
        log_id: str,
        context_lines: int = 10
    ) -> List[Dict]:
        """Get surrounding log entries for context"""
        # Implementation to fetch logs before and after the target log
        pass
```

### 7. Custom Dashboard Configuration

```python
class DashboardConfiguration(Base):
    __tablename__ = "dashboard_configurations"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    layout = Column(JSONB, nullable=False)  # Widget positions and sizes
    widgets = Column(JSONB, nullable=False)  # Widget configurations
    is_public = Column(Boolean, default=False)
    share_token = Column(String(64), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="dashboards")

# Widget configuration example
widget_config = {
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
    }
}
```

## Error Handling

### Monitoring Service Errors
```python
class MonitoringError(Exception):
    """Base monitoring error"""
    pass

class MetricNotFoundError(MonitoringError):
    """Metric does not exist"""
    pass

class AlertEvaluationError(MonitoringError):
    """Alert evaluation failed"""
    pass

class NotificationError(MonitoringError):
    """Notification delivery failed"""
    pass
```

## Testing Strategy

### Unit Tests
- Alert threshold evaluation logic
- Baseline calculation algorithms
- Notification formatting
- Dashboard widget configuration validation

### Integration Tests
- Cloud Monitoring API queries
- Alert trigger and resolution flow
- Multi-channel notification delivery
- Distributed tracing propagation
- Log search and filtering

### Performance Tests
- Dashboard load time with large datasets
- Alert evaluation latency
- Log search performance
- Trace query performance

## Configuration

### Environment Variables
```bash
# Google Cloud
GCP_PROJECT_ID=utxoiq-prod
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Notifications
SENDGRID_API_KEY=SG.xxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_FROM_NUMBER=+1234567890

# Alert Configuration
ALERT_EVALUATION_INTERVAL_SECONDS=60
ALERT_NOTIFICATION_RETRY_COUNT=3
ALERT_SUPPRESSION_ENABLED=true
```

## Deployment Considerations

### Cloud Monitoring Setup
- Enable Cloud Monitoring API
- Configure custom metrics for all services
- Set up uptime checks for critical endpoints
- Configure log-based metrics

### Alert Evaluation
- Deploy alert evaluator as Cloud Function triggered every minute
- Use Cloud Scheduler for reliable execution
- Implement idempotency for alert triggers

### Performance Optimization
- Cache metric baselines in Redis
- Use batch queries for multiple metrics
- Implement pagination for large result sets
- Pre-aggregate metrics for common time ranges
