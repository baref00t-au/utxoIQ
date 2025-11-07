# Deployment Infrastructure

This directory contains tools and configurations for canary deployments with automated rollback.

## Overview

The deployment system implements:
- **Canary deployments** with 10% traffic routing
- **Automated rollback** based on error rate and latency thresholds
- **OpenAPI schema validation** to prevent breaking changes
- **Deployment monitoring** with Grafana dashboards
- **Metrics instrumentation** for deployment tracking

## Components

### 1. Canary Monitor (`canary-monitor.py`)

Python script that monitors canary deployments and triggers automated rollback if thresholds are exceeded.

**Usage:**
```bash
python canary-monitor.py \
  --project-id utxoiq-project \
  --region us-central1 \
  --service utxoiq-web-api \
  --revision web-api-canary-abc123 \
  --duration 15 \
  --interval 60 \
  --error-rate-threshold 1.0 \
  --latency-threshold 60000
```

**Parameters:**
- `--project-id`: GCP project ID
- `--region`: GCP region (e.g., us-central1)
- `--service`: Service name (e.g., utxoiq-web-api)
- `--revision`: Canary revision name
- `--duration`: Monitoring duration in minutes (default: 15)
- `--interval`: Check interval in seconds (default: 60)
- `--error-rate-threshold`: Max error rate % (default: 1.0)
- `--latency-threshold`: Max P95 latency in ms (default: 60000)

**Thresholds:**
- Error rate: 1% (triggers rollback if exceeded)
- P95 latency: 60 seconds (triggers rollback if exceeded)
- P99 latency: 120 seconds (triggers rollback if exceeded)
- Minimum requests: 100 (before evaluation)

### 2. Deployment Metrics (`metrics.py`)

Prometheus metrics instrumentation for deployment tracking.

**Metrics:**
- `deployment_started_total`: Total deployments started
- `deployment_success_total`: Total successful deployments
- `deployment_rollback_total`: Total rollbacks
- `deployment_duration_seconds`: Deployment duration histogram
- `deployment_canary_duration_seconds`: Canary monitoring duration
- `deployment_started_timestamp`: Deployment start timestamp
- `deployment_rollback_timestamp`: Rollback timestamp
- `deployment_current_revision`: Current deployed revision info
- `deployment_canary_traffic_percentage`: Canary traffic percentage
- `openapi_schema_validation_total`: OpenAPI validation results
- `openapi_breaking_changes_total`: Breaking changes detected

**Usage in services:**
```python
from infrastructure.deployment.metrics import DeploymentMetrics

metrics = DeploymentMetrics()

# Record deployment start
metrics.record_deployment_start(
    service="web-api",
    environment="production",
    deployment_type="canary",
    revision="web-api-canary-abc123"
)

# Record success
metrics.record_deployment_success(
    service="web-api",
    environment="production",
    deployment_type="canary",
    duration_seconds=900.0
)

# Record rollback
metrics.record_deployment_rollback(
    service="web-api",
    environment="production",
    reason="Error rate exceeded threshold"
)
```

### 3. GitHub Actions Workflow

The `.github/workflows/canary-deployment.yml` workflow automates:
1. Service change detection
2. OpenAPI schema validation
3. Container image building
4. Canary deployment with traffic routing
5. Metrics monitoring
6. Automated rollback or promotion

**Workflow triggers:**
- Push to `main` branch (auto-detects changed services)
- Manual workflow dispatch (specify service)

**Environment variables:**
- `GCP_PROJECT_ID`: GCP project ID
- `GCP_REGION`: Deployment region (default: us-central1)
- `CANARY_TRAFFIC_PERCENTAGE`: Traffic to canary (default: 10%)
- `CANARY_DURATION_MINUTES`: Monitoring duration (default: 15)
- `ERROR_RATE_THRESHOLD`: Max error rate (default: 1.0%)
- `LATENCY_P95_THRESHOLD_MS`: Max P95 latency (default: 60000ms)

### 4. Grafana Dashboard

The `deployment-status.json` dashboard provides:
- Active canary deployments count
- Canary error rate gauge
- Canary P95 latency gauge
- Deployment status table
- Traffic split visualization
- Error rate comparison (canary vs stable)
- Latency comparison (canary vs stable)
- Recent deployment logs
- Rollback events counter
- Deployment success rate

