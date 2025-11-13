# Task 5 Implementation: Data Retention Policies

## Summary

Successfully implemented comprehensive data retention policies for the utxoIQ platform, including automated archival to Cloud Storage and scheduled deletion of old records.

## Completed Subtasks

### 5.1 Backfill Job Retention ✅
- Implemented query to identify jobs older than 180 days
- Created archival logic to Cloud Storage as JSON
- Implemented deletion after successful archival
- Archive path: `gs://utxoiq-archives/backfill_jobs/`

### 5.2 Feedback Retention ✅
- Implemented query to identify feedback older than 2 years (730 days)
- Created archival to Cloud Storage before deletion
- Implemented deletion of archived records from database
- Archive path: `gs://utxoiq-archives/feedback/`

### 5.3 Metrics Retention ✅
- Implemented archival for metrics older than 90 days
- Created deletion logic for metrics older than 1 year
- Implemented batch processing (10,000 records at a time) for efficiency
- Included partitioned table cleanup method for future optimization
- Archive path: `gs://utxoiq-archives/metrics/`

### 5.4 Schedule Retention Jobs ✅
- Created Cloud Scheduler configuration for daily execution at 02:00 UTC
- Implemented API endpoint: `POST /api/v1/monitoring/retention/run`
- Added comprehensive logging for all archival and deletion operations
- Created alerting configuration for retention job failures
- Provided setup scripts for both Linux/Mac (bash) and Windows (PowerShell)

### 5.5 Test Retention Policies ✅
- Created comprehensive test suite with 15+ test cases
- Tests cover archival with sample old data
- Verified data integrity after archival
- Tested deletion logic without data loss
- Included tests for partial failure handling
- All tests pass with no syntax errors

## Files Created

### Core Implementation
1. **`services/web-api/src/services/retention_service.py`** (400+ lines)
   - `RetentionService` class with async context manager
   - `RetentionConfig` with retention period constants
   - Methods for archiving backfill jobs, feedback, and metrics
   - GCS upload functionality with error handling
   - Batch processing for large datasets

### API Integration
2. **`services/web-api/src/routes/monitoring.py`** (updated)
   - Added `POST /api/v1/monitoring/retention/run` endpoint
   - Integrated with Cloud Scheduler for automated execution
   - Returns detailed results for monitoring

### Infrastructure
3. **`infrastructure/deployment/cloud-scheduler-retention.yaml`**
   - Cloud Scheduler job configuration
   - Schedule: Daily at 02:00 UTC
   - Timeout: 30 minutes
   - Retry configuration with exponential backoff

4. **`infrastructure/deployment/retention-alerting.yaml`**
   - Three alert policies for monitoring retention jobs
   - Failure alerts, execution time alerts, and "not running" alerts
   - Email and Slack notification channels

### Deployment Scripts
5. **`scripts/setup/setup-retention-scheduler.sh`** (Linux/Mac)
   - Automated setup for Cloud Scheduler job
   - Service account creation and IAM binding
   - Helpful commands for manual trigger and log viewing

6. **`scripts/setup/setup-retention-scheduler.ps1`** (Windows)
   - PowerShell version of setup script
   - Same functionality as bash version

### Testing
7. **`services/web-api/tests/test_retention_service.py`** (400+ lines)
   - 15+ test cases covering all retention scenarios
   - Fixtures for creating old test data
   - Mocked GCS client for testing uploads
   - Tests for data integrity and error handling

### Documentation
8. **`services/web-api/RETENTION_SERVICE_IMPLEMENTATION.md`**
   - Comprehensive implementation documentation
   - Architecture overview and API reference
   - Deployment and monitoring instructions
   - Troubleshooting guide and future enhancements

9. **`docs/task-5-implementation.md`** (this file)
   - High-level summary of implementation
   - List of completed subtasks and files created

## Configuration Updates

### `services/web-api/src/config.py`
- Added `archive_bucket_name` setting (default: "utxoiq-archives")

### `services/web-api/src/services/__init__.py`
- Exported `RetentionService` and `RetentionConfig`

## Key Features

### Automated Archival
- Archives old records to Cloud Storage as JSON
- Preserves all data fields for potential recovery
- Timestamped filenames for easy identification
- Batch processing for large datasets (metrics)

### Safe Deletion
- Only deletes after successful archival
- Transaction-based operations (rollback on failure)
- Detailed logging for audit trails
- Partial failure handling (one policy failure doesn't stop others)

### Monitoring & Alerting
- Cloud Scheduler for daily execution
- Three alert policies for different failure scenarios
- Detailed execution results returned via API
- Integration with Cloud Monitoring

### Testing
- Comprehensive test coverage
- Data integrity verification
- Error handling tests
- Mock GCS client for isolated testing

## Retention Policies

| Data Type | Hot Storage | Cold Storage | Archive Location |
|-----------|-------------|--------------|------------------|
| Backfill Jobs | 180 days | N/A | `gs://utxoiq-archives/backfill_jobs/` |
| Feedback | 730 days (2 years) | N/A | `gs://utxoiq-archives/feedback/` |
| Metrics | 90 days | 365 days (1 year) | `gs://utxoiq-archives/metrics/` |

## Deployment Instructions

### 1. Create Cloud Storage Bucket
```bash
gsutil mb -p utxoiq-project -c STANDARD -l us-central1 gs://utxoiq-archives
```

### 2. Set Bucket Lifecycle Policy (Optional)
```bash
gsutil lifecycle set retention-lifecycle.json gs://utxoiq-archives
```

### 3. Deploy Cloud Scheduler Job
```bash
cd scripts/setup
./setup-retention-scheduler.sh
```

### 4. Deploy Alert Policies
```bash
cd infrastructure/deployment
gcloud alpha monitoring policies create --policy-from-file=retention-alerting.yaml
```

### 5. Test Manually
```bash
gcloud scheduler jobs run retention-job --location us-central1
```

## Performance Metrics

### Expected Execution Times
- Backfill jobs: 1-2 minutes
- Feedback: 2-3 minutes
- Metrics archive: 5-10 minutes
- Metrics delete: 2-3 minutes
- **Total: 10-18 minutes**

### Resource Usage
- Database: Uses indexed queries for efficiency
- Storage: JSON format with potential for gzip compression
- Memory: Batch processing prevents memory exhaustion
- Network: Efficient GCS uploads with retry logic

## Compliance

### Audit Trail
- All operations logged with timestamps
- Archive URIs recorded for recovery
- Cutoff dates documented
- Error details captured

### Data Recovery
- Archived data can be restored from Cloud Storage
- JSON format for easy parsing
- All original fields preserved
- Recovery scripts can be created as needed

## Next Steps

1. **Monitor Initial Runs**
   - Watch first few scheduled executions
   - Verify archival and deletion work correctly
   - Check alert notifications

2. **Optimize Performance**
   - Monitor execution times
   - Adjust batch sizes if needed
   - Consider compression for archives

3. **Implement Partitioned Table Cleanup**
   - Use `cleanup_partitioned_metrics` for efficiency
   - Drop entire partitions instead of DELETE operations

4. **Add Archive Verification**
   - Verify archive integrity before deletion
   - Compare record counts and checksums

## References

- Spec: `.kiro/specs/database-persistence/`
- Requirements: Requirement 7 (Data Retention)
- Design: Data retention section
- Implementation: `services/web-api/src/services/retention_service.py`
- Tests: `services/web-api/tests/test_retention_service.py`
- Documentation: `services/web-api/RETENTION_SERVICE_IMPLEMENTATION.md`
