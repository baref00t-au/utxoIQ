# Cloud SQL Backup and Recovery

## Overview

This directory contains all configuration, scripts, and documentation for Cloud SQL PostgreSQL backup and recovery operations for the utxoIQ platform.

## Contents

### Configuration Files
- `backup-config.yaml` - Backup configuration settings
- `terraform-backup.tf` - Terraform infrastructure as code for backup setup

### Setup Scripts
- `setup-backup.sh` - Bash script to configure automated backups
- `setup-backup.ps1` - PowerShell script to configure automated backups (Windows)
- `deploy-verification-function.sh` - Deploy backup verification Cloud Function

### Verification
- `backup-verification-function.py` - Cloud Function for weekly backup verification
- `backup-verification-requirements.txt` - Python dependencies for verification function

### Testing
- `test-backup-recovery.sh` - Automated test suite for backup and recovery (Bash)
- `test-backup-recovery.ps1` - Automated test suite for backup and recovery (PowerShell)

### Documentation
- `RECOVERY_RUNBOOK.md` - Comprehensive recovery procedures for all scenarios
- `DISASTER_RECOVERY_CHECKLIST.md` - Quick reference checklist for disaster recovery
- `PITR_GUIDE.md` - Detailed guide for point-in-time recovery
- `README.md` - This file

### Database Files
- `init.sql` - Initial database schema setup

## Quick Start

### 1. Configure Automated Backups

**Linux/Mac:**
```bash
cd infrastructure/postgres
chmod +x setup-backup.sh
./setup-backup.sh
```

**Windows:**
```powershell
cd infrastructure\postgres
.\setup-backup.ps1
```

### 2. Deploy Backup Verification

```bash
cd infrastructure/postgres
chmod +x deploy-verification-function.sh
./deploy-verification-function.sh
```

### 3. Test Backup and Recovery

**Linux/Mac:**
```bash
chmod +x test-backup-recovery.sh
./test-backup-recovery.sh
```

**Windows:**
```powershell
.\test-backup-recovery.ps1
```

## Backup Configuration

### Automated Backups
- **Schedule**: Daily at 01:00 UTC
- **Retention**: 7 daily backups
- **Location**: us-east1 (separate from primary region)
- **Type**: Full database backup

### Point-in-Time Recovery (PITR)
- **Enabled**: Yes
- **Retention**: 7 days of transaction logs
- **Granularity**: Any point in time within retention period

### High Availability
- **Type**: Regional (with failover replica)
- **Automatic Failover**: Enabled
- **Maintenance Window**: Sunday 02:00 UTC

## Backup Verification

### Automated Verification
- **Schedule**: Weekly on Sunday at 03:00 UTC
- **Method**: Restore to temporary instance
- **Checks**: Instance accessibility, data integrity
- **Cleanup**: Automatic after 2 hours

### Manual Verification
```bash
# Trigger verification via API
curl -X POST https://utxoiq-api.run.app/api/v1/backup/verify \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Check verification history
curl https://utxoiq-api.run.app/api/v1/backup/verify/history \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Recovery Procedures

### Quick Recovery Commands

**List Available Backups:**
```bash
gcloud sql backups list \
  --instance=utxoiq-postgres \
  --project=utxoiq-project
```

**Restore from Latest Backup:**
```bash
# Get latest backup ID
BACKUP_ID=$(gcloud sql backups list \
  --instance=utxoiq-postgres \
  --project=utxoiq-project \
  --filter="status=SUCCESSFUL" \
  --limit=1 \
  --format="value(id)")

# Restore
gcloud sql backups restore $BACKUP_ID \
  --backup-instance=utxoiq-postgres \
  --project=utxoiq-project
```

**Point-in-Time Recovery:**
```bash
# Clone to specific time
TARGET_TIME="2024-01-15T14:30:00Z"
gcloud sql instances clone utxoiq-postgres utxoiq-postgres-pitr \
  --point-in-time="$TARGET_TIME" \
  --project=utxoiq-project
