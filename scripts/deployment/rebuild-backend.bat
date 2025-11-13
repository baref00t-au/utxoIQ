@echo off
REM Rebuild just the backend service

echo Rebuilding web-api service...
docker-compose build web-api

echo.
echo Restarting web-api...
docker-compose up -d web-api

echo.
echo Checking logs...
timeout /t 3 /nobreak > nul
docker-compose logs --tail=50 web-api
