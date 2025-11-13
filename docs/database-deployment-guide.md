# Database Deployment Guide

## Overview

This guide covers the complete deployment process for the utxoIQ database persistence layer, including Cloud SQL setup, Redis configuration, database migrations, and monitoring.

## Prerequisites

### Required Tools

```bash
# Google Cloud SDK
gcloud --version  # Should be 400.0.0+

# PostgreSQL client
psql --version  # Should be 14.0+

# Python
python --version  # Should be 3.12.x

# Alembic (for migrations)
pip install alembic sqlalchemy asyncpg
```

### Required Permissions

- Cloud SQL Admin
- Cloud Storage Admin
- Secret Manager Admin
- Cloud Scheduler Admin
- Cloud Monitoring Editor

### Environment Variables

```bash
export GCP_PROJECT_ID="utxoiq-project"
export GCP_REGION="us-central1"
export GCP_BACKUP_REGION="us-east1"
export DATABASE_NAME="utxoiq"
export DATABASE_USER="utxoiq-app"
```

---

## Phase 1: Cloud SQL Setup

### 1.1 Create Cloud SQL Instance

```bash
# Create PostgreSQL instance with high availability
gcloud sql instances create utxoiq-postgres \
  --database-version=POSTGRES_14 \
  --tier=db-custom-2-7680 \
  --region=$GCP_REGION \
  --availability-type=REGIONAL \
  --storage-type=SSD \
  --storage-size=100GB \
  --storage-auto-increase \
  --storage-auto-increase-limit=500 \
  --backup \
  --backup-start-time=01:00 \
  --backup-location=$GCP_BACKUP_REGION \
  --retained-backups-count=7 \
  --enable-point-in-time-recovery \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=2 \
  --maintenance-release-channel=production \
  --project=$GCP_PROJECT_ID

# Wait for instance to be ready
gcloud sql operations wait \
  $(gcloud sql operations list --instance=utxoiq-postgres --limit=1 --format="value(name)") \
  --project=$GCP_PROJECT_ID
```

### 1.2 Configure Instance Settings

```bash
# Set database flags for performance
gcloud sql instances patch utxoiq-postgres \
  --database-flags=\
max_connections=100,\
shared_buffers=2GB,\
effective_cache_size=6GB,\
maintenance_work_mem=512MB,\
checkpoint_completion_target=0.9,\
wal_buffers=16MB,\
default_statistics_target=100,\
random_page_cost=1.1,\
effective_io_concurrency=200,\
work_mem=10MB,\
min_wal_size=1GB,\
max_wal_size=4GB \
  --project=$GCP_PROJECT_ID
```

### 1.3 Create Database and User

```bash
# Create database
gcloud sql databases create $DATABASE_NAME \
  --instance=utxoiq-postgres \
  --project=$GCP_PROJECT_ID

# Create application user
gcloud sql users create $DATABASE_USER \
  --instance=utxoiq-postgres \
  --password=$(openssl rand -base64 32) \
  --project=$GCP_PROJECT_ID

# Store password in Secret Manager
echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create database-password \
  --data-file=- \
  --replication-policy=automatic \
  --project=$GCP_PROJECT_ID
```

### 1.4 Configure Private IP (Recommended)

```bash
# Enable Private IP for secure access
gcloud sql instances patch utxoiq-postgres \
  --network=projects/$GCP_PROJECT_ID/global/networks/default \
  --no-assign-ip \
  --project=$GCP_PROJECT_ID
```

### 1.5 Get Connection Details

```bash
# Get connection name
gcloud sql instances describe utxoiq-postgres \
  --format="value(connectionName)" \
  --project=$GCP_PROJECT_ID

# Connection string format:
# postgresql+asyncpg://user:password@/database?host=/cloudsql/PROJECT:REGION:INSTANCE
```

---

## Phase 2: Redis Setup

### 2.1 Create Redis Instance

```bash
# Create Memorystore Redis instance
gcloud redis instances create utxoiq-cache \
  --size=5 \
  --region=$GCP_REGION \
  --redis-version=redis_7_0 \
  --tier=standard \
  --network=default \
  --connect-mode=PRIVATE_SERVICE_ACCESS \
  --project=$GCP_PROJECT_ID

# Wait for instance to be ready
gcloud redis operations wait \
  $(gcloud redis operations list --region=$GCP_REGION --limit=1 --format="value(name)") \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID
```

### 2.2 Get Redis Connection Details

```bash
# Get Redis host and port
gcloud redis instances describe utxoiq-cache \
  --region=$GCP_REGION \
  --format="value(host,port)" \
  --project=$GCP_PROJECT_ID

# Connection string format:
# redis://host:port/0
```

---

## Phase 3: Database Migrations

