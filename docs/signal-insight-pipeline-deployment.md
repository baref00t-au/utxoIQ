# Signal-Insight Pipeline Deployment Guide

This guide covers deploying the complete signal-insight pipeline to Google Cloud Run, including both the `utxoiq-ingestion` and `insight-generator` services.

## Overview

The signal-insight pipeline consists of two microservices:

1. **utxoiq-ingestion**: Monitors Bitcoin blocks, generates signals, and persists them to BigQuery
2. **insight-generator**: Polls BigQuery for unprocessed signals and generates AI-powered insights

## Prerequisites

### Required Tools
- Google Cloud SDK (`gcloud` CLI) installed and configured
- Docker installed (for local testing)
- Access to a GCP project with billing enabled
- Python 3.12+ (for local development)

### Required GCP APIs
Enable the following APIs in your GCP project:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com  # For Vertex AI
```

### BigQuery Setup
Ensure the following datasets and tables exist:
- `btc.blocks` - Bitcoin block data
- `btc.known_entities` - Known exchanges, mining pools, and treasury companies
- `intel.signals` - Generated signals (created by utxoiq-ingestion)
- `intel.insights` - AI-generated insights (created by insight-generator)

## Deployment Options

### Option 1: Deploy Both Services (Recommended)

Use the unified deployment script to deploy both services:

**Windows:**
```bash
scripts\deployment\deploy-signal-insight-pipeline.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/deployment/deploy-signal-insight-pipeline.sh
./scripts/deployment/deploy-signal-insight-pipeline.sh
```

### Option 2: Deploy Services Individually

#### Deploy utxoiq-ingestion

**Windows:**
```bash
scripts\deployment\deploy-utxoiq-ingestion.bat
```

**Linux/Mac:**
```bash
# Use existing script or deploy manually
cd services/utxoiq-ingestion
gcloud run deploy utxoiq-ingestion \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --min-instances 1 \
    --max-instances 3
```

#### Deploy insight-generator

**Windows:**
```bash
scripts\deployment\deploy-insight-generator.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/deployment/deploy-insight-generator.sh
./scripts/deployment/deploy-insight-generator.sh
```

## Configuration

### Environment Variables

#### utxoiq-ingestion Service

Configure these in the Cloud Run console or via `gcloud`:

**Required:**
- `GCP_PROJECT_ID` - Your GCP project ID (e.g., `utxoiq-dev`)
- `BIGQUERY_DATASET_BTC` - BigQuery dataset for blockchain data (default: `btc`)
- `BIGQUERY_DATASET_INTEL` - BigQuery dataset for intelligence data (default: `intel`)

**Optional (for Bitcoin Core monitoring):**
- `BITCOIN_RPC_URL` - Bitcoin Core RPC URL (supports .onion addresses via Tor)
- `BITCOIN_RPC_USER` - Bitcoin Core RPC username
- `BITCOIN_RPC_PASSWORD` - Bitcoin Core RPC password (use Secret Manager)
- `POLL_INTERVAL` - Block polling interval in seconds (default: 30)
- `MEMPOOL_API_URL` - Fallback mempool API URL (default: https://mempool.space/api)

**Signal Processor Configuration:**
- `MEMPOOL_PROCESSOR_ENABLED` - Enable mempool signal processor (default: true)
- `EXCHANGE_PROCESSOR_ENABLED` - Enable exchange signal processor (default: true)
- `MINER_PROCESSOR_ENABLED` - Enable miner signal processor (default: true)
- `WHALE_PROCESSOR_ENABLED` - Enable whale signal processor (default: true)
- `TREASURY_PROCESSOR_ENABLED` - Enable treasury signal processor (default: true)
- `PREDICTIVE_PROCESSOR_ENABLED` - Enable predictive analytics (default: true)
- `CONFIDENCE_THRESHOLD` - Minimum confidence for signal persistence (default: 0.7)

#### insight-generator Service

Configure these in the Cloud Run console or via `gcloud`:

**Required:**
- `GCP_PROJECT_ID` - Your GCP project ID (e.g., `utxoiq-dev`)
- `DATASET_INTEL` - BigQuery dataset for intelligence data (default: `intel`)
- `AI_PROVIDER` - AI provider to use: `vertex_ai`, `openai`, `anthropic`, or `grok`

**Polling Configuration:**
- `POLL_INTERVAL_SECONDS` - Signal polling interval (default: 10)
- `CONFIDENCE_THRESHOLD` - Minimum confidence for insight generation (default: 0.7)

**AI Provider Configuration (choose one):**

**Vertex AI (Recommended):**
- `VERTEX_AI_PROJECT` - GCP project ID for Vertex AI
- `VERTEX_AI_LOCATION` - Vertex AI location (default: us-central1)
- `VERTEX_AI_MODEL` - Model name (default: gemini-pro)

**OpenAI:**
- `OPENAI_API_KEY` - OpenAI API key (use Secret Manager)
- `OPENAI_MODEL` - Model name (default: gpt-4-turbo)

**Anthropic:**
- `ANTHROPIC_API_KEY` - Anthropic API key (use Secret Manager)
- `ANTHROPIC_MODEL` - Model name (default: claude-3-opus-20240229)

**xAI Grok:**
- `GROK_API_KEY` - xAI API key (use Secret Manager)
- `GROK_MODEL` - Model name (default: grok-beta)

### Using Cloud Secret Manager

For sensitive values like API keys, use Cloud Secret Manager:

1. **Create a secret:**
```bash
echo -n "your-api-key-here" | gcloud secrets create openai-api-key --data-file=-
```

2. **Grant Cloud Run access:**
```bash
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

