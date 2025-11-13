# Distributed Tracing Guide

## Overview

Distributed tracing allows you to track requests as they flow through multiple services in the utxoIQ platform. This guide covers how to use tracing to debug performance issues, understand service dependencies, and optimize request flows.

## Tracing Basics

### What is Distributed Tracing?

Distributed tracing tracks a single request as it propagates through multiple services, creating a complete picture of:

- Request flow across services
- Time spent in each service
- Service dependencies
- Performance bottlenecks
- Error propagation

### Trace Components

**Trace**: A complete request journey across all services

**Span**: A single operation within a trace (e.g., database query, API call)

**Trace ID**: Unique identifier for the entire trace

**Span ID**: Unique identifier for a specific span

**Parent Span**: The span that initiated the current span

### Trace Structure

```
Trace: 550e8400-e29b-41d4-a716-446655440000
│
├─ Span: web-api.handle_request (200ms)
│  ├─ Span: web-api.authenticate (15ms)
│  ├─ Span: feature-engine.compute_signals (120ms)
│  │  ├─ Span: bigquery.query (80ms)
│  │  └─ Span: redis.get (5ms)
│  └─ Span: insight-generator.generate (50ms)
│     └─ Span: vertex-ai.predict (45ms)
```

## Viewing Traces

### Via Web UI

1. Navigate to **Monitoring** → **Traces**
2. Search for traces by:
   - Trace ID
   - Service name
   - Time range
   - Duration
   - Status code
3. Click on a trace to view details
4. Explore span hierarchy and timing

### Via API

#### Get Trace by ID

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/traces/{trace_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": "2025-11-11T10:30:45.123Z",
  "end_time": "2025-11-11T10:30:45.323Z",
  "duration_ms": 200,
  "status": "OK",
  "spans": [
    {
      "span_id": "abc123",
      "parent_span_id": null,
      "name": "web-api.handle_request",
      "service_name": "web-api",
      "start_time": "2025-11-11T10:30:45.123Z",
      "end_time": "2025-11-11T10:30:45.323Z",
      "duration_ms": 200,
      "status": "OK",
      "attributes": {
        "http.method": "POST",
        "http.url": "/api/v1/insights",
        "http.status_code": 200,
        "user_id": "user-123"
      }
    },
    {
      "span_id": "def456",
      "parent_span_id": "abc123",
      "name": "feature-engine.compute_signals",
      "service_name": "feature-engine",
      "start_time": "2025-11-11T10:30:45.138Z",
      "end_time": "2025-11-11T10:30:45.258Z",
      "duration_ms": 120,
      "status": "OK",
      "attributes": {
        "block_height": 820000,
        "signal_count": 15
      }
    }
  ]
}
```

#### Search Traces

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "web-api",
    "start_time": "2025-11-11T00:00:00Z",
    "end_time": "2025-11-11T23:59:59Z",
    "min_duration_ms": 1000,
    "status": "ERROR",
    "limit": 100
  }'
```

## Trace Analysis

### Identifying Slow Requests

Find traces with high latency:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "min_duration_ms": 1000,
    "time_range": "1h",
    "order_by": "duration DESC",
    "limit": 10
  }'
```

### Finding Bottlenecks

Identify spans consuming the most time:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/analyze \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "web-api",
    "time_range": "24h",
    "group_by": "span_name",
    "metric": "avg_duration"
  }'
```

Response:
```json
{
  "results": [
    {
      "span_name": "bigquery.query",
      "avg_duration_ms": 450,
      "p50_duration_ms": 380,
      "p95_duration_ms": 850,
      "p99_duration_ms": 1200,
      "count": 5432
    },
    {
      "span_name": "vertex-ai.predict",
      "avg_duration_ms": 320,
      "p50_duration_ms": 280,
      "p95_duration_ms": 650,
      "p99_duration_ms": 900,
      "count": 3210
    }
  ]
}
```

### Error Tracking

Find failed requests:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "ERROR",
    "time_range": "1h",
    "limit": 50
  }'
```

### Service Dependencies

Visualize service call patterns:

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/traces/dependencies \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "time_range": "24h"
  }'
```

