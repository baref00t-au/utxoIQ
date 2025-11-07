# utxoIQ Grafana Observability Dashboard

This directory contains the Grafana and Prometheus configuration for monitoring the utxoIQ platform.

## Overview

The observability stack includes:
- **Grafana**: Visualization and dashboarding
- **Prometheus**: Metrics collection and storage
- **Google Cloud Monitoring**: GCP-native metrics integration

## Dashboards

### 1. Performance Monitoring (`performance-monitoring.json`)
Tracks system performance and SLA compliance:
- Block-to-insight P95 latency (60-second threshold)
- API uptime (99.9% SLA target)
- WebSocket connection stability (< 5% disconnection rate)
- Duplicate signal rate (< 0.5% threshold)
- API request rate by endpoint

**Requirements**: 1.1, 6.5, 7.3, 14.2

### 2. Cost Tracking & Analytics (`cost-tracking.json`)
Monitors infrastructure and AI costs:
- AI inference costs per hour by signal type
- Daily AI cost with $1000 budget alert
- BigQuery cost per hour
- Daily BigQuery cost with $500 budget alert
- BigQuery query performance (P95 latency)
- Daily cost breakdown by signal type
- Cost per insight trend analysis

**Requirements**: 14.3, 23.1, 23.2, 23.3, 23.4, 23.5

### 3. Accuracy & Feedback (`accuracy-feedback.json`)
Tracks insight quality and user feedback:
- Insight accuracy by signal type (user feedback)
- Public accuracy leaderboard by model version
- Predictive signal accuracy tracking
- User feedback volume by signal type
- Error rate by type with correlation IDs
- Top 10 errors by correlation ID
- Overall insight accuracy trend

**Requirements**: 14.4, 14.5, 15.4, 17.4

## Alert Rules

### SLA Alerts (`alerts/sla-alerts.yml`)
- **HighBlockToInsightLatency**: P95 latency > 60 seconds
- **LowAPIUptime**: Uptime < 99.9%
- **HighWebSocketDisconnectionRate**: Disconnection rate > 5%
- **HighDuplicateSignalRate**: Duplicate rate > 0.5%
- **HighAPIErrorRate**: Error rate > 1%
- **ServiceDown**: Service unavailable for > 2 minutes

### Cost Alerts (`alerts/cost-alerts.yml`)
- **HighDailyAICost**: Daily AI cost > $1000
- **HighDailyBigQueryCost**: Daily BigQuery cost > $500
- **AIInferenceCostSpike**: Hourly AI cost > $50
- **ExpensiveBigQueryQuery**: Single query cost > $10
- **IncreasingCostPerInsight**: Cost per insight trending upward
- **HighTotalDailyCost**: Combined daily cost > $1500

## Setup

### Prerequisites
- Docker and Docker Compose
- GCP project with Cloud Monitoring API enabled
- Service account with monitoring permissions

### Environment Variables

Create a `.env` file in this directory:

```bash
# Grafana Admin Credentials
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password

# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GCP_SERVICE_ACCOUNT_KEY=path/to/service-account-key.json
```

### Local Development

Start the observability stack:

```bash
# Start Grafana and Prometheus
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the dashboards:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

Default Grafana credentials:
- Username: `admin`
- Password: `admin` (change on first login)

### Production Deployment

For production, deploy to GCP:

```bash
# Deploy Grafana to Cloud Run
gcloud run deploy utxoiq-grafana \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=${GCP_PROJECT_ID}

# Configure Cloud Monitoring integration
gcloud monitoring dashboards create --config-from-file=dashboards/performance-monitoring.json
gcloud monitoring dashboards create --config-from-file=dashboards/cost-tracking.json
gcloud monitoring dashboards create --config-from-file=dashboards/accuracy-feedback.json
```

## Metrics Instrumentation

### Required Metrics

Services must expose the following Prometheus metrics at `/metrics`:

#### Performance Metrics
```python
# Block-to-insight latency histogram
block_to_insight_latency_seconds = Histogram(
    'block_to_insight_latency_seconds',
    'Time from block detection to insight publication',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'code', 'job']
)

