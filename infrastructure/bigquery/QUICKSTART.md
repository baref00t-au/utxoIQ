# BigQuery Optimization Quick Start

## Overview

This directory contains comprehensive BigQuery optimization for the utxoIQ platform, implementing partitioning, clustering, cost monitoring, and automated data archival.

## Quick Setup (3 Steps)

### Step 1: Create Tables with Partitioning/Clustering

```bash
cd infrastructure/bigquery
export GCP_PROJECT_ID="utxoiq-project"
export GCP_LOCATION="US"
./setup.sh
```

**Creates**:
- `btc.blocks` - Partitioned by timestamp, clustered by height
- `intel.signals` - Partitioned by processed_at, clustered by type, block_height
- `intel.insights` - Partitioned by created_at, clustered by signal_type, confidence
- `intel.user_feedback` - Partitioned by timestamp, clustered by insight_id, user_id

### Step 2: Set Up Cost Monitoring

```bash
export GCP_BILLING_ACCOUNT_ID="your-billing-account-id"
export ALERT_EMAIL="alerts@utxoiq.com"
export MONTHLY_BIGQUERY_BUDGET=3000
./cost_monitoring.sh
```

**Creates**:
- Budget alerts at 50%, 75%, 90%, 100% thresholds
- Daily cost tracking table
- Query optimization recommendations view

### Step 3: Set Up Data Archival

```bash
export ARCHIVE_BUCKET="utxoiq-archive"
export ARCHIVE_AGE_DAYS=730  # 2 years
./data_archival.sh
```

**Creates**:
- Archive storage bucket
- Automated daily archival job (runs at 02:00 UTC)
- External tables for archived data access
- Union views for seamless data access

## Monitoring

### Generate Optimization Report

```bash
pip install -r requirements.txt
python optimization_monitor.py --project-id utxoiq-project
```

### View Daily Costs

```bash
bq query --use_legacy_sql=false \
  'SELECT * FROM `utxoiq-project.intel.bigquery_cost_tracking` 
   ORDER BY query_date DESC LIMIT 7'
```

### View Expensive Queries

```bash
bq query --use_legacy_sql=false \
  'SELECT * FROM `utxoiq-project.intel.query_optimization_recommendations` 
   LIMIT 10'
```

## Query Best Practices

### ✅ Always Use Partition Filters

```sql
-- GOOD: Uses partition pruning
SELECT * FROM `project.intel.signals`
WHERE processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND type = 'mempool';
```

### ✅ Use Clustered Columns

```sql
-- GOOD: Leverages clustering
SELECT * FROM `project.intel.insights`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND signal_type = 'exchange'
  AND confidence >= 0.7;
```

### ✅ Specify Columns (Avoid SELECT *)

```sql
-- GOOD: Reduces data scanned
SELECT insight_id, headline, confidence, created_at
FROM `project.intel.insights`
WHERE created_at >= CURRENT_DATE();
```

## Expected Results

- **Query costs**: 90%+ reduction
- **Storage costs**: 70% reduction with archival
- **Query latency**: 90% improvement for date-filtered queries
- **Data scanned**: 95% reduction with partition pruning

## Files

- `setup.sh` - Create tables with partitioning/clustering
- `cost_monitoring.sh` - Set up budget alerts and cost tracking
- `data_archival.sh` - Set up automated archival
- `optimized_queries.sql` - Example optimized queries
- `optimization_monitor.py` - Python monitoring tool
- `README.md` - Comprehensive documentation

## Support

For detailed documentation, see `README.md`.

For troubleshooting, run the optimization monitor:
```bash
python optimization_monitor.py --project-id utxoiq-project
```
