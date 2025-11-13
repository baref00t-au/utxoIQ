@echo off
echo Deploying web-api to utxoiq-dev...
echo.

cd services\web-api

gcloud run deploy utxoiq-web-api-dev --source . --region us-central1 --platform managed --allow-unauthenticated --memory 1Gi --cpu 1 --min-instances 0 --max-instances 10 --timeout 300 --set-env-vars=ENVIRONMENT=development,FIREBASE_PROJECT_ID=utxoiq,GCP_PROJECT_ID=utxoiq-dev,BIGQUERY_DATASET_INTEL=intel,BIGQUERY_DATASET_BTC=btc,VERTEX_AI_LOCATION=us-central1 --set-cloudsql-instances=utxoiq-dev:us-central1:utxoiq-db-dev --project utxoiq-dev

cd ..\..

echo.
echo Deployment complete! Get the URL with:
echo gcloud run services describe utxoiq-web-api-dev --region us-central1 --format="value(status.url)" --project utxoiq-dev
