# Notification Channel Setup Guide

## Overview

The utxoIQ monitoring system supports multiple notification channels to ensure you receive alerts through your preferred communication methods. This guide covers setup and configuration for email, Slack, and SMS notifications.

## Supported Channels

| Channel | Severities | Setup Complexity | Delivery Time |
|---------|-----------|------------------|---------------|
| Email   | All       | Low              | < 1 minute    |
| Slack   | All       | Medium           | < 1 minute    |
| SMS     | Critical only | Medium        | < 2 minutes   |

## Email Notifications

### Setup

Email notifications are automatically enabled for all users with verified email addresses.

#### 1. Verify Email Address

1. Sign in to utxoIQ
2. Navigate to **Profile** → **Settings**
3. Verify your email address via confirmation link
4. Email notifications are now active

#### 2. Add Additional Recipients

```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email_recipients": [
      "primary@example.com",
      "team@example.com",
      "oncall@example.com"
    ]
  }'
```

### Email Content

Email alerts include:

**Subject Line**:
```
[SEVERITY] Alert Name - Service Name
```

**Body Content**:
- Alert severity with color coding
- Service and metric details
- Current metric value
- Threshold value and comparison
- Timestamp of alert trigger
- Historical trend chart (inline image)
- Link to monitoring dashboard
- Quick action buttons (Acknowledge, Suppress, View Details)

### Email Template Example

```
[WARNING] High API Latency - Web API

Service: web-api
Metric: api_response_time
Current Value: 523ms
Threshold: > 500ms
Triggered At: 2025-11-11 10:30:45 UTC

The API response time has exceeded the configured threshold.

[View Dashboard] [Acknowledge Alert] [Suppress for 1 hour]

Historical Trend (Last 1 Hour):
[Chart showing response time over last hour]

Alert ID: 550e8400-e29b-41d4-a716-446655440000
Configuration: View in Dashboard

---
utxoIQ Monitoring System
Unsubscribe | Notification Settings
```

### Email Configuration

#### Customize Email Preferences

```bash
curl -X PATCH https://api.utxoiq.com/api/v1/users/notification-settings \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email_preferences": {
      "include_charts": true,
      "include_historical_context": true,
      "digest_mode": false,
      "quiet_hours": {
        "enabled": true,
        "start": "22:00",
        "end": "08:00",
        "timezone": "America/New_York"
      }
    }
  }'
```

#### Digest Mode

Consolidate multiple alerts into a single email:

```json
{
  "digest_mode": true,
  "digest_interval_minutes": 15,
  "digest_max_alerts": 10
}
```

## Slack Notifications

### Setup

#### 1. Create Slack Webhook

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. Name your app "utxoIQ Monitoring"
4. Select your workspace
5. Navigate to **Incoming Webhooks**
6. Activate **Incoming Webhooks**
7. Click **Add New Webhook to Workspace**
8. Select the channel for alerts
9. Copy the webhook URL

#### 2. Configure Webhook in utxoIQ

**Via UI**:
1. Navigate to **Profile** → **Notification Settings**
2. Click **Add Slack Webhook**
3. Paste webhook URL
4. Select default channel
5. Test connection
6. Save configuration

**Via API**:
```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/slack \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
    "default_channel": "#monitoring-alerts",
    "enabled": true
  }'
```

#### 3. Test Slack Integration

```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/slack/test \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Slack Message Format

Slack alerts use rich formatting with attachments:

```json
{
  "text": "🚨 *WARNING* Alert Triggered",
  "attachments": [{
    "color": "#ff9900",
    "title": "High API Latency - Web API",
    "title_link": "https://app.utxoiq.com/monitoring/alerts/550e8400",
    "text": "API response time has exceeded 500ms threshold",
    "fields": [
      {
        "title": "Service",
        "value": "web-api",
        "short": true
      },
      {
        "title": "Metric",
        "value": "api_response_time",
        "short": true
      },
      {
        "title": "Current Value",
        "value": "523ms",
        "short": true
      },
      {
        "title": "Threshold",
        "value": "> 500ms",
        "short": true
      }
    ],
    "footer": "utxoIQ Monitoring",
    "footer_icon": "https://app.utxoiq.com/icon.png",
    "ts": 1699704645
  }]
}
```

### Severity Color Coding

- **Info**: `#36a64f` (Green)
- **Warning**: `#ff9900` (Orange)
- **Critical**: `#ff0000` (Red)

