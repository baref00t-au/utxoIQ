# Requirements Document

## Introduction

This specification defines the database persistence layer for the utxoIQ platform. The system currently operates with in-memory data structures for backfill jobs, insight feedback, and system metrics. This feature will implement persistent storage using Cloud SQL (PostgreSQL) and Redis caching to ensure data reliability, enable historical analysis, and support production-grade operations.

## Glossary

- **Backfill System**: The process that populates historical blockchain data into BigQuery
- **Insight Feedback**: User-generated ratings, comments, and flags on AI-generated insights
- **System Metrics**: Performance and health data from backend services
- **Cloud SQL**: Google Cloud's managed PostgreSQL database service
- **Redis**: In-memory data store used for caching and rate limiting
- **Connection Pool**: A cache of database connections maintained for reuse
- **Data Retention Policy**: Rules defining how long data is stored before archival or deletion
- **Migration**: A versioned database schema change script

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want backfill job progress to persist across service restarts, so that I can track historical backfill operations and resume interrupted jobs.

#### Acceptance Criteria

1. WHEN a backfill job starts, THE Backfill System SHALL create a record in the backfill_jobs table with status "running"
2. WHEN a backfill job updates progress, THE Backfill System SHALL update the progress_percentage and estimated_completion fields within 5 seconds
3. WHEN a backfill job completes, THE Backfill System SHALL update the status to "completed" and record the completion timestamp
4. IF a backfill job fails, THEN THE Backfill System SHALL update the status to "failed" and store the error message
5. THE Backfill System SHALL retrieve the most recent backfill job status from the database within 100 milliseconds

### Requirement 2

**User Story:** As a product manager, I want user feedback on insights to be permanently stored, so that I can analyze user satisfaction trends and improve insight quality over time.

#### Acceptance Criteria

1. WHEN a user rates an insight, THE Feedback System SHALL store the rating in the insight_feedback table within 2 seconds
2. WHEN a user adds a comment, THE Feedback System SHALL store the comment text with a timestamp and user identifier
3. WHEN a user flags an insight, THE Feedback System SHALL record the flag type and reason in the database
4. THE Feedback System SHALL retrieve feedback statistics for an insight within 100 milliseconds
5. THE Feedback System SHALL support querying feedback by user, insight, date range, and rating value

### Requirement 3

**User Story:** As a DevOps engineer, I want system metrics to be stored in a time-series format, so that I can analyze performance trends and identify degradation patterns.

#### Acceptance Criteria

1. WHEN a service reports metrics, THE Monitoring System SHALL store the metrics in the system_metrics table with a timestamp
2. THE Monitoring System SHALL partition metrics data by date for efficient querying
3. THE Monitoring System SHALL retrieve metrics for a 24-hour period within 200 milliseconds
4. THE Monitoring System SHALL support aggregation queries for hourly, daily, and weekly metrics
5. THE Monitoring System SHALL automatically archive metrics older than 90 days to cold storage

### Requirement 4

**User Story:** As a backend developer, I want frequently accessed data to be cached in Redis, so that database load is reduced and API response times remain under 100 milliseconds.

#### Acceptance Criteria

1. WHEN an API endpoint queries frequently accessed data, THE Caching Layer SHALL check Redis before querying the database
2. THE Caching Layer SHALL achieve a cache hit rate of at least 90 percent for insight feedback statistics
3. WHEN cached data is updated in the database, THE Caching Layer SHALL invalidate the corresponding cache entry within 1 second
4. THE Caching Layer SHALL set appropriate TTL values based on data volatility (5 minutes for metrics, 1 hour for feedback stats)
5. IF Redis is unavailable, THEN THE Caching Layer SHALL fall back to direct database queries without service interruption

### Requirement 5

**User Story:** As a database administrator, I want database schema changes to be managed through migrations, so that schema evolution is tracked, versioned, and safely applied across environments.

#### Acceptance Criteria

1. THE Migration System SHALL maintain a migrations table tracking applied schema changes
2. WHEN a new migration is created, THE Migration System SHALL assign a sequential version number and timestamp
3. THE Migration System SHALL apply pending migrations in order during deployment
4. THE Migration System SHALL support rollback of the most recent migration
5. THE Migration System SHALL prevent applying the same migration twice

### Requirement 6

**User Story:** As a backend developer, I want database connection pooling configured, so that connection overhead is minimized and the system can handle concurrent requests efficiently.

#### Acceptance Criteria

1. THE Database Connection Pool SHALL maintain between 5 and 20 active connections based on load
2. THE Database Connection Pool SHALL reuse existing connections for new requests within 10 milliseconds
3. THE Database Connection Pool SHALL close idle connections after 5 minutes of inactivity
4. THE Database Connection Pool SHALL handle connection failures by retrying up to 3 times with exponential backoff
5. THE Database Connection Pool SHALL log connection pool metrics (active, idle, waiting) every 60 seconds

### Requirement 7

**User Story:** As a compliance officer, I want data retention policies implemented, so that user data is not stored longer than necessary and storage costs are controlled.

#### Acceptance Criteria

1. THE Data Retention System SHALL archive backfill job records older than 180 days to cold storage
2. THE Data Retention System SHALL delete insight feedback older than 2 years after archival
3. THE Data Retention System SHALL retain system metrics for 90 days in hot storage and 1 year in cold storage
4. THE Data Retention System SHALL execute retention policies daily at 02:00 UTC
5. THE Data Retention System SHALL log all data archival and deletion operations for audit purposes

### Requirement 8

**User Story:** As a site reliability engineer, I want automated database backups configured, so that data can be recovered in case of corruption or accidental deletion.

#### Acceptance Criteria

1. THE Backup System SHALL create full database backups daily at 01:00 UTC
2. THE Backup System SHALL retain daily backups for 7 days and weekly backups for 4 weeks
3. THE Backup System SHALL verify backup integrity by performing test restores weekly
4. THE Backup System SHALL store backups in a separate GCP region for disaster recovery
5. THE Backup System SHALL alert administrators within 5 minutes if a backup fails
