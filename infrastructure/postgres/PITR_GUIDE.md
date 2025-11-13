# Point-in-Time Recovery (PITR) Guide

## Overview

Point-in-Time Recovery (PITR) allows you to restore your Cloud SQL database to any specific point in time within the retention period. This is useful for recovering from accidental data modifications or deletions.

## When to Use PITR

### Ideal Scenarios
- Accidental `DELETE` or `UPDATE` without `WHERE` clause
- Incorrect data migration or import
- Application bug that corrupted data
- Need to recover specific transactions
- Want to minimize data loss

### Not Ideal For
- Complete database corruption (use full restore)
- Regional outages (use disaster recovery)
- Performance issues (not a recovery scenario)
- Schema changes (may require additional steps)

## Prerequisites

### Requirements
- Point-in-time recovery must be enabled on the instance
- Binary logging must be enabled
- Target time must be within retention period (7 days)
- Sufficient permissions (Cloud SQL Admin role)

### Verify PITR is Enabled

```bash
# Check PITR status
gcloud sql instances describe utxoiq-postgres \
    --project=utxoiq-project \
    --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled)"

# Check binary log status
gcloud sql instances describe utxoiq-postgres \
    --project=utxoiq-project \
    --format="value(settings.backupConfiguration.binaryLogEnabled)"

# Check retention period
gcloud sql instances describe utxoiq-postgres \
    --project=utxoiq-project \
    --format="value(settings.backupConfiguration.transactionLogRetentionDays)"
```

## PITR Process

### Step 1: Identify the Target Time

#### Determine When the Incident Occurred

```bash
# Check application logs for the incident
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
    --limit=100 \
    --format=json \
    --project=utxoiq-project

# Check database audit logs
gcloud logging read "resource.type=cloudsql_database AND protoPayload.methodName=~'.*delete.*'" \
    --limit=50 \
    --format=json \
    --project=utxoiq-project
```

#### Query Database for Last Known Good State

```sql
-- Find last known good record
SELECT MAX(created_at) 
FROM backfill_jobs 
WHERE status = 'completed';

-- Check when problematic data appeared
SELECT MIN(created_at) 
FROM insight_feedback 
WHERE rating < 0;  -- Example: invalid data

-- Review recent modifications
SELECT 
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC;
```

#### Set Target Time

```bash
# Target time should be BEFORE the incident
# Format: RFC 3339 (YYYY-MM-DDTHH:MM:SSZ)
TARGET_TIME="2024-01-15T14:30:00Z"

# Verify target time is within retention period
RETENTION_DAYS=7
EARLIEST_RECOVERY=$(date -u -d "$RETENTION_DAYS days ago" +"%Y-%m-%dT%H:%M:%SZ")

echo "Target time: $TARGET_TIME"
echo "Earliest possible recovery: $EARLIEST_RECOVERY"
```

### Step 2: Create a Clone Instance

#### Option A: Clone to New Instance (Recommended)

```bash
# Create clone at specific point in time
CLONE_NAME="utxoiq-postgres-pitr-$(date +%Y%m%d-%H%M%S)"

gcloud sql instances clone utxoiq-postgres "$CLONE_NAME" \
    --point-in-time="$TARGET_TIME" \
    --project=utxoiq-project

# Monitor clone operation
gcloud sql operations list \
    --instance="$CLONE_NAME" \
    --project=utxoiq-project \
    --filter="operationType=CLONE"

# Wait for completion (can take 10-30 minutes)
gcloud sql operations wait OPERATION_ID \
    --project=utxoiq-project
```

#### Option B: Clone with Custom Configuration

```bash
# Clone with specific tier and storage
gcloud sql instances clone utxoiq-postgres "$CLONE_NAME" \
    --point-in-time="$TARGET_TIME" \
    --tier=db-custom-2-7680 \
    --storage-size=100 \
    --project=utxoiq-project
```

### Step 3: Verify Cloned Data

#### Connect to Clone Instance

