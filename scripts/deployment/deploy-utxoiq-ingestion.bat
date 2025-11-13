@echo off
REM Deploy utxoiq-ingestion service to Google Cloud Run
REM This is the UNIFIED service that handles:
REM - Block monitoring (via Umbrel + Tor)
REM - Fallback to mempool.space API
REM - Block ingestion to BigQuery
REM - Signal processing

echo ========================================
echo Deploying utxoiq-ingestion to Cloud Run
echo ========================================
echo.
echo This service includes:
echo   - Block monitoring via Tor
echo   - Automatic fallback to mempool.space
echo   - BigQuery ingestion
echo   - Signal processing
echo.

REM Set variables
set PROJECT_ID=utxoiq-dev
set SERVICE_NAME=utxoiq-ingestion
set REGION=us-central1
set SERVICE_DIR=services\utxoiq-ingestion

echo Project: %PROJECT_ID%
echo Service: %SERVICE_NAME%
echo Region: %REGION%
echo.

REM Check if .env file exists
if not exist "%SERVICE_DIR%\.env" (
    echo ERROR: .env file not found in %SERVICE_DIR%
    echo Please create .env file with required configuration
    exit /b 1
)

REM Set GCP project
echo Setting GCP project...
call gcloud config set project %PROJECT_ID%
if errorlevel 1 (
    echo ERROR: Failed to set GCP project
    exit /b 1
)

REM Build and deploy to Cloud Run
echo.
echo Building and deploying to Cloud Run...
echo This will include Tor in the container for .onion access
echo.

cd %SERVICE_DIR%

call gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 1Gi ^
    --cpu 1 ^
    --timeout 3600 ^
    --min-instances 1 ^
    --max-instances 3 ^
    --set-env-vars GCP_PROJECT_ID=%GCP_PROJECT_ID%,BIGQUERY_DATASET_BTC=btc,BIGQUERY_DATASET_INTEL=intel

if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed
    cd ..\..
    exit /b 1
)

cd ..\..

echo.
echo ========================================
echo Deployment completed successfully!
echo ========================================
echo.
echo Service URL will be displayed above
echo.
echo IMPORTANT: Set environment variables in Cloud Run console:
echo   1. Go to: https://console.cloud.google.com/run/detail/%REGION%/%SERVICE_NAME%/variables
echo   2. Add secret environment variables:
echo      - BITCOIN_RPC_URL (from .env file)
echo      - MEMPOOL_API_URL (from .env file)
echo      - POLL_INTERVAL (from .env file)
echo.
echo To view logs:
echo   gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=%SERVICE_NAME%"
echo.
echo To check status:
echo   curl https://%SERVICE_NAME%-544291059247.%REGION%.run.app/status
echo.
echo To verify block monitoring:
echo   curl https://%SERVICE_NAME%-544291059247.%REGION%.run.app/status
echo   (Look for "monitor" section with "running": true)
echo.

pause
