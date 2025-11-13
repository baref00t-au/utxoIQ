@echo off
REM Rebuild and restart development environment

echo Rebuilding utxoIQ development environment...
echo.

echo Stopping containers...
docker-compose down

echo.
echo Rebuilding images...
docker-compose build --no-cache

echo.
echo Starting containers...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak > nul

echo.
echo Service Status:
docker-compose ps

echo.
echo Tailing logs (Ctrl+C to stop)...
docker-compose logs -f web-api frontend
