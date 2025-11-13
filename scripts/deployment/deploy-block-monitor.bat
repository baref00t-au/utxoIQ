@echo off
REM Deploy block-monitor service to Google Cloud Run

echo ========================================
echo Deploying block-monitor to Cloud Run
echo ========================================

REM Set variables
set PROJECT_ID=utxoiq-dev
set SERVICE_NAME=block-monitor
set REGION=us-central1
set SERVICE_DIR=services\block-monitor

echo.
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
    --memory 512Mi ^
    --cpu 1 ^
    --timeout 3600 ^
    --min-instances 1 ^
    --max-instances 1 ^
    --set-env-vars BITCOIN_RPC_URL=%BITCOIN_RPC_URL%,FEATURE_ENGINE_URL=%FEATURE_ENGINE_URL%,MEMPOOL_API_URL=%MEMPOOL_API_URL%,POLL_INTERVAL=%POLL_INTERVAL%

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
echo To view logs:
echo   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=%SERVICE_NAME%" --limit 50 --format json
echo.
echo To check status:
echo   curl https://%SERVICE_NAME%-544291059247.%REGION%.run.app/status
echo.

pause
