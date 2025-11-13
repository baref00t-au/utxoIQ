#!/bin/bash
# Setup Cloud Scheduler for automatic cleanup of old blocks

set -e

PROJECT_ID="utxoiq-dev"
REGION="us-central1"
SERVICE_URL="https://feature-engine-544291059247.us-central1.run.app"

echo "Setting up Cloud Scheduler for automatic cleanup..."

# Create Cloud Scheduler job
gcloud scheduler jobs create http cleanup-old-blocks \
  --location=$REGION \
  --schedule="*/30 * * * *" \
  --uri="$SERVICE_URL/cleanup?hours=2" \
  --http-method=POST \
  --oidc-service-account-email="544291059247-compute@developer.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL" \
  --project=$PROJECT_ID \
  --description="Clean up blocks older than 2 hours from custom dataset" \
  --time-zone="UTC" \
  --attempt-deadline=300s \
  --max-retry-attempts=3 \
  --min-backoff=30s \
  --max-backoff=300s

echo "✅ Cloud Scheduler job created successfully!"
echo ""
echo "Job details:"
echo "  Name: cleanup-old-blocks"
echo "  Schedule: Every 30 minutes"
echo "  Endpoint: $SERVICE_URL/cleanup?hours=2"
echo "  Timezone: UTC"
echo ""
echo "To view the job:"
echo "  gcloud scheduler jobs describe cleanup-old-blocks --location=$REGION --project=$PROJECT_ID"
echo ""
echo "To manually trigger the job:"
echo "  gcloud scheduler jobs run cleanup-old-blocks --location=$REGION --project=$PROJECT_ID"
