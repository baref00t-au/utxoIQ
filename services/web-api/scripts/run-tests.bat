@echo off
REM Test runner script for web-api service (Windows)
REM Sets up Docker containers, runs migrations, and executes tests

setlocal enabledelayedexpansion

echo Starting test environment setup...

REM Change to web-api directory
cd /d "%~dp0\.."

echo Starting Docker containers...
docker-compose -f docker-compose.test.yml up -d

if errorlevel 1 (
    echo Failed to start Docker containers
    exit /b 1
)

echo Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check if containers are running
docker-compose -f docker-compose.test.yml ps

echo Running database migrations...
alembic upgrade head

if errorlevel 1 (
    echo Migration failed
    docker-compose -f docker-compose.test.yml down
    exit /b 1
)

echo Running tests...
python -m pytest tests/test_endpoint_protection_simple.py -v --tb=short

set TEST_RESULT=%errorlevel%

echo Cleaning up...
docker-compose -f docker-compose.test.yml down

if %TEST_RESULT% neq 0 (
    echo Tests failed
    exit /b %TEST_RESULT%
) else (
    echo All tests passed!
    exit /b 0
)
