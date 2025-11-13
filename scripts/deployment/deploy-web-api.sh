#!/bin/bash

# Deploy web-api to Cloud Run
# Usage: ./scripts/deploy-web-api.sh

set -e

echo "🚀 Deploying utxoiq-web-api to Cloud Run..."

# Configuration
PROJECT_ID="utxoiq-dev"
SERVICE_NAME="utxoiq-web-api"
REGION="us-central1"

# Navigate to web-api directory
cd services/web-api

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars="ENVIRONMENT=production,FIREBASE_PROJECT_ID=utxoiq,GCP_PROJECT_ID=utxoiq-dev,BIGQUERY_DATASET_INTEL=intel,BIGQUERY_DATASET_BTC=btc,VERTEX_AI_LOCATION=us-central1,CORS_ORIGINS=http://localhost:3000,https://utxoiq.com" \
  --project $PROJECT_ID

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format="value(status.url)" \
  --project $PROJECT_ID)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Service URL: $SERVICE_URL"
echo ""
echo "🔗 API Documentation:"
echo "   Swagger UI: $SERVICE_URL/docs"
echo "   ReDoc: $SERVICE_URL/redoc"
echo ""
echo "🧪 Test the service:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "📝 Next steps:"
echo "   1. Update frontend/.env.local with:"
echo "      NEXT_PUBLIC_API_URL=$SERVICE_URL"
echo "      NEXT_PUBLIC_WS_URL=${SERVICE_URL/https/wss}"
echo "      NEXT_PUBLIC_USE_MOCK_DATA=false"
echo ""
echo "   2. Restart your Next.js dev server"
echo ""
echo "   3. Test authentication by signing in"
echo ""

cd ../..