3. **Configure in Cloud Run:**
```bash
gcloud run services update insight-generator \
    --update-secrets=OPENAI_API_KEY=openai-api-key:latest \
    --region=us-central1
```

## Resource Configuration

### utxoiq-ingestion

**Recommended Settings:**
- Memory: 1 GiB (handles block processing and signal generation)
- CPU: 1 vCPU
- Timeout: 3600 seconds (1 hour for long-running block monitoring)
- Min instances: 1 (keep service warm for real-time monitoring)
- Max instances: 3 (handle traffic spikes)
- Concurrency: 80 (default)

### insight-generator

**Recommended Settings:**
- Memory: 2 GiB (handles AI model inference)
- CPU: 1 vCPU
- Timeout: 300 seconds (5 minutes for AI generation)
- Min instances: 1 (continuous polling required)
- Max instances: 5 (parallel insight generation)
- Concurrency: 10 (limit concurrent AI requests)

## Auto-Scaling Configuration

Configure auto-scaling based on your workload:

```bash
# utxoiq-ingestion - stable load
gcloud run services update utxoiq-ingestion \
    --min-instances=1 \
    --max-instances=3 \
    --region=us-central1

# insight-generator - variable load
gcloud run services update insight-generator \
    --min-instances=1 \
    --max-instances=5 \
    --cpu-throttling \
    --region=us-central1
```

## Verification

### Health Checks

Check service health after deployment:

```bash
# utxoiq-ingestion
curl https://utxoiq-ingestion-PROJECT_NUMBER.us-central1.run.app/health

# insight-generator
curl https://insight-generator-PROJECT_NUMBER.us-central1.run.app/health
```

### Service Status

Check detailed service status:

```bash
# utxoiq-ingestion status (includes pipeline info)
curl https://utxoiq-ingestion-PROJECT_NUMBER.us-central1.run.app/status

# insight-generator stats
curl https://insight-generator-PROJECT_NUMBER.us-central1.run.app/stats
```

### Manual Testing

Trigger a manual polling cycle:

```bash
curl -X POST https://insight-generator-PROJECT_NUMBER.us-central1.run.app/trigger-cycle
```

## Monitoring

### View Logs

**All services:**
```bash
gcloud logging tail "resource.type=cloud_run_revision"
```

**Specific service:**
```bash
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=insight-generator"
```

**Filter by severity:**
```bash
gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR"
```

