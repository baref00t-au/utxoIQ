# Grafana Observability Deployment Guide

This guide covers deploying the utxoIQ observability stack to production on Google Cloud Platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     GCP Production                           │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Services   │─────▶│  Prometheus  │                    │
│  │  (Cloud Run) │      │  (GKE/VM)    │                    │
│  └──────────────┘      └──────┬───────┘                    │
│         │                     │                             │
│         │                     ▼                             │
│         │              ┌──────────────┐                     │
│         └─────────────▶│   Grafana    │                     │
│                        │  (Cloud Run) │                     │
│                        └──────┬───────┘                     │
│                               │                             │
│                               ▼                             │
│                        ┌──────────────┐                     │
│                        │    Cloud     │                     │
│                        │  Monitoring  │                     │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **GCP Project**: Active GCP project with billing enabled
2. **APIs Enabled**:
   - Cloud Run API
   - Cloud Monitoring API
   - Cloud Logging API
   - Compute Engine API (for GKE)
3. **IAM Permissions**:
   - `roles/run.admin` - Deploy Cloud Run services
   - `roles/monitoring.admin` - Configure monitoring
   - `roles/iam.serviceAccountUser` - Service account management
4. **Tools Installed**:
   - `gcloud` CLI
   - `kubectl` (if using GKE)
   - `docker`

## Deployment Options

### Option 1: Managed Grafana (Recommended for Production)

Use Google Cloud's managed Grafana service for simplified operations.

```bash
# Enable Cloud Monitoring and Grafana
gcloud services enable monitoring.googleapis.com
gcloud services enable cloudprofiler.googleapis.com

# Create a managed Grafana workspace
gcloud monitoring dashboards create \
  --config-from-file=dashboards/performance-monitoring.json

gcloud monitoring dashboards create \
  --config-from-file=dashboards/cost-tracking.json

gcloud monitoring dashboards create \
  --config-from-file=dashboards/accuracy-feedback.json
```

### Option 2: Self-Hosted Grafana on Cloud Run

Deploy Grafana as a containerized service on Cloud Run.

#### Step 1: Build and Push Container

```bash
# Set variables
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1
export GRAFANA_IMAGE=gcr.io/${PROJECT_ID}/utxoiq-grafana

# Build container
docker build -t ${GRAFANA_IMAGE} -f Dockerfile.grafana .

# Push to Container Registry
docker push ${GRAFANA_IMAGE}
```

#### Step 2: Create Service Account

```bash
# Create service account for Grafana
gcloud iam service-accounts create utxoiq-grafana \
  --display-name="utxoIQ Grafana Service Account"

# Grant monitoring permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:utxoiq-grafana@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/monitoring.viewer"
```

#### Step 3: Deploy to Cloud Run

```bash
# Deploy Grafana
gcloud run deploy utxoiq-grafana \
  --image=${GRAFANA_IMAGE} \
  --region=${REGION} \
  --platform=managed \
  --service-account=utxoiq-grafana@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-secrets="GRAFANA_ADMIN_PASSWORD=grafana-admin-password:latest" \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=3

# Get the service URL
gcloud run services describe utxoiq-grafana \
  --region=${REGION} \
  --format='value(status.url)'
```

### Option 3: Self-Hosted on GKE

Deploy Grafana and Prometheus on Google Kubernetes Engine for full control.

#### Step 1: Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create utxoiq-monitoring \
  --region=${REGION} \
  --num-nodes=2 \
  --machine-type=n1-standard-2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5

# Get credentials
gcloud container clusters get-credentials utxoiq-monitoring --region=${REGION}
```

#### Step 2: Deploy with Helm

```bash
# Add Grafana Helm repository
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --create-namespace \
  --set server.persistentVolume.size=50Gi

# Install Grafana
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set persistence.enabled=true \
  --set persistence.size=10Gi \
  --set adminPassword=${GRAFANA_ADMIN_PASSWORD} \
  --values grafana-values.yaml
```

## Prometheus Deployment

### Cloud Run Services Configuration

Each service must expose metrics at `/metrics` endpoint:

```python
# Add to each FastAPI service
from infrastructure.grafana.metrics_instrumentation import setup_metrics_endpoint

app = FastAPI()
setup_metrics_endpoint(app)
```

### Prometheus Configuration

Deploy Prometheus to scrape metrics from Cloud Run services:

```bash
# Create Prometheus config with Cloud Run service discovery
cat > prometheus-cloudrun.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'feature-engine'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['feature-engine-xxxxx-uc.a.run.app']
  
  - job_name: 'insight-generator'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['insight-generator-xxxxx-uc.a.run.app']
  
  - job_name: 'web-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['web-api-xxxxx-uc.a.run.app']
EOF

# Deploy Prometheus
kubectl create configmap prometheus-config \
  --from-file=prometheus.yml=prometheus-cloudrun.yml \
  --namespace=monitoring