```

### Detailed Recovery Guides

For detailed recovery procedures, see:
- [RECOVERY_RUNBOOK.md](./RECOVERY_RUNBOOK.md) - Complete recovery procedures
- [DISASTER_RECOVERY_CHECKLIST.md](./DISASTER_RECOVERY_CHECKLIST.md) - Quick reference checklist
- [PITR_GUIDE.md](./PITR_GUIDE.md) - Point-in-time recovery guide

## Monitoring

### Backup Metrics
- Backup success/failure rate
- Backup duration
- Backup size
- Verification success rate

### Alerts
- Backup failure (within 5 minutes)
- Verification failure (immediate)
- High restore time (> 1 hour)
- Backup size anomaly (> 50% change)

### Dashboards
- Cloud SQL backup dashboard in GCP Console
- Custom Grafana dashboard for backup metrics
- Verification history in backup bucket

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloud SQL Instance                       │
│                    (utxoiq-postgres)                         │
│                   Primary: us-central1                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Automated Backups (01:00 UTC)
                         │ Transaction Logs (PITR)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backup Storage                            │
│                   Region: us-east1                           │
│                  Retention: 7 days                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Weekly Verification (03:00 UTC)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backup Verification Function                    │
│                  (Cloud Function)                            │
│                                                              │
│  1. Get latest backup                                        │
│  2. Create test instance                                     │
│  3. Verify data integrity                                    │
│  4. Schedule cleanup                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Results
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Verification Results                        │
│              (Cloud Storage Bucket)                          │
│            gs://utxoiq-backups/verification-results/         │
└─────────────────────────────────────────────────────────────┘
```

## Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO)

| Scenario | RTO | RPO | Method |
|----------|-----|-----|--------|
| Accidental deletion | 30 min | 0 min | PITR |
| Database corruption | 1 hour | 24 hours | Full restore |
| Regional outage | 2 hours | 24 hours | DR failover |
| Complete loss | 3 hours | 24 hours | New instance |

## Security

### Access Control
- Backup operations require Cloud SQL Admin role
- Verification function uses dedicated service account
- Backup bucket has uniform bucket-level access
- Encryption at rest enabled for all backups

### Encryption
- Backups encrypted with Google-managed keys
- In-transit encryption for all backup operations
- Option to use customer-managed encryption keys (CMEK)

### Audit Logging
- All backup operations logged to Cloud Audit Logs
- Verification results stored in GCS with versioning
- Recovery operations tracked in incident management

## Cost Optimization

### Backup Storage
- Standard storage for recent backups (7 days)
- Coldline storage for archived backups (> 7 days)
- Automatic lifecycle management
- Estimated cost: $0.026/GB/month (Standard), $0.004/GB/month (Coldline)

### Verification
- Minimal instance tier for test restores (db-f1-micro)
- Automatic cleanup after 2 hours
- Weekly schedule to minimize costs
- Estimated cost: ~$5/month

## Troubleshooting

### Backup Failures

**Check backup status:**
```bash
gcloud sql operations list \
  --instance=utxoiq-postgres \
  --project=utxoiq-project \
  --filter="operationType=BACKUP_VOLUME"
```

**Common issues:**
- Insufficient storage space
- Instance not in RUNNABLE state
- Concurrent operations running
- Network connectivity issues

### Verification Failures

**Check verification logs:**
```bash
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=backup-verification" \
  --limit=50 \
  --format=json
```

**Common issues:**
- Insufficient permissions
- Backup not available
- Test instance creation failed
- Timeout during restore

### Recovery Issues

**Check restore operation:**
```bash
gcloud sql operations describe OPERATION_ID \
  --project=utxoiq-project
```

**Common issues:**
- Backup corrupted or incomplete
- Insufficient storage on target instance
- Version mismatch
- Network connectivity

## Maintenance

### Weekly Tasks
- Review verification results
- Check backup success rate
- Monitor storage usage
- Update documentation if needed

### Monthly Tasks
- Test PITR procedure
- Review and update recovery procedures
- Verify access credentials
- Test alerting mechanisms

### Quarterly Tasks
- Full restore test
- Disaster recovery drill
- Review RTO/RPO targets
- Team training

## Support

### Internal Contacts
- **Database Admin**: [Contact info]
- **On-Call Engineer**: PagerDuty rotation
- **DevOps Team**: #devops-utxoiq

### External Support
- **GCP Support**: [Support case link]
- **GCP Premium Support**: [Phone number]

### Documentation
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Backup and Recovery Guide](https://cloud.google.com/sql/docs/postgres/backup-recovery)
- [PITR Documentation](https://cloud.google.com/sql/docs/postgres/backup-recovery/pitr)

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial backup and recovery implementation | Database Team |

## License

Internal use only - utxoIQ Platform