```bash
# Get clone instance IP
CLONE_IP=$(gcloud sql instances describe "$CLONE_NAME" \
    --project=utxoiq-project \
    --format="value(ipAddresses[0].ipAddress)")

# Connect using Cloud SQL Proxy
cloud_sql_proxy -instances=utxoiq-project:us-central1:$CLONE_NAME=tcp:5433 &

# Connect to database
psql "host=127.0.0.1 port=5433 dbname=utxoiq user=postgres sslmode=require"
```

#### Verify Data State

```sql
-- Check row counts
SELECT 
    'backfill_jobs' as table_name,
    COUNT(*) as row_count,
    MAX(created_at) as latest_record
FROM backfill_jobs
UNION ALL
SELECT 
    'insight_feedback',
    COUNT(*),
    MAX(created_at)
FROM insight_feedback
UNION ALL
SELECT 
    'system_metrics',
    COUNT(*),
    MAX(timestamp)
FROM system_metrics;

-- Verify problematic data is not present
SELECT COUNT(*) 
FROM insight_feedback 
WHERE rating < 0;  -- Should be 0

-- Check specific records
SELECT * 
FROM backfill_jobs 
WHERE id = 'SPECIFIC_ID'
ORDER BY created_at DESC;

-- Verify data integrity
SELECT 
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### Step 4: Extract Recovered Data

#### Option A: Export Specific Tables

```bash
# Export single table
gcloud sql export sql "$CLONE_NAME" \
    gs://utxoiq-backups/pitr-recovery/backfill_jobs_$(date +%Y%m%d).sql \
    --database=utxoiq \
    --table=backfill_jobs \
    --project=utxoiq-project

# Export multiple tables
gcloud sql export sql "$CLONE_NAME" \
    gs://utxoiq-backups/pitr-recovery/recovered_data_$(date +%Y%m%d).sql \
    --database=utxoiq \
    --table=backfill_jobs,insight_feedback \
    --project=utxoiq-project

# Download exported data
gsutil cp gs://utxoiq-backups/pitr-recovery/*.sql ./recovery/
```

#### Option B: Export Specific Rows

```bash
# Connect to clone and export specific data
psql "host=127.0.0.1 port=5433 dbname=utxoiq user=postgres" <<EOF
\copy (SELECT * FROM backfill_jobs WHERE created_at >= '2024-01-15 00:00:00') TO 'recovered_jobs.csv' CSV HEADER;
\copy (SELECT * FROM insight_feedback WHERE created_at >= '2024-01-15 00:00:00') TO 'recovered_feedback.csv' CSV HEADER;
EOF
```

#### Option C: Use pg_dump for Complex Exports

```bash
# Export with pg_dump
pg_dump -h 127.0.0.1 -p 5433 -U postgres -d utxoiq \
    -t backfill_jobs \
    -t insight_feedback \
    --data-only \
    --column-inserts \
    > recovered_data.sql

# Export schema and data
pg_dump -h 127.0.0.1 -p 5433 -U postgres -d utxoiq \
    -t backfill_jobs \
    --clean \
    --if-exists \
    > recovered_with_schema.sql
```

### Step 5: Restore Data to Production

#### Preparation

```bash
# Create backup of current production state
gcloud sql backups create \
    --instance=utxoiq-postgres \
    --project=utxoiq-project \
    --description="Pre-PITR-restore backup $(date +%Y%m%d-%H%M%S)"

# Stop application traffic (if needed for consistency)
gcloud run services update utxoiq-api \
    --region=us-central1 \
    --min-instances=0 \
    --max-instances=0 \
    --project=utxoiq-project
```

#### Option A: Replace Entire Tables

```sql
-- Connect to production
psql "host=PROD_IP dbname=utxoiq user=postgres"

-- Begin transaction
BEGIN;

-- Backup current data (optional)
CREATE TABLE backfill_jobs_backup AS SELECT * FROM backfill_jobs;

-- Truncate and restore
TRUNCATE TABLE backfill_jobs CASCADE;

-- Import from clone (using pg_dump output)
\i recovered_data.sql

