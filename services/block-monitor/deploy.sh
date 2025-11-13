#!/bin/bash
# Deploy block monitor to Cloud Run with Tor support

set -e

PROJECT_ID="utxoiq-dev"
REGION="us-central1"
SERVICE_NAME="block-monitor"

# Get Bitcoin RPC password from user
read -sp "Enter Bitcoin RPC password: " BITCOIN_RPC_PASSWORD
echo

# Construct RPC URL with Tor hidden service
BITCOIN_RPC_URL="http://umbrel:${BITCOIN_RPC_PASSWORD}@hkps5arunnwerusagmrcktq76pjlej4dgenqipavkkprmozj37txqwyd.onion:8332"

echo "Deploying block monitor to Cloud Run..."
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  Using Tor: Yes"
echo

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --project=$PROJECT_ID \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --timeout=3600 \
  --min-instances=1 \
  --max-instances=1 \
  --set-env-vars="BITCOIN_RPC_URL=${BITCOIN_RPC_URL},FEATURE_ENGINE_URL=https://feature-engine-544291059247.us-central1.run.app,POLL_INTERVAL=10" \
  --no-cpu-throttling

echo
echo "✅ Deployment complete!"
echo
echo "Service URL: https://${SERVICE_NAME}-544291059247.${REGION}.run.app"
echo
echo "Check status:"
echo "  curl https://${SERVICE_NAME}-544291059247.${REGION}.run.app/health"
echo "  curl https://${SERVICE_NAME}-544291059247.${REGION}.run.app/status"
echo
echo "View logs:"
echo "  gcloud logging read 'resource.labels.service_name=${SERVICE_NAME}' --limit 50 --project=${PROJECT_ID}"