### Multiple Channels

Configure different channels for different alert types:

```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/slack/channels \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": [
      {
        "name": "#critical-alerts",
        "severity": ["critical"],
        "services": ["*"]
      },
      {
        "name": "#api-monitoring",
        "severity": ["warning", "critical"],
        "services": ["web-api", "feature-engine"]
      },
      {
        "name": "#bitcoin-alerts",
        "severity": ["info", "warning"],
        "services": ["data-ingestion"]
      }
    ]
  }'
```

### Slack Bot Commands

Install the utxoIQ Slack bot for interactive commands:

```
/utxoiq status                    # Show current system status
/utxoiq alerts                    # List active alerts
/utxoiq acknowledge <alert_id>    # Acknowledge an alert
/utxoiq suppress <alert_id> 1h    # Suppress alert for 1 hour
/utxoiq dashboard                 # Get dashboard link
```

## SMS Notifications

### Setup

SMS notifications are available for **critical severity alerts only**.

#### 1. Add Phone Numbers

**Via UI**:
1. Navigate to **Profile** → **Notification Settings**
2. Click **Add Phone Number**
3. Enter phone number in E.164 format (+1234567890)
4. Verify via SMS code
5. Enable SMS notifications

**Via API**:
```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/sms \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": [
      {
        "number": "+12025551234",
        "label": "Primary On-Call",
        "enabled": true
      },
      {
        "number": "+12025555678",
        "label": "Secondary On-Call",
        "enabled": true
      }
    ]
  }'
```

#### 2. Verify Phone Numbers

Each phone number must be verified:

```bash
# Request verification code
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/sms/verify \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12025551234"}'

# Submit verification code
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/sms/confirm \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+12025551234",
    "verification_code": "123456"
  }'
```

### SMS Message Format

SMS messages are limited to 160 characters and include:

```
[CRITICAL] web-api: API response time 1250ms > 1000ms. View: https://utxoiq.com/a/550e8400
```

**Format**:
- `[SEVERITY]` - Alert severity
- `service-name` - Affected service
- Brief description (truncated if needed)
- Short link to alert details

### SMS Limitations

- **Critical severity only**: SMS is not sent for info or warning alerts
- **160 character limit**: Messages are truncated to fit
- **Rate limiting**: Maximum 10 SMS per hour per phone number
- **Delivery tracking**: Delivery status is logged but not guaranteed
- **Cost**: SMS notifications may incur additional charges

### SMS Configuration

```bash
curl -X PATCH https://api.utxoiq.com/api/v1/users/notification-settings/sms \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sms_preferences": {
      "enabled": true,
      "critical_only": true,
      "rate_limit_per_hour": 10,
      "quiet_hours": {
        "enabled": false
      }
    }
  }'
```

## Multi-Channel Strategy

### Recommended Configuration

#### Development Environment
```json
{
  "info": ["email"],
  "warning": ["email", "slack"],
  "critical": ["email", "slack"]
}
```

#### Production Environment
```json
{
  "info": ["email"],
  "warning": ["email", "slack"],
  "critical": ["email", "slack", "sms"]
}
```

### Escalation Policy

Configure escalation for unacknowledged critical alerts:

```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/escalation \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "escalation_policy": {
      "enabled": true,
      "steps": [
        {
          "delay_minutes": 0,
          "channels": ["email", "slack"]
        },
        {
          "delay_minutes": 5,
          "channels": ["sms"],
          "recipients": ["+12025551234"]
        },
        {
          "delay_minutes": 15,
          "channels": ["sms"],
          "recipients": ["+12025555678"]
        }
      ]
    }
  }'
```

