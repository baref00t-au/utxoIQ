@echo off
REM Setup Cloud SQL for web-api
REM Usage: scripts\setup-cloud-sql.bat [dev|prod]

set ENV=%1
if "%ENV%"=="" set ENV=dev

if "%ENV%"=="prod" (
    set PROJECT_ID=utxoiq
    set INSTANCE_NAME=utxoiq-db
    set DB_TIER=db-n1-standard-1
    echo Setting up PRODUCTION Cloud SQL...
) else (
    set PROJECT_ID=utxoiq-dev
    set INSTANCE_NAME=utxoiq-db-dev
    set DB_TIER=db-f1-micro
    echo Setting up DEVELOPMENT Cloud SQL...
)

echo.
set REGION=us-central1
set DB_NAME=utxoiq
set DB_USER=utxoiq-user

REM Generate a random password
set DB_PASSWORD=utxoiq_%RANDOM%%RANDOM%

echo ========================================
echo Cloud SQL Setup
echo ========================================
echo.
echo Project: %PROJECT_ID%
echo Instance: %INSTANCE_NAME%
echo Region: %REGION%
echo Tier: %DB_TIER%
echo Database: %DB_NAME%
echo User: %DB_USER%
echo.
echo This will take 5-10 minutes...
echo.

REM Check if instance already exists
gcloud sql instances describe %INSTANCE_NAME% --project=%PROJECT_ID% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Instance %INSTANCE_NAME% already exists!
    echo.
    echo To use existing instance, get connection details:
    echo   gcloud sql instances describe %INSTANCE_NAME% --project=%PROJECT_ID%
    echo.
    echo To delete and recreate:
    echo   gcloud sql instances delete %INSTANCE_NAME% --project=%PROJECT_ID%
    echo.
    exit /b 0
)

echo Step 1/4: Creating Cloud SQL instance...
gcloud sql instances create %INSTANCE_NAME% ^
  --database-version=POSTGRES_14 ^
  --tier=%DB_TIER% ^
  --region=%REGION% ^
  --root-password=%DB_PASSWORD% ^
  --storage-type=SSD ^
  --storage-size=10GB ^
  --storage-auto-increase ^
  --backup-start-time=03:00 ^
  --maintenance-window-day=SUN ^
  --maintenance-window-hour=04 ^
  --project=%PROJECT_ID%

if %ERRORLEVEL% NEQ 0 (
    echo Failed to create Cloud SQL instance!
    exit /b 1
)

echo.
echo Step 2/4: Creating database...
gcloud sql databases create %DB_NAME% ^
  --instance=%INSTANCE_NAME% ^
  --project=%PROJECT_ID%

if %ERRORLEVEL% NEQ 0 (
    echo Failed to create database!
    exit /b 1
)

echo.
echo Step 3/4: Creating database user...
gcloud sql users create %DB_USER% ^
  --instance=%INSTANCE_NAME% ^
  --password=%DB_PASSWORD% ^
  --project=%PROJECT_ID%

if %ERRORLEVEL% NEQ 0 (
    echo Failed to create user!
    exit /b 1
)

echo.
echo Step 4/4: Getting connection details...
for /f "delims=" %%i in ('gcloud sql instances describe %INSTANCE_NAME% --format="value(connectionName)" --project=%PROJECT_ID%') do set CONNECTION_NAME=%%i

echo.
echo ========================================
echo Cloud SQL Setup Complete!
echo ========================================
echo.
echo Connection Name: %CONNECTION_NAME%
echo Database: %DB_NAME%
echo User: %DB_USER%
echo Password: %DB_PASSWORD%
echo.
echo IMPORTANT: Save these credentials securely!
echo.
echo Connection String:
echo postgresql://%DB_USER%:%DB_PASSWORD%@/%DB_NAME%?host=/cloudsql/%CONNECTION_NAME%
echo.
echo Next steps:
echo.
echo 1. Store password in Secret Manager:
echo    echo %DB_PASSWORD% ^| gcloud secrets create db-password --data-file=- --project=%PROJECT_ID%
echo.
echo 2. Update web-api environment:
echo    Add to deployment: --set-cloudsql-instances=%CONNECTION_NAME%
echo.
echo 3. Deploy web-api:
echo    scripts\deploy-web-api.bat %ENV%
echo.
echo 4. Run database migrations:
echo    Connect to Cloud SQL and run migrations from services/web-api/migrations/
echo.

REM Save credentials to file
echo # Cloud SQL Credentials > cloud-sql-credentials.txt
echo PROJECT_ID=%PROJECT_ID% >> cloud-sql-credentials.txt
echo INSTANCE_NAME=%INSTANCE_NAME% >> cloud-sql-credentials.txt
echo CONNECTION_NAME=%CONNECTION_NAME% >> cloud-sql-credentials.txt
echo DB_NAME=%DB_NAME% >> cloud-sql-credentials.txt
echo DB_USER=%DB_USER% >> cloud-sql-credentials.txt
echo DB_PASSWORD=%DB_PASSWORD% >> cloud-sql-credentials.txt

echo Credentials saved to: cloud-sql-credentials.txt
echo.
