@echo off
REM Restart development environment

echo Restarting utxoIQ development environment...
echo.

echo Stopping containers...
docker-compose down

echo.
echo Starting containers...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 5 /nobreak > nul

echo.
echo Service Status:
docker-compose ps

echo.
echo View logs with: docker-compose logs -f
