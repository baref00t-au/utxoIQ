# BigQuery Hybrid Strategy

## Overview

This document outlines the hybrid approach for Bitcoin blockchain data using both the public BigQuery dataset and our custom real-time dataset.

## Architecture

### Data Sources

1. **Public Dataset** (`bigquery-public-data.crypto_bitcoin`)
   - Historical data (blocks older than 24 hours)
   - Maintained by Google using blockchain-etl
   - No ingestion costs
   - Schema: https://github.com/blockchain-etl/bitcoin-etl

2. **Custom Dataset** (`utxoiq-dev.btc`)
   - Real-time data (last 24 hours)
   - 60-second block processing for insights
   - Custom feature extraction
   - Dedicated query performance

### Schema Alignment

We adopt the blockchain-etl schema for consistency:

#### Blocks Table
- `hash` (STRING) - Block hash
- `size` (INTEGER) - Block size in bytes
- `stripped_size` (INTEGER) - Block size without witness data
- `weight` (INTEGER) - Block weight
- `number` (INTEGER) - Block height
- `version` (INTEGER) - Block version
- `merkle_root` (STRING) - Merkle root hash
- `timestamp` (TIMESTAMP) - Block timestamp
- `nonce` (STRING) - Block nonce
- `bits` (STRING) - Difficulty bits
- `coinbase_param` (STRING) - Coinbase parameter
- `transaction_count` (INTEGER) - Number of transactions

#### Transactions Table
- `hash` (STRING) - Transaction hash
- `size` (INTEGER) - Transaction size
- `virtual_size` (INTEGER) - Virtual transaction size
- `version` (INTEGER) - Transaction version
- `lock_time` (INTEGER) - Lock time
- `block_hash` (STRING) - Parent block hash
- `block_number` (INTEGER) - Parent block height
- `block_timestamp` (TIMESTAMP) - Block timestamp
- `is_coinbase` (BOOLEAN) - Is coinbase transaction
- `input_count` (INTEGER) - Number of inputs
- `output_count` (INTEGER) - Number of outputs
- `input_value` (INTEGER) - Total input value in satoshis
- `output_value` (INTEGER) - Total output value in satoshis
- `fee` (INTEGER) - Transaction fee in satoshis

#### Inputs Table
- `transaction_hash` (STRING) - Parent transaction hash
- `index` (INTEGER) - Input index
- `spent_transaction_hash` (STRING) - Hash of transaction being spent
- `spent_output_index` (INTEGER) - Index of output being spent
- `script_asm` (STRING) - Script assembly
- `script_hex` (STRING) - Script hex
- `sequence` (INTEGER) - Sequence number
- `required_signatures` (INTEGER) - Required signatures
- `type` (STRING) - Script type
- `addresses` (STRING, REPEATED) - Input addresses
- `value` (INTEGER) - Input value in satoshis

#### Outputs Table
- `transaction_hash` (STRING) - Parent transaction hash
- `index` (INTEGER) - Output index
- `script_asm` (STRING) - Script assembly
- `script_hex` (STRING) - Script hex
- `required_signatures` (INTEGER) - Required signatures
- `type` (STRING) - Script type
- `addresses` (STRING, REPEATED) - Output addresses
- `value` (INTEGER) - Output value in satoshis

### Partitioning Strategy

Both datasets use:
- **Partition field**: `block_timestamp` (DAY)
- **Clustering**: `block_number`, `hash`

## Implementation

### 1. Unified Views

Create views that seamlessly combine historical and real-time data:

```sql
-- Unified blocks view
CREATE OR REPLACE VIEW `utxoiq-dev.btc.blocks_unified` AS
SELECT * FROM `bigquery-public-data.crypto_bitcoin.blocks`
WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT * FROM `utxoiq-dev.btc.blocks`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);

-- Unified transactions view
CREATE OR REPLACE VIEW `utxoiq-dev.btc.transactions_unified` AS
SELECT * FROM `bigquery-public-data.crypto_bitcoin.transactions`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT * FROM `utxoiq-dev.btc.transactions`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
```

### 2. Real-Time Ingestion Pipeline

Only ingest recent blocks (last 24 hours) to minimize costs:

```python
# services/feature-engine/src/processors/block_ingestion.py
from datetime import datetime, timedelta
from google.cloud import bigquery

def should_ingest_block(block_timestamp: datetime) -> bool:
    """Only ingest blocks from last 24 hours."""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    return block_timestamp >= cutoff

def ingest_block(block_data: dict):
    """Ingest block into custom dataset."""
    if not should_ingest_block(block_data['timestamp']):
        return  # Skip historical blocks
    
    client = bigquery.Client()
    table_id = "utxoiq-dev.btc.blocks"
    
    errors = client.insert_rows_json(table_id, [block_data])
    if errors:
        raise Exception(f"BigQuery insert failed: {errors}")
```

### 3. Data Retention Policy

Automatically delete old data from custom dataset:

```sql
-- Delete blocks older than 48 hours (keep 24h buffer)
DELETE FROM `utxoiq-dev.btc.blocks`
WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);

DELETE FROM `utxoiq-dev.btc.transactions`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
```

Schedule this as a Cloud Scheduler job running every 6 hours.

### 4. Query Patterns

Always use unified views in application code:

```python
# Query recent blocks (uses custom dataset)
query = """
SELECT * FROM `utxoiq-dev.btc.blocks_unified`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY number DESC
"""

# Query historical analysis (uses public dataset)
query = """
SELECT 
  DATE(timestamp) as date,
  AVG(transaction_count) as avg_tx_count
FROM `utxoiq-dev.btc.blocks_unified`
WHERE timestamp BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY date
"""
```

## Cost Analysis

### Before (Custom Only)
- Storage: ~500 GB historical + 1 GB daily = $10/month
- Streaming inserts: 144 blocks/day × 365 = $5/month
- Query costs: $50/month
- **Total: ~$65/month**

### After (Hybrid)
- Storage: ~2 GB (24h buffer) = $0.04/month
- Streaming inserts: 144 blocks/day × 365 = $5/month
- Query costs: $30/month (reduced by using public data)
- **Total: ~$35/month**

**Savings: ~$30/month (46% reduction)**

## Migration Steps

1. Create custom dataset with blockchain-etl schema
2. Deploy unified views
3. Update ingestion pipeline to only process recent blocks
4. Update application queries to use unified views
5. Set up data retention cleanup job
6. Backfill last 24 hours of data
7. Monitor query performance and costs

## Benefits

- **Cost reduction**: 46% lower BigQuery costs
- **Simplified maintenance**: No historical data backfill needed
- **Better performance**: Smaller custom dataset = faster queries
- **Real-time capability**: Still achieve 60-second insight generation
- **Flexibility**: Can still add custom columns to recent data
- **Reliability**: Google maintains historical data pipeline
