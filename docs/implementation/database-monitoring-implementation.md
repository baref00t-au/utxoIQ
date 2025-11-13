# Database Monitoring Implementation

## Overview

This document describes the implementation of database monitoring for task 7.1 of the database-persistence spec. The monitoring system tracks connection pool metrics, query performance, and Cloud SQL resource utilization.

## Implementation Summary

### Components Created

1. **Database Monitor Service** (`services/web-api/src/monitoring/database_monitor.py`)
   - Tracks connection pool metrics (size, active, idle, overflow)
   - Monitors query execution time with 200ms slow query threshold
   - Publishes custom metrics to Cloud Monitoring
   - Provides real-time metrics via API endpoints

2. **Monitoring API Endpoints** (`services/web-api/src/routes/monitoring.py`)
   - `GET /api/v1/monitoring/database/pool` - Connection pool metrics
   - `GET /api/v1/monitoring/database/queries` - Query performance metrics
   - `POST /api/v1/monitoring/database/publish-metrics` - Publish to Cloud Monitoring

3. **Cloud Monitoring Dashboard** (`infrastructure/monitoring/database-dashboard.json`)
   - Connection pool size and utilization
   - Active vs idle connections
   - Average query latency with 200ms threshold
   - Slow query percentage
   - Cloud SQL CPU and memory utilization
   - Query rate (total and slow queries)

4. **Alert Policies** (`infrastructure/monitoring/alert-policies.yaml`)
   - High query latency (>200ms for 5 minutes)
   - High slow query rate (>5% for 5 minutes)
   - Connection pool near capacity (>90% for 3 minutes)
   - Cloud SQL high CPU (>80% for 5 minutes)
   - Cloud SQL high memory (>80% for 5 minutes)

5. **Infrastructure as Code** (`infrastructure/monitoring/terraform/main.tf`)
   - Terraform configuration for alert policies
   - Notification channel setup
   - Alert documentation and runbooks

6. **Scheduled Metric Publishing** (`infrastructure/monitoring/cloud-scheduler.yaml`)
   - Cloud Scheduler job to publish metrics every minute
   - Setup script for easy deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │ Database       │         │ Database Monitor │           │
│  │ Connection     │◄────────│ Service          │           │
│  │ Pool           │         │                  │           │
│  └────────────────┘         └──────────────────┘           │
│         │                            │                      │
│         │                            │                      │
│         ▼                            ▼                      │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │ Query          │         │ Metrics API      │           │
│  │ Execution      │────────►│ Endpoints        │           │
│  └────────────────┘         └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                                       │
                                       │ Publish Metrics
                                       ▼
                        ┌──────────────────────────┐
                        │ Google Cloud Monitoring  │
                        │                          │
                        │  • Custom Metrics        │
                        │  • Dashboards            │
                        │  • Alert Policies        │
                        └──────────────────────────┘
                                       │
                                       │ Alerts
                                       ▼
                        ┌──────────────────────────┐
                        │ Notification Channels    │
                        │  • Email                 │
                        │  • Slack                 │
                        │  • PagerDuty             │
                        └──────────────────────────┘
```

## Key Features

### 1. Connection Pool Monitoring

The monitor tracks SQLAlchemy connection pool events:
- **connect**: New connection established
- **checkout**: Connection borrowed from pool
- **checkin**: Connection returned to pool

Metrics published:
- `connection_pool_size`: Total pool size
- `connection_pool_checked_in`: Available connections
- `connection_pool_checked_out`: Active connections
- `connection_pool_overflow`: Overflow connections
- `connection_pool_total`: Total connections (size + overflow)

### 2. Query Performance Tracking

The monitor provides a context manager for tracking query execution:

```python
from src.monitoring.database_monitor import get_database_monitor

monitor = get_database_monitor()

async with monitor.track_query("get_backfill_jobs") as query_metadata:
    result = await db.execute(query)
    # Query metadata automatically updated with duration
```

Features:
- Automatic slow query detection (>200ms)
- Query count and timing statistics
- Slow query percentage calculation
- Warning logs for slow queries

Metrics published:
- `query_count`: Total queries executed
- `slow_query_count`: Queries exceeding 200ms
- `slow_query_percentage`: Percentage of slow queries
- `average_query_time_ms`: Average query execution time

### 3. Cloud SQL Monitoring

The dashboard includes native Cloud SQL metrics:
- CPU utilization
- Memory utilization
- Disk I/O
- Network throughput
- Connection count

### 4. Alert Policies

All alert policies include:
- Clear trigger conditions
- Appropriate duration to reduce false positives
- Auto-close configuration
- Detailed documentation with investigation steps
- Resolution guidance

## Deployment

### Prerequisites

1. Google Cloud project with Cloud Monitoring API enabled
2. Cloud SQL instance running
3. Service account with monitoring permissions
4. Notification channels configured (email, Slack, etc.)

### Step 1: Deploy Monitoring Infrastructure

Using Terraform (recommended):

```bash
cd infrastructure/monitoring/terraform

terraform init

