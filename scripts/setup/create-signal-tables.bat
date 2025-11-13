@echo off
REM Create BigQuery tables for signal-to-insight pipeline
REM Usage: create-signal-tables.bat [project-id]

setlocal enabledelayedexpansion

REM Get project ID from argument or environment
set PROJECT_ID=%1
if "%PROJECT_ID%"=="" set PROJECT_ID=%GCP_PROJECT_ID%

if "%PROJECT_ID%"=="" (
    echo Error: Project ID not provided
    echo Usage: %0 [project-id]
    echo Or set GCP_PROJECT_ID environment variable
    exit /b 1
)

echo Creating BigQuery tables for project: %PROJECT_ID%
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set SCHEMA_DIR=%SCRIPT_DIR%..\..\infrastructure\bigquery\schemas

REM Create datasets if they don't exist
echo Ensuring datasets exist...
bq mk --dataset --project_id=%PROJECT_ID% intel 2>nul || echo Dataset intel already exists
bq mk --dataset --project_id=%PROJECT_ID% btc 2>nul || echo Dataset btc already exists
echo.

REM Create intel.signals table
echo Creating table: intel.signals
bq query --project_id=%PROJECT_ID% --use_legacy_sql=false < "%SCHEMA_DIR%\intel_signals.sql"
if %errorlevel% equ 0 (
    echo Successfully created intel.signals
) else (
    echo Failed to create intel.signals
    exit /b 1
)
echo.

REM Create intel.insights table
echo Creating table: intel.insights
bq query --project_id=%PROJECT_ID% --use_legacy_sql=false < "%SCHEMA_DIR%\intel_insights.sql"
if %errorlevel% equ 0 (
    echo Successfully created intel.insights
) else (
    echo Failed to create intel.insights
    exit /b 1
)
echo.

REM Create btc.known_entities table
echo Creating table: btc.known_entities
bq query --project_id=%PROJECT_ID% --use_legacy_sql=false < "%SCHEMA_DIR%\btc_known_entities.sql"
if %errorlevel% equ 0 (
    echo Successfully created btc.known_entities
) else (
    echo Failed to create btc.known_entities
    exit /b 1
)
echo.

REM Verify tables were created
echo Verifying tables...
echo.

echo Tables in intel dataset:
bq ls --project_id=%PROJECT_ID% intel

echo.
echo Tables in btc dataset:
bq ls --project_id=%PROJECT_ID% btc

echo.
echo All tables created successfully!
echo.
echo Next steps:
echo 1. Populate known entities: python scripts\populate_treasury_entities.py
echo 2. Deploy utxoiq-ingestion service
echo 3. Deploy insight-generator service

endlocal
