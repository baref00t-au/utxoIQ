# Monitoring Best Practices Guide

## Overview

This guide provides best practices for implementing effective monitoring, alerting, and observability in the utxoIQ platform. Follow these guidelines to ensure reliable, performant, and maintainable monitoring systems.

## Monitoring Strategy

### The Four Golden Signals

Monitor these key metrics for every service:

#### 1. Latency
Time taken to service a request.

**Metrics to track**:
- API response time (p50, p95, p99)
- Database query duration
- External API call latency
- Background job processing time

**Best practices**:
- Track percentiles, not just averages
- Set different thresholds for different endpoints
- Monitor both successful and failed requests
- Alert on p95 or p99, not average

#### 2. Traffic
Demand on your system.

**Metrics to track**:
- Requests per second
- Active connections
- Queue depth
- Concurrent users

**Best practices**:
- Track trends over time
- Identify peak usage patterns
- Plan capacity based on traffic
- Alert on unusual spikes or drops

#### 3. Errors
Rate of failed requests.

**Metrics to track**:
- Error rate (percentage)
- Error count by type
- HTTP 5xx responses
- Exception counts

**Best practices**:
- Track error rate, not just count
- Categorize errors by type
- Alert on error rate increases
- Distinguish between client and server errors

#### 4. Saturation
How "full" your service is.

**Metrics to track**:
- CPU utilization
- Memory usage
- Disk space
- Network bandwidth
- Connection pool usage

**Best practices**:
- Monitor resource utilization
- Set alerts before exhaustion
- Track growth trends
- Plan capacity proactively

## Alert Configuration

### Alert Design Principles

#### 1. Actionable Alerts
Every alert should require action.

**Good alert**:
```
API response time > 1000ms for 5 minutes
Action: Investigate slow queries, check database
```

**Bad alert**:
```
CPU usage > 50%
Action: None (50% is normal)
```

#### 2. Clear Severity Levels

**Info**: Informational, no action needed
- Deployment notifications
- Configuration changes
- Scheduled maintenance

**Warning**: Investigate within 1 hour
- Elevated latency
- Increased error rate
- Resource usage approaching limits

**Critical**: Immediate response required
- Service down
- Database connection failures
- Critical resource exhaustion

#### 3. Avoid Alert Fatigue

**Strategies**:
- Set appropriate thresholds
- Use evaluation windows to reduce noise
- Consolidate related alerts
- Suppress alerts during maintenance
- Review and tune regularly

### Threshold Selection

#### Start Conservative
Begin with higher thresholds and adjust based on false positives.

**Example progression**:
1. Initial: API latency > 2000ms
2. After tuning: API latency > 1000ms
3. Final: API latency > 500ms (p95)

#### Use Historical Data
Base thresholds on actual performance data.

```bash
# Get baseline statistics
curl -X POST https://api.utxoiq.com/api/v1/monitoring/metrics/baseline \
  -d '{
    "metric": "api_response_time",
    "days": 7
  }'
```

Use p95 or p99 as threshold baseline.

#### Account for Patterns
Different thresholds for different times:

- Peak hours: Higher thresholds
- Off-peak hours: Lower thresholds
- Weekends: Different patterns
- Seasonal variations: Adjust accordingly

### Notification Strategy

#### Multi-Channel Approach

**Email**: All severities, detailed information
- Includes charts and context
- Good for audit trail
- Review at convenience

**Slack**: Warning and critical, team awareness
- Real-time notifications
- Team collaboration
- Quick acknowledgment

**SMS**: Critical only, immediate attention
- On-call engineers
- Service outages
- Critical failures

#### Escalation Policy

Progressive notification for unacknowledged alerts:

```json
{
  "escalation_policy": {
    "steps": [
      {
        "delay_minutes": 0,
        "channels": ["email", "slack"]
      },
      {
        "delay_minutes": 5,
        "channels": ["sms"],
        "recipients": ["primary_oncall"]
      },
      {
        "delay_minutes": 15,
        "channels": ["sms"],
        "recipients": ["secondary_oncall"]
      }
    ]
  }
}
```

## Dashboard Design

### Dashboard Principles

#### 1. Purpose-Driven
Each dashboard should have a clear purpose:

