# BigQuery Schema Definitions

This directory contains SQL schema definitions for the signal-to-insight pipeline.

## Tables

### intel.signals
Stores computed blockchain signals with metadata and confidence scores.

**Partitioning**: Daily partitioning by `created_at`  
**Clustering**: `signal_type`, `block_height`

**Key Fields**:
- `signal_id`: Unique UUID identifier
- `signal_type`: mempool | exchange | miner | whale | treasury | predictive
- `block_height`: Bitcoin block height where signal was detected
- `confidence`: Score from 0.0 to 1.0
- `metadata`: JSON field with signal-specific data
- `processed`: Boolean flag for insight generation tracking

### intel.insights
Stores AI-generated insights from blockchain signals.

**Partitioning**: Daily partitioning by `created_at`  
**Clustering**: `category`, `confidence`

**Key Fields**:
- `insight_id`: Unique UUID identifier
- `signal_id`: Reference to source signal
- `category`: Matches signal_type
- `headline`: Max 80 characters
- `summary`: 2-3 sentences
- `evidence`: Struct with block_heights and transaction_ids arrays
- `chart_url`: Populated later by chart-renderer service

### btc.known_entities
Stores identified exchanges, mining pools, and treasury companies.

**Clustering**: `entity_type`, `entity_name`

**Key Fields**:
- `entity_id`: Unique identifier
- `entity_name`: Human-readable name (e.g., "Coinbase", "MicroStrategy")
- `entity_type`: exchange | mining_pool | treasury
- `addresses`: Array of Bitcoin addresses
- `metadata`: JSON field (for treasury: ticker and known_holdings_btc)

## Deployment

### Prerequisites
- Google Cloud SDK installed and authenticated
- BigQuery API enabled
- Appropriate IAM permissions (BigQuery Admin or Data Editor)

### Create Tables

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Create intel.signals table
bq query --project_id=$GCP_PROJECT_ID --use_legacy_sql=false < intel_signals.sql

# Create intel.insights table
bq query --project_id=$GCP_PROJECT_ID --use_legacy_sql=false < intel_insights.sql

# Create btc.known_entities table
bq query --project_id=$GCP_PROJECT_ID --use_legacy_sql=false < btc_known_entities.sql
```

### Verify Tables

```bash
# List tables in intel dataset
bq ls --project_id=$GCP_PROJECT_ID intel

# List tables in btc dataset
bq ls --project_id=$GCP_PROJECT_ID btc

# Show table schema
bq show --project_id=$GCP_PROJECT_ID intel.signals
bq show --project_id=$GCP_PROJECT_ID intel.insights
bq show --project_id=$GCP_PROJECT_ID btc.known_entities
```

### Query Examples

```sql
-- Get unprocessed signals with high confidence
SELECT signal_id, signal_type, block_height, confidence, created_at
FROM `intel.signals`
WHERE processed = FALSE
  AND confidence >= 0.7
ORDER BY created_at DESC
LIMIT 10;

-- Get recent insights by category
SELECT insight_id, category, headline, confidence, created_at
FROM `intel.insights`
WHERE DATE(created_at) = CURRENT_DATE()
ORDER BY created_at DESC;

-- Get treasury entities
SELECT entity_name, entity_type, JSON_EXTRACT_SCALAR(metadata, '$.ticker') as ticker
FROM `btc.known_entities`
WHERE entity_type = 'treasury'
ORDER BY entity_name;
```

## Schema Updates

When updating schemas:

1. Test changes in development environment first
2. Use `ALTER TABLE` for non-breaking changes
3. For breaking changes, create new table and migrate data
4. Update corresponding Pydantic models in `shared/types/signal_models.py`
5. Update documentation

## Maintenance

### Partition Management

BigQuery automatically manages partitions. To check partition info:

```bash
# Show partition information
bq show --project_id=$GCP_PROJECT_ID intel.signals

# Query partition metadata
SELECT
  table_name,
  partition_id,
  total_rows,
  total_logical_bytes
FROM `intel.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN ('signals', 'insights')
ORDER BY partition_id DESC
LIMIT 10;
```

### Cost Optimization

- Partitioning reduces query costs by scanning only relevant dates
- Clustering improves query performance for filtered queries
- Use `WHERE DATE(created_at) = CURRENT_DATE()` to scan single partition
- Avoid `SELECT *` - specify only needed columns

## Related Files

- Python models: `shared/types/signal_models.py`
- Entity population script: `scripts/populate_treasury_entities.py`
- Migration scripts: `infrastructure/bigquery/migrations/`
