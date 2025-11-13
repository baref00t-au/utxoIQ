# Database-Backed API Documentation

## Overview

This document describes all API endpoints that interact with the Cloud SQL database for persistent storage. All endpoints use async database operations with connection pooling and Redis caching where appropriate.

## Base URL

```
Production: https://utxoiq-api.run.app
Development: http://localhost:8000
```

## Authentication

Most endpoints require authentication via Firebase Auth JWT token:

```http
Authorization: Bearer <firebase-jwt-token>
```

## Backfill Job Endpoints

### POST /api/v1/monitoring/backfill/start

Start a new backfill job and create database record.

#### Request Body

```json
{
  "job_type": "blocks",
  "start_block": 800000,
  "end_block": 810000,
  "created_by": "admin@utxoiq.com"
}
```

#### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "blocks",
  "start_block": 800000,
  "end_block": 810000,
  "current_block": 800000,
  "status": "running",
  "progress_percentage": 0.0,
  "estimated_completion": null,
  "error_message": null,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": null,
  "created_by": "admin@utxoiq.com"
}
```

#### Error Responses

```json
// 400 Bad Request - Invalid data
{
  "detail": "end_block must be greater than or equal to start_block"
}

// 500 Internal Server Error - Database failure
{
  "detail": "Failed to create backfill job"
}
```

---

### POST /api/v1/monitoring/backfill/progress

Update backfill job progress in database.

#### Query Parameters

- `job_id` (UUID, required): Job identifier

#### Request Body

```json
{
  "current_block": 805000,
  "progress_percentage": 50.0,
  "estimated_completion": "2024-01-15T12:00:00Z",
  "status": "running"
}
```

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "blocks",
  "start_block": 800000,
  "end_block": 810000,
  "current_block": 805000,
  "status": "running",
  "progress_percentage": 50.0,
  "estimated_completion": "2024-01-15T12:00:00Z",
  "error_message": null,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": null,
  "created_by": "admin@utxoiq.com"
}
```

#### Error Responses

```json
// 404 Not Found
{
  "detail": "Backfill job 550e8400-e29b-41d4-a716-446655440000 not found"
}

// 400 Bad Request
{
  "detail": "current_block cannot exceed end_block"
}
```

---

### GET /api/v1/monitoring/backfill/status

Query backfill job status from database with caching.

#### Query Parameters

- `status` (string, optional): Filter by status ('running', 'completed', 'failed', 'paused')
- `job_type` (string, optional): Filter by job type
- `limit` (integer, optional, default=10, max=100): Maximum results
- `offset` (integer, optional, default=0): Pagination offset

#### Response (200 OK)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "job_type": "blocks",
    "start_block": 800000,
    "end_block": 810000,
    "current_block": 810000,
    "status": "completed",
    "progress_percentage": 100.0,
    "estimated_completion": null,
    "error_message": null,
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T12:00:00Z",
    "created_by": "admin@utxoiq.com"
  }
]
```

#### Example Requests

```bash
# Get all running jobs
curl "https://utxoiq-api.run.app/api/v1/monitoring/backfill/status?status=running"

# Get completed block backfills
curl "https://utxoiq-api.run.app/api/v1/monitoring/backfill/status?status=completed&job_type=blocks"

# Paginate through jobs
curl "https://utxoiq-api.run.app/api/v1/monitoring/backfill/status?limit=20&offset=40"
```

---

### GET /api/v1/monitoring/backfill/{job_id}

Get specific backfill job with caching.

#### Path Parameters

- `job_id` (UUID, required): Job identifier

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "blocks",
  "start_block": 800000,
  "end_block": 810000,
  "current_block": 805000,
  "status": "running",
  "progress_percentage": 50.0,
  "estimated_completion": "2024-01-15T12:00:00Z",
  "error_message": null,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": null,
  "created_by": "admin@utxoiq.com"
}
```

#### Caching

- **Cache Key**: `backfill:job:{job_id}`
- **TTL**: 5 minutes
- **Invalidation**: On progress update

---

## Feedback Endpoints

### POST /api/v1/feedback/rate

Rate an insight (1-5 stars) with optional comment.

