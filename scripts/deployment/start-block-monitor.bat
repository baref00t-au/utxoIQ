@echo off
REM Start block monitor in background using Windows Task Scheduler

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set VENV_PYTHON=%PROJECT_DIR%\venv312\Scripts\python.exe
set MONITOR_SCRIPT=%SCRIPT_DIR%block-monitor.py
set LOG_FILE=%PROJECT_DIR%\logs\block-monitor.log

REM Create logs directory if it doesn't exist
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Get Bitcoin RPC password from .env
for /f "tokens=2 delims==" %%a in ('findstr "BITCOIN_RPC_PASSWORD" "%PROJECT_DIR%\.env"') do set BITCOIN_RPC_PASSWORD=%%a

REM Start monitor
echo Starting Bitcoin Block Monitor...
echo Log file: %LOG_FILE%
echo.

"%VENV_PYTHON%" "%MONITOR_SCRIPT%" ^
  --rpc-url "http://umbrel:%BITCOIN_RPC_PASSWORD%@umbrel.local:8332" ^
  --feature-engine-url "https://feature-engine-544291059247.us-central1.run.app" ^
  --poll-interval 10 >> "%LOG_FILE%" 2>&1