-- Verify counts
SELECT COUNT(*) FROM backfill_jobs;
SELECT COUNT(*) FROM backfill_jobs_backup;

-- Commit if satisfied
COMMIT;
-- Or rollback if issues
-- ROLLBACK;
```

#### Option B: Selective Row Restoration

```sql
-- Connect to production
BEGIN;

-- Delete problematic rows
DELETE FROM insight_feedback 
WHERE rating < 0;

-- Insert recovered rows
\copy insight_feedback FROM 'recovered_feedback.csv' CSV HEADER;

-- Verify
SELECT COUNT(*) FROM insight_feedback WHERE rating < 0;

COMMIT;
```

#### Option C: Merge Data

```sql
-- Connect to production
BEGIN;

-- Create temporary table with recovered data
CREATE TEMP TABLE recovered_jobs AS 
SELECT * FROM backfill_jobs WHERE 1=0;

\copy recovered_jobs FROM 'recovered_jobs.csv' CSV HEADER;

-- Merge using UPSERT
INSERT INTO backfill_jobs 
SELECT * FROM recovered_jobs
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status,
    progress_percentage = EXCLUDED.progress_percentage,
    current_block = EXCLUDED.current_block,
    updated_at = EXCLUDED.updated_at;

COMMIT;
```

### Step 6: Verify Production Data

```sql
-- Check row counts match expectations
SELECT COUNT(*) FROM backfill_jobs;
SELECT COUNT(*) FROM insight_feedback;

-- Verify no invalid data
SELECT COUNT(*) FROM insight_feedback WHERE rating < 0;
SELECT COUNT(*) FROM insight_feedback WHERE rating > 5;

-- Check data consistency
SELECT 
    status,
    COUNT(*) as count
FROM backfill_jobs
GROUP BY status;

-- Verify timestamps
SELECT 
    MIN(created_at) as earliest,
    MAX(created_at) as latest
FROM backfill_jobs;
```

### Step 7: Restore Application Traffic

```bash
# Scale up services
gcloud run services update utxoiq-api \
    --region=us-central1 \
    --min-instances=1 \
    --max-instances=10 \
    --project=utxoiq-project

# Monitor for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
    --limit=50 \
    --format=json \
    --project=utxoiq-project

# Test API endpoints
curl https://utxoiq-api.run.app/api/v1/monitoring/backfill/status
curl https://utxoiq-api.run.app/api/v1/feedback/stats/insight-123
```

### Step 8: Cleanup

```bash
# Delete clone instance
gcloud sql instances delete "$CLONE_NAME" \
    --project=utxoiq-project

# Clean up local files
rm -rf recovery/
rm recovered_*.sql recovered_*.csv

# Clean up GCS exports (after verification)
gsutil rm gs://utxoiq-backups/pitr-recovery/*.sql
```

## Advanced PITR Scenarios

### Scenario 1: Recovering from Multiple Tables

```bash
# Create clone
gcloud sql instances clone utxoiq-postgres utxoiq-pitr-multi \
    --point-in-time="$TARGET_TIME"

# Export all affected tables
for table in backfill_jobs insight_feedback system_metrics; do
    gcloud sql export sql utxoiq-pitr-multi \
        gs://utxoiq-backups/pitr-recovery/${table}.sql \
        --database=utxoiq \
        --table=$table
done

# Download and review
gsutil -m cp gs://utxoiq-backups/pitr-recovery/*.sql ./recovery/

# Import to production (in transaction)
psql "host=PROD_IP dbname=utxoiq user=postgres" <<EOF
BEGIN;
\i recovery/backfill_jobs.sql
\i recovery/insight_feedback.sql
\i recovery/system_metrics.sql
COMMIT;
EOF
```

### Scenario 2: Recovering with Schema Changes

```bash
# If schema changed between target time and now
# 1. Clone at target time
gcloud sql instances clone utxoiq-postgres utxoiq-pitr-schema \
    --point-in-time="$TARGET_TIME"

# 2. Export data only (no schema)
pg_dump -h CLONE_IP -U postgres -d utxoiq \
    --data-only \
    --column-inserts \
    -t backfill_jobs \
    > data_only.sql