#### Request Body

```json
{
  "insight_id": "insight-2024-01-15-001",
  "rating": 5,
  "comment": "Very insightful analysis of mempool congestion",
  "user_id": "user-123"
}
```

#### Response (200 OK)

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "insight_id": "insight-2024-01-15-001",
  "user_id": "user-123",
  "rating": 5,
  "comment": "Very insightful analysis of mempool congestion",
  "flag_type": null,
  "flag_reason": null,
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

#### Behavior

- **Upsert**: Updates existing feedback if user already rated this insight
- **Cache Invalidation**: Invalidates feedback stats cache for the insight
- **Validation**: Rating must be 1-5

---

### POST /api/v1/feedback/comment

Add a comment to an insight.

#### Request Body

```json
{
  "insight_id": "insight-2024-01-15-001",
  "comment": "This explains the recent fee spike perfectly",
  "user_id": "user-123"
}
```

#### Response (200 OK)

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "insight_id": "insight-2024-01-15-001",
  "user_id": "user-123",
  "rating": null,
  "comment": "This explains the recent fee spike perfectly",
  "flag_type": null,
  "flag_reason": null,
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

---

### POST /api/v1/feedback/flag

Flag an insight for review.

#### Request Body

```json
{
  "insight_id": "insight-2024-01-15-001",
  "flag_type": "inaccurate",
  "flag_reason": "The transaction volume numbers don't match blockchain data",
  "user_id": "user-123"
}
```

#### Flag Types

- `inaccurate`: Data or analysis is incorrect
- `misleading`: Interpretation is misleading
- `spam`: Spam or irrelevant content

#### Response (200 OK)

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "insight_id": "insight-2024-01-15-001",
  "user_id": "user-123",
  "rating": null,
  "comment": null,
  "flag_type": "inaccurate",
  "flag_reason": "The transaction volume numbers don't match blockchain data",
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

---

### GET /api/v1/feedback/stats

Get aggregated feedback statistics for an insight.

#### Query Parameters

- `insight_id` (string, required): Insight identifier

#### Response (200 OK)

```json
{
  "insight_id": "insight-2024-01-15-001",
  "total_ratings": 42,
  "average_rating": 4.3,
  "rating_distribution": {
    "1": 1,
    "2": 2,
    "3": 5,
    "4": 14,
    "5": 20
  },
  "total_comments": 18,
  "total_flags": 2,
  "flag_types": {
    "inaccurate": 1,
    "misleading": 1
  }
}
```

#### Caching

- **Cache Key**: `feedback:stats:{insight_id}`
- **TTL**: 1 hour
- **Invalidation**: On any feedback update for the insight

---

### GET /api/v1/feedback/comments

Get comments for an insight with pagination.

#### Query Parameters

- `insight_id` (string, required): Insight identifier
- `limit` (integer, optional, default=20, max=100): Maximum results
- `offset` (integer, optional, default=0): Pagination offset

#### Response (200 OK)

```json
{
  "insight_id": "insight-2024-01-15-001",
  "comments": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "user_id": "user-123",
      "comment": "Very insightful analysis",
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### GET /api/v1/feedback/user

Get user's feedback history with pagination.

#### Query Parameters

- `user_id` (string, required): User identifier
- `limit` (integer, optional, default=50, max=100): Maximum results
- `offset` (integer, optional, default=0): Pagination offset

#### Response (200 OK)

```json
{
  "user_id": "user-123",
  "feedback": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "insight_id": "insight-2024-01-15-001",
      "rating": 5,
      "comment": "Very insightful",
      "flag_type": null,
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

## Metrics Endpoints

### POST /api/v1/monitoring/metrics

Record a system metric in database.

#### Request Body

```json
{
  "service_name": "web-api",
  "metric_type": "cpu",
  "metric_value": 45.2,
  "unit": "percent",
  "metric_metadata": {
    "instance_id": "web-api-abc123",
    "region": "us-central1"
  }
}
```

#### Response (201 Created)

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "service_name": "web-api",
  "metric_type": "cpu",
  "metric_value": 45.2,
  "unit": "percent",
  "timestamp": "2024-01-15T14:30:00Z",
  "metric_metadata": {
    "instance_id": "web-api-abc123",
    "region": "us-central1"
  }
}
```

---

### POST /api/v1/monitoring/metrics/batch

Record multiple system metrics in a batch.

#### Request Body

```json
[
  {
    "service_name": "web-api",
    "metric_type": "cpu",
    "metric_value": 45.2,
    "unit": "percent"
  },
  {
    "service_name": "web-api",
    "metric_type": "memory",
    "metric_value": 1024.5,
    "unit": "MB"
  },
  {
    "service_name": "web-api",
    "metric_type": "latency",
    "metric_value": 120.3,
    "unit": "ms"
  }
]
```

#### Response (201 Created)

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "service_name": "web-api",
    "metric_type": "cpu",
    "metric_value": 45.2,
    "unit": "percent",
    "timestamp": "2024-01-15T14:30:00Z",
    "metric_metadata": null
  },
  // ... more metrics
]
```

