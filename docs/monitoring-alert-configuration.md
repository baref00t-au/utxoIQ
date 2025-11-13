# Alert Configuration Guide

## Overview

The utxoIQ monitoring system provides customizable alerts that notify you when metrics exceed defined thresholds. This guide covers how to configure, manage, and optimize your alert configurations.

## Alert Configuration Basics

### Alert Components

Every alert configuration consists of:

1. **Metric Type**: The metric to monitor (CPU, memory, latency, error rate)
2. **Threshold**: The value that triggers the alert
3. **Comparison Operator**: How to compare the metric value to the threshold
4. **Severity Level**: The importance of the alert (info, warning, critical)
5. **Notification Channels**: Where to send alerts (email, Slack, SMS)
6. **Evaluation Window**: How long to observe the metric before triggering

### Supported Metrics

#### System Metrics
- `cpu_usage` - CPU utilization percentage (0-100)
- `memory_usage` - Memory utilization percentage (0-100)
- `disk_usage` - Disk space utilization percentage (0-100)

#### Application Metrics
- `api_response_time` - API endpoint latency in milliseconds
- `error_rate` - Error rate as percentage of total requests
- `request_rate` - Requests per second
- `queue_depth` - Number of pending tasks in queue

#### Bitcoin-Specific Metrics
- `mempool_size` - Number of transactions in mempool
- `mempool_fee_rate` - Average fee rate in sat/vB
- `block_processing_time` - Time to process a block in seconds
- `insight_generation_time` - Time to generate insights in seconds

## Creating Alert Configurations

### Via Web UI

1. Navigate to **Monitoring** → **Alerts**
2. Click **Create Alert**
3. Fill in the alert configuration form:
   - **Name**: Descriptive name for the alert
   - **Service**: Select the service to monitor
   - **Metric**: Choose the metric type
   - **Threshold Type**: Select absolute, percentage, or rate of change
   - **Threshold Value**: Enter the numeric threshold
   - **Comparison**: Choose operator (>, <, >=, <=, ==)
   - **Severity**: Select info, warning, or critical
   - **Evaluation Window**: Set observation period (60-3600 seconds)
   - **Notification Channels**: Select email, Slack, and/or SMS
4. Click **Create Alert**

### Via API

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/alerts \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High API Latency",
    "service_name": "web-api",
    "metric_type": "api_response_time",
    "threshold_type": "absolute",
    "threshold_value": 500,
    "comparison_operator": ">",
    "severity": "warning",
    "evaluation_window_seconds": 300,
    "notification_channels": ["email", "slack"]
  }'
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "High API Latency",
  "service_name": "web-api",
  "metric_type": "api_response_time",
  "threshold_value": 500,
  "severity": "warning",
  "enabled": true,
  "created_at": "2025-11-11T10:30:00Z"
}
```

## Threshold Types

### Absolute Value
Triggers when the metric crosses a specific value.

**Example**: Alert when CPU usage exceeds 80%
```json
{
  "threshold_type": "absolute",
  "threshold_value": 80,
  "comparison_operator": ">"
}
```

### Percentage Change
Triggers when the metric changes by a percentage compared to baseline.

**Example**: Alert when error rate increases by 50% from baseline
```json
{
  "threshold_type": "percentage",
  "threshold_value": 50,
  "comparison_operator": ">"
}
```

### Rate of Change
Triggers when the metric changes at a specific rate per time unit.

**Example**: Alert when request rate increases by 100 req/s per minute
```json
{
  "threshold_type": "rate",
  "threshold_value": 100,
  "comparison_operator": ">"
}
```

## Severity Levels

### Info
- Non-critical notifications
- Informational alerts for awareness
- No immediate action required
- Sent to email and Slack only

**Use cases**: Deployment notifications, configuration changes, scheduled maintenance

### Warning
- Potential issues that need attention
- May require investigation
- Not immediately critical
- Sent to email and Slack

**Use cases**: Elevated latency, increased error rates, resource usage approaching limits

### Critical
- Urgent issues requiring immediate action
- Service degradation or outage
- Sent to email, Slack, and SMS
- Triggers on-call escalation

**Use cases**: Service down, database connection failures, critical resource exhaustion

## Notification Channels

### Email Notifications

Email alerts include:
- Alert severity and service name
- Current metric value and threshold
- Timestamp of alert trigger
- Link to monitoring dashboard
- Historical context chart

**Configuration**: Email addresses are configured in user profile settings.

### Slack Notifications

Slack alerts include:
- Color-coded severity indicator
- Service and metric details
- Current value vs threshold
- Quick action buttons
- Timestamp

**Configuration**: 
1. Create a Slack webhook URL in your workspace
2. Add webhook URL to notification settings
3. Select Slack channel in alert configuration

### SMS Notifications

SMS alerts are **critical severity only** and include:
- Service name
- Brief issue description
- Timestamp

**Configuration**:
1. Add phone numbers in user profile (up to 5 numbers)
2. Verify phone numbers via SMS code
3. Enable SMS for critical alerts

**Limitations**:
- Maximum 160 characters per message
- Critical severity only
- Rate limited to prevent spam
- Delivery status tracked

## Alert Suppression

### Maintenance Windows

Suppress alerts during planned maintenance to prevent notification spam.

**Via UI**:
1. Edit alert configuration
2. Enable **Suppression**
3. Set start and end times
4. Save configuration

**Via API**:
```bash
curl -X PATCH https://api.utxoiq.com/api/v1/monitoring/alerts/{alert_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "suppression_enabled": true,
    "suppression_start": "2025-11-11T22:00:00Z",
    "suppression_end": "2025-11-12T02:00:00Z"
  }'
