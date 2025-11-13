@echo off
REM Deploy web-api to Cloud Run (Windows)
REM Usage: 
REM   scripts\deploy-web-api.bat dev      (deploys to utxoiq-dev)
REM   scripts\deploy-web-api.bat prod     (deploys to utxoiq)

REM Get environment argument (default to dev)
set ENV=%1
if "%ENV%"=="" set ENV=dev

REM Configuration based on environment
if "%ENV%"=="prod" (
    set PROJECT_ID=utxoiq
    set SERVICE_NAME=utxoiq-web-api
    set ENVIRONMENT=production
    echo Deploying to PRODUCTION (utxoiq)...
) else (
    set PROJECT_ID=utxoiq-dev
    set SERVICE_NAME=utxoiq-web-api-dev
    set ENVIRONMENT=development
    echo Deploying to DEVELOPMENT (utxoiq-dev)...
)

echo.
set REGION=us-central1

REM Navigate to web-api directory
cd services\web-api

REM Set Cloud SQL connection name
if "%ENV%"=="prod" (
    set SQL_INSTANCE=utxoiq:us-central1:utxoiq-db
) else (
    set SQL_INSTANCE=utxoiq-dev:us-central1:utxoiq-db-dev
)

echo Deploying with Cloud SQL: %SQL_INSTANCE%
echo.

REM Deploy to Cloud Run
gcloud run deploy %SERVICE_NAME% ^
  --source . ^
  --region %REGION% ^
  --platform managed ^
  --allow-unauthenticated ^
  --memory 1Gi ^
  --cpu 1 ^
  --min-instances 0 ^
  --max-instances 10 ^
  --timeout 300 ^
  --set-env-vars=ENVIRONMENT=%ENVIRONMENT%,FIREBASE_PROJECT_ID=utxoiq,GCP_PROJECT_ID=%PROJECT_ID%,BIGQUERY_DATASET_INTEL=intel,BIGQUERY_DATASET_BTC=btc,VERTEX_AI_LOCATION=us-central1 ^
  --set-cloudsql-instances=%SQL_INSTANCE% ^
  --project %PROJECT_ID%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Deployment failed!
    cd ..\..
    exit /b 1
)

REM Get the service URL
for /f "delims=" %%i in ('gcloud run services describe %SERVICE_NAME% --region %REGION% --format="value(status.url)" --project %PROJECT_ID%') do set SERVICE_URL=%%i

echo.
echo ========================================
echo Deployment complete!
echo ========================================
echo.
echo Service URL: %SERVICE_URL%
echo.
echo API Documentation:
echo    Swagger UI: %SERVICE_URL%/docs
echo    ReDoc: %SERVICE_URL%/redoc
echo.
echo Test the service:
echo    curl %SERVICE_URL%/health
echo.
REM Create WebSocket URL
set WS_URL=%SERVICE_URL:https=wss%

echo Next steps:
if "%ENV%"=="prod" (
    echo    1. Update frontend\.env.production with:
    echo       NEXT_PUBLIC_API_URL=%SERVICE_URL%
    echo       NEXT_PUBLIC_WS_URL=%WS_URL%
    echo       NEXT_PUBLIC_USE_MOCK_DATA=false
    echo.
    echo    2. Deploy frontend to production
) else (
    echo    1. Update frontend\.env.local with:
    echo       NEXT_PUBLIC_API_URL=%SERVICE_URL%
    echo       NEXT_PUBLIC_WS_URL=%WS_URL%
    echo       NEXT_PUBLIC_USE_MOCK_DATA=false
    echo.
    echo    2. Restart your Next.js dev server
)
echo.
echo    3. Test authentication by signing in
echo.

cd ..\..
