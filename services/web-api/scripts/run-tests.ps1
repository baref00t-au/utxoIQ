# Test runner script for web-api service (PowerShell)
# Sets up Docker containers, runs migrations, and executes tests

$ErrorActionPreference = "Stop"

Write-Host "Starting test environment setup..." -ForegroundColor Cyan

# Change to web-api directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptPath "..")

try {
    Write-Host "Starting Docker containers..." -ForegroundColor Yellow
    docker-compose -f docker-compose.test.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start Docker containers"
    }
    
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check container status
    docker-compose -f docker-compose.test.yml ps
    
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    alembic upgrade head
    
    if ($LASTEXITCODE -ne 0) {
        throw "Migration failed"
    }
    
    Write-Host "Running tests..." -ForegroundColor Yellow
    python -m pytest tests/test_endpoint_protection_simple.py -v --tb=short
    
    $testResult = $LASTEXITCODE
    
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    docker-compose -f docker-compose.test.yml down
    
    if ($testResult -ne 0) {
        Write-Host "Tests failed" -ForegroundColor Red
        exit $testResult
    } else {
        Write-Host "All tests passed!" -ForegroundColor Green
        exit 0
    }
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    docker-compose -f docker-compose.test.yml down
    exit 1
}
