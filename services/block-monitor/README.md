# Block Monitor Service

Real-time Bitcoin block monitoring service that connects to Bitcoin Core via Tor and sends blocks to the feature-engine for ingestion into BigQuery.

## Features

- ✅ **Tor Support**: Connects to Bitcoin Core via Tor hidden service (.onion)
- ✅ **Cloud Run Deployment**: Runs 24/7 on Google Cloud Run
- ✅ **Health Checks**: Built-in health and status endpoints
- ✅ **Automatic Retries**: Handles network failures gracefully
- ✅ **Real-time Monitoring**: 10-second polling interval
- ✅ **Minimal Cost**: ~$7/month for always-on monitoring

## Architecture

```
Umbrel Bitcoin Node (Tor Hidden Service)
    ↓ (via Tor SOCKS5 proxy)
Block Monitor (Cloud Run)
    ↓ (HTTPS)
Feature Engine (Cloud Run)
    ↓ (BigQuery API)
Custom Dataset (1-hour buffer)
```

## Deployment

### Prerequisites

1. Bitcoin Core with Tor hidden service enabled (Umbrel does this automatically)
2. Bitcoin RPC credentials
3. Google Cloud SDK installed and authenticated

### Deploy to Cloud Run

```bash
cd services/block-monitor

# Windows
deploy.bat

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

You'll be prompted for your Bitcoin RPC password. The script will:
1. Build Docker image with Tor
2. Deploy to Cloud Run with min-instances=1 (always on)
3. Configure environment variables
4. Set up health checks

### Configuration

Environment variables (set during deployment):

```bash
BITCOIN_RPC_URL=http://umbrel:PASSWORD@ONION_ADDRESS.onion:8332
FEATURE_ENGINE_URL=https://feature-engine-544291059247.us-central1.run.app
POLL_INTERVAL=10
PORT=8080
```

## Monitoring

### Health Check

```bash
curl https://block-monitor-544291059247.us-central1.run.app/health
```

Response:
```json
{
  "status": "healthy",
  "service": "block-monitor",
  "timestamp": "2025-11-11T22:00:00.000000",
  "monitoring": true,
  "last_processed_height": 923156
}
```

### Status Check

```bash
curl https://block-monitor-544291059247.us-central1.run.app/status
```

Response:
```json
{
  "status": "running",
  "last_processed_height": 923156,
  "poll_interval": 10,
  "using_tor": true
}
```

### View Logs

```bash
# Recent logs
gcloud logging read "resource.labels.service_name=block-monitor" \
  --limit 50 \
  --project utxoiq-dev

# Follow logs in real-time
gcloud logging tail "resource.labels.service_name=block-monitor" \
  --project utxoiq-dev
```

## How It Works

### 1. Tor Connection

The service runs a Tor daemon inside the container and uses SOCKS5 proxy to connect to your Umbrel's Bitcoin Core hidden service:

```
Container:
  ├── Tor daemon (port 9050)
  ├── Python app (uses SOCKS5 proxy)
  └── Health check server (port 8080)
```

### 2. Block Detection

Every 10 seconds:
1. Query Bitcoin Core for current block height
2. If new block detected, fetch full block data (including transactions)
3. Send to feature-engine via HTTPS
4. Feature-engine ingests into BigQuery custom dataset

### 3. Data Flow

```python
# 1. Get block via Tor
block_data = rpc.getblock(block_hash, verbosity=2)

# 2. Convert Decimals to floats
json_data = json.dumps(block_data, cls=DecimalEncoder)

# 3. Send to feature-engine
response = requests.post(
    "https://feature-engine.../ingest/block",
    data=json_data
)

# 4. Feature-engine processes and stores in BigQuery
```

## Cost Breakdown

### Cloud Run Costs

- **CPU**: 1 vCPU × 730 hours/month = $0.024/hour = **$17.52/month**
- **Memory**: 512 MB × 730 hours/month = $0.0025/GB-hour = **$0.91/month**
- **Requests**: ~260,000/month (health checks) = **$0.00** (within free tier)

**Total**: ~$18.43/month

### Cost Optimization Options

1. **Reduce to 0.5 vCPU**: ~$9/month (may be slower)
2. **Use Cloud Scheduler + Cloud Functions**: ~$0.50/month (1-minute minimum interval, may miss blocks)
3. **Run locally**: $0 (requires always-on machine)

### Recommended: Cloud Run

The ~$18/month cost is worth it for:
- 24/7 uptime
- No local infrastructure
- Automatic restarts
- Integrated logging
- Secure Tor connectivity

## Troubleshooting

### Service Not Starting

Check logs for Tor connection issues:
```bash
gcloud logging read "resource.labels.service_name=block-monitor" \
  --limit 20 \
  --project utxoiq-dev
```

Common issues:
- Tor daemon failed to start
- Invalid .onion address
- Bitcoin RPC credentials incorrect

### Blocks Not Being Ingested

1. Check feature-engine is accessible:
```bash
curl https://feature-engine-544291059247.us-central1.run.app/health
```

2. Check block timestamp (must be within 1 hour):
```bash
curl https://block-monitor-544291059247.us-central1.run.app/status
```

3. Verify BigQuery data:
```bash
python scripts/verify-deployment.py
```

### Tor Connection Issues

Test Tor connectivity from within the container:
```bash
# Get a shell in the running container
gcloud run services proxy block-monitor --region us-central1 --project utxoiq-dev

# Test Tor
curl --socks5-hostname 127.0.0.1:9050 http://check.torproject.org
```

## Security

### Tor Hidden Service

Your Bitcoin node's .onion address is only accessible via Tor, providing:
- **Privacy**: Your node's IP address is hidden
- **Security**: End-to-end encryption
- **Firewall bypass**: No port forwarding needed

### Credentials

Bitcoin RPC password is stored as an environment variable in Cloud Run (encrypted at rest).

To rotate credentials:
1. Update password in Umbrel
2. Redeploy service with new password

### Network Security

- Block monitor → Bitcoin Core: Via Tor (encrypted)
- Block monitor → Feature engine: HTTPS (encrypted)
- Feature engine → BigQuery: Google internal network (encrypted)

## Maintenance

### Update Service

```bash
cd services/block-monitor
./deploy.bat  # or ./deploy.sh
```

### Stop Service

```bash
gcloud run services update block-monitor \
  --min-instances=0 \
  --region=us-central1 \
  --project=utxoiq-dev
```

### Restart Service

```bash
# Force new revision
gcloud run services update block-monitor \
  --region=us-central1 \
  --project=utxoiq-dev \
  --update-env-vars="RESTART=$(date +%s)"
```

## Files

- `Dockerfile` - Container definition with Tor
- `block-monitor.py` - Main monitoring service
- `requirements.txt` - Python dependencies
- `torrc` - Tor configuration
- `start.sh` - Startup script (Tor + monitor)
- `deploy.sh` / `deploy.bat` - Deployment scripts
- `README.md` - This file

## Next Steps

1. ✅ Deploy to Cloud Run
2. ⏳ Monitor for 24 hours
3. ⏳ Set up alerting for failures
4. ⏳ Add metrics dashboard
5. ⏳ Optimize costs if needed
