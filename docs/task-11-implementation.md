# Task 11 Implementation: BigQuery Storage and Query Optimization

**Status**: ✅ Complete  
**Date**: 2025-11-07  
**Requirements**: 20.1, 20.2, 20.3, 20.4, 20.5

## Overview

Implemented comprehensive BigQuery optimization strategy including partitioned/clustered tables, optimized query patterns, cost monitoring with budget alerts, and automated data archival for historical data older than 2 years.

## Implementation Summary

### 1. Partitioned Tables (Requirement 20.1)

**Implementation**: `infrastructure/bigquery/setup.sh`

All time-series tables are partitioned by timestamp for efficient date-based filtering:

- `btc.blocks` - Partitioned by `timestamp` (daily)
- `intel.signals` - Partitioned by `processed_at` (daily)
- `intel.insights` - Partitioned by `created_at` (daily)
- `intel.user_feedback` - Partitioned by `timestamp` (daily)

**Benefits**:
- Partition pruning reduces data scanned by 90%+ for date-filtered queries
- Lower query costs (only scan relevant partitions)
- Faster query execution times

**Example**:
```bash
bq mk --table \
  --time_partitioning_field=processed_at \
  --time_partitioning_type=DAY \
  --clustering_fields=type,block_height \
  $PROJECT_ID:intel.signals \
  ./schemas/intel_signals.json
```

### 2. Clustered Tables (Requirement 20.2)

**Implementation**: `infrastructure/bigquery/setup.sh`

Tables are clustered by frequently filtered columns:

- `btc.blocks` - Clustered by `height`
- `intel.signals` - Clustered by `type`, `block_height`
- `intel.insights` - Clustered by `signal_type`, `confidence`
- `intel.user_feedback` - Clustered by `insight_id`, `user_id`

**Benefits**:
- Co-located data for common filter patterns
- Reduced data scanned for WHERE clauses on clustered columns
- Improved JOIN performance

### 3. Optimized Query Patterns (Requirement 20.3)

**Implementation**: `infrastructure/bigquery/optimized_queries.sql`

Created comprehensive SQL file with:

#### Best Practice Queries
- Recent signals by type (uses clustering on 'type')
- Signals for specific block range (uses clustering on 'block_height')
- Aggregate signal strength by type (partition + cluster optimization)
- High-confidence insights by signal type
- Insights with user feedback aggregation
- Daily brief queries

#### Materialized Views
- `intel.daily_signal_stats` - Pre-aggregated daily statistics
- `intel.insight_accuracy_leaderboard` - Insight accuracy rankings

#### Query Optimization Guidelines
- Always filter on partitioned columns first
- Use clustered columns in WHERE and JOIN clauses
- Avoid SELECT * - specify only needed columns
- Use approximate aggregation for large datasets

**Example Optimized Query**:
```sql
-- ✅ GOOD: Uses partition pruning and clustering
SELECT 
  signal_id, type, strength, block_height
FROM `project.intel.signals`
WHERE 
  processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND type = 'mempool'
ORDER BY processed_at DESC
LIMIT 100;
```

### 4. Cost Monitoring with Budget Alerts (Requirement 20.4)

**Implementation**: `infrastructure/bigquery/cost_monitoring.sh`

Comprehensive cost monitoring system:

#### Budget Alerts
- Monthly BigQuery budget with configurable thresholds
- Alert thresholds at 50%, 75%, 90%, and 100%
- Pub/Sub topic for budget notifications
- Integration with Cloud Monitoring

#### Log-based Metrics
- `bigquery_bytes_processed` - Total bytes processed by queries
- `bigquery_query_count` - Count of queries executed

#### Cost Tracking
- Scheduled query for daily cost tracking
- `intel.bigquery_cost_tracking` table with daily aggregations
- Cost analysis by user/service
- Query optimization recommendations view

#### Monitoring Components
```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="BigQuery Monthly Budget" \
  --budget-amount=${MONTHLY_BUDGET}USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=75 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

#### Cost Analysis Views
- `intel.bigquery_cost_tracking` - Daily cost aggregations
- `intel.query_optimization_recommendations` - Optimization suggestions

### 5. Data Archival Strategy (Requirement 20.5)

**Implementation**: `infrastructure/bigquery/data_archival.sh`

Automated archival for data older than 2 years:

#### Archive Storage
- Cloud Storage bucket with ARCHIVE storage class
- Lifecycle policy: ARCHIVE after 90 days, delete after 7 years
- Parquet format with Snappy compression

#### Archival Procedures
- `archive.archive_old_signals()` - Archive signals by date
- `archive.archive_old_insights()` - Archive insights by date
- `archive.archive_old_feedback()` - Archive feedback by date

#### Automated Archival
- Scheduled daily job at 02:00 UTC
- Archives data older than 730 days (2 years)
- Logs all operations in `archive.archival_log`

#### Data Access
- External tables for querying archived data
- Union views for seamless access to active + archived data:
  - `intel.signals_all` - All signals (active + archived)
  - `intel.insights_all` - All insights (active + archived)

**Archival Process**:
```sql
-- Export to Cloud Storage
EXPORT DATA OPTIONS(
  uri='gs://utxoiq-archive/signals/2023/01/*.parquet',
  format='PARQUET',
  compression='SNAPPY'
) AS
SELECT * FROM `project.intel.signals`
WHERE DATE(processed_at) = '2023-01-01';