---

### GET /api/v1/monitoring/metrics

Query metrics with time range filters.

#### Query Parameters

- `service_name` (string, optional): Filter by service name
- `metric_type` (string, optional): Filter by metric type
- `start_time` (datetime, required): Start of time range (ISO 8601)
- `end_time` (datetime, required): End of time range (ISO 8601)
- `limit` (integer, optional, default=1000, max=10000): Maximum results
- `offset` (integer, optional, default=0): Pagination offset

#### Response (200 OK)

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "service_name": "web-api",
    "metric_type": "cpu",
    "metric_value": 45.2,
    "unit": "percent",
    "timestamp": "2024-01-15T14:30:00Z",
    "metric_metadata": null
  }
]
```

#### Example Requests

```bash
# Get CPU metrics for last hour
curl "https://utxoiq-api.run.app/api/v1/monitoring/metrics?\
service_name=web-api&\
metric_type=cpu&\
start_time=2024-01-15T13:30:00Z&\
end_time=2024-01-15T14:30:00Z"

# Get all metrics for a service
curl "https://utxoiq-api.run.app/api/v1/monitoring/metrics?\
service_name=feature-engine&\
start_time=2024-01-15T00:00:00Z&\
end_time=2024-01-15T23:59:59Z"
```

#### Caching

- **Cache Key**: `metrics:{service}:{metric_type}:recent`
- **TTL**: 5 minutes
- **Condition**: Only for last 1 hour of data

---

### GET /api/v1/monitoring/metrics/aggregate

Get aggregated metrics for hourly or daily rollups.

#### Query Parameters

- `service_name` (string, required): Service name to aggregate
- `metric_type` (string, required): Metric type to aggregate
- `start_time` (datetime, required): Aggregation start time (ISO 8601)
- `end_time` (datetime, required): Aggregation end time (ISO 8601)
- `interval` (string, required): Aggregation interval ('hour' or 'day')

#### Response (200 OK)

```json
{
  "service_name": "web-api",
  "metric_type": "cpu",
  "interval": "hour",
  "start_time": "2024-01-15T00:00:00Z",
  "end_time": "2024-01-15T23:59:59Z",
  "data": [
    {
      "timestamp": "2024-01-15T00:00:00Z",
      "avg_value": 42.5,
      "min_value": 35.2,
      "max_value": 58.7,
      "count": 60
    },
    {
      "timestamp": "2024-01-15T01:00:00Z",
      "avg_value": 38.1,
      "min_value": 32.4,
      "max_value": 45.9,
      "count": 60
    }
  ]
}
```

#### Caching

- **Cache Key**: `metrics:agg:{service}:{type}:{interval}:{start}:{end}`
- **TTL**: 1 hour
- **Invalidation**: Time-based expiration only

---

## Database Monitoring Endpoints

### GET /api/v1/monitoring/database/pool

Get current database connection pool metrics.

#### Response (200 OK)

```json
{
  "status": "success",
  "metrics": {
    "size": 10,
    "checked_in": 7,
    "checked_out": 3,
    "overflow": 2,
    "total_connections": 12
  }
}
```

---

### GET /api/v1/monitoring/database/queries

Get database query performance metrics.

#### Response (200 OK)

```json
{
  "status": "success",
  "metrics": {
    "total_queries": 1523,
    "slow_queries": 42,
    "slow_query_percentage": 2.76,
    "average_query_time": 85.3,
    "slow_query_threshold": 200
  }
}
```

---

### POST /api/v1/monitoring/database/publish-metrics

Publish database metrics to Cloud Monitoring.

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Database metrics published to Cloud Monitoring"
}
```

