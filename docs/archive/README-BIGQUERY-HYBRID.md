# BigQuery Hybrid Dataset Implementation

## Quick Start

This implementation combines the public BigQuery Bitcoin dataset with a custom real-time dataset for optimal cost and performance.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Queries                       │
│              (Use *_unified views only)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Unified Views                            │
│  • blocks_unified      • transactions_unified                │
│  • inputs_unified      • outputs_unified                     │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
┌───────────────────────────┐  ┌───────────────────────────┐
│   Public Dataset          │  │   Custom Dataset          │
│   (Historical > 24h)      │  │   (Real-time < 24h)       │
│                           │  │                           │
│ • No ingestion cost       │  │ • 60-second processing    │
│ • Google maintained       │  │ • Custom features         │
│ • Full history            │  │ • Auto cleanup            │
└───────────────────────────┘  └───────────────────────────┘
```

### Benefits

- **46% cost reduction** - Use free public data for historical queries
- **Real-time insights** - 60-second block processing for recent data
- **Simplified maintenance** - No historical backfill needed
- **Better performance** - Smaller custom dataset = faster queries
- **Flexibility** - Can add custom columns to recent data

## Setup Instructions

### 1. Create Dataset and Tables

```bash
# Make scripts executable
chmod +x scripts/bigquery/*.sh

# Create dataset with blockchain-etl schema
./scripts/bigquery/create-hybrid-dataset.sh
```

### 2. Create Unified Views

```bash
# Create views that combine public + custom data
./scripts/bigquery/create-unified-views.sh
```

### 3. Backfill Recent Blocks

```bash
# Install dependencies
pip install python-bitcoinrpc google-cloud-bigquery

# Backfill last 24 hours
python scripts/backfill-recent-blocks.py \
  --rpc-url http://user:pass@localhost:8332
```

### 4. Deploy Ingestion Service

```bash
cd services/feature-engine

# Install dependencies
pip install -r requirements.txt

# Deploy to Cloud Run
gcloud run deploy feature-engine \
  --source . \
  --region us-central1 \
  --set-env-vars PROJECT_ID=utxoiq-dev
```

### 5. Set Up Cleanup Job

```bash
# Schedule cleanup every 6 hours
gcloud scheduler jobs create http bigquery-cleanup \
  --schedule="0 */6 * * *" \
  --uri="https://feature-engine-xxx.run.app/cleanup" \
  --http-method=POST
```

### 6. Test the Setup

```bash
# Run test queries
./scripts/bigquery/test-hybrid-queries.sh
```

## Usage

### Query Recent Blocks (Last Hour)

```sql
SELECT 
  number,
  hash,
  timestamp,
  transaction_count
FROM `utxoiq-dev.btc.blocks_unified`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY number DESC;
```

### Query Historical Analysis

```sql
SELECT 
  DATE(timestamp) as date,
  AVG(transaction_count) as avg_tx_count,
  SUM(transaction_count) as total_tx_count
FROM `utxoiq-dev.btc.blocks_unified`
WHERE timestamp BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY date
ORDER BY date;
```

### Query Large Transactions

```sql
SELECT 
  hash,
  block_number,
  block_timestamp,
  output_value / 100000000 as btc_amount,
  fee / 100000000 as fee_btc
FROM `utxoiq-dev.btc.transactions_unified`
WHERE output_value > 100000000000  -- > 1000 BTC
  AND block_timestamp >= '2024-01-01'
ORDER BY output_value DESC
LIMIT 100;
```

## Python Usage

```python
from services.feature_engine.src.adapters.bigquery_adapter import BigQueryAdapter

# Initialize adapter
bq = BigQueryAdapter(project_id="utxoiq-dev", dataset_id="btc")

# Query recent blocks
recent_blocks = bq.query_recent_blocks(hours=1, limit=10)

# Query specific block
block = bq.query_block_by_height(870000)

# Query transactions for block
transactions = bq.query_transactions_by_block(870000)

# Cleanup old data
results = bq.cleanup_old_data(hours=48)
print(f"Deleted {results['blocks']} blocks")
```

## Cost Analysis

### Before (Custom Only)
- Storage: 500 GB × $0.02/GB = **$10/month**
- Streaming: 144 blocks/day × 365 × $0.01/200MB = **$5/month**
- Queries: **$50/month**
- **Total: ~$65/month**

### After (Hybrid)
- Storage: 2 GB × $0.02/GB = **$0.04/month**
- Streaming: 144 blocks/day × 365 × $0.01/200MB = **$5/month**
- Queries: **$30/month** (50% reduction)
- **Total: ~$35/month**

**Savings: $30/month (46% reduction)**

## Schema Reference

### Blocks Table

| Field | Type | Description |
|-------|------|-------------|
| hash | STRING | Block hash |
| number | INTEGER | Block height |
| timestamp | TIMESTAMP | Block timestamp |
| size | INTEGER | Block size in bytes |
| transaction_count | INTEGER | Number of transactions |
| merkle_root | STRING | Merkle root hash |
| nonce | STRING | Block nonce |
| bits | STRING | Difficulty bits |

### Transactions Table

| Field | Type | Description |
|-------|------|-------------|
| hash | STRING | Transaction hash |
| block_number | INTEGER | Parent block height |
| block_timestamp | TIMESTAMP | Block timestamp |
| input_count | INTEGER | Number of inputs |
| output_count | INTEGER | Number of outputs |
| input_value | INTEGER | Total input value (satoshis) |
| output_value | INTEGER | Total output value (satoshis) |
| fee | INTEGER | Transaction fee (satoshis) |
| is_coinbase | BOOLEAN | Is coinbase transaction |

## Maintenance

### Manual Cleanup

```bash
# Clean up data older than 48 hours
curl -X POST https://feature-engine-xxx.run.app/cleanup?hours=48
```

### Check Status

```bash
# Get ingestion status
curl https://feature-engine-xxx.run.app/status
```

### Monitor Costs

```bash
# Check BigQuery storage
bq show --format=prettyjson utxoiq-dev:btc.blocks | jq '.numBytes, .numRows'

# Check query costs (last 100 jobs)
bq ls -j --max_results=100 --format=prettyjson | \
  jq '[.[] | select(.statistics.query.totalBytesProcessed != null) | 
  .statistics.query.totalBytesProcessed | tonumber] | add'
```

## Troubleshooting

### Views Return No Data

Check public dataset access:
```bash
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) FROM \`bigquery-public-data.crypto_bitcoin.blocks\`"
```

### High Query Costs

Ensure queries use partition filters:
```sql
-- Good: Uses partition filter
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)

-- Bad: Full table scan
WHERE number > 800000
```

### Ingestion Errors

Check service logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=feature-engine" --limit 50
```

## Documentation

- [Full Strategy Document](docs/bigquery-hybrid-strategy.md)
- [Migration Guide](docs/bigquery-migration-guide.md)
- [blockchain-etl Schema](https://github.com/blockchain-etl/bitcoin-etl)
- [Public Dataset](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=crypto_bitcoin)

## Support

For issues or questions:
- Check service status: `curl https://feature-engine-xxx.run.app/health`
- Review logs: `gcloud logging read "resource.type=cloud_run_revision"`
- Check BigQuery jobs: `bq ls -j --max_results=100`