-- Delete from main table
DELETE FROM `project.intel.signals`
WHERE DATE(processed_at) = '2023-01-01';
```

#### Manual Archival
- `manual_archive.sh` script for specific date ranges
- Usage: `./manual_archive.sh 2023-01-01 2023-12-31`

## Files Created

### Core Implementation
1. **infrastructure/bigquery/setup.sh** - Table creation with partitioning/clustering
2. **infrastructure/bigquery/optimized_queries.sql** - Optimized query patterns
3. **infrastructure/bigquery/cost_monitoring.sh** - Cost monitoring setup
4. **infrastructure/bigquery/data_archival.sh** - Archival strategy setup

### Supporting Files
5. **infrastructure/bigquery/README.md** - Comprehensive documentation
6. **infrastructure/bigquery/optimization_monitor.py** - Python monitoring tool
7. **infrastructure/bigquery/requirements.txt** - Python dependencies
8. **infrastructure/bigquery/manual_archive.sh** - Manual archival script (generated)

### Schema Files (Already Existed)
- `infrastructure/bigquery/schemas/btc_blocks.json`
- `infrastructure/bigquery/schemas/intel_signals.json`
- `infrastructure/bigquery/schemas/intel_insights.json`
- `infrastructure/bigquery/schemas/intel_user_feedback.json`

## Setup Instructions

### 1. Initial Setup

```bash
cd infrastructure/bigquery

# Set environment variables
export GCP_PROJECT_ID="utxoiq-project"
export GCP_LOCATION="US"

# Create datasets and tables
./setup.sh
```

### 2. Cost Monitoring Setup

```bash
# Set environment variables
export GCP_BILLING_ACCOUNT_ID="your-billing-account-id"
export ALERT_EMAIL="alerts@utxoiq.com"
export DAILY_BIGQUERY_BUDGET=100
export MONTHLY_BIGQUERY_BUDGET=3000

# Run cost monitoring setup
./cost_monitoring.sh
```

### 3. Data Archival Setup

```bash
# Set environment variables
export ARCHIVE_BUCKET="utxoiq-archive"
export ARCHIVE_AGE_DAYS=730  # 2 years

# Run archival setup
./data_archival.sh
```

### 4. Install Python Monitoring Tool

```bash
pip install -r requirements.txt

# Generate optimization report
python optimization_monitor.py --project-id utxoiq-project
```

## Usage Examples

### Query Optimization

```sql
-- Get recent high-confidence insights (optimized)
SELECT 
  insight_id, signal_type, confidence, headline, created_at
FROM `project.intel.insights`
WHERE 
  created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND signal_type = 'exchange'
  AND confidence >= 0.7
ORDER BY created_at DESC
LIMIT 50;
```

### Cost Monitoring

```bash
# View daily costs
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.intel.bigquery_cost_tracking` 
   ORDER BY query_date DESC LIMIT 30'

# View expensive queries
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.intel.query_optimization_recommendations` 
   LIMIT 20'
```

### Data Archival

```bash
# Manual archival for date range
./manual_archive.sh 2023-01-01 2023-12-31

# View archival log
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.archive.archival_log` 
   ORDER BY archived_at DESC LIMIT 20'

# Query archived data
bq query --use_legacy_sql=false \
  'SELECT * FROM `project.intel.signals_all` 
   WHERE processed_at >= "2023-01-01" LIMIT 10'
```

### Monitoring Report

```bash
# Generate comprehensive report
python optimization_monitor.py \
  --project-id utxoiq-project \
  --output optimization_report.txt
```

## Performance Metrics

### Expected Improvements

With proper partitioning and clustering:

- **Query latency**: 90% reduction for date-filtered queries
- **Data scanned**: 95% reduction with partition pruning
- **Query costs**: 90%+ reduction for optimized queries
- **Storage costs**: 70% reduction with archival strategy

### Cost Estimates

**Before Optimization**:
- Full table scans on 1TB dataset: ~$5 per query
- 1000 queries/day: ~$5,000/day = ~$150,000/month

**After Optimization**:
- Partition-pruned queries on 10GB: ~$0.05 per query
- 1000 queries/day: ~$50/day = ~$1,500/month
- **Savings**: ~$148,500/month (99% reduction)

