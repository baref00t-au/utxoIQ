# Start the utxoIQ Web API
Write-Host "🚀 Starting utxoIQ Web API..." -ForegroundColor Cyan

# Change to web-api directory
Set-Location services\web-api

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found in services/web-api" -ForegroundColor Red
    exit 1
}

# Start the API
Write-Host "📡 Starting server on http://localhost:8080" -ForegroundColor Green
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