- **Service Health**: Overall system status
- **Performance**: Latency and throughput
- **Errors**: Error tracking and debugging
- **Capacity**: Resource utilization and planning
- **Business**: User activity and engagement

#### 2. Hierarchy of Information
Organize information by importance:

**Top**: Critical metrics (error rate, latency, availability)
**Middle**: Supporting metrics (traffic, resource usage)
**Bottom**: Detailed metrics (per-endpoint stats)

#### 3. Consistent Layout
Use consistent layouts across dashboards:

```
┌─────────────────────────────────────┐
│  Critical Metrics (Stat Cards)      │
├─────────────────────────────────────┤
│  Trend Charts (Line/Area)           │
├─────────────────────────────────────┤
│  Comparisons (Bar Charts)           │
├─────────────────────────────────────┤
│  Details (Tables)                   │
└─────────────────────────────────────┘
```

### Widget Selection

#### Line Charts
**Use for**: Trends over time
**Best for**: Latency, traffic, error rate
**Time range**: 1h to 7d

#### Bar Charts
**Use for**: Comparisons
**Best for**: Requests by endpoint, errors by type
**Time range**: 1h to 24h

#### Gauges
**Use for**: Current status
**Best for**: CPU, memory, disk usage
**Time range**: Real-time (5m)

#### Stat Cards
**Use for**: Key metrics
**Best for**: Current values with trends
**Time range**: 5m with comparison

#### Tables
**Use for**: Detailed data
**Best for**: Top endpoints, error details
**Time range**: 1h to 24h

### Dashboard Examples

#### Service Health Dashboard

```json
{
  "name": "Service Health",
  "widgets": [
    {
      "type": "stat_card",
      "title": "Availability",
      "metric": "uptime_percentage",
      "time_range": "24h"
    },
    {
      "type": "stat_card",
      "title": "Error Rate",
      "metric": "error_rate",
      "time_range": "5m"
    },
    {
      "type": "line_chart",
      "title": "Response Time (p95)",
      "metric": "response_time_p95",
      "time_range": "24h"
    },
    {
      "type": "line_chart",
      "title": "Request Rate",
      "metric": "request_rate",
      "time_range": "24h"
    }
  ]
}
```

## Logging Best Practices

### Log Levels

#### DEBUG
Detailed information for debugging.

**Use for**:
- Variable values
- Function entry/exit
- Detailed state information

**Example**:
```python
logger.debug(f"Processing block {block_height} with {tx_count} transactions")
```

#### INFO
General informational messages.

**Use for**:
- Service startup/shutdown
- Configuration changes
- Successful operations

**Example**:
```python
logger.info(f"Successfully processed block {block_height}")
```

#### WARNING
Warning messages for potential issues.

**Use for**:
- Deprecated API usage
- Fallback to default values
- Recoverable errors

**Example**:
```python
logger.warning(f"Cache miss for key {key}, fetching from database")
```

#### ERROR
Error messages for failures.

**Use for**:
- Failed operations
- Exceptions
- Data validation errors

**Example**:
```python
logger.error(f"Failed to connect to database: {error}", exc_info=True)
```

#### CRITICAL
Critical errors requiring immediate attention.

**Use for**:
- Service failures
- Data corruption
- Security breaches

**Example**:
```python
logger.critical(f"Database connection pool exhausted")
```

### Structured Logging

Use structured logging for better searchability:

```python
logger.info(
    "Request processed",
    extra={
        "trace_id": trace_id,
        "user_id": user_id,
        "endpoint": "/api/v1/insights",
        "method": "POST",
        "status_code": 200,
        "duration_ms": 145
    }
)
```

### Log Context

Include context in every log:

```python
logger.error(
    "Failed to generate insight",
    extra={
        "trace_id": trace_id,
        "block_height": block_height,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "retry_count": retry_count
    },
    exc_info=True
)
```

### What to Log

**Always log**:
- Request/response for API calls
- Database queries (with duration)
- External API calls
- Errors and exceptions
- Authentication events
- Configuration changes

**Never log**:
- Passwords or secrets
- API keys or tokens
- Personal identifiable information (PII)
- Credit card numbers
- Full request/response bodies (unless necessary)

## Distributed Tracing

### Instrumentation Strategy

#### Trace All External Calls

