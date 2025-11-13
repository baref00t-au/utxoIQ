# Cloud Logging Configuration for Audit Events

This directory contains Terraform configuration for Cloud Logging audit log retention and monitoring.

## Overview

The audit logging system captures security-critical events including:
- Successful and failed login attempts
- API key creation and revocation
- Role and subscription tier changes
- Authorization failures

## Components

### 1. Log Bucket (`audit-logs`)
- **Retention**: 365 days (1 year) as per compliance requirements
- **Analytics**: Enabled for querying and analysis
- **Purpose**: Primary storage for audit logs with fast access

### 2. Cloud Storage Archive
- **Bucket**: `{project-id}-audit-logs-archive`
- **Storage Class**: NEARLINE (cost-effective for infrequent access)
- **Lifecycle**:
  - After 90 days: Transition to ARCHIVE storage class
  - After 7 years: Automatic deletion
- **Versioning**: Enabled for audit trail integrity
- **Purpose**: Long-term archival storage for compliance

### 3. Log Sink
- **Name**: `audit-logs-storage-sink`
- **Filter**: Captures all audit event types
- **Destination**: Cloud Storage bucket for archival
- **Purpose**: Automatic export of audit logs to long-term storage

### 4. Log-Based Metrics

#### Failed Login Attempts
- **Metric**: `failed_login_attempts`
- **Type**: DELTA counter
- **Labels**: `reason`, `auth_method`
- **Purpose**: Monitor authentication failures for security threats

#### Successful Logins
- **Metric**: `successful_logins`
- **Type**: DELTA counter
- **Labels**: `auth_method`
- **Purpose**: Track authentication patterns

#### API Key Events
- **Metric**: `api_key_events`
- **Type**: DELTA counter
- **Labels**: `event_type`
- **Purpose**: Monitor API key lifecycle events

#### Authorization Failures
- **Metric**: `authorization_failures`
- **Type**: DELTA counter
- **Labels**: `event_type`, `user_role`
- **Purpose**: Track access control violations

### 5. Alert Policies

#### Excessive Failed Logins
- **Threshold**: > 10 failed attempts per minute
- **Duration**: 60 seconds
- **Auto-close**: 30 minutes
- **Purpose**: Detect potential brute force or credential stuffing attacks

## Deployment

### Prerequisites
- Terraform >= 1.0
- GCP project with appropriate permissions
- Notification channels configured (optional)

### Deploy Infrastructure

```bash
cd infrastructure/monitoring

# Initialize Terraform
terraform init

# Review planned changes
terraform plan \
  -var="project_id=your-project-id" \
  -var="environment=prod" \
  -var="region=us-central1"

# Apply configuration
terraform apply \
  -var="project_id=your-project-id" \
  -var="environment=prod" \
  -var="region=us-central1"
```

### Configure Alert Notifications

To receive alerts for security events:

1. Create notification channels in Cloud Monitoring:
   ```bash
   gcloud alpha monitoring channels create \
     --display-name="Security Team Email" \
     --type=email \
     --channel-labels=email_address=security@example.com
   ```

2. Get the channel ID:
   ```bash
   gcloud alpha monitoring channels list
   ```

3. Update Terraform variables:
   ```bash
   terraform apply \
     -var="project_id=your-project-id" \
     -var="environment=prod" \
     -var="alert_notification_channels=[\"projects/PROJECT_ID/notificationChannels/CHANNEL_ID\"]"
   ```

## Querying Audit Logs

### Using Cloud Console
1. Navigate to Cloud Logging > Logs Explorer
2. Use the following query:
   ```
   logName="projects/PROJECT_ID/logs/audit"
   jsonPayload.event_type="successful_login"
   ```

### Using gcloud CLI

```bash
# View recent successful logins
gcloud logging read \
  'jsonPayload.event_type="successful_login"' \
  --limit 50 \
  --format json

# View failed login attempts
gcloud logging read \
  'jsonPayload.event_type="failed_login"' \
  --limit 50 \
  --format json

# View API key events
gcloud logging read \
  'jsonPayload.event_type=~"api_key_.*"' \
  --limit 50 \
  --format json

# View authorization failures
gcloud logging read \
  'jsonPayload.event_type="authorization_failure"' \
  --limit 50 \
  --format json
```

### Using BigQuery (for analytics)

Export logs to BigQuery for advanced analysis:

```sql
-- Count failed logins by reason
SELECT
  jsonPayload.reason,
  COUNT(*) as count
FROM
  `project.dataset.audit_logs_*`
WHERE
  jsonPayload.event_type = 'failed_login'
  AND _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY
  jsonPayload.reason
ORDER BY
  count DESC;

-- Identify users with multiple failed login attempts
SELECT
  jsonPayload.email,
  jsonPayload.ip_address,
  COUNT(*) as failed_attempts
FROM
  `project.dataset.audit_logs_*`
WHERE
  jsonPayload.event_type = 'failed_login'
  AND _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
GROUP BY
  jsonPayload.email,
  jsonPayload.ip_address
HAVING
  failed_attempts > 5
ORDER BY
  failed_attempts DESC;
```

## Compliance

### Retention Policy
- **Primary Storage**: 1 year in Cloud Logging bucket
- **Archive Storage**: 7 years in Cloud Storage
- **Compliance**: Meets common regulatory requirements (SOC 2, GDPR, HIPAA)

### Access Control
- Audit logs are protected with IAM permissions
- Only authorized personnel can access audit logs
- All access to audit logs is itself logged

### Integrity
- Log versioning enabled in Cloud Storage
- Immutable log entries in Cloud Logging
- Correlation IDs for request tracing

## Monitoring Dashboard

Create a custom dashboard in Cloud Monitoring:

```bash
# Example: Create dashboard via gcloud
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

Dashboard should include:
- Failed login rate over time
- Successful login rate by auth method
- API key creation/revocation events
- Authorization failure rate by user role

## Troubleshooting

### Logs Not Appearing
1. Check log sink status:
   ```bash
   gcloud logging sinks describe audit-logs-storage-sink
   ```

2. Verify IAM permissions:
   ```bash
   gcloud storage buckets get-iam-policy gs://PROJECT_ID-audit-logs-archive
   ```

3. Check application logging configuration:
   ```python
   # Verify structured logging is enabled
   import logging
   logger = logging.getLogger("audit")
   logger.info("Test audit log", extra={"event_type": "test"})
   ```

### High Storage Costs
- Review lifecycle policies in Cloud Storage
- Consider adjusting retention periods
- Use ARCHIVE storage class for older logs

### Missing Correlation IDs
- Ensure correlation ID middleware is enabled
- Check that `X-Correlation-ID` header is set
- Verify context variable is properly configured

## Security Best Practices

1. **Restrict Access**: Limit who can view audit logs
2. **Monitor Alerts**: Respond promptly to security alerts
3. **Regular Reviews**: Periodically review audit logs for anomalies
4. **Backup**: Ensure Cloud Storage bucket has versioning enabled
5. **Encryption**: All logs are encrypted at rest and in transit

## References

- [Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [Log-based Metrics](https://cloud.google.com/logging/docs/logs-based-metrics)
- [Cloud Storage Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)
- [Cloud Monitoring Alerts](https://cloud.google.com/monitoring/alerts)
