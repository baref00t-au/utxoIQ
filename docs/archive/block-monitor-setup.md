# Block Monitor Setup

## Overview

The block monitor is a Python script that continuously polls Bitcoin Core for new blocks and sends them to the feature-engine service for ingestion into BigQuery.

## Status: ✅ Working

- **Service**: feature-engine deployed to Cloud Run
- **Monitor**: block-monitor.py script tested and working
- **Latest Block**: 923156 (as of 2025-11-11 21:49 UTC)
- **Blocks Ingested**: 11 blocks in custom dataset
- **Transactions**: 13,103 transactions processed

## How It Works

```
Bitcoin Core (Umbrel) 
    ↓ (RPC polling every 10s)
Block Monitor Script
    ↓ (HTTP POST with JSON)
Feature Engine (Cloud Run)
    ↓ (BigQuery insert_rows_json)
Custom Dataset (btc.blocks, btc.transactions)
    ↓ (Unified views with deduplication)
Query Layer (blocks_unified, transactions_unified)
```

## Running the Monitor

### Local Development (Manual)

```bash
# Activate Python environment
.\venv312\Scripts\Activate.ps1

# Set RPC credentials
$env:BITCOIN_RPC_PASSWORD = "your-password"

# Run monitor
python scripts/block-monitor.py \
  --rpc-url "http://umbrel:$env:BITCOIN_RPC_PASSWORD@umbrel.local:8332" \
  --poll-interval 10
```

### Production Deployment Options

#### Option 1: Cloud Run (Recommended)

Deploy the block monitor as a Cloud Run service that runs continuously:

```bash
# Create Dockerfile for block-monitor
cd scripts
gcloud run deploy block-monitor \
  --source . \
  --region us-central1 \
  --project utxoiq-dev \
  --set-env-vars BITCOIN_RPC_URL=http://umbrel:PASSWORD@umbrel.local:8332 \
  --set-env-vars FEATURE_ENGINE_URL=https://feature-engine-544291059247.us-central1.run.app \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 1
```

**Pros:**
- Always running
- Automatic restarts on failure
- Integrated logging
- No local infrastructure needed

**Cons:**
- Requires public Bitcoin RPC endpoint or VPN
- Costs ~$7/month for always-on instance

#### Option 2: Cloud Scheduler + Cloud Functions

Trigger block checks every minute via Cloud Scheduler:

```bash
# Deploy function
gcloud functions deploy check-new-blocks \
  --runtime python312 \
  --trigger-http \
  --entry-point check_blocks \
  --set-env-vars BITCOIN_RPC_URL=... \
  --region us-central1
```

**Pros:**
- Cheaper (~$0.50/month)
- Serverless

**Cons:**
- 1-minute minimum interval
- May miss blocks during high activity

#### Option 3: Local Service (Current)

Run block-monitor.py on a local machine or server:

```bash
# Using systemd (Linux)
sudo systemctl enable block-monitor
sudo systemctl start block-monitor

# Using Windows Service
nssm install BlockMonitor "C:\Python312\python.exe" "C:\utxoIQ\scripts\block-monitor.py"
```

**Pros:**
- Direct access to local Bitcoin node
- No cloud costs
- Full control

**Cons:**
- Requires always-on machine
- Manual maintenance
- No automatic failover

## Configuration

### Environment Variables

```bash
# Bitcoin Core RPC
BITCOIN_RPC_URL=http://user:password@host:8332

# Feature Engine
FEATURE_ENGINE_URL=https://feature-engine-544291059247.us-central1.run.app

# Optional
POLL_INTERVAL=10  # seconds between checks
```

### Command Line Options

```bash
python scripts/block-monitor.py \
  --rpc-url "http://umbrel:pass@umbrel.local:8332" \
  --feature-engine-url "https://feature-engine-544291059247.us-central1.run.app" \
  --start-height 923153 \  # Optional: start from specific height
  --poll-interval 10        # Optional: seconds between checks
```

## Monitoring

### Check Service Status

```bash
# Feature engine health
curl https://feature-engine-544291059247.us-central1.run.app/health

# Feature engine status (shows latest block)
curl https://feature-engine-544291059247.us-central1.run.app/status
```

### View Logs

```bash
# Cloud Run logs
gcloud logging read "resource.labels.service_name=feature-engine" \
  --limit 50 \
  --project utxoiq-dev

# Local monitor logs
# Logs are printed to stdout
```

### Verify Data

```bash
# Run verification script
python scripts/verify-deployment.py
```

## Troubleshooting

### Block Monitor Not Starting

1. Check Bitcoin RPC connection:
```bash
curl --user umbrel:PASSWORD --data-binary '{"jsonrpc":"1.0","id":"test","method":"getblockcount","params":[]}' http://umbrel.local:8332
```

2. Check feature-engine is accessible:
```bash
curl https://feature-engine-544291059247.us-central1.run.app/health
```

### Blocks Not Being Ingested

1. Check feature-engine logs for errors
2. Verify block timestamp is within 1-hour window
3. Check BigQuery dataset for blocks

### Duplicate Blocks

The unified views automatically deduplicate using `DISTINCT ON (number)`, so duplicates won't appear in queries.

## Cost Optimization

### Current Setup (Hybrid Approach)

- **Custom dataset**: ~$0.02/month (storage for 1 hour of blocks)
- **Public dataset**: $5/TB queried (historical data)
- **Cloud Run**: $0 (within free tier for feature-engine)
- **Cloud Scheduler**: $0.10/month (cleanup job)
- **Total**: ~$0.12/month + query costs

### With Always-On Block Monitor

- **Cloud Run (min-instances=1)**: ~$7/month
- **Total**: ~$7.12/month + query costs

### Recommended: Local Monitor

Run block-monitor.py on your local machine or Umbrel node to avoid Cloud Run costs while maintaining real-time ingestion.

## Next Steps

1. ✅ Block monitor working locally
2. ⏳ Decide on production deployment strategy
3. ⏳ Set up monitoring alerts
4. ⏳ Configure automatic restarts
5. ⏳ Add metrics dashboard

## Files

- `scripts/block-monitor.py` - Main monitoring script
- `scripts/verify-deployment.py` - Verification script
- `services/feature-engine/` - Ingestion service
- `docs/bigquery-deployment-status.md` - Deployment status
