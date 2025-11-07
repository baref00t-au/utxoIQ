# BigQuery Optimization Guide

This directory contains scripts and configurations for optimizing BigQuery storage, queries, and costs for the utxoIQ platform.

## Overview

The utxoIQ platform uses BigQuery for storing and analyzing Bitcoin blockchain data and AI-generated insights. This optimization strategy implements:

1. **Partitioned and Clustered Tables** - Efficient data organization
2. **Optimized Query Patterns** - Best practices for query performance
3. **Cost Monitoring** - Budget alerts and cost tracking
4. **Data Archival** - Automated archival of historical data (> 2 years)

## Table Structure

### Partitioning Strategy

All time-series tables are partitioned by timestamp to enable efficient date-based filtering:

- `btc.blocks` - Partitioned by `timestamp` (daily)
- `intel.signals` - Partitioned by `processed_at` (daily)
- `intel.insights` - Partitioned by `created_at` (daily)
- `intel.user_feedback` - Partitioned by `timestamp` (daily)

**Benefits:**
- Partition pruning reduces data scanned by 90%+ for date-filtered queries
- Lower query costs (only scan relevant partitions)
- Faster query execution times

### Clustering Strategy

Tables are clustered by frequently filtered columns:

- `btc.blocks` - Clustered by `height`
- `intel.signals` - Clustered by `type`, `block_height`
- `intel.insights` - Clustered by `signal_type`, `confidence`
- `intel.user_feedback` - Clustered by `insight_id`, `user_id`

**Benefits:**
- Co-located data for common filter patterns
- Reduced data scanned for WHERE clauses on clustered columns
- Improved JOIN performance

## Setup Instructions

### 1. Initial Setup

Create datasets and tables with partitioning and clustering:

```bash
cd infrastructure/bigquery
chmod +x setup.sh
./setup.sh
```

This creates:
- `btc` dataset (raw blockchain data)
- `intel` dataset (processed intelligence)
- All tables with proper partitioning and clustering

### 2. Cost Monitoring Setup

Set up budget alerts and cost tracking:

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_BILLING_ACCOUNT_ID="your-billing-account-id"
export ALERT_EMAIL="alerts@yourdomain.com"
export DAILY_BIGQUERY_BUDGET=100
export MONTHLY_BIGQUERY_BUDGET=3000

# Run cost monitoring setup
chmod +x cost_monitoring.sh
./cost_monitoring.sh
```

This creates:
- Monthly budget alerts at 50%, 75%, 90%, 100% thresholds
- Pub/Sub topic for budget notifications
- Log-based metrics for query costs
- Scheduled query for daily cost tracking
- Query optimization recommendations view

### 3. Data Archival Setup

Set up automated archival for data older than 2 years:

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export ARCHIVE_BUCKET="utxoiq-archive"
export ARCHIVE_AGE_DAYS=730  # 2 years

# Run archival setup
chmod +x data_archival.sh
./data_archival.sh
```

This creates:
- Archive storage bucket with lifecycle policies
- `archive` dataset for archived data
- Stored procedures for archival operations
- Scheduled daily archival job (runs at 02:00 UTC)
- External tables for querying archived data
- Union views for seamless access to active + archived data

## Query Optimization

### Best Practices

#### 1. Always Filter on Partitioned Columns

✅ **GOOD** - Uses partition pruning:
```sql
SELECT * FROM `project.intel.signals`
WHERE processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND type = 'mempool';
```

❌ **BAD** - Full table scan:
```sql
SELECT * FROM `project.intel.signals`
WHERE type = 'mempool';
```

#### 2. Use Clustered Columns in WHERE Clauses

✅ **GOOD** - Leverages clustering:
```sql
SELECT * FROM `project.intel.insights`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND signal_type = 'exchange'
  AND confidence >= 0.7;
```

#### 3. Avoid SELECT * - Specify Columns

✅ **GOOD** - Reduces data scanned:
```sql
SELECT insight_id, headline, confidence, created_at
FROM `project.intel.insights`
WHERE created_at >= CURRENT_DATE();
```

❌ **BAD** - Scans all columns:
```sql
SELECT * FROM `project.intel.insights`
WHERE created_at >= CURRENT_DATE();
```

#### 4. Use Approximate Aggregation for Large Datasets

✅ **GOOD** - Faster for large datasets:
```sql
SELECT 
  signal_type,
  APPROX_COUNT_DISTINCT(insight_id) as unique_insights
FROM `project.intel.insights`
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
GROUP BY signal_type;
```

### Optimized Query Examples

See `optimized_queries.sql` for comprehensive examples of:
- Recent signals by type
- Signals for specific block ranges
- Aggregate signal strength by type
- High-confidence insights by signal type
- Insights with user feedback aggregation
- Daily brief queries

### Materialized Views

Pre-aggregated views for common queries:

- `intel.daily_signal_stats` - Daily signal statistics by type
- `intel.insight_accuracy_leaderboard` - Insight accuracy rankings

## Cost Monitoring

### View Current Costs

```bash
# Daily costs by user
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.intel.bigquery_cost_tracking` 
   ORDER BY query_date DESC LIMIT 30'

# Expensive queries
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.intel.query_optimization_recommendations` 
   LIMIT 20'
```

### Budget Alerts

Budget alerts are sent to the configured Pub/Sub topic when:
- 50% of monthly budget is reached
- 75% of monthly budget is reached
- 90% of monthly budget is reached
- 100% of monthly budget is reached

### Cost Optimization Tips

1. **Use partition filters** - Always filter on partitioned timestamp columns
2. **Limit date ranges** - Query only the data you need
3. **Use clustering** - Filter on clustered columns for better performance
4. **Avoid SELECT *** - Specify only needed columns
5. **Use materialized views** - Pre-aggregate common queries
6. **Monitor query costs** - Review `query_optimization_recommendations` view

## Data Archival

### Automatic Archival

Data older than 2 years is automatically archived daily at 02:00 UTC:

1. Data is exported to Cloud Storage in Parquet format
2. Data is deleted from main tables
3. Archival operation is logged in `archive.archival_log`

### Manual Archival

Archive specific date ranges manually:

```bash
# Archive data for a date range
./manual_archive.sh 2023-01-01 2023-12-31
```

### Accessing Archived Data

#### Query Archived Data Directly

```sql
-- Query archived signals
SELECT * FROM `project.archive.signals_archived`
WHERE processed_at >= '2023-01-01'
LIMIT 10;
```

#### Query All Data (Active + Archived)

```sql
-- Query all signals (active + archived)
SELECT * FROM `project.intel.signals_all`
WHERE processed_at >= '2023-01-01'
LIMIT 10;
```

### Archive Storage Lifecycle

1. **Initial Export** - Data exported to Cloud Storage (STANDARD class)
2. **After 90 days** - Automatically moved to ARCHIVE storage class
3. **After 7 years** - Automatically deleted from archive

### View Archival Log

```bash
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.archive.archival_log` 
   ORDER BY archived_at DESC LIMIT 20'
```

## Performance Metrics

### Expected Performance

With proper partitioning and clustering:

- **Query latency**: 90% reduction for date-filtered queries
- **Data scanned**: 95% reduction with partition pruning
- **Query costs**: 90%+ reduction for optimized queries
- **Storage costs**: 70% reduction with archival strategy

### Monitoring Queries

```sql
-- Check partition sizes
SELECT
  table_name,
  partition_id,
  total_rows,
  total_logical_bytes / POW(10, 9) as size_gb
FROM `project.intel.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN ('signals', 'insights')
ORDER BY total_logical_bytes DESC
LIMIT 20;

-- Check clustering effectiveness
SELECT
  table_name,
  clustering_ordinal_position,
  clustering_field_name
FROM `project.intel.INFORMATION_SCHEMA.COLUMNS`
WHERE clustering_ordinal_position IS NOT NULL
ORDER BY table_name, clustering_ordinal_position;
```

## Troubleshooting

### High Query Costs

1. Check `query_optimization_recommendations` view
2. Verify queries use partition filters
3. Ensure queries filter on clustered columns
4. Avoid SELECT * - specify columns

### Slow Queries

1. Add partition filters on timestamp columns
2. Use clustered columns in WHERE clauses
3. Consider creating materialized views for complex aggregations
4. Review query execution plan in BigQuery console

### Archival Issues

1. Check `archive.archival_log` for errors
2. Verify Cloud Storage bucket permissions
3. Ensure scheduled query is enabled
4. Check Pub/Sub topic for error messages

## Maintenance

### Regular Tasks

- **Weekly**: Review `query_optimization_recommendations`
- **Monthly**: Check `bigquery_cost_tracking` for trends
- **Quarterly**: Review archival strategy and adjust thresholds
- **Annually**: Audit partition and clustering effectiveness

### Schema Updates

When adding new tables:

1. Always use partitioning for time-series data
2. Cluster by frequently filtered columns (max 4 columns)
3. Update `setup.sh` with new table definitions
4. Add archival procedures if needed

## References

- [BigQuery Partitioning](https://cloud.google.com/bigquery/docs/partitioned-tables)
- [BigQuery Clustering](https://cloud.google.com/bigquery/docs/clustered-tables)
- [BigQuery Cost Optimization](https://cloud.google.com/bigquery/docs/best-practices-costs)
- [BigQuery Performance Best Practices](https://cloud.google.com/bigquery/docs/best-practices-performance-overview)

## Support

For issues or questions:
- Review query execution plans in BigQuery console
- Check `query_optimization_recommendations` view
- Review archival logs in `archive.archival_log`
- Contact platform team for assistance
