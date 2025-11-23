@echo off
REM Deploy complete signal-insight pipeline to Google Cloud Run
REM This deploys both utxoiq-ingestion and insight-generator services

echo ========================================
echo Deploying Signal-Insight Pipeline
echo ========================================
echo.
echo This will deploy:
echo   1. utxoiq-ingestion - Block monitoring and signal generation
echo   2. insight-generator - AI-powered insight generation
echo.

REM Set variables
set PROJECT_ID=utxoiq-dev
set REGION=us-central1

echo Project: %PROJECT_ID%
echo Region: %REGION%
echo.

REM Confirm deployment
set /p CONFIRM="Deploy both services? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Deployment cancelled
    exit /b 0
)

echo.
echo ========================================
echo Step 1: Deploying utxoiq-ingestion
echo ========================================
echo.

REM Deploy utxoiq-ingestion directly without calling the other script
cd services\utxoiq-ingestion

echo Deploying utxoiq-ingestion to Cloud Run...
echo.

call gcloud run deploy utxoiq-ingestion ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 1Gi ^
    --cpu 1 ^
    --timeout 3600 ^
    --min-instances 1 ^
    --max-instances 3 ^
    --set-env-vars GCP_PROJECT_ID=%PROJECT_ID%,BIGQUERY_DATASET_BTC=btc,BIGQUERY_DATASET_INTEL=intel

cd ..\..

if errorlevel 1 (
    echo ERROR: Failed to deploy utxoiq-ingestion
    exit /b 1
)

echo utxoiq-ingestion deployed successfully!
if errorlevel 1 (
    echo ERROR: Failed to deploy utxoiq-ingestion
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Deploying insight-generator
echo ========================================
echo.

REM Deploy insight-generator directly without calling the other script
cd services\insight-generator

echo Deploying insight-generator to Cloud Run...
echo.

call gcloud run deploy insight-generator ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --memory 2Gi ^
    --cpu 1 ^
    --timeout 300 ^
    --min-instances 1 ^
    --max-instances 5 ^
    --set-env-vars GCP_PROJECT_ID=%PROJECT_ID%,DATASET_INTEL=intel,POLL_INTERVAL_SECONDS=10,CONFIDENCE_THRESHOLD=0.7

cd ..\..

if errorlevel 1 (
    echo ERROR: Failed to deploy insight-generator
    exit /b 1
)

echo insight-generator deployed successfully!
if errorlevel 1 (
    echo ERROR: Failed to deploy insight-generator
    exit /b 1
)

echo.
echo ========================================
echo Pipeline Deployment Complete!
echo ========================================
echo.
echo Both services have been deployed successfully!
echo.
echo IMPORTANT: Configure additional environment variables in Cloud Run console:
echo.
echo For utxoiq-ingestion (optional - for Bitcoin Core monitoring):
echo   1. Go to Cloud Run console: https://console.cloud.google.com/run
echo   2. Select utxoiq-ingestion service
echo   3. Click "Edit & Deploy New Revision"
echo   4. Add environment variables:
echo      - BITCOIN_RPC_URL (if using Bitcoin Core)
echo      - MEMPOOL_API_URL (default: https://mempool.space/api)
echo      - POLL_INTERVAL (default: 30)
echo.
echo For insight-generator (REQUIRED - choose AI provider):
echo   1. Go to Cloud Run console: https://console.cloud.google.com/run
echo   2. Select insight-generator service
echo   3. Click "Edit & Deploy New Revision"
echo   4. Add environment variables for your AI provider:
echo.
echo      Vertex AI (recommended):
echo        AI_PROVIDER=vertex_ai
echo        VERTEX_AI_PROJECT=%PROJECT_ID%
echo        VERTEX_AI_LOCATION=us-central1
echo.
echo      OR OpenAI:
echo        AI_PROVIDER=openai
echo        OPENAI_API_KEY=sk-... (use Secret Manager)
echo        OPENAI_MODEL=gpt-4-turbo
echo.
echo Health checks:
echo   gcloud run services describe utxoiq-ingestion --region=%REGION% --format="value(status.url)"
echo   gcloud run services describe insight-generator --region=%REGION% --format="value(status.url)"
echo.
echo To view logs:
echo   gcloud logging tail "resource.type=cloud_run_revision"
echo.
echo See docs/signal-insight-pipeline-deployment.md for complete configuration guide
echo.

pause