terraform apply \
  -var="project_id=utxoiq-project" \
  -var="alert_email=alerts@utxoiq.com"
```

### Step 2: Deploy Dashboard

```bash
cd infrastructure/monitoring

export GCP_PROJECT_ID=utxoiq-project
./deploy-monitoring.sh
```

### Step 3: Setup Metric Publishing

```bash
cd infrastructure/monitoring

export GCP_PROJECT_ID=utxoiq-project
export API_SERVICE_URL=https://utxoiq-api-xxxxx.run.app
./setup-scheduler.sh
```

### Step 4: Verify Setup

1. Check that metrics are being published:
```bash
gcloud monitoring metrics-descriptors list \
  --filter="metric.type:custom.googleapis.com/database"
```

2. View the dashboard:
```bash
# Get dashboard URL from Terraform output or deployment script
```

3. Test alert policies:
```bash
# Trigger a test alert by simulating high load
```

## Usage

### Accessing Metrics via API

Get connection pool metrics:
```bash
curl https://utxoiq-api-xxxxx.run.app/api/v1/monitoring/database/pool
```

Get query performance metrics:
```bash
curl https://utxoiq-api-xxxxx.run.app/api/v1/monitoring/database/queries
```

Manually publish metrics:
```bash
curl -X POST https://utxoiq-api-xxxxx.run.app/api/v1/monitoring/database/publish-metrics
```

### Tracking Queries in Code

```python
from src.monitoring.database_monitor import get_database_monitor

async def get_backfill_jobs(db: AsyncSession):
    monitor = get_database_monitor()
    
    async with monitor.track_query("list_backfill_jobs"):
        result = await db.execute(
            select(BackfillJob).order_by(BackfillJob.started_at.desc())
        )
        return result.scalars().all()
```

### Viewing Metrics in Cloud Console

1. Navigate to Cloud Monitoring > Dashboards
2. Select "utxoIQ Database Monitoring"
3. View real-time metrics and historical trends

### Responding to Alerts

When an alert fires:

1. Check the alert documentation for investigation steps
2. Review the dashboard for context
3. Check Cloud SQL Performance Insights
4. Review application logs
5. Follow resolution guidance in alert policy

## Monitoring Best Practices

### 1. Connection Pool Tuning

Monitor these metrics to optimize pool settings:
- If `checked_out` frequently equals `size`, increase `db_pool_size`
- If `overflow` is consistently high, increase `db_max_overflow`
- If connections are idle, reduce `db_pool_size`

### 2. Query Optimization

When slow query percentage is high:
- Review slow query log in Cloud SQL
- Use `EXPLAIN ANALYZE` for expensive queries
- Add indexes for frequently queried columns
- Implement query result caching
- Optimize N+1 query patterns

### 3. Alert Tuning

Adjust alert thresholds based on baseline:
- Monitor metrics for 1-2 weeks to establish baseline
- Set thresholds above normal variance
- Use appropriate durations to reduce noise
- Implement alert grouping for related issues

### 4. Dashboard Customization

Customize the dashboard for your needs:
- Add service-specific metrics
- Create separate dashboards for different services
- Add SLO/SLI tracking
- Include business metrics alongside technical metrics

## Troubleshooting

### Metrics Not Appearing

1. Verify monitoring service is initialized in `main.py`
2. Check that metrics are being published via scheduler
3. Verify service account has monitoring permissions
4. Check Cloud Monitoring API is enabled

### Alerts Not Firing

1. Verify notification channels are configured
2. Check alert policy conditions match metric names
3. Ensure metrics are being published regularly
4. Review alert policy history in Cloud Console

### High False Positive Rate

1. Increase alert duration
2. Adjust thresholds based on baseline metrics
3. Use auto-close to prevent alert fatigue
4. Implement alert grouping

## Requirements Satisfied

This implementation satisfies all requirements from task 7.1:

✅ **Create dashboard for connection pool metrics**
- Dashboard includes pool size, active/idle connections, overflow metrics
- Real-time visualization with historical trends

✅ **Add alerts for high query latency (>200ms)**
- Alert policy triggers when average query time exceeds 200ms for 5 minutes
- Includes investigation steps and resolution guidance

✅ **Monitor database CPU and memory usage**
- Dashboard includes Cloud SQL CPU and memory utilization
- Alert policies for high CPU (>80%) and memory (>80%)

✅ **Track slow query log**
- Automatic slow query detection with 200ms threshold
- Slow query count and percentage metrics
- Warning logs for slow queries
- Integration with Cloud SQL slow query log

✅ **Requirements: 6**
- Satisfies Requirement 6 for connection pool monitoring and performance tracking

## Next Steps

1. **Task 7.2**: Configure Redis cache monitoring
2. **Task 7.3**: Add application-level metrics
3. **Task 7.4**: Test monitoring and alerts

## References

- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Cloud SQL Monitoring](https://cloud.google.com/sql/docs/postgres/monitoring)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Alert Policy Best Practices](https://cloud.google.com/monitoring/alerts/best-practices)
