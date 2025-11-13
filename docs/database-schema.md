# Database Schema Documentation

## Overview

The utxoIQ platform uses Cloud SQL (PostgreSQL) for persistent storage of operational data. This document describes the database schema, relationships, and design decisions.

## Database Configuration

### Connection Details
- **Database**: PostgreSQL 14+
- **Service**: Google Cloud SQL
- **Instance**: `utxoiq-postgres`
- **Region**: us-central1 (primary), us-east1 (backup)
- **High Availability**: Regional instance with automatic failover

### Connection Pool Settings
```python
pool_size=10              # Minimum connections
max_overflow=20           # Additional connections under load
pool_timeout=30           # Wait time for connection (seconds)
pool_recycle=3600         # Recycle connections after 1 hour
pool_pre_ping=True        # Verify connections before use
```

## Tables

### 1. backfill_jobs

Tracks blockchain data backfill operations for historical data ingestion.

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique job identifier |
| `job_type` | VARCHAR(50) | NOT NULL | Type of backfill ('blocks', 'transactions', etc.) |
| `start_block` | INTEGER | NOT NULL | Starting block height |
| `end_block` | INTEGER | NOT NULL | Ending block height |
| `current_block` | INTEGER | NOT NULL | Current progress block height |
| `status` | VARCHAR(20) | NOT NULL | Job status ('running', 'completed', 'failed', 'paused') |
| `progress_percentage` | FLOAT | DEFAULT 0.0 | Progress as percentage (0-100) |
| `estimated_completion` | TIMESTAMP | NULL | Estimated completion time |
| `error_message` | TEXT | NULL | Error details if failed |
| `started_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Job start timestamp |
| `completed_at` | TIMESTAMP | NULL | Job completion timestamp |
| `created_by` | VARCHAR(100) | NULL | User or service that created the job |

#### Indexes

```sql
CREATE INDEX idx_backfill_status ON backfill_jobs(status);
CREATE INDEX idx_backfill_started ON backfill_jobs(started_at);
CREATE INDEX idx_backfill_job_type ON backfill_jobs(job_type);
```

#### Relationships
- No foreign key relationships
- Self-contained job tracking

#### Usage Patterns
- **Write**: Create job on start, update progress every N blocks
- **Read**: Query active jobs, retrieve job history
- **Retention**: Archive jobs older than 180 days

#### Example Queries

```sql
-- Get all running backfill jobs
SELECT * FROM backfill_jobs 
WHERE status = 'running' 
ORDER BY started_at DESC;

-- Get job progress
SELECT 
    id,
    job_type,
    progress_percentage,
    current_block,
    end_block,
    estimated_completion
FROM backfill_jobs 
WHERE id = 'job-uuid-here';

-- Get failed jobs in last 24 hours
SELECT * FROM backfill_jobs 
WHERE status = 'failed' 
  AND started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;
```

---

### 2. insight_feedback

Stores user feedback on AI-generated insights including ratings, comments, and flags.

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique feedback identifier |
| `insight_id` | VARCHAR(100) | NOT NULL | Insight identifier (from BigQuery) |
| `user_id` | VARCHAR(100) | NOT NULL | User identifier (from Firebase Auth) |
| `rating` | INTEGER | NULL, CHECK (1-5) | Star rating (1-5) |
| `comment` | TEXT | NULL | User comment text |
| `flag_type` | VARCHAR(50) | NULL | Flag type ('inaccurate', 'misleading', 'spam') |
| `flag_reason` | TEXT | NULL | Detailed flag reason |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Feedback creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### Indexes

```sql
CREATE INDEX idx_feedback_insight ON insight_feedback(insight_id);
CREATE INDEX idx_feedback_user ON insight_feedback(user_id);
CREATE INDEX idx_feedback_created ON insight_feedback(created_at);
```

#### Constraints

```sql
-- Ensure one feedback per user-insight combination
ALTER TABLE insight_feedback 
ADD CONSTRAINT uq_insight_user_feedback 
UNIQUE (insight_id, user_id);