**Access:** http://localhost:3000/d/deployment-status

## Setup

### Prerequisites

1. **GCP Project** with Cloud Run and Cloud Monitoring enabled
2. **Service Account** with permissions:
   - `run.admin`
   - `monitoring.viewer`
   - `logging.viewer`
3. **GitHub Secrets** configured:
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY` (service account JSON key)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Test canary monitor
python canary-monitor.py --help
```

### Grafana Dashboard Setup

```bash
# Import dashboard to Grafana
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @../grafana/dashboards/deployment-status.json
```

## Deployment Process

### Automatic Deployment (Push to main)

1. Push changes to `main` branch
2. Workflow detects changed services
3. Validates OpenAPI schema (for web-api)
4. Builds and pushes container images
5. Deploys canary with 10% traffic
6. Monitors for 15 minutes
7. Automatically rolls back if thresholds exceeded
8. Promotes to 100% if successful

### Manual Deployment

```bash
# Trigger workflow manually
gh workflow run canary-deployment.yml \
  -f service=web-api \
  -f skip_canary=false
```

### Direct Deployment (Skip Canary)

```bash
# Deploy directly without canary
gh workflow run canary-deployment.yml \
  -f service=web-api \
  -f skip_canary=true
```

## Monitoring

### View Deployment Status

```bash
# Check Cloud Run services
gcloud run services list --region us-central1

# Check specific service revisions
gcloud run revisions list \
  --service utxoiq-web-api \
  --region us-central1

# Check traffic split
gcloud run services describe utxoiq-web-api \
  --region us-central1 \
  --format 'value(status.traffic)'
```

### View Metrics

```bash
# Query deployment metrics
gcloud monitoring time-series list \
  --filter 'metric.type="run.googleapis.com/request_count"' \
  --format json

# View Prometheus metrics
curl http://localhost:8000/metrics
```

### View Logs

```bash
# View deployment logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json

# View canary logs
gcloud logging read "resource.labels.revision_name=~\".*-canary-.*\"" \
  --limit 50
```

## Rollback Procedures

### Automatic Rollback

Rollback is triggered automatically if:
- Error rate > 1%
- P95 latency > 60 seconds
- P99 latency > 120 seconds

The workflow will:
1. Route all traffic back to stable revision
2. Delete canary revision
3. Create GitHub commit status with failure reason
4. Record rollback metrics

### Manual Rollback

```bash
# List revisions
gcloud run revisions list \
  --service utxoiq-web-api \
  --region us-central1

# Route traffic to specific revision
gcloud run services update-traffic utxoiq-web-api \
  --region us-central1 \
  --to-revisions REVISION_NAME=100

# Delete canary revision
gcloud run revisions delete CANARY_REVISION \
  --region us-central1 \
  --quiet
```

## Troubleshooting

### Canary Not Receiving Traffic

Check traffic split:
```bash
gcloud run services describe utxoiq-web-api \
  --region us-central1 \
  --format 'value(status.traffic)'
```

### High Error Rate

View error logs:
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 100
```

### Rollback Failed

Manually route traffic:
```bash
gcloud run services update-traffic utxoiq-web-api \
  --region us-central1 \
  --to-latest
```

### OpenAPI Validation Failed

View breaking changes:
```bash
# Check workflow logs
gh run view --log

# Compare schemas manually
openapi-diff openapi-previous.json openapi-current.json
```

## Best Practices

1. **Always validate OpenAPI schema** before deploying web-api
2. **Monitor canary for at least 15 minutes** to collect sufficient data
3. **Set appropriate thresholds** based on service SLAs
4. **Use feature flags** for risky changes
5. **Test in staging** before production deployment
6. **Document rollback procedures** for each service
7. **Review deployment metrics** regularly
8. **Keep canary traffic low** (10%) to minimize impact

## Requirements Mapping

This implementation satisfies:
- **Requirement 22.1**: Canary deployment with 10% traffic routing
- **Requirement 22.2**: Error rate monitoring during canary
- **Requirement 22.3**: Automated rollback when error rate > 1%
- **Requirement 22.4**: OpenAPI schema compatibility validation
- **Requirement 22.5**: Deployment status dashboard with rollback controls

## References

- [Cloud Run Traffic Management](https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)
- [Cloud Monitoring API](https://cloud.google.com/monitoring/api/v3)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)
