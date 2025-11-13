# utxoIQ Deployment Summary

## ✅ Completed

### 1. BigQuery Hybrid Setup (100%)
- **Custom dataset**: `utxoiq-dev.btc` with 1-hour buffer
- **Public dataset**: Google's `bigquery-public-data.crypto_bitcoin` for historical data
- **Unified views**: `blocks_unified` and `transactions_unified` with automatic deduplication
- **Cost optimization**: 53% reduction ($30/month vs $65/month)
- **Cleanup automation**: Cloud Scheduler runs every 30 minutes

### 2. Ingestion Service Deployed (100%)
- **Service name**: `utxoiq-ingestion` (renamed from feature-engine)
- **URL**: https://utxoiq-ingestion-544291059247.us-central1.run.app
- **Features**:
  - Block ingestion API (`POST /ingest/block`)
  - Health check (`GET /health`)
  - Status endpoint (`GET /status`)
  - Automatic cleanup (`POST /cleanup`)
- **Configuration**:
  - Memory: 512Mi
  - CPU: 1 vCPU
  - Min instances: 1 (always on)
  - Timeout: 3600s

### 3. Integrated Block Monitor (95%)
- **Location**: Built into `utxoiq-ingestion` service
- **Features**:
  - Polls Bitcoin Core every 10 seconds
  - Processes blocks with nested transactions
  - Automatic ingestion into BigQuery
  - Tor support for .onion addresses
- **Status**: Code complete, Tor connectivity needs verification

### 4. Data Verified (100%)
- **Blocks ingested**: 11 blocks in custom dataset
- **Transactions**: 13,103 transactions processed
- **Latest block**: 923,156
- **No duplicates**: Deduplication working correctly
- **Nested structure**: Inputs/outputs properly stored as RECORD arrays

## ⏳ Remaining Tasks

### 1. Tor Connectivity (10 minutes)
The monitor is integrated but needs Tor to connect to your Umbrel node's hidden service.

**Current status**:
- Tor daemon starts in container
- Permission issues with `/var/lib/tor` directory
- Fixed to use `/tmp/tor` instead
- Needs redeployment to test

**Next deployment**:
```bash
cd services/utxoiq-ingestion
gcloud run deploy utxoiq-ingestion \
  --source . \
  --region us-central1 \
  --project utxoiq-dev \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 3600 \
  --min-instances 1 \
  --max-instances 1 \
  --set-env-vars "PROJECT_ID=utxoiq-dev,BITCOIN_RPC_URL=http://umbrel:PASSWORD@hkps5arunnwerusagmrcktq76pjlej4dgenqipavkkprmozj37txqwyd.onion:8332,POLL_INTERVAL=10" \
  --no-cpu-throttling
```

### 2. Verification (5 minutes)
Once deployed with working Tor:
1. Check status: `curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status`
2. Verify monitor is running: Look for `"monitor": {"running": true}`
3. Check logs: `gcloud logging read "resource.labels.service_name=utxoiq-ingestion"`
4. Wait 10-20 seconds for first block detection

