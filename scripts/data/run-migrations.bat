@echo off
echo Running Alembic migrations on Cloud SQL...
echo.

cd services\web-api

REM Set environment variables for Cloud SQL connection
set CLOUD_SQL_CONNECTION_NAME=utxoiq-dev:us-central1:utxoiq-db-dev
set DB_USER=postgres
set DB_PASSWORD=utxoiq_SecurePass123!
set DB_NAME=utxoiq
set DB_HOST=127.0.0.1
set DB_PORT=5432
set ENVIRONMENT=development
set GCP_PROJECT_ID=utxoiq-dev
set FIREBASE_PROJECT_ID=utxoiq

echo Starting Cloud SQL Proxy...
start /B cloud-sql-proxy utxoiq-dev:us-central1:utxoiq-db-dev

REM Wait for proxy to start
timeout /t 5 /nobreak

echo Running Alembic migrations...
alembic upgrade head

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Migrations completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Migration failed!
    echo ========================================
)

REM Stop Cloud SQL Proxy
taskkill /F /IM cloud-sql-proxy.exe 2>nul

cd ..\..