### 3.1 Setup Alembic

```bash
cd services/web-api

# Initialize Alembic (if not already done)
alembic init infrastructure/postgres/migrations

# Configure alembic.ini
cat > infrastructure/postgres/migrations/alembic.ini << EOF
[alembic]
script_location = infrastructure/postgres/migrations
sqlalchemy.url = postgresql+asyncpg://user:password@/database?host=/cloudsql/PROJECT:REGION:INSTANCE

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
```

### 3.2 Create Migration Scripts

```bash
# Create initial schema migration
alembic revision -m "create_initial_schema"

# Edit the generated migration file to include:
# - backfill_jobs table
# - insight_feedback table
# - system_metrics table
# - All indexes and constraints
```

### 3.3 Run Migrations

```bash
# Connect via Cloud SQL Proxy
cloud_sql_proxy -instances=$GCP_PROJECT_ID:$GCP_REGION:utxoiq-postgres=tcp:5432 &

# Run migrations
alembic upgrade head

# Verify tables created
psql "postgresql://user:password@localhost:5432/utxoiq" \
  -c "\dt"

# Stop proxy
pkill cloud_sql_proxy
```

---

## Phase 4: Application Configuration

### 4.1 Update Environment Variables

```bash
# Create .env file for web-api service
cat > services/web-api/.env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://$DATABASE_USER:PASSWORD@/utxoiq?host=/cloudsql/$GCP_PROJECT_ID:$GCP_REGION:utxoiq-postgres
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis
REDIS_URL=redis://REDIS_HOST:6379/0
REDIS_MAX_CONNECTIONS=50

# GCP
GCP_PROJECT_ID=$GCP_PROJECT_ID

# Retention
METRICS_RETENTION_DAYS=90
FEEDBACK_RETENTION_DAYS=730
BACKFILL_RETENTION_DAYS=180
EOF
```

### 4.2 Update Cloud Run Service

```bash
# Build and deploy web-api with database support
cd services/web-api

# Build container
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/web-api:latest

# Deploy to Cloud Run with Cloud SQL connection
gcloud run deploy web-api \
  --image gcr.io/$GCP_PROJECT_ID/web-api:latest \
  --platform managed \
  --region $GCP_REGION \
  --add-cloudsql-instances $GCP_PROJECT_ID:$GCP_REGION:utxoiq-postgres \
  --set-env-vars DATABASE_URL="postgresql+asyncpg://$DATABASE_USER:PASSWORD@/utxoiq?host=/cloudsql/$GCP_PROJECT_ID:$GCP_REGION:utxoiq-postgres" \
  --set-env-vars REDIS_URL="redis://REDIS_HOST:6379/0" \
  --set-secrets DATABASE_PASSWORD=database-password:latest \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 300 \
  --allow-unauthenticated \
  --project $GCP_PROJECT_ID
```

---

## Phase 5: Backup Configuration

### 5.1 Verify Automated Backups

```bash
# Check backup configuration
gcloud sql instances describe utxoiq-postgres \
  --format="value(settings.backupConfiguration)" \
  --project=$GCP_PROJECT_ID

# List existing backups
gcloud sql backups list \
  --instance=utxoiq-postgres \
  --project=$GCP_PROJECT_ID
```

### 5.2 Setup Backup Verification

```bash
# Deploy backup verification Cloud Function
cd infrastructure/postgres

# Deploy function
gcloud functions deploy backup-verification \
  --runtime python39 \
  --trigger-http \
  --entry-point verify_backup \
  --source . \
  --region $GCP_REGION \
  --memory 256MB \
  --timeout 540s \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID \
  --set-env-vars INSTANCE_NAME=utxoiq-postgres \
  --project $GCP_PROJECT_ID

# Create Cloud Scheduler job for weekly verification
gcloud scheduler jobs create http backup-verification-weekly \
  --schedule="0 3 * * 0" \
  --uri="https://$GCP_REGION-$GCP_PROJECT_ID.cloudfunctions.net/backup-verification" \
  --http-method=POST \
  --time-zone="UTC" \
  --location=$GCP_REGION \
  --project=$GCP_PROJECT_ID
```

### 5.3 Create Backup Storage Bucket

```bash
# Create bucket for archived data
gsutil mb -p $GCP_PROJECT_ID -c STANDARD -l $GCP_BACKUP_REGION gs://utxoiq-backups

# Set lifecycle policy for cost optimization
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 30}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://utxoiq-backups
```

---

## Phase 6: Data Retention Setup

### 6.1 Deploy Retention Service

The retention service is already part of the web-api service. Configure Cloud Scheduler to trigger it:

```bash
# Create Cloud Scheduler job for daily retention
gcloud scheduler jobs create http retention-daily \
  --schedule="0 2 * * *" \
  --uri="https://web-api-HASH-uc.a.run.app/api/v1/monitoring/retention/run" \
  --http-method=POST \
  --time-zone="UTC" \
  --location=$GCP_REGION \
  --oidc-service-account-email=cloud-scheduler@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience="https://web-api-HASH-uc.a.run.app" \
  --project=$GCP_PROJECT_ID
```

### 6.2 Grant Permissions

```bash
# Grant Cloud Scheduler permission to invoke Cloud Run
gcloud run services add-iam-policy-binding web-api \
  --member="serviceAccount:cloud-scheduler@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID

# Grant web-api service account access to Cloud Storage
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:web-api@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

---

## Phase 7: Monitoring Setup

### 7.1 Create Monitoring Dashboard

```bash
# Create custom dashboard for database metrics
gcloud monitoring dashboards create --config-from-file=infrastructure/monitoring/database-dashboard.json
```

### 7.2 Configure Alerts

```bash
# Deploy alert policies
gcloud alpha monitoring policies create --policy-from-file=infrastructure/monitoring/alert-policies.yaml
```

### 7.3 Setup Metric Publishing

```bash
# Create Cloud Scheduler job for metric publishing
gcloud scheduler jobs create http database-metrics-publisher \
  --schedule="* * * * *" \
  --uri="https://web-api-HASH-uc.a.run.app/api/v1/monitoring/database/publish-metrics" \
  --http-method=POST \
  --time-zone="UTC" \
  --location=$GCP_REGION \
  --oidc-service-account-email=cloud-scheduler@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --oidc-token-audience="https://web-api-HASH-uc.a.run.app" \
  --project=$GCP_PROJECT_ID
```

---

## Phase 8: Testing

### 8.1 Database Connection Test

```bash
# Test database connection
curl https://web-api-HASH-uc.a.run.app/api/v1/monitoring/database/pool

# Expected response:
# {
#   "status": "success",
#   "metrics": {
#     "size": 10,
#     "checked_in": 10,
#     "checked_out": 0,
#     "overflow": 0,
#     "total_connections": 10
#   }
# }
```

### 8.2 Create Test Backfill Job

```bash
# Start a test backfill job
curl -X POST https://web-api-HASH-uc.a.run.app/api/v1/monitoring/backfill/start \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "test",
    "start_block": 1,
    "end_block": 100,
    "created_by": "deployment-test"
  }'

# Verify job created
curl "https://web-api-HASH-uc.a.run.app/api/v1/monitoring/backfill/status?status=running"
```

### 8.3 Test Feedback System

```bash
# Submit test feedback
curl -X POST https://web-api-HASH-uc.a.run.app/api/v1/feedback/rate \
  -H "Content-Type: application/json" \
  -d '{
    "insight_id": "test-insight-001",
    "rating": 5,
    "user_id": "test-user"
  }'

# Get feedback stats
curl "https://web-api-HASH-uc.a.run.app/api/v1/feedback/stats?insight_id=test-insight-001"
```

### 8.4 Test Metrics Recording

```bash
# Record test metric
curl -X POST https://web-api-HASH-uc.a.run.app/api/v1/monitoring/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "test-service",
    "metric_type": "test",
    "metric_value": 42.0,
    "unit": "count"
  }'

# Query metrics
curl "https://web-api-HASH-uc.a.run.app/api/v1/monitoring/metrics?\
service_name=test-service&\
metric_type=test&\
start_time=2024-01-01T00:00:00Z&\
end_time=2024-12-31T23:59:59Z"
```

### 8.5 Run Integration Tests

```bash
cd services/web-api
pytest tests/integration/test_database_api.py -v
```

---

## Phase 9: Production Checklist

### Pre-Deployment

- [ ] Cloud SQL instance created and configured
- [ ] Redis instance created and accessible
- [ ] Database migrations applied successfully
- [ ] Backup configuration verified
- [ ] Backup verification function deployed
- [ ] Retention policies configured
- [ ] Monitoring dashboard created
- [ ] Alert policies configured
- [ ] Cloud Scheduler jobs created
- [ ] IAM permissions granted
- [ ] Integration tests passing

### Post-Deployment

- [ ] Database connection pool metrics normal
- [ ] Query performance within SLA (<200ms p95)
- [ ] Cache hit rate >90%
- [ ] Backups completing successfully
- [ ] Backup verification passing
- [ ] Retention jobs running
- [ ] Metrics publishing to Cloud Monitoring
- [ ] Alerts configured and tested
- [ ] Documentation updated
- [ ] Team trained on operations

---

## Rollback Procedures

### Rollback Application

```bash
# Rollback to previous Cloud Run revision
gcloud run services update-traffic web-api \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID
```

### Rollback Database Migration

```bash
# Connect via Cloud SQL Proxy
cloud_sql_proxy -instances=$GCP_PROJECT_ID:$GCP_REGION:utxoiq-postgres=tcp:5432 &

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Stop proxy
pkill cloud_sql_proxy
```

### Restore from Backup

```bash
# List available backups
gcloud sql backups list \
  --instance=utxoiq-postgres \
  --project=$GCP_PROJECT_ID

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=utxoiq-postgres \
  --project=$GCP_PROJECT_ID