#### Usage

This endpoint should be called periodically (every 60 seconds) by a cron job to publish metrics to Cloud Monitoring for dashboard visualization and alerting.

---

## Data Retention Endpoint

### POST /api/v1/monitoring/retention/run

Execute all data retention policies.

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Retention policies executed successfully",
  "results": {
    "backfill_jobs": {
      "archived": 15,
      "deleted": 15,
      "errors": 0
    },
    "feedback": {
      "archived": 234,
      "deleted": 234,
      "errors": 0
    },
    "metrics": {
      "archived": 1523,
      "deleted": 0,
      "errors": 0
    }
  }
}
```

#### Usage

This endpoint is designed to be called by Cloud Scheduler daily at 02:00 UTC. It archives and deletes old records according to retention policies.

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request creating a resource
- `400 Bad Request`: Invalid request data or validation error
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Database or server error

### Error Types

#### Validation Errors (400)
- Invalid data format
- Missing required fields
- Value out of range
- Constraint violations

#### Not Found Errors (404)
- Resource doesn't exist
- Invalid UUID

#### Database Errors (500)
- Connection failures
- Query execution errors
- Transaction rollback
- Integrity constraint violations

---

## Rate Limiting

All endpoints are subject to rate limiting:

- **Authenticated Users**: 1000 requests per hour
- **Anonymous**: 100 requests per hour
- **Batch Endpoints**: 100 requests per hour

Rate limit headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705329600
```

---

## SDK Examples

### Python

```python
import requests
from datetime import datetime, timedelta

# Start backfill job
response = requests.post(
    "https://utxoiq-api.run.app/api/v1/monitoring/backfill/start",
    json={
        "job_type": "blocks",
        "start_block": 800000,
        "end_block": 810000,
        "created_by": "admin@utxoiq.com"
    }
)
job = response.json()
job_id = job["id"]

# Update progress
requests.post(
    f"https://utxoiq-api.run.app/api/v1/monitoring/backfill/progress?job_id={job_id}",
    json={
        "current_block": 805000,
        "progress_percentage": 50.0
    }
)

# Rate insight
requests.post(
    "https://utxoiq-api.run.app/api/v1/feedback/rate",
    json={
        "insight_id": "insight-123",
        "rating": 5,
        "user_id": "user-123"
    }
)

# Query metrics
end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)
response = requests.get(
    "https://utxoiq-api.run.app/api/v1/monitoring/metrics",
    params={
        "service_name": "web-api",
        "metric_type": "cpu",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
)
metrics = response.json()
```

### JavaScript/TypeScript

```typescript
// Start backfill job
const response = await fetch(
  'https://utxoiq-api.run.app/api/v1/monitoring/backfill/start',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      job_type: 'blocks',
      start_block: 800000,
      end_block: 810000,
      created_by: 'admin@utxoiq.com'
    })
  }
);
const job = await response.json();

// Rate insight
await fetch('https://utxoiq-api.run.app/api/v1/feedback/rate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    insight_id: 'insight-123',
    rating: 5,
    user_id: 'user-123'
  })
});

// Get feedback stats
const statsResponse = await fetch(
  'https://utxoiq-api.run.app/api/v1/feedback/stats?insight_id=insight-123'
);
const stats = await statsResponse.json();
```

---

## Testing

### Health Check

```bash
curl https://utxoiq-api.run.app/health
```

### Integration Tests

```bash
# Run API integration tests
cd services/web-api
pytest tests/integration/test_database_api.py -v
```

---

## Support

For API issues or questions:
- **Documentation**: https://docs.utxoiq.com
- **GitHub Issues**: https://github.com/utxoiq/platform/issues
- **Email**: support@utxoiq.com
