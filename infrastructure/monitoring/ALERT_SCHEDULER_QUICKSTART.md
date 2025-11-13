# Alert Scheduler Quick Start Guide

## Overview

The alert scheduler evaluates monitoring alerts every 60 seconds and sends notifications when thresholds are exceeded.

## Quick Deploy

### 1. Set Environment Variables

```bash
# Required
export GCP_PROJECT_ID="your-project-id"
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"

# Optional (for notifications)
export REDIS_URL="redis://host:6379"
export SENDGRID_API_KEY="SG.xxx"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"
export TWILIO_ACCOUNT_SID="ACxxx"
export TWILIO_AUTH_TOKEN="xxx"
export TWILIO_FROM_NUMBER="+1234567890"
export ALERT_EMAIL_RECIPIENTS="alerts@example.com,oncall@example.com"
export ALERT_SMS_RECIPIENTS="+1234567890,+0987654321"
```

### 2. Deploy

**Linux/Mac:**
```bash
cd infrastructure/monitoring
chmod +x deploy-alert-evaluator.sh
./deploy-alert-evaluator.sh
```

**Windows:**
```powershell
cd infrastructure\monitoring
.\deploy-alert-evaluator.ps1
```

### 3. Test

**Linux/Mac:**
```bash
chmod +x test-alert-scheduler.sh
./test-alert-scheduler.sh
```

**Windows:**
```powershell
.\test-alert-scheduler.ps1
```

## Common Commands

### Manual Trigger
```bash
gcloud scheduler jobs run alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID
```

### View Logs
```bash
gcloud functions logs read alert-evaluator \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --gen2 \
    --limit=50
```

### Pause Scheduler
```bash
gcloud scheduler jobs pause alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID
```

### Resume Scheduler
```bash
gcloud scheduler jobs resume alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID
```

### Update Schedule
```bash
# Change to every 5 minutes
gcloud scheduler jobs update http alert-evaluation-job \
    --location=us-central1 \
    --schedule="*/5 * * * *" \
    --project=YOUR_PROJECT_ID
```

## Monitoring

### Check Status
```bash
# Scheduler job status
gcloud scheduler jobs describe alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID

# Function status
gcloud functions describe alert-evaluator \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --gen2
```

### View Recent Executions
```bash
# Last 10 executions
gcloud functions logs read alert-evaluator \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --gen2 \
    --limit=10 | grep "Alert evaluation complete"
```

### Check for Errors
```bash
# Recent errors
gcloud functions logs read alert-evaluator \
    --region=us-central1 \
    --project=YOUR_PROJECT_ID \
    --gen2 \
    --limit=50 | grep -i error
```

## Troubleshooting

### Function Not Running

1. **Check scheduler status:**
   ```bash
   gcloud scheduler jobs describe alert-evaluation-job \
       --location=us-central1 \
       --project=YOUR_PROJECT_ID \
       --format="value(state)"
   ```
   Should return: `ENABLED`

2. **Check recent executions:**
   ```bash
   gcloud scheduler jobs describe alert-evaluation-job \
       --location=us-central1 \
       --project=YOUR_PROJECT_ID \
       --format="value(lastAttemptTime)"
   ```

3. **Manually trigger:**
   ```bash
   gcloud scheduler jobs run alert-evaluation-job \
       --location=us-central1 \
       --project=YOUR_PROJECT_ID
   ```

### Alerts Not Triggering

1. **Check alert configurations:**
   - Verify alerts are enabled in database
   - Check threshold values and operators
   - Verify metric types match Cloud Monitoring

2. **Check metrics exist:**
   ```bash
   gcloud monitoring time-series list \
       --filter='metric.type="custom.googleapis.com/SERVICE/METRIC"' \
       --project=YOUR_PROJECT_ID
   ```

3. **Check function logs:**
   ```bash
   gcloud functions logs read alert-evaluator \
       --region=us-central1 \
       --project=YOUR_PROJECT_ID \
       --gen2 \
       --limit=50
   ```

### Notifications Not Sending

1. **Verify environment variables:**
   ```bash
   gcloud functions describe alert-evaluator \
       --region=us-central1 \
       --project=YOUR_PROJECT_ID \
       --gen2 \
       --format="value(serviceConfig.environmentVariables)"
   ```

2. **Check notification service credentials:**
   - SendGrid API key valid
   - Slack webhook URL accessible
   - Twilio credentials correct

3. **Test notification services independently:**
   - Send test email via SendGrid
   - Post test message to Slack webhook
   - Send test SMS via Twilio

## Cost Optimization

### Reduce Frequency

For non-critical environments, reduce evaluation frequency:

```bash
# Every 5 minutes
gcloud scheduler jobs update http alert-evaluation-job \
    --location=us-central1 \
    --schedule="*/5 * * * *" \
    --project=YOUR_PROJECT_ID

# Every 15 minutes
gcloud scheduler jobs update http alert-evaluation-job \
    --location=us-central1 \
    --schedule="*/15 * * * *" \
    --project=YOUR_PROJECT_ID
```

### Pause During Off-Hours

Pause scheduler during off-hours:

```bash
# Pause at 6 PM
gcloud scheduler jobs pause alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID

# Resume at 8 AM
gcloud scheduler jobs resume alert-evaluation-job \
    --location=us-central1 \
    --project=YOUR_PROJECT_ID
```

## Best Practices

1. **Start with longer intervals** (5 minutes) and reduce as needed
2. **Use alert suppression** during maintenance windows
3. **Monitor function execution** for errors and performance
4. **Set up alerts** for the function itself
5. **Test notifications** before relying on them
6. **Review alert history** regularly to tune thresholds
7. **Use Redis caching** to reduce Cloud Monitoring API calls
8. **Implement alert grouping** to reduce notification fatigue

## Support

For detailed documentation, see:
- `infrastructure/monitoring/alert-evaluator-function/README.md`
- `docs/task-5-alert-scheduler-implementation.md`

For issues or questions:
1. Check function logs
2. Review test results
3. Consult troubleshooting guide
4. Contact DevOps team
