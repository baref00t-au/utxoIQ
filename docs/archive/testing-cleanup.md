# Testing Data Cleanup

## Overview

The utxoiq-ingestion service has a `/cleanup` endpoint that deletes blocks and transactions older than a specified number of hours. This is useful for:
- Maintaining a rolling window of recent data
- Cleaning up test data
- Managing BigQuery storage costs

## Current Configuration

- **Realtime Window**: 1 hour (configured in service)
- **Default Cleanup**: 2 hours (can be customized)
- **Tables Affected**: 
  - `btc.blocks`
  - `btc.transactions`

## How Cleanup Works

The cleanup endpoint:
1. Deletes blocks older than X hours
2. Deletes transactions from those blocks
3. Returns count of deleted rows
4. Warns if > 200 blocks deleted (indicates ingestion was down)

## Testing Cleanup

### Step 1: Check Current Data

First, see what data you have:

```cmd
REM Check current status
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM Look for:
REM - "block_count": 122
REM - "oldest_age_hours": 20
REM - "span_hours": 19
```

### Step 2: Test Cleanup (Dry Run)

Since your oldest data is 20 hours old, you can safely test cleanup:

```cmd
REM Delete data older than 19 hours (should delete most blocks)
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=19"

REM Expected response:
REM {
REM   "status": "success",
REM   "deleted": {
REM     "blocks": 100-120,
REM     "transactions": 250000-300000
REM   },
REM   "cutoff_hours": 19,
REM   "warning": null
REM }
```

### Step 3: Verify Cleanup

Check that old data was deleted:

```cmd
REM Check status again
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM Should show:
REM - "block_count": 2-5 (only recent blocks)
REM - "oldest_age_hours": 0-1
REM - "span_hours": 0-1
```

### Step 4: Verify New Blocks Still Coming

Wait 30-60 seconds and check again:

```cmd
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM Should show:
REM - "latest_block_height": increased
REM - "block_count": growing again
REM - Monitor still running
```

## Testing with Public Dataset

Once you have data from the public Bitcoin dataset:

### Scenario 1: Import Historical Data

```cmd
REM 1. Import blocks from public dataset (e.g., last 24 hours)
REM    (This would be done via BigQuery SQL or data pipeline)

REM 2. Check how much data you have
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM 3. Clean up data older than 1 hour (keep only recent)
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=1"

REM 4. Verify only recent data remains
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status
```

### Scenario 2: Test Rolling Window

```cmd
REM Set up a rolling 2-hour window

REM 1. Let data accumulate for a few hours
REM 2. Run cleanup every hour to maintain 2-hour window
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=2"

REM 3. Schedule this as a cron job (Cloud Scheduler)
```

## Cleanup Parameters

### Conservative (Keep More Data)
```cmd
REM Keep last 24 hours
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=24"
```

### Moderate (Default)
```cmd
REM Keep last 2 hours
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=2"
```

### Aggressive (Keep Less Data)
```cmd
REM Keep last 1 hour
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=1"
```

### Nuclear (Delete Almost Everything)
```cmd
REM Keep last 10 minutes
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=0.17"
```

## Safety Features

### Warning System
If cleanup deletes > 200 blocks, it returns a warning:
```json
{
  "status": "success",
  "deleted": {
    "blocks": 250,
    "transactions": 625000
  },
  "cutoff_hours": 5,
  "warning": "Cleanup deleted more than 200 blocks"
}
```

This indicates:
- Ingestion may have been down
- You're deleting more data than expected
- Review before running again

### No Accidental Deletion
- Cleanup only affects YOUR dataset (`utxoiq-dev.btc`)
- Public Bitcoin dataset is never touched
- Monitor continues running after cleanup
- New blocks continue being ingested

## Automation with Cloud Scheduler

To run cleanup automatically:

```cmd
REM Create Cloud Scheduler job
gcloud scheduler jobs create http cleanup-old-blocks ^
  --schedule="0 * * * *" ^
  --uri="https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=2" ^
  --http-method=POST ^
  --location=us-central1 ^
  --description="Clean up blocks older than 2 hours"

REM This runs every hour at minute 0
```

## Monitoring Cleanup

### Check Cleanup History

View logs to see cleanup history:

```cmd
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=utxoiq-ingestion AND textPayload=~'Cleanup completed'" --limit 10
```

### Monitor Storage Costs

Check BigQuery storage:

```cmd
REM Get dataset size
bq show --format=prettyjson utxoiq-dev:btc | findstr "numBytes"

REM Calculate cost (first 10 GB free, then $0.02/GB/month)
```

## Recommended Cleanup Strategy

### Development
- **Window**: 2 hours
- **Frequency**: Every hour
- **Cost**: Minimal (~$0.20/month storage)

### Production
- **Window**: 24 hours
- **Frequency**: Every 6 hours
- **Cost**: ~$2/month storage

### Testing
- **Window**: 1 hour
- **Frequency**: Every 30 minutes
- **Cost**: Minimal (~$0.10/month storage)

## Troubleshooting

### Cleanup Returns 0 Deleted
**Cause**: No data older than specified hours
**Solution**: Check status endpoint for oldest_age_hours

### Cleanup Fails with Error
**Cause**: BigQuery permissions or table doesn't exist
**Solution**: Check service logs and BigQuery permissions

### Too Much Data Deleted
**Cause**: Ingestion was down or wrong hours parameter
**Solution**: Review logs, adjust hours parameter

### Monitor Stops After Cleanup
**Cause**: This shouldn't happen - monitor is independent
**Solution**: Check status endpoint, review logs

## Current Test Plan

Based on your current data (122 blocks, 20 hours old):

```cmd
REM 1. Check current state
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM 2. Delete data older than 19 hours (keeps ~1 hour)
curl -X POST "https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=19"

REM 3. Verify cleanup worked
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status

REM 4. Wait 2 minutes for new blocks
timeout /t 120

REM 5. Verify monitor still working
curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status
```

Expected results:
- Step 2: ~100-120 blocks deleted
- Step 3: Only 2-5 blocks remain
- Step 5: New blocks being added, monitor still running

## Summary

The cleanup endpoint is safe to test because:
- ✅ Only affects your custom dataset
- ✅ Monitor continues running
- ✅ New blocks keep coming
- ✅ Can't accidentally delete public data
- ✅ Returns detailed statistics
- ✅ Warns if too much deleted

Ready to test whenever you want!
