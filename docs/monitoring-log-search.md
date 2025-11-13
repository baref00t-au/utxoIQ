# Log Search and Aggregation Guide

## Overview

The utxoIQ monitoring system provides centralized log aggregation across all services with powerful search capabilities. This guide covers log search syntax, filtering, and analysis techniques.

## Log Search Basics

### Accessing Log Search

**Via Web UI**:
1. Navigate to **Monitoring** → **Logs**
2. Enter search query in search bar
3. Apply filters (service, severity, time range)
4. View results in chronological order

**Via API**:
```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error",
    "start_time": "2025-11-11T00:00:00Z",
    "end_time": "2025-11-11T23:59:59Z",
    "severity": "ERROR",
    "service": "web-api",
    "limit": 100
  }'
```

### Log Entry Structure

Each log entry contains:

```json
{
  "timestamp": "2025-11-11T10:30:45.123Z",
  "severity": "ERROR",
  "service_name": "web-api",
  "message": "Database connection failed",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "abc123def456",
  "labels": {
    "environment": "production",
    "version": "2.1.0",
    "instance_id": "web-api-5f7b8c9d-xyz"
  },
  "source_location": {
    "file": "database.py",
    "line": 145,
    "function": "connect"
  },
  "http_request": {
    "method": "POST",
    "url": "/api/v1/insights",
    "status": 500,
    "user_agent": "Mozilla/5.0...",
    "remote_ip": "203.0.113.42"
  },
  "json_payload": {
    "error_code": "DB_CONNECTION_FAILED",
    "retry_count": 3,
    "connection_pool_size": 10
  }
}
```

## Search Syntax

### Full-Text Search

Search across all text fields:

```
error
```

Matches logs containing "error" in any field.

### Exact Phrase

Use quotes for exact phrase matching:

```
"database connection failed"
```

### Boolean Operators

#### AND
```
error AND database
```

Both terms must be present.

#### OR
```
error OR warning
```

Either term must be present.

#### NOT
```
error NOT timeout
```

First term present, second term absent.

#### Grouping
```
(error OR warning) AND database
```

Use parentheses to group conditions.

### Field-Specific Search

Search specific fields using `field:value` syntax:

```
severity:ERROR
service_name:web-api
message:"connection failed"
labels.environment:production
http_request.status:500
```

### Wildcards

Use `*` for wildcard matching:

```
error*          # Matches error, errors, errored
*connection*    # Matches any text containing connection
web-*           # Matches web-api, web-frontend, etc.
```

### Regular Expressions

Use `~` for regex matching:

```
message~"error.*timeout"
service_name~"web-.*"
```

### Numeric Comparisons

```
http_request.status>=500
http_request.status<400
json_payload.retry_count>3
```

Operators: `>`, `<`, `>=`, `<=`, `=`, `!=`

### Time-Based Search

```
timestamp>"2025-11-11T10:00:00Z"
timestamp<"2025-11-11T11:00:00Z"
```

## Filtering

### By Severity

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "ERROR"
  }'
```

**Severity Levels**:
- `DEBUG` - Detailed debugging information
- `INFO` - Informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

### By Service

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "web-api"
  }'
```

**Available Services**:
- `web-api`
- `feature-engine`
- `insight-generator`
- `chart-renderer`
- `data-ingestion`
- `x-bot`

### By Time Range

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2025-11-11T00:00:00Z",
    "end_time": "2025-11-11T23:59:59Z"
  }'
```

**Relative Time Ranges**:
```json
{
  "time_range": "1h"  // Last 1 hour
}
```

Options: `5m`, `15m`, `30m`, `1h`, `4h`, `12h`, `24h`, `7d`, `30d`

### By Trace ID

Find all logs for a specific request:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### By Labels

Filter by custom labels:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": {
      "environment": "production",
      "version": "2.1.0"
    }
  }'
```

## Advanced Search

### Combined Filters

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database AND (error OR timeout)",
    "severity": "ERROR",
    "service": "web-api",
    "start_time": "2025-11-11T00:00:00Z",
    "end_time": "2025-11-11T23:59:59Z",
    "labels": {
      "environment": "production"
    },
    "limit": 100,
    "order_by": "timestamp DESC"
  }'
```

### Aggregation Queries

Count logs by severity:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/aggregate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "group_by": ["severity"],
    "aggregation": "count",
    "time_range": "24h"
  }'
```

Response:
```json
{
  "results": [
    {"severity": "ERROR", "count": 1234},
    {"severity": "WARNING", "count": 5678},
    {"severity": "INFO", "count": 98765}
  ]
}
```

### Time-Series Aggregation

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/aggregate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "group_by": ["severity"],
    "aggregation": "count",
    "time_range": "24h",
    "interval": "1h"
  }'
```

Response:
```json
{
  "results": [
    {
      "timestamp": "2025-11-11T00:00:00Z",
      "ERROR": 45,
      "WARNING": 123,
      "INFO": 3456
    },
    {
      "timestamp": "2025-11-11T01:00:00Z",
      "ERROR": 52,
      "WARNING": 134,
      "INFO": 3789
    }
  ]
}
```

## Log Context

### View Surrounding Logs

Get logs before and after a specific log entry:

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/logs/{log_id}/context \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "before": 10,
    "after": 10
  }'
```