```python
@tracer.start_as_current_span("database.query")
def query_database(query: str):
    span = trace.get_current_span()
    span.set_attribute("db.statement", query)
    span.set_attribute("db.system", "postgresql")
    
    result = execute_query(query)
    
    span.set_attribute("db.rows_affected", len(result))
    return result
```

#### Add Meaningful Attributes

```python
span.set_attribute("user_id", user_id)
span.set_attribute("block_height", block_height)
span.set_attribute("cache_hit", cache_hit)
span.set_attribute("retry_count", retry_count)
```

#### Use Consistent Naming

**Format**: `service.operation`

**Examples**:
- `web-api.handle_request`
- `feature-engine.compute_signals`
- `bigquery.query`
- `redis.get`

### Trace Analysis Workflow

1. **Identify slow requests**: Find traces > 1s
2. **Analyze critical path**: Find longest span chain
3. **Check span durations**: Identify bottlenecks
4. **Review attributes**: Look for patterns
5. **Correlate with logs**: Get detailed context
6. **Optimize**: Focus on critical path

## Performance Optimization

### Metric Collection

#### Sampling Strategy
- **High-frequency metrics**: Sample at 1-minute intervals
- **Low-frequency metrics**: Sample at 5-minute intervals
- **Expensive metrics**: Sample at 15-minute intervals

#### Aggregation
Pre-aggregate metrics to reduce query load:

```python
# Instead of querying raw data
SELECT AVG(response_time) FROM metrics WHERE timestamp > NOW() - INTERVAL '1 hour'

# Use pre-aggregated data
SELECT avg_response_time FROM metrics_1m WHERE timestamp > NOW() - INTERVAL '1 hour'
```

#### Caching
Cache frequently accessed metrics:

```python
@cache(ttl=60)  # Cache for 1 minute
def get_current_metrics(service: str):
    return fetch_metrics(service)
```

### Dashboard Performance

#### Limit Widgets
Maximum 12-15 widgets per dashboard.

#### Optimize Queries
- Use appropriate time ranges
- Leverage pre-aggregated data
- Add proper indexes
- Use caching

#### Lazy Loading
Load widgets as they come into view:

```typescript
<LazyLoad height={300}>
  <MetricChart metric="response_time" />
</LazyLoad>
```

## Incident Response

### Incident Workflow

1. **Detection**: Alert triggers
2. **Acknowledgment**: On-call engineer acknowledges
3. **Investigation**: Review metrics, logs, traces
4. **Mitigation**: Apply fix or workaround
5. **Resolution**: Verify issue is resolved
6. **Post-mortem**: Document and learn

### Investigation Checklist

When an alert triggers:

1. **Check dashboard**: Review service health dashboard
2. **Review recent changes**: Check deployments, config changes
3. **Examine logs**: Search for errors around alert time
4. **Analyze traces**: Find slow or failed requests
5. **Check dependencies**: Review downstream service health
6. **Correlate metrics**: Look for related metric changes

### Communication

#### During Incident
- Acknowledge alert immediately
- Update status page
- Notify stakeholders
- Document actions taken

#### After Resolution
- Send resolution notification
- Update status page
- Schedule post-mortem
- Document lessons learned

## Capacity Planning

### Trend Analysis

Monitor growth trends:

```bash
# Get 30-day trend
curl -X POST https://api.utxoiq.com/api/v1/monitoring/metrics/trend \
  -d '{
    "metric": "request_rate",
    "time_range": "30d",
    "projection_days": 90
  }'
```

### Resource Planning

#### CPU
- Alert at 70% utilization
- Plan capacity at 80% utilization
- Scale before reaching 90%

#### Memory
- Alert at 80% utilization
- Plan capacity at 85% utilization
- Scale before reaching 90%

#### Disk
- Alert at 70% utilization
- Plan capacity at 80% utilization
- Scale before reaching 85%

### Growth Projections

Calculate when resources will be exhausted:

```python
def calculate_exhaustion_date(current_usage, growth_rate, capacity):
    """
    Calculate when resource will be exhausted.
    
    Args:
        current_usage: Current resource usage (e.g., 70%)
        growth_rate: Monthly growth rate (e.g., 5%)
        capacity: Maximum capacity (e.g., 90%)
    
    Returns:
        Months until exhaustion
    """
    remaining = capacity - current_usage
    months = remaining / growth_rate
    return months
```