kubectl apply -f prometheus-deployment.yaml
```

## Alert Configuration

### Cloud Monitoring Alerts

Create alert policies in Cloud Monitoring:

```bash
# Create alert policy for high latency
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Block-to-Insight Latency" \
  --condition-display-name="P95 Latency > 60s" \
  --condition-threshold-value=60 \
  --condition-threshold-duration=300s \
  --condition-filter='metric.type="custom.googleapis.com/block_to_insight_latency_seconds"'

# Create alert policy for high cost
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Daily AI Cost" \
  --condition-display-name="Daily Cost > $1000" \
  --condition-threshold-value=1000 \
  --condition-threshold-duration=600s \
  --condition-filter='metric.type="custom.googleapis.com/ai_inference_cost_usd"'
```

### Notification Channels

Configure notification channels for alerts:

```bash
# Email notification
gcloud alpha monitoring channels create \
  --display-name="utxoIQ Ops Team" \
  --type=email \
  --channel-labels=email_address=ops@utxoiq.com

# Slack notification
gcloud alpha monitoring channels create \
  --display-name="utxoIQ Slack" \
  --type=slack \
  --channel-labels=url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Security Configuration

### Authentication

Enable authentication for Grafana:

```bash
# Create secret for admin password
echo -n "your-secure-password" | gcloud secrets create grafana-admin-password \
  --data-file=- \
  --replication-policy=automatic

# Grant access to service account
gcloud secrets add-iam-policy-binding grafana-admin-password \
  --member="serviceAccount:utxoiq-grafana@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Network Security

Configure Cloud Armor for DDoS protection:

```bash
# Create security policy
gcloud compute security-policies create grafana-security-policy \
  --description="Security policy for Grafana"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=grafana-security-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600
```

## Monitoring the Monitoring

Set up meta-monitoring to ensure observability stack health:

```bash
# Create uptime check for Grafana
gcloud monitoring uptime create grafana-uptime \
  --resource-type=uptime-url \
  --host=your-grafana-url.run.app \
  --path=/api/health

# Create alert for Grafana downtime
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Grafana Service Down" \
  --condition-display-name="Grafana Unhealthy" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=120s \
  --condition-filter='metric.type="monitoring.googleapis.com/uptime_check/check_passed"'
```

## Cost Optimization

### Reduce Metrics Cardinality

```python
# Limit label values to reduce cardinality
MAX_LABEL_VALUES = 100

def sanitize_label(value: str) -> str:
    """Sanitize label values to prevent cardinality explosion"""
    if len(value) > 50:
        return value[:50]
    return value
```

### Configure Retention Policies

```bash
# Set Prometheus retention to 15 days
kubectl patch deployment prometheus-server \
  --namespace=monitoring \
  --type=json \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--storage.tsdb.retention.time=15d"}]'
```

## Backup and Disaster Recovery

### Backup Grafana Dashboards

```bash
# Export all dashboards
for dashboard in $(curl -s http://grafana-url/api/search | jq -r '.[].uid'); do
  curl -s http://grafana-url/api/dashboards/uid/$dashboard | \
    jq '.dashboard' > backup-$dashboard.json
done

# Upload to Cloud Storage
gsutil -m cp backup-*.json gs://utxoiq-grafana-backups/$(date +%Y%m%d)/
```

### Restore Dashboards

```bash
# Download from Cloud Storage
gsutil -m cp gs://utxoiq-grafana-backups/latest/* .

# Import dashboards
for dashboard in backup-*.json; do
  curl -X POST http://grafana-url/api/dashboards/db \
    -H "Content-Type: application/json" \
    -d @$dashboard
done
```

## Troubleshooting

### High Cardinality Issues

```bash
# Check metric cardinality
curl http://prometheus-url/api/v1/status/tsdb | jq '.data.seriesCountByMetricName'

# Identify high-cardinality metrics
curl http://prometheus-url/api/v1/label/__name__/values | \
  jq -r '.data[]' | \
  xargs -I {} sh -c 'echo -n "{}: "; curl -s "http://prometheus-url/api/v1/query?query=count({})" | jq .data.result[0].value[1]'
```

### Missing Metrics

```bash
# Check Prometheus targets
curl http://prometheus-url/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check service metrics endpoint
curl https://your-service.run.app/metrics
```

### Dashboard Not Loading

```bash
# Check Grafana logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=utxoiq-grafana" \
  --limit=50 \
  --format=json

# Check datasource connectivity
curl http://grafana-url/api/datasources/proxy/1/api/v1/query?query=up
```

## Maintenance

### Update Dashboards

```bash
# Update dashboard in production
gcloud monitoring dashboards update DASHBOARD_ID \
  --config-from-file=dashboards/performance-monitoring.json
```

### Rotate Credentials

```bash
# Update Grafana admin password
gcloud secrets versions add grafana-admin-password \
  --data-file=new-password.txt

# Restart Grafana to pick up new secret
gcloud run services update utxoiq-grafana \
  --region=${REGION} \
  --update-secrets=GRAFANA_ADMIN_PASSWORD=grafana-admin-password:latest
```

## References

- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Grafana on GKE](https://cloud.google.com/architecture/deploying-grafana-on-gke)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
