# Cloud Run Configuration Quick Reference

This document provides quick reference commands for configuring the signal-insight pipeline services on Cloud Run.

## Service Configuration

### Update Environment Variables

**utxoiq-ingestion:**
```bash
gcloud run services update utxoiq-ingestion \
    --set-env-vars GCP_PROJECT_ID=utxoiq-dev,BIGQUERY_DATASET_BTC=btc,BIGQUERY_DATASET_INTEL=intel \
    --region=us-central1
```

**insight-generator:**
```bash
gcloud run services update insight-generator \
    --set-env-vars GCP_PROJECT_ID=utxoiq-dev,DATASET_INTEL=intel,AI_PROVIDER=vertex_ai \
    --region=us-central1
```

### Update Resource Limits

**Increase memory:**
```bash
gcloud run services update insight-generator \
    --memory=4Gi \
    --region=us-central1
```

**Increase CPU:**
```bash
gcloud run services update insight-generator \
    --cpu=2 \
    --region=us-central1
```

**Increase timeout:**
```bash
gcloud run services update insight-generator \
    --timeout=600 \
    --region=us-central1
```

### Configure Auto-Scaling

**Set min/max instances:**
```bash
gcloud run services update insight-generator \
    --min-instances=1 \
    --max-instances=10 \
    --region=us-central1
```

**Set concurrency:**
```bash
gcloud run services update insight-generator \
    --concurrency=20 \
    --region=us-central1
```

**Enable CPU throttling (save costs):**
```bash
gcloud run services update insight-generator \
    --cpu-throttling \
    --region=us-central1
```

**Disable CPU throttling (better performance):**
```bash
gcloud run services update insight-generator \
    --no-cpu-throttling \
    --region=us-central1
```

## Secret Management

### Create Secrets

**OpenAI API Key:**
```bash
echo -n "sk-your-openai-key" | gcloud secrets create openai-api-key --data-file=-
```

**Anthropic API Key:**
```bash
echo -n "sk-ant-your-anthropic-key" | gcloud secrets create anthropic-api-key --data-file=-
```

**Grok API Key:**
```bash
echo -n "xai-your-grok-key" | gcloud secrets create grok-api-key --data-file=-
```

**Bitcoin RPC Password:**
```bash
echo -n "your-rpc-password" | gcloud secrets create bitcoin-rpc-password --data-file=-
```

### Grant Access to Secrets

```bash
# Get service account email
PROJECT_NUMBER=$(gcloud projects describe utxoiq-dev --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant access to secret
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

### Mount Secrets as Environment Variables

```bash
gcloud run services update insight-generator \
    --update-secrets=OPENAI_API_KEY=openai-api-key:latest \
    --region=us-central1
```

### Mount Multiple Secrets

```bash
gcloud run services update insight-generator \
    --update-secrets=OPENAI_API_KEY=openai-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --region=us-central1
```

## AI Provider Configuration

### Vertex AI (Recommended)

```bash
gcloud run services update insight-generator \
    --set-env-vars AI_PROVIDER=vertex_ai,VERTEX_AI_PROJECT=utxoiq-dev,VERTEX_AI_LOCATION=us-central1 \
    --region=us-central1
```

### OpenAI

```bash
gcloud run services update insight-generator \
    --set-env-vars AI_PROVIDER=openai,OPENAI_MODEL=gpt-4-turbo \
    --update-secrets=OPENAI_API_KEY=openai-api-key:latest \
    --region=us-central1
```

### Anthropic

```bash
gcloud run services update insight-generator \
    --set-env-vars AI_PROVIDER=anthropic,ANTHROPIC_MODEL=claude-3-opus-20240229 \
    --update-secrets=ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --region=us-central1
```

### xAI Grok

```bash
gcloud run services update insight-generator \
    --set-env-vars AI_PROVIDER=grok,GROK_MODEL=grok-beta \
    --update-secrets=GROK_API_KEY=grok-api-key:latest \
    --region=us-central1
```

## Signal Processor Configuration

### Enable/Disable Processors

```bash
gcloud run services update utxoiq-ingestion \
    --set-env-vars MEMPOOL_PROCESSOR_ENABLED=true,EXCHANGE_PROCESSOR_ENABLED=true,MINER_PROCESSOR_ENABLED=true,WHALE_PROCESSOR_ENABLED=true,TREASURY_PROCESSOR_ENABLED=true,PREDICTIVE_PROCESSOR_ENABLED=true \
    --region=us-central1
```

### Adjust Confidence Threshold

```bash
# Higher threshold = fewer but higher quality signals
gcloud run services update utxoiq-ingestion \
    --set-env-vars CONFIDENCE_THRESHOLD=0.8 \
    --region=us-central1

# Lower threshold = more signals but lower quality
gcloud run services update utxoiq-ingestion \
    --set-env-vars CONFIDENCE_THRESHOLD=0.6 \
    --region=us-central1
```

### Configure Time Windows

```bash
gcloud run services update utxoiq-ingestion \
    --set-env-vars MEMPOOL_TIME_WINDOW=1h,EXCHANGE_TIME_WINDOW=24h,MINER_TIME_WINDOW=7d \
    --region=us-central1
```

## Monitoring Configuration

### Enable Monitoring

```bash
gcloud run services update utxoiq-ingestion \
    --set-env-vars MONITORING_ENABLED=true \
    --region=us-central1
