#!/bin/bash
# Deploy database monitoring dashboard and alert policies to Google Cloud Monitoring

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-project}"
DASHBOARD_FILE="database-dashboard.json"
ALERT_POLICIES_FILE="alert-policies.yaml"

echo "Deploying database monitoring to project: $PROJECT_ID"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID"

# Create dashboard
echo "Creating Cloud Monitoring dashboard..."
DASHBOARD_ID=$(gcloud monitoring dashboards create --config-from-file="$DASHBOARD_FILE" --format="value(name)")
echo "Dashboard created: $DASHBOARD_ID"

# Parse and create alert policies
echo "Creating alert policies..."

# Note: Alert policies need to be created via API or gcloud commands
# The YAML file serves as documentation and can be used with Terraform

echo "Alert policies configuration available in: $ALERT_POLICIES_FILE"
echo "To create alert policies, use Terraform or the Cloud Console"

# Create notification channels (example)
echo ""
echo "To create notification channels, run:"
echo "  gcloud alpha monitoring channels create \\"
echo "    --display-name='Database Alerts Email' \\"
echo "    --type=email \\"
echo "    --channel-labels=email_address=alerts@utxoiq.com"

echo ""
echo "Monitoring deployment complete!"
echo "Dashboard URL: https://console.cloud.google.com/monitoring/dashboards/custom/$DASHBOARD_ID?project=$PROJECT_ID"