### Cloud Monitoring Metrics

Key metrics to monitor:
- `run.googleapis.com/request_count` - Request volume
- `run.googleapis.com/request_latencies` - Response times
- `run.googleapis.com/container/cpu/utilizations` - CPU usage
- `run.googleapis.com/container/memory/utilizations` - Memory usage
- Custom metrics emitted by MonitoringModule

### Set Up Alerts

Create alerts for critical conditions:

```bash
# High error rate
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate - insight-generator" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s

# Stale signals (unprocessed > 1 hour)
# Configure via MonitoringModule error metrics
```

## Troubleshooting

### Common Issues

**1. Service fails to start:**
- Check logs: `gcloud logging tail`
- Verify environment variables are set correctly
- Ensure BigQuery datasets exist
- Check IAM permissions

**2. No signals generated:**
- Verify `BITCOIN_RPC_URL` is configured (if using Bitcoin Core)
- Check block monitor status: `/status` endpoint
- Verify signal processors are enabled
- Check BigQuery write permissions

**3. No insights generated:**
- Verify AI provider configuration
- Check API key is valid (Secret Manager)
- Verify signals exist in `intel.signals` table
- Check confidence threshold settings
- View polling stats: `/stats` endpoint

**4. High latency:**
- Increase memory allocation
- Increase max instances for auto-scaling
- Check BigQuery query performance
- Monitor AI provider API latency

**5. Cost concerns:**
- Reduce min instances to 0 (cold starts acceptable)
- Lower max instances
- Increase confidence threshold (fewer insights)
- Use cheaper AI provider (Vertex AI vs OpenAI)
- Implement request batching

### Debug Mode

Enable debug logging:

```bash
gcloud run services update insight-generator \
    --set-env-vars LOG_LEVEL=DEBUG \
    --region=us-central1
```

## Cost Optimization

### Estimated Costs (per month)

**utxoiq-ingestion:**
- Cloud Run: ~$10-30 (1 instance, 1 GiB, 1 vCPU)
- BigQuery writes: ~$5-10 (streaming inserts)
- Total: ~$15-40/month

**insight-generator:**
- Cloud Run: ~$20-50 (1-5 instances, 2 GiB, 1 vCPU)
- BigQuery queries: ~$5-15 (polling queries)
- AI API calls: Variable (see below)
- Total: ~$25-65/month + AI costs

**AI Provider Costs (per 1000 insights):**
- Vertex AI Gemini Pro: ~$0.50-1.00
- OpenAI GPT-4 Turbo: ~$2.00-4.00
- Anthropic Claude 3 Opus: ~$3.00-6.00
- xAI Grok: ~$1.00-2.00 (pricing varies)

### Cost Reduction Strategies

1. **Use Vertex AI** (cheapest, integrated with GCP)
2. **Increase confidence threshold** (fewer low-quality insights)
3. **Reduce polling frequency** (10s → 30s)
4. **Disable optional processors** (treasury, predictive)
5. **Use min-instances=0** (accept cold starts)
6. **Batch signal processing** (process multiple signals per cycle)

## Rollback

If deployment fails or issues arise:

```bash
# List revisions
gcloud run revisions list --service=insight-generator --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic insight-generator \
    --to-revisions=REVISION_NAME=100 \
    --region=us-central1
```

## Next Steps

After successful deployment:

1. **Populate known entities** - Run `scripts/bigquery/populate_known_entities.py`
2. **Test end-to-end** - Trigger block processing and verify insights
3. **Configure monitoring** - Set up alerts and dashboards
4. **Optimize costs** - Adjust resource limits and thresholds
5. **Enable features** - Configure optional processors and predictive analytics

## Support

For issues or questions:
- Check logs: `gcloud logging tail`
- Review documentation: `docs/`
- Check service status: `/health` and `/status` endpoints
- Review BigQuery data: Query `intel.signals` and `intel.insights` tables

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Signal-Insight Pipeline Design](.kiro/specs/signal-insight-pipeline/design.md)
