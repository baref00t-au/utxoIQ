#!/bin/bash

# BigQuery Data Archival Strategy
# Archives historical data older than 2 years to cold storage (Cloud Storage)
# Implements lifecycle management and cost optimization

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"utxoiq-project"}
ARCHIVE_BUCKET=${ARCHIVE_BUCKET:-"utxoiq-archive"}
ARCHIVE_AGE_DAYS=${ARCHIVE_AGE_DAYS:-730}  # 2 years
LOCATION=${GCP_LOCATION:-"US"}

echo "Setting up BigQuery data archival strategy for project: $PROJECT_ID"
echo "Archive threshold: ${ARCHIVE_AGE_DAYS} days ($(($ARCHIVE_AGE_DAYS / 365)) years)"

# ============================================================================
# 1. Create Archive Storage Bucket
# ============================================================================

echo "Creating archive storage bucket..."
gsutil mb -p $PROJECT_ID -c ARCHIVE -l $LOCATION gs://$ARCHIVE_BUCKET/ \
  || echo "Bucket already exists"

# Set lifecycle policy for archive bucket
cat > /tmp/archive_lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "ARCHIVE"
        },
        "condition": {
          "age": 90,
          "matchesStorageClass": ["STANDARD", "NEARLINE", "COLDLINE"]
        }
      },
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 2555,
          "matchesStorageClass": ["ARCHIVE"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/archive_lifecycle.json gs://$ARCHIVE_BUCKET/
echo "Archive bucket lifecycle policy set (ARCHIVE after 90 days, delete after 7 years)"

# ============================================================================
# 2. Create Archive Tables in BigQuery
# ============================================================================

echo "Creating archive dataset..."
bq mk --dataset \
  --location=$LOCATION \
  --description="Archived historical data (> 2 years old)" \
  $PROJECT_ID:archive || echo "Dataset archive already exists"

# ============================================================================
# 3. Create Archival Stored Procedures
# ============================================================================

echo "Creating archival stored procedures..."

# Procedure to archive old signals
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE PROCEDURE \`$PROJECT_ID.archive.archive_old_signals\`(archive_date DATE)
BEGIN
  DECLARE archive_threshold TIMESTAMP;
  DECLARE rows_archived INT64;
  
  SET archive_threshold = TIMESTAMP(archive_date);
  
  -- Export old data to Cloud Storage
  EXPORT DATA OPTIONS(
    uri=CONCAT('gs://$ARCHIVE_BUCKET/signals/', FORMAT_DATE('%Y/%m', archive_date), '/*.parquet'),
    format='PARQUET',
    compression='SNAPPY',
    overwrite=false
  ) AS
  SELECT *
  FROM \`$PROJECT_ID.intel.signals\`
  WHERE DATE(processed_at) = archive_date;
  
  -- Count rows to be deleted
  SET rows_archived = (
    SELECT COUNT(*)
    FROM \`$PROJECT_ID.intel.signals\`
    WHERE DATE(processed_at) = archive_date
  );
  
  -- Delete archived data from main table
  DELETE FROM \`$PROJECT_ID.intel.signals\`
  WHERE DATE(processed_at) = archive_date;
  
  -- Log archival operation
  INSERT INTO \`$PROJECT_ID.archive.archival_log\` (
    table_name,
    archive_date,
    rows_archived,
    archived_at,
    storage_path
  )
  VALUES (
    'intel.signals',
    archive_date,
    rows_archived,
    CURRENT_TIMESTAMP(),
    CONCAT('gs://$ARCHIVE_BUCKET/signals/', FORMAT_DATE('%Y/%m', archive_date), '/')
  );
  
  SELECT CONCAT('Archived ', CAST(rows_archived AS STRING), ' rows from intel.signals for date ', CAST(archive_date AS STRING)) as result;
END;
"

# Procedure to archive old insights
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE PROCEDURE \`$PROJECT_ID.archive.archive_old_insights\`(archive_date DATE)
BEGIN
  DECLARE archive_threshold TIMESTAMP;
  DECLARE rows_archived INT64;
  
  SET archive_threshold = TIMESTAMP(archive_date);
  
  -- Export old data to Cloud Storage
  EXPORT DATA OPTIONS(
    uri=CONCAT('gs://$ARCHIVE_BUCKET/insights/', FORMAT_DATE('%Y/%m', archive_date), '/*.parquet'),
    format='PARQUET',
    compression='SNAPPY',
    overwrite=false
  ) AS
  SELECT *
  FROM \`$PROJECT_ID.intel.insights\`
  WHERE DATE(created_at) = archive_date;
  
  -- Count rows to be deleted
  SET rows_archived = (
    SELECT COUNT(*)
    FROM \`$PROJECT_ID.intel.insights\`
    WHERE DATE(created_at) = archive_date
  );
  
  -- Delete archived data from main table
  DELETE FROM \`$PROJECT_ID.intel.insights\`
  WHERE DATE(created_at) = archive_date;
  
  -- Log archival operation
  INSERT INTO \`$PROJECT_ID.archive.archival_log\` (
    table_name,
    archive_date,
    rows_archived,
    archived_at,
    storage_path
  )
  VALUES (
    'intel.insights',
    archive_date,
    rows_archived,
    CURRENT_TIMESTAMP(),
    CONCAT('gs://$ARCHIVE_BUCKET/insights/', FORMAT_DATE('%Y/%m', archive_date), '/')
  );
  
  SELECT CONCAT('Archived ', CAST(rows_archived AS STRING), ' rows from intel.insights for date ', CAST(archive_date AS STRING)) as result;
END;
"

# Procedure to archive old user feedback
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE PROCEDURE \`$PROJECT_ID.archive.archive_old_feedback\`(archive_date DATE)
BEGIN
  DECLARE rows_archived INT64;
  
  -- Export old data to Cloud Storage
  EXPORT DATA OPTIONS(
    uri=CONCAT('gs://$ARCHIVE_BUCKET/feedback/', FORMAT_DATE('%Y/%m', archive_date), '/*.parquet'),
    format='PARQUET',
    compression='SNAPPY',
    overwrite=false
  ) AS
  SELECT *
  FROM \`$PROJECT_ID.intel.user_feedback\`
  WHERE DATE(timestamp) = archive_date;
  
  -- Count rows to be deleted
  SET rows_archived = (
    SELECT COUNT(*)
    FROM \`$PROJECT_ID.intel.user_feedback\`
    WHERE DATE(timestamp) = archive_date
  );
  
  -- Delete archived data from main table
  DELETE FROM \`$PROJECT_ID.intel.user_feedback\`
  WHERE DATE(timestamp) = archive_date;
  
  -- Log archival operation
  INSERT INTO \`$PROJECT_ID.archive.archival_log\` (
    table_name,
    archive_date,
    rows_archived,
    archived_at,
    storage_path
  )
  VALUES (
    'intel.user_feedback',
    archive_date,
    rows_archived,
    CURRENT_TIMESTAMP(),
    CONCAT('gs://$ARCHIVE_BUCKET/feedback/', FORMAT_DATE('%Y/%m', archive_date), '/')
  );
  
  SELECT CONCAT('Archived ', CAST(rows_archived AS STRING), ' rows from intel.user_feedback for date ', CAST(archive_date AS STRING)) as result;
END;
"

# ============================================================================
# 4. Create Archival Log Table
# ============================================================================

echo "Creating archival log table..."
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE TABLE IF NOT EXISTS \`$PROJECT_ID.archive.archival_log\` (
  table_name STRING NOT NULL,
  archive_date DATE NOT NULL,
  rows_archived INT64 NOT NULL,
  archived_at TIMESTAMP NOT NULL,
  storage_path STRING NOT NULL
)
PARTITION BY archive_date
CLUSTER BY table_name;
"

# ============================================================================
# 5. Create Scheduled Query for Automatic Archival
# ============================================================================

echo "Creating scheduled archival query..."

# Schedule daily archival job for data older than 2 years
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  --schedule='every day 02:00' \
  --display_name='Daily Data Archival Job' \
  --replace \
"
-- Archive signals older than ${ARCHIVE_AGE_DAYS} days
CALL \`$PROJECT_ID.archive.archive_old_signals\`(
  DATE_SUB(CURRENT_DATE(), INTERVAL ${ARCHIVE_AGE_DAYS} DAY)
);

-- Archive insights older than ${ARCHIVE_AGE_DAYS} days
CALL \`$PROJECT_ID.archive.archive_old_insights\`(
  DATE_SUB(CURRENT_DATE(), INTERVAL ${ARCHIVE_AGE_DAYS} DAY)
);

-- Archive feedback older than ${ARCHIVE_AGE_DAYS} days
CALL \`$PROJECT_ID.archive.archive_old_feedback\`(
  DATE_SUB(CURRENT_DATE(), INTERVAL ${ARCHIVE_AGE_DAYS} DAY)
);
" || echo "Scheduled query already exists"

# ============================================================================
# 6. Create External Tables for Archived Data Access
# ============================================================================

echo "Creating external table definitions for archived data..."

# External table for archived signals
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE EXTERNAL TABLE \`$PROJECT_ID.archive.signals_archived\`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://$ARCHIVE_BUCKET/signals/*/*.parquet'],
  hive_partition_uri_prefix = 'gs://$ARCHIVE_BUCKET/signals/',
  require_hive_partition_filter = false
);
"

# External table for archived insights
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE EXTERNAL TABLE \`$PROJECT_ID.archive.insights_archived\`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://$ARCHIVE_BUCKET/insights/*/*.parquet'],
  hive_partition_uri_prefix = 'gs://$ARCHIVE_BUCKET/insights/',
  require_hive_partition_filter = false
);
"

# External table for archived feedback
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE EXTERNAL TABLE \`$PROJECT_ID.archive.feedback_archived\`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://$ARCHIVE_BUCKET/feedback/*/*.parquet'],
  hive_partition_uri_prefix = 'gs://$ARCHIVE_BUCKET/feedback/',
  require_hive_partition_filter = false
);
"

# ============================================================================
# 7. Create Union Views for Seamless Access
# ============================================================================

echo "Creating union views for seamless data access..."

# Union view for signals (active + archived)
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE VIEW \`$PROJECT_ID.intel.signals_all\` AS
SELECT *, 'active' as data_source
FROM \`$PROJECT_ID.intel.signals\`
UNION ALL
SELECT *, 'archived' as data_source
FROM \`$PROJECT_ID.archive.signals_archived\`;
"

# Union view for insights (active + archived)
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE VIEW \`$PROJECT_ID.intel.insights_all\` AS
SELECT *, 'active' as data_source
FROM \`$PROJECT_ID.intel.insights\`
UNION ALL
SELECT *, 'archived' as data_source
FROM \`$PROJECT_ID.archive.insights_archived\`;
"

# ============================================================================
# 8. Create Manual Archival Script
# ============================================================================

cat > /tmp/manual_archive.sh <<'ARCHIVE_SCRIPT'
#!/bin/bash
# Manual archival script for specific date ranges

PROJECT_ID=${GCP_PROJECT_ID:-"utxoiq-project"}

if [ $# -ne 2 ]; then
  echo "Usage: $0 <start_date> <end_date>"
  echo "Example: $0 2023-01-01 2023-12-31"
  exit 1
fi

START_DATE=$1
END_DATE=$2

echo "Archiving data from $START_DATE to $END_DATE..."

# Generate date range
current_date=$START_DATE
while [ "$current_date" != "$END_DATE" ]; do
  echo "Archiving data for $current_date..."
  
  # Archive signals
  bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
    "CALL \`$PROJECT_ID.archive.archive_old_signals\`(DATE('$current_date'));"
  
  # Archive insights
  bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
    "CALL \`$PROJECT_ID.archive.archive_old_insights\`(DATE('$current_date'));"
  
  # Archive feedback
  bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
    "CALL \`$PROJECT_ID.archive.archive_old_feedback\`(DATE('$current_date'));"
  
  # Move to next date
  current_date=$(date -I -d "$current_date + 1 day")
done

echo "Archival complete!"
ARCHIVE_SCRIPT

chmod +x /tmp/manual_archive.sh
mv /tmp/manual_archive.sh ./manual_archive.sh

echo ""
echo "============================================================================"
echo "BigQuery Data Archival Strategy Setup Complete!"
echo "============================================================================"
echo ""
echo "Archive Configuration:"
echo "  - Archive Bucket: gs://$ARCHIVE_BUCKET"
echo "  - Archive Threshold: ${ARCHIVE_AGE_DAYS} days ($(($ARCHIVE_AGE_DAYS / 365)) years)"
echo "  - Storage Class: ARCHIVE (after 90 days in bucket)"
echo "  - Retention: 7 years in archive, then deleted"
echo ""
echo "Components Created:"
echo "  ✓ Archive storage bucket: gs://$ARCHIVE_BUCKET"
echo "  ✓ Archive dataset: archive"
echo "  ✓ Archival stored procedures:"
echo "    - archive.archive_old_signals()"
echo "    - archive.archive_old_insights()"
echo "    - archive.archive_old_feedback()"
echo "  ✓ Archival log table: archive.archival_log"
echo "  ✓ Scheduled daily archival job (runs at 02:00 UTC)"
echo "  ✓ External tables for archived data access"
echo "  ✓ Union views for seamless data access:"
echo "    - intel.signals_all"
echo "    - intel.insights_all"
echo ""
echo "Manual Archival:"
echo "  - Script created: ./manual_archive.sh"
echo "  - Usage: ./manual_archive.sh <start_date> <end_date>"
echo "  - Example: ./manual_archive.sh 2023-01-01 2023-12-31"
echo ""
echo "To view archival log:"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.archive.archival_log\` ORDER BY archived_at DESC LIMIT 20'"
echo ""
echo "To query archived data:"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.archive.signals_archived\` LIMIT 10'"
echo ""
echo "To query all data (active + archived):"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.intel.signals_all\` WHERE processed_at >= \"2023-01-01\" LIMIT 10'"
echo ""

# Clean up temp files
rm -f /tmp/archive_lifecycle.json
