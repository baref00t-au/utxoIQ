# BigQuery Hybrid Migration Guide

## Overview

This guide walks through migrating from a custom-only BigQuery setup to the hybrid approach using both the public dataset and custom real-time dataset.

## Prerequisites

- GCP project with BigQuery API enabled
- `bq` CLI tool installed and authenticated
- Terraform installed (for infrastructure provisioning)
- Python 3.12+ (for testing)

## Migration Steps

### Step 1: Analyze Current Schema

First, document your current schema to understand what needs to change:

```bash
# Export current schema
bq show --schema --format=prettyjson utxoiq-dev:btc.blocks > current_blocks_schema.json
bq show --schema --format=prettyjson utxoiq-dev:btc.transactions > current_transactions_schema.json
```

Compare with blockchain-etl schema in `infrastructure/bigquery/schemas/`.

### Step 2: Create New Dataset (if needed)

If starting fresh or creating a new dataset:

```bash
# Make scripts executable
chmod +x scripts/bigquery/*.sh

# Create dataset and tables
./scripts/bigquery/create-hybrid-dataset.sh
```

This creates:
- Dataset: `utxoiq-dev:btc`
- Tables: `blocks`, `transactions`, `inputs`, `outputs`
- Partitioning: By timestamp (DAY)
- Clustering: Optimized for common queries

### Step 3: Create Unified Views

Create views that seamlessly combine public and custom data:

```bash
./scripts/bigquery/create-unified-views.sh
```

This creates:
- `blocks_unified`
- `transactions_unified`
- `inputs_unified`
- `outputs_unified`

### Step 4: Update Application Code

Update all BigQuery queries to use unified views:

**Before:**
```python
query = "SELECT * FROM `utxoiq-dev.btc.blocks` WHERE ..."
```

**After:**
```python
query = "SELECT * FROM `utxoiq-dev.btc.blocks_unified` WHERE ..."
```

### Step 5: Deploy Updated Ingestion Service

Deploy the updated feature-engine service:

```bash
cd services/feature-engine

# Install dependencies
pip install -r requirements.txt

# Test locally
python -m uvicorn src.main:app --reload

# Deploy to Cloud Run
gcloud run deploy feature-engine \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Step 6: Backfill Last 24 Hours

Backfill recent blocks into the custom dataset:

```python
# scripts/backfill-recent-blocks.py
from datetime import datetime, timedelta
from services.feature_engine.src.adapters.bigquery_adapter import BigQueryAdapter
from services.feature_engine.src.processors.bitcoin_block_processor import BitcoinBlockProcessor
from bitcoinrpc.authproxy import AuthServiceProxy

# Connect to Bitcoin Core
rpc = AuthServiceProxy("http://user:pass@localhost:8332")

# Get current block height
current_height = rpc.getblockcount()

# Calculate 24 hours ago (approximately 144 blocks)
start_height = current_height - 144

# Initialize adapters
bq_adapter = BigQueryAdapter()
processor = BitcoinBlockProcessor()

# Backfill blocks
for height in range(start_height, current_height + 1):
    block_hash = rpc.getblockhash(height)
    block_data = rpc.getblock(block_hash, 2)  # Verbosity 2 includes transactions
    
    # Process and insert
    processed_block = processor.process_block(block_data)
    bq_adapter.insert_block(processed_block)
    
    print(f"Backfilled block {height}")
```

### Step 7: Set Up Cleanup Job

Schedule automatic cleanup of old data:

```bash
# Using Cloud Scheduler (via Terraform)
cd infrastructure/terraform
terraform apply

# Or manually create the job
gcloud scheduler jobs create http bigquery-cleanup \
  --schedule="0 */6 * * *" \
  --uri="https://feature-engine-xxx.run.app/cleanup" \
  --http-method=POST \
  --oidc-service-account-email=feature-engine@utxoiq-dev.iam.gserviceaccount.com
```

### Step 8: Test Hybrid Queries

Verify the hybrid setup is working:

```bash
./scripts/bigquery/test-hybrid-queries.sh
```

Expected output:
- Recent blocks come from custom dataset
- Historical blocks come from public dataset
- Queries work seamlessly across both

### Step 9: Monitor Performance

Track query performance and costs:

```bash
# Check query costs
bq ls -j --max_results=100 --format=prettyjson | \
  jq '.[] | select(.statistics.query.totalBytesProcessed != null) | 
  {query: .configuration.query.query, bytes: .statistics.query.totalBytesProcessed}'

# Monitor table sizes
bq show --format=prettyjson utxoiq-dev:btc.blocks | \
  jq '.numBytes, .numRows'
```

### Step 10: Migrate Existing Queries

Update all application queries systematically:

1. **Insight generation queries** - Update to use `blocks_unified`
2. **Alert evaluation queries** - Update to use `transactions_unified`
3. **Historical analysis** - Already benefits from public dataset
4. **API endpoints** - Update all BigQuery references

## Rollback Plan

If issues arise, you can rollback:

1. **Keep old tables** - Don't delete original tables immediately
2. **Switch queries back** - Change `_unified` back to original table names
3. **Stop ingestion** - Pause new data ingestion to custom dataset
4. **Investigate** - Debug issues without affecting production

## Validation Checklist

- [ ] All unified views created successfully
- [ ] Recent blocks (last 24h) in custom dataset
- [ ] Queries return correct data from both sources
- [ ] Application code updated to use unified views
- [ ] Cleanup job scheduled and tested
- [ ] Query performance meets requirements
- [ ] Cost reduction verified (check billing)
- [ ] Monitoring and alerting configured

## Cost Comparison

### Before Migration
```
Storage: 500 GB × $0.02/GB = $10/month
Streaming: 144 blocks/day × 365 × $0.01/200MB = $5/month
Queries: ~$50/month
Total: ~$65/month
```

### After Migration
```
Storage: 2 GB × $0.02/GB = $0.04/month
Streaming: 144 blocks/day × 365 × $0.01/200MB = $5/month
Queries: ~$30/month (50% reduction using public data)
Total: ~$35/month
```

**Savings: $30/month (46% reduction)**

## Troubleshooting

### Issue: Views return no data

**Solution:** Check that public dataset is accessible:
```bash
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`bigquery-public-data.crypto_bitcoin.blocks\`"
```

### Issue: Duplicate data in queries

**Solution:** Verify 24-hour boundary is correct:
```sql
-- Check for overlaps
SELECT 
  'Custom' as source,
  MIN(timestamp) as min_ts,
  MAX(timestamp) as max_ts
FROM `utxoiq-dev.btc.blocks`
UNION ALL
SELECT 
  'Public' as source,
  MIN(timestamp) as min_ts,
  MAX(timestamp) as max_ts
FROM `bigquery-public-data.crypto_bitcoin.blocks`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
```

### Issue: High query costs

**Solution:** Ensure queries use partitioning:
```sql
-- Good: Uses partition filter
SELECT * FROM `utxoiq-dev.btc.blocks_unified`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)

-- Bad: Full table scan
SELECT * FROM `utxoiq-dev.btc.blocks_unified`
WHERE number > 800000
```

## Next Steps

After successful migration:

1. **Monitor for 1 week** - Ensure stability and correct data
2. **Delete old tables** - Free up storage from old schema
3. **Optimize queries** - Take advantage of public dataset for analytics
4. **Document patterns** - Share learnings with team
5. **Consider additional optimizations** - Materialized views, etc.

## Support

For issues or questions:
- Check logs: `gcloud logging read "resource.type=cloud_run_revision"`
- Review BigQuery job history: `bq ls -j --max_results=100`
- Contact: [Your team contact info]