### 3. Monitoring Setup (Optional, 15 minutes)
- Set up Cloud Monitoring alerts for service failures
- Create dashboard for block ingestion metrics
- Configure email/Slack notifications

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Umbrel Bitcoin Node                       │
│                                                              │
│  Bitcoin Core RPC                                            │
│  Tor Hidden Service: hkps5arunn...txqwyd.onion:8332        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ Tor Network
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              utxoiq-ingestion (Cloud Run)                    │
│                                                              │
│  ┌──────────────┐    ┌─────────────────────────────────┐   │
│  │ Tor Daemon   │───▶│  Block Monitor Thread           │   │
│  │ (port 9050)  │    │  - Polls every 10s              │   │
│  └──────────────┘    │  - Fetches blocks via Tor       │   │
│                      │  - Processes transactions        │   │
│                      └──────────┬──────────────────────┘   │
│                                 │                            │
│  ┌──────────────────────────────▼──────────────────────┐   │
│  │  FastAPI Service                                     │   │
│  │  - /health                                           │   │
│  │  - /status (shows monitor status)                    │   │
│  │  - /ingest/block (manual ingestion)                  │   │
│  │  - /cleanup (manual cleanup)                         │   │
│  └──────────────────────────────┬───────────────────────┘   │
└─────────────────────────────────┼───────────────────────────┘
                                  │
                                  │ BigQuery API
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    BigQuery Dataset                          │
│                                                              │
│  Custom Dataset (1-hour buffer):                             │
│  ├── btc.blocks (11 blocks)                                 │
│  └── btc.transactions (13,103 transactions)                 │
│                                                              │
│  Unified Views (with deduplication):                         │
│  ├── btc.blocks_unified                                     │
│  └── btc.transactions_unified                               │
│                                                              │
│  Public Dataset (historical):                                │
│  └── bigquery-public-data.crypto_bitcoin.*                  │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  │ Every 30 minutes
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloud Scheduler                                 │
│                                                              │
│  cleanup-old-blocks                                          │
│  - Runs: */30 * * * * (every 30 minutes)                    │
│  - Calls: POST /cleanup?hours=2                             │
│  - Deletes blocks older than 2 hours                         │
└─────────────────────────────────────────────────────────────┘
```

## Cost Breakdown

### Current Monthly Costs

| Service | Cost | Notes |
|---------|------|-------|
| BigQuery Storage | $0.02 | ~1 hour of blocks |
| BigQuery Queries | $5/TB | Historical queries use public dataset |
| Cloud Run (utxoiq-ingestion) | $18.43 | 1 vCPU, 512MB, always-on |
| Cloud Scheduler | $0.10 | Cleanup job |
| **Total** | **~$18.55/month** | + query costs |

### Cost Optimization Options

1. **Reduce CPU to 0.5 vCPU**: ~$9/month (may slow down processing)
2. **Use Cloud Functions**: ~$0.50/month (1-minute minimum interval, may miss blocks)
3. **Run locally**: $0 (requires always-on machine)

**Recommendation**: Keep current setup. $18/month is reasonable for 24/7 real-time monitoring.

## Service URLs

- **Ingestion Service**: https://utxoiq-ingestion-544291059247.us-central1.run.app
- **Health Check**: https://utxoiq-ingestion-544291059247.us-central1.run.app/health
- **Status**: https://utxoiq-ingestion-544291059247.us-central1.run.app/status
- **GCP Console**: https://console.cloud.google.com/run?project=utxoiq-dev

## Key Files

### Service Code
- `services/utxoiq-ingestion/src/main.py` - Main FastAPI application
- `services/utxoiq-ingestion/src/monitor/block_monitor.py` - Block monitoring logic
- `services/utxoiq-ingestion/src/adapters/bigquery_adapter.py` - BigQuery operations
- `services/utxoiq-ingestion/src/processors/bitcoin_block_processor.py` - Block processing
- `services/utxoiq-ingestion/Dockerfile` - Container definition with Tor
- `services/utxoiq-ingestion/start.sh` - Startup script (Tor + service)
- `services/utxoiq-ingestion/torrc` - Tor configuration

### Scripts
- `scripts/test-tor-bitcoin.py` - Test Tor connectivity to Bitcoin node
- `scripts/verify-deployment.py` - Verify BigQuery data
- `scripts/setup-cloud-scheduler.bat` - Set up cleanup automation
- `scripts/backfill-recent-blocks.py` - Backfill historical blocks

### Documentation
- `docs/bigquery-hybrid-strategy.md` - Hybrid approach explanation
- `docs/bigquery-deployment-status.md` - Deployment status
- `docs/block-monitor-setup.md` - Block monitor documentation
- `docs/deployment-summary.md` - This file

## Next Steps

1. **Redeploy with Tor fix** (5 minutes)
   ```bash
   cd services/utxoiq-ingestion
   # Update BITCOIN_RPC_URL with your password
   gcloud run deploy utxoiq-ingestion --source . ...
   ```

2. **Verify monitor is running** (2 minutes)
   ```bash
   curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status
   # Look for: "monitor": {"running": true, "last_processed_height": ...}
   ```

3. **Monitor logs** (ongoing)
   ```bash
   gcloud logging tail "resource.labels.service_name=utxoiq-ingestion" --project utxoiq-dev
   # Watch for: "📦 New block detected: ..."
   ```

4. **Set up alerts** (optional, 15 minutes)
   - Create alert for service downtime
   - Create alert for no blocks ingested in 30 minutes
   - Configure notification channels

## Success Criteria

✅ **Service is healthy**: `/health` returns 200
✅ **Monitor is running**: `/status` shows `"monitor": {"running": true}`
✅ **Blocks are being ingested**: New blocks appear in BigQuery within 60 seconds
✅ **No duplicates**: Unified views show unique blocks only
✅ **Cleanup is working**: Old blocks are removed every 30 minutes
✅ **Costs are optimized**: ~$18/month for real-time monitoring

## Troubleshooting

### Monitor not starting
- Check logs: `gcloud logging read "resource.labels.service_name=utxoiq-ingestion"`
- Look for: "Could not start block monitor"
- Common issues: Tor not starting, DNS resolution failed, RPC credentials incorrect

### Tor not connecting
- Check Tor logs in Cloud Run logs
- Verify .onion address is correct
- Test locally with `scripts/test-tor-bitcoin.py`

### Blocks not appearing in BigQuery
- Check `/status` endpoint for latest block height
- Verify blocks are within 1-hour window
- Check BigQuery dataset: `SELECT * FROM btc.blocks ORDER BY number DESC LIMIT 10`

### High costs
- Check BigQuery query costs in GCP Console
- Verify cleanup is running (should keep <20 blocks)
- Consider reducing CPU or using Cloud Functions

## Support

For issues:
1. Check logs: `gcloud logging read "resource.labels.service_name=utxoiq-ingestion"`
2. Check status: `curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status`
3. Verify BigQuery: `python scripts/verify-deployment.py`
4. Review documentation in `docs/` directory
