# Cloud SQL Database Recovery Runbook

## Overview

This runbook provides step-by-step procedures for recovering the utxoIQ Cloud SQL PostgreSQL database from backups in various disaster scenarios.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Recovery Scenarios](#recovery-scenarios)
3. [Full Database Restore](#full-database-restore)
4. [Point-in-Time Recovery](#point-in-time-recovery)
5. [Partial Data Recovery](#partial-data-recovery)
6. [Disaster Recovery](#disaster-recovery)
7. [Verification Procedures](#verification-procedures)
8. [Rollback Procedures](#rollback-procedures)
9. [Post-Recovery Checklist](#post-recovery-checklist)

## Prerequisites

### Required Access

- GCP Project Owner or Cloud SQL Admin role
- Access to `gcloud` CLI with authenticated credentials
- Access to backup bucket: `gs://utxoiq-backups`
- VPN or authorized network access to Cloud SQL

### Required Information

- Project ID: `utxoiq-project`
- Instance Name: `utxoiq-postgres`
- Backup Bucket: `utxoiq-backups`
- Primary Region: `us-central1`
- Backup Region: `us-east1`

### Tools

```bash
# Verify gcloud is installed and authenticated
gcloud --version
gcloud auth list

# Verify access to Cloud SQL
gcloud sql instances list --project=utxoiq-project

# Verify access to backup bucket
gsutil ls gs://utxoiq-backups/
```

## Recovery Scenarios

### Scenario 1: Accidental Data Deletion
**Symptoms**: Specific tables or rows deleted accidentally  
**Recovery Method**: Point-in-Time Recovery (PITR)  
**Downtime**: 15-30 minutes  
**Data Loss**: Minimal (up to last transaction log)

### Scenario 2: Database Corruption
**Symptoms**: Database errors, inconsistent data, failed queries  
**Recovery Method**: Full restore from latest backup  
**Downtime**: 30-60 minutes  
**Data Loss**: Up to 24 hours (since last backup)

### Scenario 3: Regional Outage
**Symptoms**: Primary region unavailable  
**Recovery Method**: Restore from backup in secondary region  
**Downtime**: 1-2 hours  
**Data Loss**: Up to 24 hours

### Scenario 4: Complete Instance Loss
**Symptoms**: Instance deleted or completely corrupted  
**Recovery Method**: Create new instance from backup  
**Downtime**: 1-3 hours  
**Data Loss**: Up to 24 hours

## Full Database Restore

### Step 1: Assess the Situation

```bash
# Check instance status
gcloud sql instances describe utxoiq-postgres \
    --project=utxoiq-project

# List available backups
gcloud sql backups list \
    --instance=utxoiq-postgres \
    --project=utxoiq-project

# Check backup details
gcloud sql backups describe BACKUP_ID \
    --instance=utxoiq-postgres \
    --project=utxoiq-project
```

### Step 2: Create Backup of Current State (if possible)

```bash
# Create on-demand backup before restore
gcloud sql backups create \
    --instance=utxoiq-postgres \
    --project=utxoiq-project \
    --description="Pre-recovery backup $(date +%Y%m%d-%H%M%S)"
```

### Step 3: Stop Application Traffic

```bash
# Scale down web-api service to 0 instances
gcloud run services update utxoiq-api \
    --region=us-central1 \
    --min-instances=0 \
    --max-instances=0 \
    --project=utxoiq-project

# Verify no active connections
gcloud sql operations list \
    --instance=utxoiq-postgres \
    --project=utxoiq-project \
    --filter="status=RUNNING"
```

### Step 4: Restore from Backup

```bash
# Restore from specific backup
gcloud sql backups restore BACKUP_ID \
    --backup-instance=utxoiq-postgres \
    --backup-project=utxoiq-project \
    --async

# Monitor restore operation
gcloud sql operations list \
    --instance=utxoiq-postgres \
    --project=utxoiq-project \
    --filter="operationType=RESTORE_VOLUME"

# Wait for completion
gcloud sql operations wait OPERATION_ID \
    --project=utxoiq-project
```

### Step 5: Verify Database

```bash
# Connect to database
gcloud sql connect utxoiq-postgres \
    --user=postgres \
    --project=utxoiq-project

# Run verification queries
SELECT COUNT(*) FROM backfill_jobs;
SELECT COUNT(*) FROM insight_feedback;
SELECT COUNT(*) FROM system_metrics;

# Check latest timestamps
SELECT MAX(created_at) FROM backfill_jobs;
SELECT MAX(created_at) FROM insight_feedback;
SELECT MAX(timestamp) FROM system_metrics;
```

### Step 6: Restore Application Traffic

```bash
# Scale up web-api service
gcloud run services update utxoiq-api \
    --region=us-central1 \
    --min-instances=1 \
    --max-instances=10 \
    --project=utxoiq-project

# Monitor for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=utxoiq-api" \
    --limit=50 \
    --format=json
```

## Point-in-Time Recovery

### When to Use PITR

- Accidental data deletion or modification
- Need to recover to specific timestamp
- Want to minimize data loss

### PITR Procedure

#### Step 1: Identify Target Timestamp

```bash
# Determine the exact time before the incident
TARGET_TIME="2024-01-15T14:30:00Z"

# Verify PITR is enabled
gcloud sql instances describe utxoiq-postgres \
    --project=utxoiq-project \
    --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled)"
```

#### Step 2: Create Clone Instance

```bash
# Create a clone at specific point in time
gcloud sql instances clone utxoiq-postgres utxoiq-postgres-pitr-$(date +%Y%m%d) \
    --point-in-time="$TARGET_TIME" \
    --project=utxoiq-project

# Monitor clone operation
gcloud sql operations list \
    --instance=utxoiq-postgres-pitr-$(date +%Y%m%d) \
    --project=utxoiq-project
```

#### Step 3: Verify Cloned Data

```bash
# Connect to cloned instance
gcloud sql connect utxoiq-postgres-pitr-$(date +%Y%m%d) \
    --user=postgres \
    --project=utxoiq-project

# Verify data is at correct point in time
SELECT MAX(created_at) FROM backfill_jobs;
SELECT MAX(created_at) FROM insight_feedback;

# Export specific data if needed
pg_dump -h CLONE_IP -U postgres -t specific_table > recovered_data.sql
```

#### Step 4: Restore Data to Production

**Option A: Promote Clone (Full Replacement)**

```bash
# Stop production traffic
gcloud run services update utxoiq-api --min-instances=0 --max-instances=0

# Rename instances
gcloud sql instances patch utxoiq-postgres --name=utxoiq-postgres-old
gcloud sql instances patch utxoiq-postgres-pitr-$(date +%Y%m%d) --name=utxoiq-postgres

# Update connection strings and restart services
```

**Option B: Selective Data Import**

```bash
# Export specific tables from clone
pg_dump -h CLONE_IP -U postgres -t table_to_recover > recovered_table.sql

# Import to production
psql -h PROD_IP -U postgres -d utxoiq < recovered_table.sql
```

#### Step 5: Cleanup

```bash
# Delete clone instance after successful recovery
gcloud sql instances delete utxoiq-postgres-pitr-$(date +%Y%m%d) \
    --project=utxoiq-project
```

## Partial Data Recovery

### Recovering Specific Tables

```bash
# Create temporary instance from backup
gcloud sql instances clone utxoiq-postgres utxoiq-temp-recovery \
    --project=utxoiq-project

# Export specific table
gcloud sql export sql utxoiq-temp-recovery gs://utxoiq-backups/recovery/table_export.sql \
    --database=utxoiq \
    --table=backfill_jobs

# Download and review
gsutil cp gs://utxoiq-backups/recovery/table_export.sql .

# Import to production (if verified)
gcloud sql import sql utxoiq-postgres gs://utxoiq-backups/recovery/table_export.sql \
    --database=utxoiq

# Cleanup
gcloud sql instances delete utxoiq-temp-recovery
```

## Disaster Recovery

### Regional Failover Procedure

#### Step 1: Assess Regional Outage

```bash
# Check instance status
gcloud sql instances describe utxoiq-postgres \
    --project=utxoiq-project

# Check regional health
gcloud compute regions describe us-central1
```

#### Step 2: Create Instance in Secondary Region

```bash
# Get latest backup from backup region
gcloud sql backups list \
    --instance=utxoiq-postgres \
    --project=utxoiq-project \
    --filter="location:us-east1"

# Create new instance in secondary region from backup
gcloud sql instances create utxoiq-postgres-dr \
    --backup=BACKUP_ID \
    --region=us-east1 \
    --tier=db-custom-2-7680 \
    --database-version=POSTGRES_15 \
    --project=utxoiq-project
```

#### Step 3: Update Application Configuration

```bash
# Update Cloud Run services to use new instance
gcloud run services update utxoiq-api \
    --region=us-east1 \
    --set-env-vars="DATABASE_HOST=NEW_INSTANCE_IP" \
    --project=utxoiq-project

# Update Cloud SQL connection name
gcloud run services update utxoiq-api \
    --region=us-east1 \
    --set-cloudsql-instances="utxoiq-project:us-east1:utxoiq-postgres-dr" \
    --project=utxoiq-project
```

#### Step 4: Verify DR Instance

```bash
# Run health checks
curl https://utxoiq-api-HASH-ue.a.run.app/health

# Check database connectivity
gcloud sql connect utxoiq-postgres-dr \
    --user=postgres \
    --project=utxoiq-project
```

## Verification Procedures

### Data Integrity Checks

```sql
-- Check row counts
SELECT 
    'backfill_jobs' as table_name, 
    COUNT(*) as row_count 
FROM backfill_jobs
UNION ALL
SELECT 
    'insight_feedback', 
    COUNT(*) 
FROM insight_feedback
UNION ALL
SELECT 
    'system_metrics', 
    COUNT(*) 
FROM system_metrics;

-- Check for data consistency
SELECT 
    status, 
    COUNT(*) 
FROM backfill_jobs 
GROUP BY status;

-- Verify timestamps are reasonable
SELECT 
    MIN(created_at) as earliest,
    MAX(created_at) as latest,
    COUNT(*) as total
FROM backfill_jobs;

-- Check for orphaned records
SELECT COUNT(*) 
FROM insight_feedback f
LEFT JOIN backfill_jobs b ON f.insight_id = b.id::text
WHERE b.id IS NULL;
```

### Application Health Checks

```bash
# Test API endpoints
curl -X GET https://utxoiq-api-HASH.a.run.app/api/v1/monitoring/backfill/status

# Check logs for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
    --limit=100 \
    --format=json

# Monitor metrics
gcloud monitoring time-series list \
    --filter='metric.type="cloudsql.googleapis.com/database/up"' \
    --project=utxoiq-project
```

## Rollback Procedures

### If Recovery Fails

```bash
# Stop new instance
gcloud sql instances patch utxoiq-postgres \
    --activation-policy=NEVER \
    --project=utxoiq-project

# Restore from pre-recovery backup
gcloud sql backups restore PRE_RECOVERY_BACKUP_ID \
    --backup-instance=utxoiq-postgres \
    --project=utxoiq-project

# Verify rollback
gcloud sql connect utxoiq-postgres --user=postgres
```

### Emergency Contacts

- **On-Call Engineer**: [PagerDuty rotation]
- **Database Admin**: [Contact info]
- **GCP Support**: [Support case link]
- **Incident Channel**: #incidents-utxoiq

## Post-Recovery Checklist

### Immediate (0-1 hour)

- [ ] Verify database is accessible
- [ ] Confirm row counts match expectations
- [ ] Test critical API endpoints
- [ ] Check application logs for errors
- [ ] Verify no data corruption
- [ ] Monitor query performance
- [ ] Confirm backup schedule resumed

### Short-term (1-24 hours)

- [ ] Run full data integrity checks
- [ ] Verify all services are healthy
- [ ] Check monitoring dashboards
- [ ] Review recovery metrics
- [ ] Document recovery timeline
- [ ] Update incident report
- [ ] Notify stakeholders

### Long-term (1-7 days)

- [ ] Conduct post-mortem meeting
- [ ] Update recovery procedures
- [ ] Implement preventive measures
- [ ] Test recovery procedures
- [ ] Update documentation
- [ ] Train team on lessons learned
- [ ] Review backup retention policy

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

| Scenario | RTO | RPO | Method |
|----------|-----|-----|--------|
| Accidental deletion | 30 min | 0 min | PITR |
| Database corruption | 1 hour | 24 hours | Full restore |
| Regional outage | 2 hours | 24 hours | DR failover |
| Complete loss | 3 hours | 24 hours | New instance |

## Testing Schedule

- **Monthly**: Test PITR procedure
- **Quarterly**: Test full restore procedure
- **Annually**: Test disaster recovery procedure
- **Weekly**: Automated backup verification

## Additional Resources

- [Cloud SQL Backup Documentation](https://cloud.google.com/sql/docs/postgres/backup-recovery)
- [Point-in-Time Recovery Guide](https://cloud.google.com/sql/docs/postgres/backup-recovery/pitr)
- [Disaster Recovery Planning](https://cloud.google.com/architecture/dr-scenarios-planning-guide)
- Internal Wiki: [Database Operations](https://wiki.utxoiq.com/database)

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial runbook | Database Team |