-- Validate rating range
ALTER TABLE insight_feedback 
ADD CONSTRAINT chk_rating_range 
CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));
```

#### Relationships
- **insight_id**: References insights in BigQuery (soft reference)
- **user_id**: References users in Firebase Auth (soft reference)

#### Usage Patterns
- **Write**: Upsert on user-insight combination
- **Read**: Aggregate stats per insight, query user history
- **Retention**: Archive feedback older than 2 years

#### Example Queries

```sql
-- Get feedback statistics for an insight
SELECT 
    insight_id,
    COUNT(*) FILTER (WHERE rating IS NOT NULL) as total_ratings,
    AVG(rating) as average_rating,
    COUNT(*) FILTER (WHERE comment IS NOT NULL) as total_comments,
    COUNT(*) FILTER (WHERE flag_type IS NOT NULL) as total_flags
FROM insight_feedback 
WHERE insight_id = 'insight-123'
GROUP BY insight_id;

-- Get rating distribution
SELECT 
    rating,
    COUNT(*) as count
FROM insight_feedback 
WHERE insight_id = 'insight-123' 
  AND rating IS NOT NULL
GROUP BY rating
ORDER BY rating;

-- Get recent comments
SELECT 
    user_id,
    comment,
    created_at
FROM insight_feedback 
WHERE insight_id = 'insight-123' 
  AND comment IS NOT NULL
ORDER BY created_at DESC
LIMIT 20;

-- Get flagged insights
SELECT 
    insight_id,
    COUNT(*) as flag_count,
    ARRAY_AGG(DISTINCT flag_type) as flag_types
