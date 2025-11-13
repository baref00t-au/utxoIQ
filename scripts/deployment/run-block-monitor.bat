@echo off
REM Run block monitor locally on Windows

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set VENV_PYTHON=%PROJECT_DIR%\venv312\Scripts\python.exe
set MONITOR_SCRIPT=%SCRIPT_DIR%block-monitor.py

REM Get Bitcoin RPC password from .env (handle special characters)
for /f "usebackq tokens=1,* delims==" %%a in ("%PROJECT_DIR%\.env") do (
    if "%%a"=="BITCOIN_RPC_PASSWORD" set "BITCOIN_RPC_PASSWORD=%%b"
)

REM Configuration
set "BITCOIN_RPC_URL=http://umbrel:%BITCOIN_RPC_PASSWORD%@umbrel.local:8332"
set FEATURE_ENGINE_URL=https://utxoiq-ingestion-544291059247.us-central1.run.app
set POLL_INTERVAL=10

echo ============================================================
echo utxoIQ Block Monitor (Local)
echo ============================================================
echo.
echo Bitcoin RPC: umbrel.local:8332
echo Ingestion Service: %FEATURE_ENGINE_URL%
echo Poll Interval: %POLL_INTERVAL% seconds
echo.
echo Starting monitor... (Press Ctrl+C to stop)
echo.

REM Run monitor
"%VENV_PYTHON%" "%MONITOR_SCRIPT%" ^
  --rpc-url "%BITCOIN_RPC_URL%" ^
  --feature-engine-url "%FEATURE_ENGINE_URL%" ^
  --poll-interval %POLL_INTERVAL%

pause