## Notification Delivery

### Retry Logic

Failed notifications are automatically retried:

- **Email**: 3 retries with exponential backoff (1m, 5m, 15m)
- **Slack**: 3 retries with exponential backoff (30s, 2m, 5m)
- **SMS**: 1 retry after 1 minute

### Delivery Status

Check notification delivery status:

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/alerts/{alert_id}/notifications \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "notifications": [
    {
      "channel": "email",
      "status": "delivered",
      "sent_at": "2025-11-11T10:30:46Z",
      "delivered_at": "2025-11-11T10:30:48Z"
    },
    {
      "channel": "slack",
      "status": "delivered",
      "sent_at": "2025-11-11T10:30:46Z",
      "delivered_at": "2025-11-11T10:30:47Z"
    },
    {
      "channel": "sms",
      "status": "delivered",
      "sent_at": "2025-11-11T10:30:46Z",
      "delivered_at": "2025-11-11T10:30:50Z",
      "recipient": "+1202555****"
    }
  ]
}
```

## Testing Notifications

### Test All Channels

```bash
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": ["email", "slack", "sms"],
    "severity": "warning"
  }'
```

### Test Specific Channel

```bash
# Test email
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/email/test \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test Slack
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/slack/test \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test SMS
curl -X POST https://api.utxoiq.com/api/v1/users/notification-settings/sms/test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12025551234"}'
```

## Troubleshooting

### Email Not Received

1. **Check spam folder**: Alerts may be filtered as spam
2. **Verify email address**: Ensure email is verified in profile
3. **Check email preferences**: Ensure notifications are enabled
4. **Review quiet hours**: Check if alert was sent during quiet hours
5. **Check delivery logs**: Review notification delivery status

### Slack Not Working

1. **Verify webhook URL**: Ensure webhook is valid and active
2. **Check channel permissions**: Ensure bot has permission to post
3. **Test webhook**: Use test endpoint to verify connection
4. **Review Slack app**: Ensure app is installed in workspace
5. **Check rate limits**: Slack has rate limits on webhook calls

### SMS Not Delivered

1. **Verify phone number**: Ensure number is verified and in E.164 format
2. **Check severity**: SMS is critical severity only
3. **Review rate limits**: Maximum 10 SMS per hour
4. **Check carrier**: Some carriers may block automated SMS
5. **Verify balance**: Ensure SMS credits are available (if applicable)

## Best Practices

### Channel Selection

1. **Email**: Use for all severities, detailed information, audit trail
2. **Slack**: Use for warning and critical, team awareness, quick response
3. **SMS**: Use for critical only, on-call engineers, immediate attention

### Notification Fatigue

1. **Tune thresholds**: Reduce false positives
2. **Use digest mode**: Consolidate multiple alerts
3. **Configure quiet hours**: Respect off-hours
4. **Escalation policies**: Progressive notification strategy
5. **Regular review**: Audit and optimize notification settings

### Security

1. **Protect webhook URLs**: Keep Slack webhooks confidential
2. **Verify phone numbers**: Ensure SMS goes to correct recipients
3. **Use HTTPS**: All webhook URLs must use HTTPS
4. **Rotate credentials**: Periodically rotate webhook URLs
5. **Audit access**: Review who has notification access

## API Reference

### Get Notification Settings
`GET /api/v1/users/notification-settings`

### Update Email Settings
`PATCH /api/v1/users/notification-settings/email`

### Configure Slack
`POST /api/v1/users/notification-settings/slack`

### Add SMS Number
`POST /api/v1/users/notification-settings/sms`

### Test Notifications
`POST /api/v1/users/notification-settings/test`

For detailed API documentation, see [API Reference](./api-reference-monitoring.md).
