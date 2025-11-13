# Data Retention Service Implementation

## Overview

The data retention service implements automated archival and deletion policies for old records in the utxoIQ platform. It ensures compliance with data retention requirements while controlling storage costs.

## Implementation Status

✅ **Task 5.1: Backfill Job Retention** - COMPLETED
- Query to identify jobs older than 180 days
- Archival to Cloud Storage as JSON
- Deletion after successful archival

✅ **Task 5.2: Feedback Retention** - COMPLETED
- Query to identify feedback older than 2 years
- Archive to Cloud Storage before deletion
- Delete archived records from database

✅ **Task 5.3: Metrics Retention** - COMPLETED
- Archive metrics older than 90 days to cold storage
- Delete metrics older than 1 year from cold storage
- Partitioned table cleanup for efficiency

✅ **Task 5.4: Schedule Retention Jobs** - COMPLETED
- Cloud Scheduler job for daily execution at 02:00 UTC
- Logging for all archival and deletion operations
- Alerting for retention job failures

✅ **Task 5.5: Test Retention Policies** - COMPLETED
- Tests for archival with sample old data
- Data integrity verification after archival
- Deletion logic testing without data loss

## Architecture

### Retention Service (`retention_service.py`)

The `RetentionService` class provides methods for:
- Archiving old backfill jobs (>180 days)
- Archiving old feedback (>2 years)
- Archiving old metrics (>90 days)
- Deleting very old metrics (>1 year)
- Running all retention policies together

### Configuration (`RetentionConfig`)

```python
BACKFILL_JOB_RETENTION_DAYS = 180
FEEDBACK_RETENTION_DAYS = 730  # 2 years
METRICS_HOT_STORAGE_DAYS = 90
METRICS_COLD_STORAGE_DAYS = 365  # 1 year total
ARCHIVE_BUCKET_NAME = "utxoiq-archives"
```

### Cloud Storage Structure

```
gs://utxoiq-archives/
├── backfill_jobs/
│   ├── backfill_jobs_20250110_020015.json
│   ├── backfill_jobs_20250111_020012.json
│   └── ...
├── feedback/
│   ├── feedback_20250110_020045.json
│   ├── feedback_20250111_020043.json
│   └── ...
└── metrics/
    ├── metrics_20250110_020130_batch_0.json
    ├── metrics_20250110_020145_batch_10000.json
    └── ...
```

## API Endpoint

### POST /api/v1/monitoring/retention/run

Executes all data retention policies. Designed to be called by Cloud Scheduler.

**Response:**
```json
{
  "status": "success",
  "message": "Retention policies executed successfully",
  "results": {
    "execution_time": "2025-01-10T02:00:15.123456",
    "backfill_jobs": {
      "archived_count": 15,
      "deleted_count": 15,
      "archive_uri": "gs://utxoiq-archives/backfill_jobs/backfill_jobs_20250110_020015.json",
      "cutoff_date": "2024-07-13T02:00:15.123456"
    },
    "feedback": {
      "archived_count": 42,
      "deleted_count": 42,
      "archive_uri": "gs://utxoiq-archives/feedback/feedback_20250110_020045.json",
      "cutoff_date": "2023-01-10T02:00:45.123456"
    },
    "metrics_archive": {
      "archived_count": 125000,
      "archive_uris": [
        "gs://utxoiq-archives/metrics/metrics_20250110_020130_batch_0.json",
        "gs://utxoiq-archives/metrics/metrics_20250110_020145_batch_10000.json"
      ],
      "cutoff_date": "2024-10-12T02:01:30.123456"
    },
    "metrics_delete": {
      "deleted_count": 50000,
      "cutoff_date": "2024-01-10T02:02:00.123456"
    }
  }
}
```

## Cloud Scheduler Setup

### Deployment

Run the setup script to create the Cloud Scheduler job:

**Linux/Mac:**
```bash
cd scripts/setup
chmod +x setup-retention-scheduler.sh
./setup-retention-scheduler.sh
```

**Windows:**
```powershell
cd scripts\setup
.\setup-retention-scheduler.ps1
```

### Manual Trigger

To manually trigger the retention job:
```bash
gcloud scheduler jobs run retention-job \
  --location us-central1 \
  --project utxoiq-project
```

### View Logs

To view retention job logs:
```bash
gcloud logging read \
  "resource.type=cloud_scheduler_job AND resource.labels.job_id=retention-job" \
  --limit 50 \
  --project utxoiq-project
```

## Monitoring & Alerting

### Alert Policies

Three alert policies are configured:

1. **Retention Job Failure Alert**
   - Triggers when job fails 2 consecutive times
   - Sends email and Slack notifications
   - Auto-closes after 24 hours

2. **Retention Job Long Execution Time**
   - Triggers when job takes >25 minutes (timeout is 30 minutes)
   - Sends email notification
   - Auto-closes after 1 hour

3. **Retention Job Not Running**
   - Triggers when job hasn't run successfully in 26 hours
   - Sends email and Slack notifications
   - Auto-closes after 1 hour

### Deployment

