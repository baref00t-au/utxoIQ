@echo off
REM Set up automatic cleanup using Cloud Scheduler

echo ========================================
echo Setting up Automatic Cleanup
echo ========================================
echo.

set PROJECT_ID=utxoiq-dev
set REGION=us-central1
set SERVICE_URL=https://utxoiq-ingestion-544291059247.us-central1.run.app/cleanup?hours=2

echo Project: %PROJECT_ID%
echo Region: %REGION%
echo Service URL: %SERVICE_URL%
echo.

REM Set GCP project
echo Setting GCP project...
call gcloud config set project %PROJECT_ID%

REM Create Cloud Scheduler job
echo.
echo Creating Cloud Scheduler job...
echo This will run cleanup every hour to maintain a 2-hour rolling window
echo.

call gcloud scheduler jobs create http cleanup-old-blocks ^
  --schedule="0 * * * *" ^
  --uri="%SERVICE_URL%" ^
  --http-method=POST ^
  --location=%REGION% ^
  --description="Clean up blocks older than 2 hours" ^
  --attempt-deadline=60s

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create scheduler job
    echo.
    echo Possible reasons:
    echo 1. Job already exists (use 'gcloud scheduler jobs update' instead)
    echo 2. Cloud Scheduler API not enabled
    echo 3. Insufficient permissions
    echo.
    echo To enable Cloud Scheduler API:
    echo   gcloud services enable cloudscheduler.googleapis.com
    echo.
    echo To update existing job:
    echo   gcloud scheduler jobs update http cleanup-old-blocks --schedule="0 * * * *" --location=%REGION%
    echo.
    exit /b 1
)

echo.
echo ========================================
echo Scheduler job created successfully!
echo ========================================
echo.
echo Schedule: Every hour at minute 0 (0 * * * *)
echo Action: Delete blocks older than 2 hours
echo.
echo To view the job:
echo   gcloud scheduler jobs describe cleanup-old-blocks --location=%REGION%
echo.
echo To run manually:
echo   gcloud scheduler jobs run cleanup-old-blocks --location=%REGION%
echo.
echo To pause:
echo   gcloud scheduler jobs pause cleanup-old-blocks --location=%REGION%
echo.
echo To resume:
echo   gcloud scheduler jobs resume cleanup-old-blocks --location=%REGION%
echo.
echo To delete:
echo   gcloud scheduler jobs delete cleanup-old-blocks --location=%REGION%
echo.

pause