Response:
```json
{
  "nodes": [
    {"id": "web-api", "label": "Web API", "request_count": 10000},
    {"id": "feature-engine", "label": "Feature Engine", "request_count": 8500},
    {"id": "insight-generator", "label": "Insight Generator", "request_count": 5000}
  ],
  "edges": [
    {"source": "web-api", "target": "feature-engine", "request_count": 8500, "avg_duration_ms": 120},
    {"source": "web-api", "target": "insight-generator", "request_count": 5000, "avg_duration_ms": 50}
  ]
}
```

## Span Attributes

### Standard Attributes

All spans include standard attributes:

```json
{
  "span_id": "abc123",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_span_id": "parent123",
  "name": "operation_name",
  "service_name": "web-api",
  "start_time": "2025-11-11T10:30:45.123Z",
  "end_time": "2025-11-11T10:30:45.323Z",
  "duration_ms": 200,
  "status": "OK"
}
```

### HTTP Attributes

For HTTP requests:

```json
{
  "attributes": {
    "http.method": "POST",
    "http.url": "/api/v1/insights",
    "http.status_code": 200,
    "http.user_agent": "Mozilla/5.0...",
    "http.request_size": 1024,
    "http.response_size": 4096
  }
}
```

### Database Attributes

For database operations:

```json
{
  "attributes": {
    "db.system": "postgresql",
    "db.name": "utxoiq",
    "db.statement": "SELECT * FROM insights WHERE id = $1",
    "db.operation": "SELECT",
    "db.rows_affected": 1
  }
}
```

### Custom Attributes

Application-specific attributes:

```json
{
  "attributes": {
    "user_id": "user-123",
    "block_height": 820000,
    "insight_id": "insight-456",
    "cache_hit": true,
    "retry_count": 0
  }
}
```

## Trace Sampling

### Sampling Strategy

Not all requests are traced to reduce overhead:

- **Always sampled**: Errors and slow requests (>1s)
- **Head-based sampling**: 10% of normal requests
- **Tail-based sampling**: Interesting traces based on patterns

### Configure Sampling

```bash
curl -X PATCH https://api.utxoiq.com/api/v1/monitoring/tracing/config \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sampling_rate": 0.1,
    "always_sample_errors": true,
    "always_sample_slow_requests": true,
    "slow_request_threshold_ms": 1000
  }'
```

## Performance Analysis

### Latency Breakdown

Analyze where time is spent:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/{trace_id}/breakdown \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_duration_ms": 200,
  "breakdown": [
    {
      "service": "web-api",
      "duration_ms": 30,
      "percentage": 15
    },
    {
      "service": "feature-engine",
      "duration_ms": 120,
      "percentage": 60
    },
    {
      "service": "insight-generator",
      "duration_ms": 50,
      "percentage": 25
    }
  ],
  "critical_path": [
    "web-api.handle_request",
    "feature-engine.compute_signals",
    "bigquery.query"
  ]
}
```

### Critical Path Analysis

Identify the longest path through the trace:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/{trace_id}/critical-path \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Span Statistics

Get statistics for specific span types:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/stats \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "span_name": "bigquery.query",
    "time_range": "24h"
  }'
```

Response:
```json
{
  "span_name": "bigquery.query",
  "count": 5432,
  "avg_duration_ms": 450,
  "min_duration_ms": 50,
  "max_duration_ms": 2500,
  "p50_duration_ms": 380,
  "p95_duration_ms": 850,
  "p99_duration_ms": 1200,
  "error_rate": 0.02
}
```

## Trace Visualization

### Timeline View

View spans on a timeline:

```
Time (ms)  0    50   100  150  200
           |----|----|----|----|
web-api    [====================]
  auth       [==]
  feature        [============]
    bigquery       [========]
    redis              [=]
  insight                [====]
    vertex-ai              [===]
```

### Flame Graph

Visualize span hierarchy and duration:

```
web-api.handle_request (200ms)
├─ web-api.authenticate (15ms)
├─ feature-engine.compute_signals (120ms)
│  ├─ bigquery.query (80ms)
│  └─ redis.get (5ms)
└─ insight-generator.generate (50ms)
   └─ vertex-ai.predict (45ms)
```

### Service Map

Visualize service dependencies:

```
┌─────────┐
│ web-api │
└────┬────┘
     │
     ├──────────────┬──────────────┐
     │              │              │
┌────▼────┐   ┌────▼────┐   ┌────▼────┐
│ feature │   │ insight │   │  chart  │
│ engine  │   │generator│   │renderer │
└────┬────┘   └────┬────┘   └─────────┘
     │              │
     ├──────┬───────┴──────┐
     │      │              │
┌────▼──┐ ┌─▼────┐   ┌────▼────┐
│BigQuery│ │Redis │   │Vertex AI│
└────────┘ └──────┘   └─────────┘
```

## Debugging with Traces

### Scenario 1: Slow API Response

1. **Find slow traces**:
```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/search \
  -d '{"min_duration_ms": 1000, "limit": 10}'
```

2. **Analyze trace**:
```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/traces/{trace_id}
```

3. **Identify bottleneck**: Look for spans with high duration

4. **Check span details**: Review attributes for clues

5. **Correlate with logs**:
```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/logs/trace/{trace_id}
```

### Scenario 2: Error Investigation

1. **Find error traces**:
```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/traces/search \
  -d '{"status": "ERROR", "time_range": "1h"}'
```

2. **Examine error span**: Find span with error status

3. **Check error attributes**:
```json
{
  "attributes": {
    "error": true,
    "error.type": "DatabaseConnectionError",
    "error.message": "Connection timeout",
    "error.stack": "..."
  }
}
```

4. **Trace error propagation**: Follow parent spans to see how error propagated

5. **Review logs**: Get detailed error context from logs

### Scenario 3: Service Dependency Issue

1. **View service map**:
```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/traces/dependencies
```

2. **Identify failing edge**: Look for high error rate between services

3. **Find example traces**: Get traces showing the failure

4. **Analyze timing**: Check if timeouts or retries are occurring

5. **Review service health**: Check metrics for downstream service

## Best Practices

### Instrumentation

1. **Trace all external calls**: Database, API, cache operations
2. **Add meaningful attributes**: Include context for debugging
3. **Use consistent naming**: Follow naming conventions for spans
4. **Avoid over-instrumentation**: Don't trace every function
5. **Include business context**: Add user IDs, resource IDs, etc.

### Analysis

1. **Start with slow traces**: Focus on performance issues first
2. **Look for patterns**: Identify common bottlenecks
3. **Check critical path**: Optimize longest path first
4. **Correlate with metrics**: Compare traces with metric data
5. **Review regularly**: Make tracing part of regular monitoring

### Performance

1. **Use sampling**: Don't trace every request
2. **Limit span count**: Avoid creating too many spans
3. **Batch exports**: Export traces in batches
4. **Set retention**: Archive old traces
5. **Monitor overhead**: Ensure tracing doesn't impact performance

## Troubleshooting

### Missing Traces

1. **Check sampling**: Trace may not have been sampled
2. **Verify instrumentation**: Ensure service is instrumented
3. **Check time range**: Trace may be outside search range
4. **Review retention**: Traces older than 30 days are archived
5. **Verify trace ID**: Ensure trace ID is correct

### Incomplete Traces

1. **Check service status**: Downstream service may be down
2. **Review timeouts**: Spans may have timed out
3. **Verify propagation**: Ensure trace context is propagated
4. **Check errors**: Errors may have interrupted trace
5. **Review logs**: Check for service errors

### Slow Trace Queries

1. **Narrow time range**: Use shorter time periods
2. **Add filters**: Filter by service or status
3. **Use trace ID**: Direct lookup is fastest
4. **Limit results**: Fetch fewer traces
5. **Check indexes**: Ensure proper indexing

## API Reference

### Get Trace
`GET /api/v1/monitoring/traces/{trace_id}`

### Search Traces
`POST /api/v1/monitoring/traces/search`

### Analyze Traces
`POST /api/v1/monitoring/traces/analyze`

### Get Dependencies
`GET /api/v1/monitoring/traces/dependencies`

### Get Trace Breakdown
`POST /api/v1/monitoring/traces/{trace_id}/breakdown`

### Get Critical Path
`POST /api/v1/monitoring/traces/{trace_id}/critical-path`

### Get Span Statistics
`POST /api/v1/monitoring/traces/stats`

For detailed API documentation, see [API Reference](./api-reference-monitoring.md).