## Security Monitoring

### Authentication Events

Log all authentication events:

```python
logger.info(
    "User login",
    extra={
        "user_id": user_id,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": True
    }
)
```

### Failed Login Attempts

Alert on suspicious patterns:

```json
{
  "alert": "Multiple Failed Logins",
  "threshold": "5 failed attempts in 5 minutes",
  "action": "Lock account and notify security team"
}
```

### API Key Usage

Monitor API key usage:

```python
logger.info(
    "API key used",
    extra={
        "api_key_id": api_key_id,
        "endpoint": endpoint,
        "ip_address": ip_address,
        "rate_limit_remaining": rate_limit_remaining
    }
)
```

### Anomaly Detection

Alert on unusual patterns:
- Unusual traffic spikes
- Requests from new locations
- Unusual API usage patterns
- Elevated error rates

## Compliance and Auditing

### Audit Logging

Log all significant events:

```python
audit_logger.info(
    "Configuration changed",
    extra={
        "user_id": user_id,
        "action": "update_alert_config",
        "resource_id": alert_id,
        "changes": changes,
        "timestamp": datetime.utcnow()
    }
)
```

### Data Retention

**Metrics**: 90 days in hot storage, 1 year in cold storage
**Logs**: 30 days in hot storage, 90 days in cold storage
**Traces**: 30 days in hot storage, 90 days in cold storage
**Audit logs**: 1 year in hot storage, 7 years in cold storage

### Compliance Requirements

Ensure monitoring meets compliance requirements:

- **GDPR**: Don't log PII without consent
- **PCI DSS**: Don't log credit card numbers
- **HIPAA**: Encrypt logs containing health data
- **SOC 2**: Maintain audit trails

## Continuous Improvement

### Regular Reviews

#### Weekly
- Review alert frequency
- Check for false positives
- Tune thresholds
- Update dashboards

#### Monthly
- Analyze incident patterns
- Review capacity trends
- Update documentation
- Train team members

#### Quarterly
- Review monitoring strategy
- Evaluate new tools
- Update best practices
- Conduct training sessions

### Metrics for Monitoring

Monitor your monitoring system:

- **Alert frequency**: Alerts per day
- **False positive rate**: False positives / total alerts
- **Mean time to detect (MTTD)**: Time to detect issues
- **Mean time to resolve (MTTR)**: Time to resolve issues
- **Dashboard usage**: Dashboard views per day
- **Query performance**: Dashboard load time

### Feedback Loop

Continuously improve based on incidents:

1. **Document incidents**: Record what happened
2. **Identify gaps**: What monitoring was missing?
3. **Add metrics**: Fill monitoring gaps
4. **Update alerts**: Improve alert accuracy
5. **Share learnings**: Update documentation

## Checklist

### New Service Monitoring

- [ ] Implement Four Golden Signals
- [ ] Add distributed tracing
- [ ] Configure structured logging
- [ ] Create service dashboard
- [ ] Set up alerts
- [ ] Document runbooks
- [ ] Test alert notifications
- [ ] Review with team

### Alert Configuration

- [ ] Define clear severity levels
- [ ] Set actionable thresholds
- [ ] Configure notification channels
- [ ] Set up escalation policy
- [ ] Test alert delivery
- [ ] Document response procedures
- [ ] Review and tune regularly

### Dashboard Creation

- [ ] Define dashboard purpose
- [ ] Select appropriate widgets
- [ ] Configure data sources
- [ ] Set appropriate time ranges
- [ ] Test performance
- [ ] Share with team
- [ ] Document usage

## Resources

### Documentation
- [Alert Configuration Guide](./monitoring-alert-configuration.md)
- [Notification Channels Setup](./monitoring-notification-channels.md)
- [Custom Dashboards Guide](./monitoring-custom-dashboards.md)
- [Log Search Guide](./monitoring-log-search.md)
- [Distributed Tracing Guide](./monitoring-distributed-tracing.md)

### Tools
- Google Cloud Monitoring
- Google Cloud Logging
- Google Cloud Trace
- BigQuery for analytics
- Grafana for visualization

### Support
- Documentation: https://docs.utxoiq.com
- Support: support@utxoiq.com
- Status Page: https://status.utxoiq.com
