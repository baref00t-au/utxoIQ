#!/bin/bash
# Deploy feature-engine service to Cloud Run

set -e

PROJECT_ID="utxoiq-dev"
SERVICE_NAME="feature-engine"
REGION="us-central1"

echo "="*60
echo "Deploying Feature Engine to Cloud Run"
echo "="*60
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Navigate to service directory
cd services/feature-engine

# Deploy to Cloud Run
echo "Deploying service..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format='value(status.url)')

echo ""
echo "="*60
echo "Deployment Complete!"
echo "="*60
echo "Service URL: $SERVICE_URL"
echo ""
echo "Test endpoints:"
echo "  Health: $SERVICE_URL/health"
echo "  Status: $SERVICE_URL/status"
echo "  Cleanup: $SERVICE_URL/cleanup (POST)"
echo ""
echo "Next steps:"
echo "  1. Test health endpoint"
echo "  2. Set up Cloud Scheduler for cleanup"
echo "  3. Configure monitoring alerts"