Response includes:
- 10 log entries before target log
- Target log (highlighted)
- 10 log entries after target log

### Trace Context

View all logs for a request trace:

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/logs/trace/{trace_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Returns logs from all services involved in the request, ordered chronologically.

## Export and Analysis

### Export to CSV

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/export \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error",
    "format": "csv",
    "start_time": "2025-11-11T00:00:00Z",
    "end_time": "2025-11-11T23:59:59Z"
  }' \
  -o logs.csv
```

### Export to JSON

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/export \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "error",
    "format": "json",
    "start_time": "2025-11-11T00:00:00Z",
    "end_time": "2025-11-11T23:59:59Z"
  }' \
  -o logs.json
```

### Stream Logs

Real-time log streaming:

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/logs/stream \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: text/event-stream" \
  -d '{
    "service": "web-api",
    "severity": "ERROR"
  }'
```

## Common Search Patterns

### Find All Errors

```
severity:ERROR
```

### Find Database Errors

```
severity:ERROR AND (database OR postgres OR sql)
```

### Find Slow Requests

```
http_request.status:200 AND json_payload.duration>1000
```

### Find Failed API Calls

```
http_request.status>=500
```

### Find Authentication Failures

```
message:"authentication failed" OR message:"unauthorized"
```

### Find Memory Issues

```
message~".*memory.*" AND severity:ERROR
```

### Find Specific User Activity

```
json_payload.user_id:"user-123"
```

### Find Deployment Issues

```
labels.version:"2.1.0" AND severity:ERROR AND timestamp>"2025-11-11T10:00:00Z"
```

## Performance Optimization

### Use Specific Time Ranges

Narrow time ranges improve search performance:

```json
{
  "start_time": "2025-11-11T10:00:00Z",
  "end_time": "2025-11-11T11:00:00Z"
}
```

### Filter by Service

Reduce search scope by specifying service:

```json
{
  "service": "web-api"
}
```

### Use Field-Specific Search

More efficient than full-text search:

```
severity:ERROR
```

vs

```
ERROR
```

### Limit Results

Use pagination for large result sets:

```json
{
  "limit": 100,
  "offset": 0
}
```

## Best Practices

### Search Strategy

1. **Start broad**: Begin with simple queries
2. **Refine iteratively**: Add filters to narrow results
3. **Use time ranges**: Always specify time bounds
4. **Filter by service**: Reduce search scope
5. **Use trace IDs**: Follow request flows

### Log Analysis

1. **Look for patterns**: Identify recurring errors
2. **Check context**: View surrounding logs
3. **Follow traces**: Track requests across services
4. **Aggregate data**: Use aggregation for trends
5. **Export for analysis**: Download logs for deeper analysis

### Troubleshooting Workflow

1. **Identify issue**: Search for error messages
2. **Find first occurrence**: Sort by timestamp
3. **Get context**: View surrounding logs
4. **Follow trace**: Track request through services
5. **Analyze patterns**: Aggregate similar errors
6. **Correlate metrics**: Check metrics at same time

## Saved Searches

### Create Saved Search

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/saved-searches \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database Errors",
    "query": "severity:ERROR AND (database OR postgres)",
    "filters": {
      "service": "web-api"
    }
  }'
```

### List Saved Searches

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/logs/saved-searches \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Execute Saved Search

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/logs/saved-searches/{search_id}/execute \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "time_range": "24h"
  }'
```

## Troubleshooting

### No Results Found

1. **Check time range**: Ensure time range includes expected logs
2. **Verify service name**: Confirm service name is correct
3. **Review query syntax**: Check for syntax errors
4. **Broaden search**: Remove filters to see if logs exist
5. **Check retention**: Logs older than 30 days are archived

### Slow Search

1. **Narrow time range**: Use shorter time periods
2. **Add service filter**: Reduce search scope
3. **Use field-specific search**: More efficient than full-text
4. **Reduce result limit**: Fetch fewer results
5. **Avoid wildcards**: Wildcards can be slow

### Missing Logs

1. **Check service status**: Ensure service is logging
2. **Verify log level**: Check if log level is configured correctly
3. **Review retention**: Logs are retained for 30 days
4. **Check filters**: Ensure filters aren't excluding logs
5. **Verify permissions**: Ensure you have access to service logs

## API Reference

### Search Logs
`POST /api/v1/monitoring/logs/search`

### Aggregate Logs
`POST /api/v1/monitoring/logs/aggregate`

### Get Log Context
`GET /api/v1/monitoring/logs/{log_id}/context`

### Get Trace Logs
`GET /api/v1/monitoring/logs/trace/{trace_id}`

### Export Logs
`POST /api/v1/monitoring/logs/export`

### Stream Logs
`GET /api/v1/monitoring/logs/stream`

### Create Saved Search
`POST /api/v1/monitoring/logs/saved-searches`

For detailed API documentation, see [API Reference](./api-reference-monitoring.md).