# WebSocket connection metrics
websocket_connections_total = Counter('websocket_connections_total', 'Total WebSocket connections')
websocket_disconnections_total = Counter('websocket_disconnections_total', 'Total WebSocket disconnections')

# Signal quality metrics
signals_generated_total = Counter('signals_generated_total', 'Total signals generated', ['signal_type'])
duplicate_signals_total = Counter('duplicate_signals_total', 'Total duplicate signals', ['signal_type'])
```

#### Cost Metrics
```python
# AI inference costs
ai_inference_cost_usd = Counter(
    'ai_inference_cost_usd',
    'AI inference cost in USD',
    ['signal_type', 'model_version']
)

# BigQuery costs
bigquery_cost_usd = Counter('bigquery_cost_usd', 'BigQuery cost in USD', ['query_type'])
bigquery_query_cost_usd = Gauge('bigquery_query_cost_usd', 'Individual query cost', ['query_id'])
bigquery_query_duration_seconds = Histogram(
    'bigquery_query_duration_seconds',
    'BigQuery query duration',
    ['query_type'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60]
)

# Insight generation metrics
insights_generated_total = Counter('insights_generated_total', 'Total insights generated', ['signal_type'])
```

#### Accuracy Metrics
```python
# User feedback metrics
user_feedback_total = Counter('user_feedback_total', 'Total user feedback', ['signal_type', 'model_version'])
user_feedback_useful_total = Counter(
    'user_feedback_useful_total',
    'Total useful feedback',
    ['signal_type', 'model_version']
)

# Prediction accuracy metrics
predictions_evaluated_total = Counter(
    'predictions_evaluated_total',
    'Total predictions evaluated',
    ['prediction_type']
)
prediction_accurate_total = Counter(
    'prediction_accurate_total',
    'Total accurate predictions',
    ['prediction_type']
)

# Error tracking metrics
api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['correlation_id', 'error_type', 'error_message']
)
```

### Example Implementation

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response

app = FastAPI()

# Define metrics
block_to_insight_latency_seconds = Histogram(
    'block_to_insight_latency_seconds',
    'Time from block detection to insight publication',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/process-block")
async def process_block(block_data: dict):
    with block_to_insight_latency_seconds.time():
        # Process block and generate insight
        result = await generate_insight(block_data)
    return result
```

## Dashboard Customization

### Adding New Panels

1. Edit the dashboard JSON file
2. Add a new panel object to the `panels` array
3. Configure the query, visualization, and thresholds
4. Restart Grafana to load changes

### Modifying Alert Thresholds

1. Edit the alert YAML file in `alerts/`
2. Update the `expr` field with new threshold values
3. Restart Prometheus to reload alert rules

## Troubleshooting

### Grafana Not Starting
- Check Docker logs: `docker-compose logs grafana`
- Verify environment variables in `.env`
- Ensure port 3000 is not in use

### Missing Metrics
- Verify services are exposing `/metrics` endpoint
- Check Prometheus targets: http://localhost:9090/targets
- Review Prometheus configuration in `prometheus.yml`

### GCP Integration Issues
- Verify service account has `monitoring.viewer` role
- Check GCP project ID is correct
- Ensure Cloud Monitoring API is enabled

## Maintenance

### Backup Dashboards
```bash
# Export all dashboards
docker exec utxoiq-grafana grafana-cli admin export-dashboard > backup.json
```

### Update Grafana
```bash
# Pull latest image
docker-compose pull grafana

# Restart with new image
docker-compose up -d grafana
```

## References

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Google Cloud Monitoring](https://cloud.google.com/monitoring/docs)
- [utxoIQ Requirements](../../.kiro/specs/utxoiq-mvp/requirements.md)
- [utxoIQ Design](../../.kiro/specs/utxoiq-mvp/design.md)