```

### Configure Polling Interval

```bash
# insight-generator polling interval
gcloud run services update insight-generator \
    --set-env-vars POLL_INTERVAL_SECONDS=10 \
    --region=us-central1

# utxoiq-ingestion block polling interval
gcloud run services update utxoiq-ingestion \
    --set-env-vars POLL_INTERVAL=30 \
    --region=us-central1
```

## Traffic Management

### Split Traffic Between Revisions

```bash
# 50/50 split for canary deployment
gcloud run services update-traffic insight-generator \
    --to-revisions=REVISION_1=50,REVISION_2=50 \
    --region=us-central1
```

### Route All Traffic to Specific Revision

```bash
gcloud run services update-traffic insight-generator \
    --to-revisions=REVISION_NAME=100 \
    --region=us-central1
```

### Route All Traffic to Latest

```bash
gcloud run services update-traffic insight-generator \
    --to-latest \
    --region=us-central1
```

## Service Management

### List Services

```bash
gcloud run services list --region=us-central1
```

### Describe Service

```bash
gcloud run services describe insight-generator --region=us-central1
```

### List Revisions

```bash
gcloud run revisions list --service=insight-generator --region=us-central1
```

### Delete Service

```bash
gcloud run services delete insight-generator --region=us-central1
```

### Delete Revision

```bash
gcloud run revisions delete REVISION_NAME --region=us-central1
```

## IAM and Permissions

### Allow Unauthenticated Access

```bash
gcloud run services add-iam-policy-binding insight-generator \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region=us-central1
```

### Require Authentication

```bash
gcloud run services remove-iam-policy-binding insight-generator \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --region=us-central1
```

### Grant Service Account Access

```bash
gcloud run services add-iam-policy-binding insight-generator \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker" \
    --region=us-central1
```

## Logging

### View Logs

```bash
# All logs
gcloud logging tail "resource.type=cloud_run_revision"

# Specific service
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=insight-generator"

# Error logs only
gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR"

# With correlation ID
gcloud logging tail "resource.type=cloud_run_revision AND jsonPayload.correlation_id=CORRELATION_ID"
```

### Export Logs to BigQuery

```bash
gcloud logging sinks create insight-generator-logs \
    bigquery.googleapis.com/projects/utxoiq-dev/datasets/logs \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="insight-generator"'
```

## Cost Optimization

### Reduce Costs (Accept Cold Starts)

```bash
gcloud run services update insight-generator \
    --min-instances=0 \
    --max-instances=3 \
    --cpu-throttling \
    --region=us-central1
```

### Optimize for Performance (Higher Costs)

```bash
gcloud run services update insight-generator \
    --min-instances=2 \
    --max-instances=10 \
    --no-cpu-throttling \
    --memory=4Gi \
    --cpu=2 \
    --region=us-central1
```

### Balanced Configuration

```bash
gcloud run services update insight-generator \
    --min-instances=1 \
    --max-instances=5 \
    --cpu-throttling \
    --memory=2Gi \
    --cpu=1 \
    --region=us-central1
```

## Testing

### Test Health Endpoint

```bash
curl https://insight-generator-PROJECT_NUMBER.us-central1.run.app/health
```

### Trigger Manual Polling Cycle

```bash
curl -X POST https://insight-generator-PROJECT_NUMBER.us-central1.run.app/trigger-cycle
```

### Check Service Stats

```bash
curl https://insight-generator-PROJECT_NUMBER.us-central1.run.app/stats
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 https://insight-generator-PROJECT_NUMBER.us-central1.run.app/health
```

## Troubleshooting Commands

### Check Service Status

```bash
gcloud run services describe insight-generator --region=us-central1 --format=json
```

### Check Latest Revision

```bash
gcloud run revisions describe $(gcloud run services describe insight-generator --region=us-central1 --format="value(status.latestReadyRevisionName)") --region=us-central1
```

### Check Environment Variables

```bash
gcloud run services describe insight-generator --region=us-central1 --format="value(spec.template.spec.containers[0].env)"
```

### Check Resource Limits

```bash
gcloud run services describe insight-generator --region=us-central1 --format="value(spec.template.spec.containers[0].resources)"
```

### Force New Deployment

```bash
gcloud run services update insight-generator \
    --region=us-central1 \
    --no-traffic
```

## Useful Aliases

Add these to your `.bashrc` or `.zshrc`:

```bash
# Cloud Run aliases
alias cr-list='gcloud run services list --region=us-central1'
alias cr-logs='gcloud logging tail "resource.type=cloud_run_revision"'
alias cr-errors='gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR"'

# Service-specific aliases
alias ig-health='curl https://insight-generator-PROJECT_NUMBER.us-central1.run.app/health'
alias ig-stats='curl https://insight-generator-PROJECT_NUMBER.us-central1.run.app/stats'
alias ig-trigger='curl -X POST https://insight-generator-PROJECT_NUMBER.us-central1.run.app/trigger-cycle'
alias ig-logs='gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=insight-generator"'

alias ui-health='curl https://utxoiq-ingestion-PROJECT_NUMBER.us-central1.run.app/health'
alias ui-status='curl https://utxoiq-ingestion-PROJECT_NUMBER.us-central1.run.app/status'
alias ui-logs='gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=utxoiq-ingestion"'
```

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [gcloud run commands](https://cloud.google.com/sdk/gcloud/reference/run)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
