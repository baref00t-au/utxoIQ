# Alert Evaluator Cloud Function

This Cloud Function evaluates monitoring alerts every 60 seconds and sends notifications when thresholds are exceeded.

## Overview

The alert evaluator:
- Runs every 60 seconds via Cloud Scheduler
- Evaluates all enabled alert configurations
- Queries current metrics from Cloud Monitoring
- Triggers alerts when thresholds are crossed
- Resolves alerts when conditions clear
- Sends notifications via email, Slack, and SMS
- Implements idempotency to prevent duplicate alerts

## Architecture

```
Cloud Scheduler (every 60s)
    ↓
Cloud Function (alert-evaluator)
    ↓
├── Query Cloud Monitoring metrics
├── Check alert configurations (Cloud SQL)
├── Evaluate thresholds
└── Send notifications (SendGrid, Slack, Twilio)
```

## Environment Variables

Required:
- `GCP_PROJECT_ID` - Google Cloud project ID
- `DATABASE_URL` - PostgreSQL connection string (asyncpg format)

Optional:
- `REDIS_URL` - Redis connection string for caching
- `SENDGRID_API_KEY` - SendGrid API key for email notifications
- `SLACK_WEBHOOK_URL` - Slack webhook URL for Slack notifications
- `TWILIO_ACCOUNT_SID` - Twilio account SID for SMS
- `TWILIO_AUTH_TOKEN` - Twilio auth token for SMS
- `TWILIO_FROM_NUMBER` - Twilio phone number for SMS
- `ALERT_EMAIL_RECIPIENTS` - Comma-separated email addresses
- `ALERT_SMS_RECIPIENTS` - Comma-separated phone numbers

## Deployment

### Prerequisites

1. Install gcloud CLI
2. Authenticate with GCP: `gcloud auth login`
3. Set project: `gcloud config set project YOUR_PROJECT_ID`
4. Enable required APIs:
   ```bash
   gcloud services enable cloudfunctions.googleapis.com
   gcloud services enable cloudscheduler.googleapis.com
   gcloud services enable monitoring.googleapis.com
   ```

### Deploy

**Linux/Mac:**
```bash
export GCP_PROJECT_ID="your-project-id"
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
export REDIS_URL="redis://host:6379"
export SENDGRID_API_KEY="your-sendgrid-key"
export SLACK_WEBHOOK_URL="your-slack-webhook"

cd infrastructure/monitoring
chmod +x deploy-alert-evaluator.sh
./deploy-alert-evaluator.sh
```

**Windows (PowerShell):**
```powershell
$env:GCP_PROJECT_ID = "your-project-id"
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
$env:REDIS_URL = "redis://host:6379"
$env:SENDGRID_API_KEY = "your-sendgrid-key"
$env:SLACK_WEBHOOK_URL = "your-slack-webhook"

cd infrastructure\monitoring
.\deploy-alert-evaluator.ps1
```

## Testing

### Manual Trigger

Trigger the function manually via Cloud Scheduler:
```bash
gcloud scheduler jobs run alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID
```

### View Logs

View function logs:
```bash
gcloud functions logs read alert-evaluator \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --gen2 \
    --limit=50
```

### Local Testing

Test the function locally:
```bash
cd alert-evaluator-function

# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db"

# Run function
python main.py
```

## Monitoring

### Cloud Monitoring Metrics

The function automatically reports metrics to Cloud Monitoring:
- Execution count
- Execution duration
- Error count
- Alert evaluation summary

### Logs

All evaluation results are logged with structured logging:
- Execution ID for tracing
- Alert evaluation summary
- Individual alert results
- Error details with stack traces

### Alerts

Set up alerts for the function itself:
- Function execution failures
- High error rate
- Long execution duration
- No executions (scheduler failure)

## Idempotency

The function implements idempotency to prevent duplicate alerts:

1. **Active Alert Check**: Before triggering an alert, checks if an active (unresolved) alert already exists for the configuration
2. **Database Transaction**: Uses database transactions to ensure atomic alert creation
3. **Execution ID**: Each execution has a unique ID for tracing and debugging

## Error Handling

The function handles errors gracefully:

1. **Per-Alert Errors**: If one alert evaluation fails, others continue
2. **Metric Not Found**: Logs warning and skips alert if metric data unavailable
3. **Notification Failures**: Logs error but marks alert as triggered
4. **Database Errors**: Rolls back transaction and logs error
5. **Retry Logic**: Cloud Scheduler automatically retries failed executions

## Performance

- **Cold Start**: ~2-3 seconds
- **Warm Execution**: ~500ms per alert
- **Timeout**: 540 seconds (9 minutes)
- **Memory**: 512MB
- **Max Instances**: 10 (prevents overwhelming downstream services)

## Cost Estimation

Based on 1 execution per minute:
- Cloud Functions: ~$0.50/month (43,200 invocations)
- Cloud Scheduler: $0.10/month (1 job)
- Cloud Monitoring API: Included in free tier
- Total: ~$0.60/month

## Troubleshooting

### Function Not Executing

1. Check Cloud Scheduler job status:
   ```bash
   gcloud scheduler jobs describe alert-evaluation-job \
       --location=us-central1 \
       --project=YOUR_PROJECT_ID
   ```

2. Check function deployment:
   ```bash
   gcloud functions describe alert-evaluator \
       --region=us-central1 \
       --project=YOUR_PROJECT_ID \
       --gen2
   ```

### Alerts Not Triggering

1. Check function logs for errors
2. Verify alert configurations are enabled
3. Verify metrics exist in Cloud Monitoring
4. Check threshold values and operators

### Notifications Not Sending

1. Verify environment variables are set
2. Check notification service credentials
3. Review function logs for notification errors
4. Test notification services independently

## Security

- Function uses service account authentication
- Database credentials stored in environment variables
- API keys stored in Secret Manager (recommended)
- Function not publicly accessible (requires authentication)
- HTTPS only for all external calls

## Maintenance

### Update Function

Redeploy with updated code:
```bash
./deploy-alert-evaluator.sh
```

### Update Schedule

Change evaluation frequency:
```bash
gcloud scheduler jobs update http alert-evaluation-job \
    --location=us-central1 \
    --schedule="*/5 * * * *"  # Every 5 minutes
```

### Pause Evaluations

Pause the scheduler job:
```bash
gcloud scheduler jobs pause alert-evaluation-job \
    --location=us-central1
```

Resume:
```bash
gcloud scheduler jobs resume alert-evaluation-job \
    --location=us-central1
```

## Future Enhancements

- [ ] Support for custom metric queries
- [ ] Alert grouping and deduplication
- [ ] Anomaly detection with ML
- [ ] Alert escalation policies
- [ ] Integration with PagerDuty/Opsgenie
- [ ] Alert acknowledgment workflow
- [ ] Historical alert analytics
