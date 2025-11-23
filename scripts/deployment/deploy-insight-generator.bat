@echo off
REM Deploy insight-generator service to Google Cloud Run
REM This service polls BigQuery for unprocessed signals and generates AI insights

echo ========================================
echo Deploying insight-generator to Cloud Run
echo ========================================
echo.
echo This service includes:
echo   - Signal polling from BigQuery
echo   - AI-powered insight generation
echo   - Multi-provider support (Vertex AI, OpenAI, Anthropic, Grok)
echo   - Insight persistence to BigQuery
echo.

REM Set variables
set PROJECT_ID=utxoiq-dev
set SERVICE_NAME=insight-generator
set REGION=us-central1
set SERVICE_DIR=services\insight-generator

echo Project: %PROJECT_ID%
echo Service: %SERVICE_NAME%
echo Region: %REGION%
echo.

REM Check if .env file exists (optional - can configure via Cloud Run console)
if not exist "%SERVICE_DIR%\.env" (
    echo WARNING: .env file not found in %SERVICE_DIR%
    echo Environment variables will need to be configured in Cloud Run console after deployment
    echo Press Ctrl+C to cancel or any key to continue...
    pause >nul
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
echo.

cd %SERVICE_DIR%

call gcloud run deploy %SERVICE_NAME% ^
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
echo IMPORTANT: Configure AI provider in Cloud Run console:
echo   1. Go to: https://console.cloud.google.com/run/detail/%REGION%/%SERVICE_NAME%/variables
echo   2. Add environment variables for your chosen AI provider:
echo.
echo   For Vertex AI (recommended):
echo      - AI_PROVIDER=vertex_ai
echo      - VERTEX_AI_PROJECT=%PROJECT_ID%
echo      - VERTEX_AI_LOCATION=us-central1
echo.
echo   For OpenAI:
echo      - AI_PROVIDER=openai
echo      - OPENAI_API_KEY=sk-... (use Secret Manager)
echo      - OPENAI_MODEL=gpt-4-turbo
echo.
echo   For Anthropic:
echo      - AI_PROVIDER=anthropic
echo      - ANTHROPIC_API_KEY=sk-ant-... (use Secret Manager)
echo      - ANTHROPIC_MODEL=claude-3-opus-20240229
echo.
echo   For xAI Grok:
echo      - AI_PROVIDER=grok
echo      - GROK_API_KEY=xai-... (use Secret Manager)
echo      - GROK_MODEL=grok-beta
echo.
echo To view logs:
echo   gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=%SERVICE_NAME%"
echo.
echo To check health:
echo   curl https://%SERVICE_NAME%-544291059247.%REGION%.run.app/health
echo.
echo To manually trigger a polling cycle:
echo   curl -X POST https://%SERVICE_NAME%-544291059247.%REGION%.run.app/trigger-cycle
echo.
echo To view stats:
echo   curl https://%SERVICE_NAME%-544291059247.%REGION%.run.app/stats
echo.

pause
