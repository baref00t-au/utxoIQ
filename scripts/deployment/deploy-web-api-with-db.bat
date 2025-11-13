@echo off
echo Deploying web-api to utxoiq-dev with database...
echo.

cd services\web-api

gcloud run deploy utxoiq-web-api-dev ^
  --source . ^
  --region us-central1 ^
  --platform managed ^
  --allow-unauthenticated ^
  --memory 1Gi ^
  --cpu 1 ^
  --min-instances 0 ^
  --max-instances 10 ^
  --timeout 300 ^
  --set-env-vars="ENVIRONMENT=development,FIREBASE_PROJECT_ID=utxoiq,GCP_PROJECT_ID=utxoiq-dev,BIGQUERY_DATASET_INTEL=intel,BIGQUERY_DATASET_BTC=btc,VERTEX_AI_LOCATION=us-central1,CLOUD_SQL_CONNECTION_NAME=utxoiq-dev:us-central1:utxoiq-db-dev,DB_USER=postgres,DB_PASSWORD=utxoiq_SecurePass123!,DB_NAME=utxoiq,DB_HOST=127.0.0.1,DB_PORT=5432,STRIPE_SECRET_KEY=sk_test_dummy,STRIPE_WEBHOOK_SECRET=whsec_dummy" ^
  --set-cloudsql-instances=utxoiq-dev:us-central1:utxoiq-db-dev ^
  --project utxoiq-dev

cd ..\..

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Deployment successful!
    echo ========================================
    echo.
    echo Get the service URL:
    gcloud run services describe utxoiq-web-api-dev --region us-central1 --format="value(status.url)" --project utxoiq-dev
)