Deploy alert policies:
```bash
cd infrastructure/deployment
gcloud alpha monitoring policies create \
  --policy-from-file=retention-alerting.yaml
```

## Testing

### Run Tests

```bash
cd services/web-api
pytest tests/test_retention_service.py -v
```

### Test Coverage

The test suite covers:
- ✅ Archiving old backfill jobs
- ✅ Archiving old feedback
- ✅ Archiving old metrics
- ✅ Deleting very old metrics
- ✅ Running all policies together
- ✅ Handling partial failures
- ✅ Data integrity verification
- ✅ GCS upload success and failure
- ✅ Empty database scenarios

### Manual Testing

1. Create test data with old timestamps:
```python
from datetime import datetime, timedelta
from src.models.db_models import BackfillJob
from src.database import AsyncSessionLocal

async def create_test_data():
    old_date = datetime.utcnow() - timedelta(days=200)
    async with AsyncSessionLocal() as session:
        job = BackfillJob(
            job_type="test",
            start_block=1000,
            end_block=2000,
            current_block=2000,
            status="completed",
            progress_percentage=100.0,
            started_at=old_date
        )
        session.add(job)
        await session.commit()
```

2. Trigger retention job:
```bash
curl -X POST https://utxoiq-api.run.app/api/v1/monitoring/retention/run
```

3. Verify archival in Cloud Storage:
```bash
gsutil ls gs://utxoiq-archives/backfill_jobs/
gsutil cat gs://utxoiq-archives/backfill_jobs/backfill_jobs_*.json
```

4. Verify deletion from database:
```sql
SELECT COUNT(*) FROM backfill_jobs WHERE started_at < NOW() - INTERVAL '180 days';
```

## Error Handling

### GCS Upload Failures

If Cloud Storage upload fails:
- Error is logged with full details
- Transaction is rolled back (no deletion occurs)
- DatabaseError exception is raised
- Alert is triggered if job fails

### Database Errors

If database operations fail:
- Error is logged with context
- Transaction is rolled back
- Custom exception is raised
- Other retention policies continue (partial failure handling)

### Partial Failures

The `run_all_retention_policies` method handles partial failures:
- Each policy runs independently
- Failures are captured in results
- Other policies continue execution
- All results are returned for monitoring

## Performance Considerations

### Batch Processing

Metrics archival uses batch processing:
- Processes 10,000 records at a time
- Prevents memory exhaustion
- Creates multiple archive files for large datasets

### Database Indexes

Retention queries use indexes:
- `idx_backfill_started` on `backfill_jobs.started_at`
- `idx_feedback_created` on `insight_feedback.created_at`
- `idx_metrics_timestamp` on `system_metrics.timestamp`

### Execution Time

Expected execution times:
- Backfill jobs: 1-2 minutes
- Feedback: 2-3 minutes
- Metrics archive: 5-10 minutes
- Metrics delete: 2-3 minutes
- **Total: 10-18 minutes**

Timeout is set to 30 minutes to allow for larger datasets.

## Compliance & Audit

### Audit Logging

All retention operations are logged:
- Execution timestamp
- Number of records archived
- Number of records deleted
- Archive URIs
- Cutoff dates
- Any errors encountered

### Data Recovery

Archived data can be recovered:
1. Download archive from Cloud Storage
2. Parse JSON data
3. Re-insert into database if needed

Example:
```bash
gsutil cp gs://utxoiq-archives/backfill_jobs/backfill_jobs_20250110_020015.json .
python scripts/restore_archived_data.py backfill_jobs_20250110_020015.json
```

## Future Enhancements

### Potential Improvements

1. **Incremental Archival**
   - Archive data in smaller batches throughout the day
   - Reduce peak load on database and storage

2. **Compression**
   - Compress JSON archives with gzip
   - Reduce storage costs

3. **Partitioned Table Cleanup**
   - Implement `cleanup_partitioned_metrics` for efficient deletion
   - Drop entire partitions instead of DELETE operations

4. **Archive Verification**
   - Verify archive integrity before deletion
   - Compare record counts and checksums

5. **Retention Policy Configuration**
   - Make retention periods configurable via environment variables
   - Allow per-customer retention policies

## Troubleshooting

### Job Not Running

Check Cloud Scheduler status:
```bash
gcloud scheduler jobs describe retention-job \
  --location us-central1 \
  --project utxoiq-project
```

### Job Failing

View error logs:
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND textPayload=~'retention'" \
  --limit 100 \
  --project utxoiq-project
```

### Slow Execution

Check database performance:
```sql
SELECT * FROM pg_stat_activity WHERE query LIKE '%backfill_jobs%';
```

### Storage Issues

Check Cloud Storage bucket:
```bash
gsutil du -sh gs://utxoiq-archives/
gsutil ls -lh gs://utxoiq-archives/backfill_jobs/
```

## References

- Requirements: `.kiro/specs/database-persistence/requirements.md` (Requirement 7)
- Design: `.kiro/specs/database-persistence/design.md`
- Tasks: `.kiro/specs/database-persistence/tasks.md` (Task 5)
- Tests: `services/web-api/tests/test_retention_service.py`