```

---

## Troubleshooting

### Connection Issues

```bash
# Check Cloud SQL instance status
gcloud sql instances describe utxoiq-postgres \
  --project=$GCP_PROJECT_ID

# Check Cloud Run service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=web-api" \
  --limit=50 \
  --format=json

# Test connection from Cloud Shell
gcloud sql connect utxoiq-postgres --user=$DATABASE_USER --database=$DATABASE_NAME
```

### Performance Issues

```bash
# Check slow queries
psql "postgresql://user:password@localhost:5432/utxoiq" << EOF
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
EOF

# Check connection pool metrics
curl https://web-api-HASH-uc.a.run.app/api/v1/monitoring/database/pool

# Check query metrics
curl https://web-api-HASH-uc.a.run.app/api/v1/monitoring/database/queries
```

### Backup Issues

```bash
# Check backup status
gcloud sql operations list \
  --instance=utxoiq-postgres \
  --filter="operationType=BACKUP_VOLUME" \
  --project=$GCP_PROJECT_ID

# Manually trigger backup
gcloud sql backups create \
  --instance=utxoiq-postgres \
  --project=$GCP_PROJECT_ID
```

---

## Maintenance

### Weekly Tasks

- Review backup verification results
- Check database performance metrics
- Monitor storage usage
- Review slow query log

### Monthly Tasks

- Test backup restore procedure
- Review and update retention policies
- Optimize database indexes
- Update documentation

### Quarterly Tasks

- Disaster recovery drill
- Review and update alert thresholds
- Capacity planning review
- Security audit

---

## Cost Optimization

### Database

```bash
# Monitor database costs
gcloud billing accounts list
gcloud billing projects describe $GCP_PROJECT_ID

# Optimize storage
# - Enable automatic storage increase
# - Use lifecycle policies for backups
# - Archive old data to Cloud Storage
```

### Redis

```bash
# Monitor Redis memory usage
gcloud redis instances describe utxoiq-cache \
  --region=$GCP_REGION \
  --format="value(memorySizeGb,currentLocationId)"

# Optimize cache usage
# - Implement proper TTL values
# - Monitor eviction rate
# - Adjust memory size if needed
```

---

## Support

### Internal Contacts

- **Database Admin**: [Contact info]
- **DevOps Team**: #devops-utxoiq
- **On-Call Engineer**: PagerDuty rotation

### External Support

- **GCP Support**: [Support case link]
- **Cloud SQL Documentation**: https://cloud.google.com/sql/docs
- **Redis Documentation**: https://cloud.google.com/memorystore/docs/redis

---

## Appendix

### A. Connection String Formats

```bash
# Cloud SQL with Unix socket (Cloud Run)
postgresql+asyncpg://user:password@/database?host=/cloudsql/PROJECT:REGION:INSTANCE

# Cloud SQL with TCP (local development via proxy)
postgresql+asyncpg://user:password@localhost:5432/database

# Redis
redis://host:port/0
```

### B. Useful Commands

```bash
# List all Cloud SQL instances
gcloud sql instances list --project=$GCP_PROJECT_ID

# Get Cloud SQL connection name
gcloud sql instances describe utxoiq-postgres \
  --format="value(connectionName)" \
  --project=$GCP_PROJECT_ID

# List Redis instances
gcloud redis instances list --region=$GCP_REGION --project=$GCP_PROJECT_ID

# Check Cloud Run service status
gcloud run services describe web-api \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID

# View Cloud Scheduler jobs
gcloud scheduler jobs list --location=$GCP_REGION --project=$GCP_PROJECT_ID
```

### C. Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `DB_POOL_SIZE` | Minimum connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Additional connections under load | `20` |
| `DB_POOL_TIMEOUT` | Connection wait timeout (seconds) | `30` |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | `3600` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `REDIS_MAX_CONNECTIONS` | Maximum Redis connections | `50` |
| `GCP_PROJECT_ID` | GCP project identifier | `utxoiq-project` |
| `METRICS_RETENTION_DAYS` | Metrics retention period | `90` |
| `FEEDBACK_RETENTION_DAYS` | Feedback retention period | `730` |
| `BACKFILL_RETENTION_DAYS` | Backfill job retention period | `180` |
