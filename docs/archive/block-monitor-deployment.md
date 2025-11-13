# Block Monitor Deployment Guide

## Overview

The block-monitor service monitors your Umbrel Bitcoin node via Tor and sends new blocks to the utxoiq-ingestion service for processing.

## Architecture

```
Umbrel Node (.onion)
    ↓ (via Tor)
Block Monitor (Cloud Run)
    ↓ (HTTP)
utxoiq-ingestion (Cloud Run)
    ↓
BigQuery
```

## Features

- **Primary Source**: Umbrel Bitcoin Core via Tor hidden service
- **Fallback Source**: mempool.space API (automatic failover after 3 consecutive failures)
- **Resilient**: Auto-recovery when Umbrel comes back online
- **Efficient**: 30-second polling interval, processes blocks within 60 seconds
- **Monitored**: Health check and status endpoints

## Prerequisites

1. **Umbrel Node**
   - Bitcoin Core fully synced
   - Tor hidden service enabled
   - RPC credentials configured

2. **GCP Project**
   - Project ID: `utxoiq-dev`
   - Cloud Run API enabled
   - Billing enabled

3. **Services Deployed**
   - utxoiq-ingestion service must be deployed first

## Configuration

### Environment Variables

Create `services/block-monitor/.env`:

```bash
# Bitcoin Core RPC (Tor Hidden Service)
BITCOIN_RPC_URL=http://umbrel:PASSWORD@YOUR_ONION_ADDRESS.onion:8332

# utxoiq-ingestion service URL
FEATURE_ENGINE_URL=https://utxoiq-ingestion-544291059247.us-central1.run.app

# mempool.space API for fallback
MEMPOOL_API_URL=https://mempool.space/api

# Poll interval (seconds)
POLL_INTERVAL=30

# Health check port
PORT=8080
```

## Deployment Steps

### 1. Deploy utxoiq-ingestion First

```cmd
cd services\utxoiq-ingestion
gcloud run deploy utxoiq-ingestion ^
    --source . ^
    --region us-central1 ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 1Gi ^
    --cpu 1
```

### 2. Deploy block-monitor

```cmd
REM Use the deployment script
scripts\deploy-block-monitor.bat

REM Or manually:
cd services\block-monitor
gcloud run deploy block-monitor ^
    --source . ^
    --region us-central1 ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 512Mi ^
    --cpu 1 ^
    --timeout 3600 ^
    --min-instances 1 ^
    --max-instances 1
```

**Important**: 
- `--min-instances 1` keeps the service always running (no cold starts)
- `--timeout 3600` allows long-running block monitoring
- Tor is included in the Docker container automatically

## Verification

### 1. Check Service Status

```cmd
curl https://block-monitor-544291059247.us-central1.run.app/status
```

Expected response:
```json
{
  "status": "running",
  "last_processed_height": 923264,
  "poll_interval": 30,
  "using_tor": true,
  "using_fallback": false,
  "consecutive_failures": 0,
  "data_source": "umbrel"
}
```

### 2. Check Health

```cmd
curl https://block-monitor-544291059247.us-central1.run.app/health
```

### 3. View Logs

```cmd
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=block-monitor" --limit 50 --format json
```

## Monitoring

### Key Metrics to Watch

1. **Data Source**: Should be "umbrel" most of the time
2. **Consecutive Failures**: Should be 0 or low
3. **Using Fallback**: Should be false (only true during Umbrel outages)
4. **Last Processed Height**: Should increase every ~10 minutes

### Alerts to Set Up

1. **Fallback Mode Active** - Alert if `using_fallback=true` for > 30 minutes
2. **No New Blocks** - Alert if `last_processed_height` hasn't changed in > 30 minutes
3. **High Failure Rate** - Alert if `consecutive_failures > 5`

## Failover Behavior

### Automatic Failover to mempool.space

1. Umbrel RPC fails 3 consecutive times
2. Service switches to mempool.space API
3. Logs: `🔄 Switching to mempool.space fallback`
4. Status endpoint shows: `"data_source": "mempool.space"`

### Automatic Recovery

1. Service continues trying Umbrel every poll interval
2. When Umbrel responds successfully:
3. Logs: `✅ Umbrel connection restored, switching back from fallback`
4. Status endpoint shows: `"data_source": "umbrel"`

## Troubleshooting

### Service Not Starting

```cmd
REM Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=block-monitor" --limit 20

REM Common issues:
REM 1. BITCOIN_RPC_URL not set
REM 2. Tor not starting in container
REM 3. .onion address incorrect
```

### Tor Connection Failing

```cmd
REM Check if Tor is running in container
gcloud run services describe block-monitor --region us-central1

REM Verify .onion address is correct
REM Test locally first: scripts\test-umbrel-tor-connection.py
```

### Blocks Not Being Processed

```cmd
REM Check utxoiq-ingestion service
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM Check BigQuery for recent blocks
bq query --use_legacy_sql=false "SELECT MAX(number) as latest_block FROM btc.blocks"
```

### High Latency

- Tor latency is typically 2-5 seconds per request
- If consistently > 5 seconds, Tor circuit may be slow
- Service will automatically use mempool.space if too slow

## Cost Estimation

### Cloud Run Costs (us-central1)

- **CPU**: 1 vCPU × 730 hours/month = ~$24/month
- **Memory**: 512 MB × 730 hours/month = ~$4/month
- **Requests**: Minimal (health checks only)
- **Total**: ~$28/month

**Note**: Using `--min-instances 1` keeps service always running (no cold starts but higher cost)

### Alternative: On-Demand

Remove `--min-instances 1` to reduce cost to ~$5/month, but:
- Cold starts every time service scales to zero
- May miss blocks during startup
- Not recommended for production

## Security Considerations

1. **RPC Credentials**: Stored as environment variables in Cloud Run
2. **Tor Traffic**: All Bitcoin RPC traffic goes through Tor network
3. **No Public Endpoints**: Only health/status endpoints are public
4. **Service-to-Service**: Communication with utxoiq-ingestion is over HTTPS

## Maintenance

### Update Configuration

```cmd
REM Update environment variables
gcloud run services update block-monitor ^
    --region us-central1 ^
    --update-env-vars POLL_INTERVAL=60

REM Redeploy with new code
scripts\deploy-block-monitor.bat
```

### Restart Service

```cmd
REM Force new revision
gcloud run services update block-monitor --region us-central1 --update-env-vars RESTART=$(date +%s)
```

### View Real-time Logs

```cmd
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=block-monitor"
```

## Next Steps

1. Deploy utxoiq-ingestion service
2. Deploy block-monitor service
3. Verify blocks are being ingested into BigQuery
4. Set up monitoring alerts
5. Test failover by temporarily stopping Umbrel

## Support

For issues:
1. Check service logs
2. Verify Umbrel is accessible via Tor locally
3. Test mempool.space fallback manually
4. Check BigQuery for recent data