# 3. Manually adjust INSERT statements for new schema
# Edit data_only.sql to match current schema

# 4. Import adjusted data
psql -h PROD_IP -U postgres -d utxoiq < data_only.sql
```

### Scenario 3: Partial Table Recovery

```sql
-- Recover only specific rows based on criteria
-- Connect to clone
psql "host=CLONE_IP dbname=utxoiq user=postgres"

-- Export specific rows
\copy (
    SELECT * FROM backfill_jobs 
    WHERE created_at BETWEEN '2024-01-15 00:00:00' AND '2024-01-15 23:59:59'
    AND status = 'completed'
) TO 'partial_recovery.csv' CSV HEADER;

-- Import to production
psql "host=PROD_IP dbname=utxoiq user=postgres"
\copy backfill_jobs FROM 'partial_recovery.csv' CSV HEADER;
```

## Troubleshooting

### Clone Creation Fails

```bash
# Check if PITR is enabled
gcloud sql instances describe utxoiq-postgres \
    --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled)"

# Check if target time is within retention
gcloud sql instances describe utxoiq-postgres \
    --format="value(settings.backupConfiguration.transactionLogRetentionDays)"

# Check for ongoing operations
gcloud sql operations list \
    --instance=utxoiq-postgres \
    --filter="status=RUNNING"
```

### Data Doesn't Match Expected State

```sql
-- Check transaction log position
SELECT pg_current_wal_lsn();

-- Check last transaction time
SELECT MAX(xact_commit) FROM pg_stat_database;

-- Verify target time was correct
SELECT NOW(), NOW() - INTERVAL '7 days';
```

### Import Fails

```bash
# Check for constraint violations
psql -h PROD_IP -U postgres -d utxoiq <<EOF
-- Temporarily disable constraints
ALTER TABLE backfill_jobs DISABLE TRIGGER ALL;

-- Import data
\i recovered_data.sql

-- Re-enable constraints
ALTER TABLE backfill_jobs ENABLE TRIGGER ALL;

-- Verify constraints
SELECT * FROM backfill_jobs WHERE id IS NULL;
EOF
```

## Best Practices

### Before PITR
1. Document the incident timeline
2. Identify exact target time
3. Create production backup
4. Notify stakeholders
5. Plan rollback strategy

### During PITR
1. Verify clone data before importing
2. Use transactions for imports
3. Test on staging first if possible
4. Monitor application during restore
5. Keep detailed logs

### After PITR
1. Verify data integrity
2. Monitor application behavior
3. Document recovery process
4. Conduct post-mortem
5. Update procedures

## Recovery Time Estimates

| Data Size | Clone Time | Verification | Import | Total |
|-----------|------------|--------------|--------|-------|
| < 10 GB | 10-15 min | 5 min | 5 min | 20-25 min |
| 10-50 GB | 15-25 min | 10 min | 10 min | 35-45 min |
| 50-100 GB | 25-40 min | 15 min | 15 min | 55-70 min |
| > 100 GB | 40-60 min | 20 min | 20 min | 80-100 min |

## Checklist

- [ ] PITR is enabled on instance
- [ ] Target time identified and verified
- [ ] Target time is within retention period
- [ ] Production backup created
- [ ] Clone instance created successfully
- [ ] Clone data verified
- [ ] Recovery data exported
- [ ] Application traffic stopped (if needed)
- [ ] Data imported to production
- [ ] Production data verified
- [ ] Application traffic restored
- [ ] Clone instance deleted
- [ ] Recovery documented

## Additional Resources

- [Cloud SQL PITR Documentation](https://cloud.google.com/sql/docs/postgres/backup-recovery/pitr)
- [PostgreSQL WAL Documentation](https://www.postgresql.org/docs/current/wal-intro.html)
- [Recovery Runbook](./RECOVERY_RUNBOOK.md)
- [Disaster Recovery Checklist](./DISASTER_RECOVERY_CHECKLIST.md)