### Storage Savings

**Before Archival**:
- 3 years of data: ~5TB
- Storage cost: ~$100/month

**After Archival**:
- Active data (< 2 years): ~3TB at $20/month
- Archived data (> 2 years): ~2TB at $2/month (ARCHIVE class)
- **Savings**: ~$78/month (78% reduction)

## Monitoring and Maintenance

### Daily Tasks
- Review cost tracking dashboard
- Check for queries missing partition filters

### Weekly Tasks
- Review `query_optimization_recommendations` view
- Analyze expensive queries and optimize

### Monthly Tasks
- Review `bigquery_cost_tracking` for trends
- Verify budget alerts are working
- Check archival log for any errors

### Quarterly Tasks
- Review archival strategy and adjust thresholds
- Audit partition and clustering effectiveness
- Update materialized views if needed

## Integration with Services

### Feature Engine
- Use optimized queries for signal processing
- Filter on `processed_at` partition column
- Use `type` clustering for signal type filtering

### Insight Generator
- Query insights with `created_at` partition filter
- Use `signal_type` and `confidence` clustering
- Leverage materialized views for aggregations

### Web API
- Use partition filters in all date-based queries
- Implement query result caching
- Use union views for historical data access

### Grafana Dashboard
- Query cost tracking tables for metrics
- Display partition usage statistics
- Show archival status and storage savings

## Troubleshooting

### High Query Costs

1. Check `query_optimization_recommendations` view
2. Verify queries use partition filters
3. Ensure queries filter on clustered columns
4. Run optimization monitor: `python optimization_monitor.py`

### Slow Queries

1. Add partition filters on timestamp columns
2. Use clustered columns in WHERE clauses
3. Consider creating materialized views
4. Review query execution plan in BigQuery console

### Archival Issues

1. Check `archive.archival_log` for errors
2. Verify Cloud Storage bucket permissions
3. Ensure scheduled query is enabled
4. Check Pub/Sub topic for error messages

## Testing

### Verify Partitioning

```sql
-- Check partition information
SELECT
  table_name,
  partition_id,
  total_rows,
  total_logical_bytes / POW(10, 9) as size_gb
FROM `project.intel.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name IN ('signals', 'insights')
ORDER BY total_logical_bytes DESC
LIMIT 20;
```

### Verify Clustering

```sql
-- Check clustering configuration
SELECT
  table_name,
  clustering_ordinal_position,
  clustering_field_name
FROM `project.intel.INFORMATION_SCHEMA.COLUMNS`
WHERE clustering_ordinal_position IS NOT NULL
ORDER BY table_name, clustering_ordinal_position;
```

### Test Query Performance

```bash
# Run test query and check bytes processed
bq query --use_legacy_sql=false --dry_run \
  'SELECT * FROM `project.intel.signals` 
   WHERE processed_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)'
```

## Security Considerations

- Budget alerts sent to secure Pub/Sub topic
- Archive bucket with restricted IAM permissions
- Cost tracking data accessible only to authorized users
- Archival logs for audit trail

## Compliance

- Data retention policy: 2 years active, 7 years archived
- Automated archival ensures compliance
- Audit trail in `archive.archival_log`
- GDPR-compliant data deletion after 7 years

## Future Enhancements

1. **Machine Learning Cost Prediction**
   - Predict future costs based on usage patterns
   - Automated budget adjustments

2. **Advanced Query Optimization**
   - Automatic query rewriting for optimization
   - Query plan analysis and recommendations

3. **Multi-region Archival**
   - Geo-redundant archive storage
   - Cross-region disaster recovery

4. **Real-time Cost Alerts**
   - Slack/email notifications for cost spikes
   - Automated query throttling

## References

- [BigQuery Partitioning Documentation](https://cloud.google.com/bigquery/docs/partitioned-tables)
- [BigQuery Clustering Documentation](https://cloud.google.com/bigquery/docs/clustered-tables)
- [BigQuery Cost Optimization](https://cloud.google.com/bigquery/docs/best-practices-costs)
- [BigQuery Performance Best Practices](https://cloud.google.com/bigquery/docs/best-practices-performance-overview)

## Conclusion

Task 11 successfully implements comprehensive BigQuery optimization including:

✅ Partitioned tables for intel.signals by timestamp (Requirement 20.1)  
✅ Clustered tables for intel.insights by signal_type (Requirement 20.2)  
✅ Optimized query patterns to minimize full table scans (Requirement 20.3)  
✅ BigQuery cost monitoring with budget alerts (Requirement 20.4)  
✅ Data archival strategy for historical data > 2 years (Requirement 20.5)

Expected cost savings: **99% reduction in query costs**, **78% reduction in storage costs**.