```

### Temporary Disable

Temporarily disable an alert without deleting it:

```bash
curl -X PATCH https://api.utxoiq.com/api/v1/monitoring/alerts/{alert_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## Alert Management

### Listing Alerts

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/alerts \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Query Parameters**:
- `service_name` - Filter by service
- `severity` - Filter by severity level
- `enabled` - Filter by enabled status

### Updating Alerts

```bash
curl -X PATCH https://api.utxoiq.com/api/v1/monitoring/alerts/{alert_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_value": 600,
    "notification_channels": ["email", "slack", "sms"]
  }'
```

### Deleting Alerts

```bash
curl -X DELETE https://api.utxoiq.com/api/v1/monitoring/alerts/{alert_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Best Practices

### Threshold Selection

1. **Start Conservative**: Begin with higher thresholds and adjust based on false positives
2. **Use Baselines**: Reference historical data to set realistic thresholds
3. **Consider Time of Day**: Different thresholds for peak vs off-peak hours
4. **Account for Growth**: Adjust thresholds as traffic increases

### Notification Strategy

1. **Severity Mapping**: 
   - Info: FYI notifications, no action needed
   - Warning: Investigate within 1 hour
   - Critical: Immediate response required

2. **Channel Selection**:
   - Email: All severities, detailed information
   - Slack: Warning and critical, team awareness
   - SMS: Critical only, on-call engineers

3. **Avoid Alert Fatigue**:
   - Don't over-alert on minor issues
   - Use appropriate evaluation windows
   - Consolidate related alerts
   - Review and tune regularly

### Evaluation Windows

- **Short windows (60-120s)**: Critical metrics requiring immediate response
- **Medium windows (300-600s)**: Standard application metrics
- **Long windows (900-3600s)**: Trend-based alerts, capacity planning

### Alert Naming

Use descriptive names that include:
- Service name
- Metric being monitored
- Threshold context

**Examples**:
- ✅ "Web API - Response Time > 500ms"
- ✅ "Feature Engine - CPU Usage > 80%"
- ❌ "High CPU"
- ❌ "Alert 1"

## Common Alert Configurations

### High API Latency
```json
{
  "name": "Web API - High Response Time",
  "service_name": "web-api",
  "metric_type": "api_response_time",
  "threshold_type": "absolute",
  "threshold_value": 500,
  "comparison_operator": ">",
  "severity": "warning",
  "evaluation_window_seconds": 300,
  "notification_channels": ["email", "slack"]
}
```

### Critical Error Rate
```json
{
  "name": "Feature Engine - High Error Rate",
  "service_name": "feature-engine",
  "metric_type": "error_rate",
  "threshold_type": "absolute",
  "threshold_value": 5,
  "comparison_operator": ">",
  "severity": "critical",
  "evaluation_window_seconds": 180,
  "notification_channels": ["email", "slack", "sms"]
}
```

### Memory Exhaustion
```json
{
  "name": "Insight Generator - Memory Critical",
  "service_name": "insight-generator",
  "metric_type": "memory_usage",
  "threshold_type": "absolute",
  "threshold_value": 90,
  "comparison_operator": ">",
  "severity": "critical",
  "evaluation_window_seconds": 120,
  "notification_channels": ["email", "slack", "sms"]
}
```

### Mempool Congestion
```json
{
  "name": "Bitcoin - Mempool Congestion",
  "service_name": "data-ingestion",
  "metric_type": "mempool_size",
  "threshold_type": "absolute",
  "threshold_value": 100000,
  "comparison_operator": ">",
  "severity": "info",
  "evaluation_window_seconds": 600,
  "notification_channels": ["email"]
}
```

## Troubleshooting

### Alert Not Triggering

1. **Check alert is enabled**: Verify `enabled: true` in configuration
2. **Verify metric exists**: Ensure service is reporting the metric
3. **Check evaluation window**: May need longer observation period
4. **Review threshold**: Threshold may be too high/low
5. **Check suppression**: Ensure not in maintenance window

### Too Many False Positives

1. **Increase threshold**: Adjust to more realistic value
2. **Lengthen evaluation window**: Reduce sensitivity to spikes
3. **Change threshold type**: Consider percentage or rate instead of absolute
4. **Review baseline**: Ensure baseline calculation is accurate

### Notifications Not Received

1. **Verify notification channels**: Check configuration includes desired channels
2. **Check email/phone settings**: Ensure contact info is correct
3. **Review spam filters**: Check email spam/junk folders
4. **Check Slack webhook**: Verify webhook URL is valid
5. **Review notification logs**: Check alert history for delivery status

## API Reference

### Create Alert
`POST /api/v1/monitoring/alerts`

### List Alerts
`GET /api/v1/monitoring/alerts`

### Get Alert
`GET /api/v1/monitoring/alerts/{alert_id}`

### Update Alert
`PATCH /api/v1/monitoring/alerts/{alert_id}`

### Delete Alert
`DELETE /api/v1/monitoring/alerts/{alert_id}`

### Get Alert History
`GET /api/v1/monitoring/alerts/history`

For detailed API documentation, see [API Reference](./api-reference-monitoring.md).