FROM insight_feedback 
WHERE flag_type IS NOT NULL
GROUP BY insight_id
HAVING COUNT(*) >= 3
ORDER BY flag_count DESC;
```

---

### 3. system_metrics

Time-series data for system monitoring and observability.

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique metric identifier |
| `service_name` | VARCHAR(100) | NOT NULL | Service name ('web-api', 'feature-engine', etc.) |
| `metric_type` | VARCHAR(50) | NOT NULL | Metric type ('cpu', 'memory', 'latency', etc.) |
| `metric_value` | FLOAT | NOT NULL | Metric value |
| `unit` | VARCHAR(20) | NOT NULL | Unit of measurement ('percent', 'ms', 'bytes') |
| `timestamp` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Metric timestamp |
| `metric_metadata` | JSONB | NULL | Additional metadata as JSON |

#### Indexes

```sql
CREATE INDEX idx_metrics_service_time ON system_metrics(service_name, timestamp);
CREATE INDEX idx_metrics_type_time ON system_metrics(metric_type, timestamp);
CREATE INDEX idx_metrics_timestamp ON system_metrics(timestamp);
```

#### Partitioning

```sql
-- Partition by month for efficient time-series queries
CREATE TABLE system_metrics (
    -- columns as above
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE system_metrics_2024_01 
PARTITION OF system_metrics 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Automate partition creation with pg_partman extension
```

#### Relationships
- No foreign key relationships
- Self-contained metrics storage

#### Usage Patterns
- **Write**: Batch insert every 60 seconds
- **Read**: Query recent metrics (last 24 hours), aggregate for dashboards
- **Retention**: Archive metrics older than 90 days, delete after 1 year

#### Example Queries

```sql
-- Get recent CPU metrics for a service
SELECT 
    timestamp,
    metric_value
FROM system_metrics 
WHERE service_name = 'web-api' 
  AND metric_type = 'cpu'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;

-- Aggregate metrics by hour
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value
FROM system_metrics 
WHERE service_name = 'web-api' 
  AND metric_type = 'latency'
  AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;

-- Get all metrics for a service at a point in time
SELECT 
    metric_type,
    metric_value,
    unit,
    metric_metadata
FROM system_metrics 
WHERE service_name = 'feature-engine' 
  AND timestamp BETWEEN '2024-01-15 14:00:00' AND '2024-01-15 14:05:00'
ORDER BY metric_type;

-- Find services with high CPU usage
SELECT 
    service_name,
    AVG(metric_value) as avg_cpu
FROM system_metrics 
WHERE metric_type = 'cpu' 
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY service_name
HAVING AVG(metric_value) > 80
ORDER BY avg_cpu DESC;
```

---

## Database Migrations

### Migration Tool
- **Tool**: Alembic
- **Location**: `infrastructure/postgres/migrations/`
- **Tracking**: `alembic_version` table

### Migration Files

```
infrastructure/postgres/migrations/
├── versions/
│   ├── 001_create_backfill_jobs.py
│   ├── 002_create_insight_feedback.py
│   ├── 003_create_system_metrics.py
│   └── 004_add_indexes.py
├── env.py
└── alembic.ini
```

### Running Migrations

```bash
# Apply all pending migrations
cd infrastructure/postgres
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Show migration history
alembic history

# Create new migration
alembic revision -m "description"
```

---

## Data Retention Policies

### Backfill Jobs
- **Hot Storage**: 180 days
- **Archive**: Cloud Storage (JSON format)
- **Deletion**: After successful archival
- **Schedule**: Daily at 02:00 UTC

### Insight Feedback
- **Hot Storage**: 2 years
- **Archive**: Cloud Storage before deletion
- **Deletion**: After archival
- **Schedule**: Daily at 02:00 UTC

### System Metrics
- **Hot Storage**: 90 days
- **Cold Storage**: 1 year (Cloud Storage)
- **Deletion**: After 1 year in cold storage
- **Schedule**: Daily at 02:00 UTC

### Implementation

```python
# Retention service runs daily via Cloud Scheduler
# See: services/web-api/src/services/retention_service.py

# Endpoint: POST /api/v1/monitoring/retention/run
# Triggered by: Cloud Scheduler at 02:00 UTC
```

---

## Backup and Recovery

### Automated Backups
- **Schedule**: Daily at 01:00 UTC
- **Retention**: 7 daily backups
- **Location**: us-east1 (separate region)
- **Type**: Full database backup

### Point-in-Time Recovery (PITR)
- **Enabled**: Yes
- **Retention**: 7 days of transaction logs
- **Granularity**: Any point in time within retention

### Backup Verification
- **Schedule**: Weekly on Sunday at 03:00 UTC
- **Method**: Restore to temporary instance
- **Validation**: Data integrity checks
- **Cleanup**: Automatic after 2 hours

### Recovery Procedures
See: `infrastructure/postgres/RECOVERY_RUNBOOK.md`

---

## Performance Optimization

### Indexing Strategy
- **Primary Keys**: UUID with B-tree index
- **Foreign Keys**: Indexed for join performance
- **Time Columns**: Indexed for range queries
- **Composite Indexes**: For common query patterns

### Query Optimization
- **Connection Pooling**: Reuse connections
- **Prepared Statements**: Reduce parsing overhead
- **Batch Operations**: Reduce round trips
- **Partitioning**: Improve time-series queries

### Caching Strategy
- **Redis**: Cache frequently accessed data
- **TTL**: 5 minutes for metrics, 1 hour for feedback stats
- **Invalidation**: On write operations
- **Fallback**: Direct database queries if cache unavailable

---

## Monitoring

### Database Metrics
- Connection pool utilization
- Query latency (p50, p95, p99)
- Slow query count (>200ms)
- Transaction rate
- Database CPU and memory

### Alerts
- Connection pool exhaustion (>90% utilization)
- High query latency (p95 >200ms)
- Slow query rate (>5%)
- Backup failure
- Replication lag (>60 seconds)

### Dashboards
- Cloud SQL dashboard in GCP Console
- Custom Grafana dashboard for application metrics
- Query performance dashboard

---

## Security

### Access Control
- **Application**: Service account with minimal permissions
- **Admins**: IAM-based access via Cloud SQL Proxy
- **Backups**: Separate service account for backup operations

### Encryption
- **At Rest**: Google-managed encryption keys
- **In Transit**: TLS 1.2+ for all connections
- **Backups**: Encrypted with same keys as database

### Audit Logging
- All database operations logged to Cloud Audit Logs
- Retention: 400 days
- Monitoring: Automated alerts for suspicious activity

---

## Troubleshooting

### Common Issues

#### Connection Pool Exhausted
```python
# Symptom: "QueuePool limit of size X overflow Y reached"
# Solution: Increase pool_size or max_overflow in config
# Check: GET /api/v1/monitoring/database/pool
```

#### Slow Queries
```python
# Symptom: High query latency
# Solution: Add indexes, optimize queries, check EXPLAIN plans
# Check: GET /api/v1/monitoring/database/queries
```

#### Disk Space
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('utxoiq'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## References

- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
