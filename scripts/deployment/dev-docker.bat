@echo off
REM Development environment startup script for Windows

echo Starting utxoIQ development environment in Docker...
echo.

REM Stop any existing containers
echo Stopping existing containers...
docker-compose down

REM Build and start all services
echo Building and starting services...
docker-compose up --build -d

REM Wait for services to be healthy
echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak > nul

REM Show service status
echo.
echo Service Status:
docker-compose ps

REM Show logs
echo.
echo Tailing logs (Ctrl+C to stop)...
echo.
docker-compose logs -f frontend web-api
