# Disaster Recovery Checklist

## Quick Reference Guide

This checklist provides a quick reference for disaster recovery procedures. For detailed steps, refer to [RECOVERY_RUNBOOK.md](./RECOVERY_RUNBOOK.md).

## Pre-Incident Preparation

### Daily
- [ ] Verify automated backups completed successfully
- [ ] Check backup retention (7 daily backups present)
- [ ] Monitor database health metrics
- [ ] Review error logs for anomalies

### Weekly
- [ ] Run automated backup verification
- [ ] Review verification results
- [ ] Test database connectivity
- [ ] Update recovery documentation if needed

### Monthly
- [ ] Perform PITR test recovery
- [ ] Review and update contact list
- [ ] Verify access credentials are current
- [ ] Test alerting mechanisms

### Quarterly
- [ ] Full restore test to temporary instance
- [ ] Disaster recovery drill
- [ ] Review and update RTO/RPO targets
- [ ] Team training on recovery procedures

## Incident Response

### Phase 1: Detection and Assessment (0-15 minutes)

- [ ] Incident detected and logged
- [ ] Severity level determined
- [ ] On-call engineer notified
- [ ] Incident channel created (#incident-YYYYMMDD-HHMM)
- [ ] Initial assessment completed

**Assessment Questions:**
- What is the nature of the incident?
- Is the database accessible?
- Are backups available?
- What is the estimated data loss?
- What is the impact on users?

### Phase 2: Immediate Response (15-30 minutes)

- [ ] Incident commander assigned
- [ ] Stakeholders notified
- [ ] Status page updated
- [ ] Recovery strategy selected
- [ ] Pre-recovery backup created (if possible)
- [ ] Application traffic stopped

**Decision Matrix:**

| Incident Type | Recovery Method | Expected RTO |
|--------------|-----------------|--------------|
| Accidental deletion | PITR | 30 min |
| Corruption | Full restore | 1 hour |
| Regional outage | DR failover | 2 hours |
| Complete loss | New instance | 3 hours |

### Phase 3: Recovery Execution (30 minutes - 3 hours)

#### For Full Restore:
- [ ] Latest backup identified
- [ ] Restore operation initiated
- [ ] Restore progress monitored
- [ ] Restore completion verified
- [ ] Data integrity checks passed

#### For PITR:
- [ ] Target timestamp identified
- [ ] Clone instance created
- [ ] Data verified in clone
- [ ] Data restored to production
- [ ] Clone instance cleaned up

#### For DR Failover:
- [ ] Secondary region instance created
- [ ] Application configuration updated
- [ ] DNS/routing updated
- [ ] Services restarted
- [ ] Connectivity verified

### Phase 4: Verification (Concurrent with Recovery)

- [ ] Database is accessible
- [ ] Row counts verified
- [ ] Critical queries tested
- [ ] Application endpoints tested
- [ ] No data corruption detected
- [ ] Performance metrics normal

**Verification Commands:**
```bash
# Quick health check
gcloud sql instances describe utxoiq-postgres

# Row count verification
psql -c "SELECT COUNT(*) FROM backfill_jobs;"
psql -c "SELECT COUNT(*) FROM insight_feedback;"
psql -c "SELECT COUNT(*) FROM system_metrics;"

# API health check
curl https://utxoiq-api.run.app/health
```

### Phase 5: Service Restoration (After verification)

- [ ] Application traffic restored
- [ ] Services scaled to normal levels
- [ ] Monitoring dashboards checked
- [ ] Error rates within normal range
- [ ] User-facing services operational
- [ ] Status page updated (resolved)

### Phase 6: Post-Recovery (1-24 hours)

- [ ] Full data integrity audit completed
- [ ] All services confirmed healthy
- [ ] Backup schedule resumed
- [ ] Recovery timeline documented
- [ ] Incident report drafted
- [ ] Stakeholders notified of resolution

### Phase 7: Post-Mortem (1-7 days)

- [ ] Post-mortem meeting scheduled
- [ ] Root cause analysis completed
- [ ] Timeline documented
- [ ] Action items identified
- [ ] Preventive measures planned
- [ ] Documentation updated
- [ ] Team debriefing conducted

## Emergency Contacts

### Primary Contacts
- **Incident Commander**: [Name] - [Phone] - [Email]
- **Database Admin**: [Name] - [Phone] - [Email]
- **On-Call Engineer**: PagerDuty rotation
- **Engineering Manager**: [Name] - [Phone] - [Email]

### Escalation Path
1. On-Call Engineer (0-15 min)
2. Database Admin (15-30 min)
3. Engineering Manager (30-60 min)
4. CTO (60+ min or critical incidents)

### External Support
- **GCP Support**: [Support case link]
- **GCP Premium Support**: [Phone number]
- **Database Consultant**: [Contact info]

## Communication Templates

### Initial Notification
```
INCIDENT: Database Recovery in Progress
Severity: [P1/P2/P3]
Impact: [Description]
Status: [Investigating/Recovering/Resolved]
ETA: [Estimated time]
Updates: Every 30 minutes in #incident-YYYYMMDD-HHMM
```

### Status Update
```
UPDATE: Database Recovery Progress
Time: [HH:MM UTC]
Status: [Current phase]
Progress: [Percentage or milestone]
Next Steps: [What's happening next]
ETA: [Updated estimate]
```

### Resolution Notice
```
RESOLVED: Database Recovery Complete
Duration: [Total time]
Impact: [Summary]
Data Loss: [None/Minimal/Estimated]
Next Steps: [Monitoring/Post-mortem]
Post-Mortem: [Date and time]
```

## Critical Information

### Instance Details
- **Project ID**: utxoiq-project
- **Instance Name**: utxoiq-postgres
- **Primary Region**: us-central1
- **Backup Region**: us-east1
- **Backup Bucket**: gs://utxoiq-backups

### Connection Information
```bash
# Cloud SQL Proxy
cloud_sql_proxy -instances=utxoiq-project:us-central1:utxoiq-postgres=tcp:5432

# Direct connection (from authorized network)
psql "host=INSTANCE_IP dbname=utxoiq user=postgres sslmode=require"

# gcloud connection
gcloud sql connect utxoiq-postgres --user=postgres --project=utxoiq-project
```

### Quick Commands

```bash
# List backups
gcloud sql backups list --instance=utxoiq-postgres --project=utxoiq-project

# Create on-demand backup
gcloud sql backups create --instance=utxoiq-postgres --project=utxoiq-project

# Restore from backup
gcloud sql backups restore BACKUP_ID --backup-instance=utxoiq-postgres --project=utxoiq-project

# Stop application traffic
gcloud run services update utxoiq-api --min-instances=0 --max-instances=0

# Restore application traffic
gcloud run services update utxoiq-api --min-instances=1 --max-instances=10

# Check instance status
gcloud sql instances describe utxoiq-postgres --project=utxoiq-project

# Monitor operations
gcloud sql operations list --instance=utxoiq-postgres --project=utxoiq-project
```

## Recovery Metrics

### Target Metrics
- **RTO (Recovery Time Objective)**: 2 hours
- **RPO (Recovery Point Objective)**: 24 hours
- **Backup Success Rate**: 99.9%
- **Verification Success Rate**: 100%

### Actual Metrics (Track per incident)
- Incident detection time: _____ minutes
- Recovery initiation time: _____ minutes
- Recovery completion time: _____ minutes
- Total downtime: _____ minutes
- Data loss: _____ hours/minutes
- Services affected: _____

## Lessons Learned Template

### Incident Summary
- **Date**: 
- **Duration**: 
- **Severity**: 
- **Root Cause**: 

### What Went Well
1. 
2. 
3. 

### What Could Be Improved
1. 
2. 
3. 

### Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
|        |       |          |        |

## Testing Log

| Date | Test Type | Result | Duration | Notes |
|------|-----------|--------|----------|-------|
|      |           |        |          |       |

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-01-15 | 1.0 | Initial checklist | Database Team |

---

**Remember**: Stay calm, follow the procedures, communicate clearly, and document everything.
