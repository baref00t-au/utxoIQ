#!/bin/bash
# Deploy complete signal-insight pipeline to Google Cloud Run
# This deploys both utxoiq-ingestion and insight-generator services

set -e

echo "========================================"
echo "Deploying Signal-Insight Pipeline"
echo "========================================"
echo ""
echo "This will deploy:"
echo "  1. utxoiq-ingestion - Block monitoring and signal generation"
echo "  2. insight-generator - AI-powered insight generation"
echo ""

# Set variables
PROJECT_ID=${GCP_PROJECT_ID:-utxoiq-dev}
REGION=${GCP_REGION:-us-central1}

echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Confirm deployment
read -p "Deploy both services? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "========================================"
echo "Step 1: Deploying utxoiq-ingestion"
echo "========================================"
echo ""

# Deploy utxoiq-ingestion
cd services/utxoiq-ingestion

gcloud run deploy utxoiq-ingestion \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --min-instances 1 \
    --max-instances 3 \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET_BTC=btc,BIGQUERY_DATASET_INTEL=intel

cd ../..

echo ""
echo "========================================"
echo "Step 2: Deploying insight-generator"
echo "========================================"
echo ""

# Deploy insight-generator
cd services/insight-generator

gcloud run deploy insight-generator \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 5 \
    --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,DATASET_INTEL=intel,POLL_INTERVAL_SECONDS=10,CONFIDENCE_THRESHOLD=0.7

cd ../..

echo ""
echo "========================================"
echo "Pipeline Deployment Complete!"
echo "========================================"
echo ""
echo "Both services have been deployed successfully."
echo ""
echo "Next steps:"
echo "  1. Configure environment variables in Cloud Run console"
echo "  2. Set up Cloud Secret Manager for API keys"
echo "  3. Configure auto-scaling and resource limits"
echo "  4. Test the complete pipeline end-to-end"
echo ""
echo "Service URLs:"
echo "  utxoiq-ingestion: https://utxoiq-ingestion-544291059247.$REGION.run.app"
echo "  insight-generator: https://insight-generator-544291059247.$REGION.run.app"
echo ""
echo "Health checks:"
echo "  curl https://utxoiq-ingestion-544291059247.$REGION.run.app/health"
echo "  curl https://insight-generator-544291059247.$REGION.run.app/health"
echo ""
echo "To view logs for both services:"
echo "  gcloud logging tail \"resource.type=cloud_run_revision\""
echo ""
