# utxoIQ Grafana Observability Setup Script (PowerShell)
# This script sets up the Grafana and Prometheus monitoring stack on Windows

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "utxoIQ Grafana Observability Setup" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker Compose is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (!(Test-Path .env)) {
    Write-Host "Warning: .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "Please edit .env file with your configuration before continuing." -ForegroundColor Yellow
    Write-Host "Press Enter to continue after editing .env, or Ctrl+C to exit..." -ForegroundColor Yellow
    Read-Host
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Validate required environment variables
$GRAFANA_ADMIN_USER = $env:GRAFANA_ADMIN_USER
$GRAFANA_ADMIN_PASSWORD = $env:GRAFANA_ADMIN_PASSWORD

if ([string]::IsNullOrEmpty($GRAFANA_ADMIN_USER) -or [string]::IsNullOrEmpty($GRAFANA_ADMIN_PASSWORD)) {
    Write-Host "Error: GRAFANA_ADMIN_USER and GRAFANA_ADMIN_PASSWORD must be set in .env" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Creating required directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path provisioning\datasources | Out-Null
New-Item -ItemType Directory -Force -Path provisioning\dashboards | Out-Null
New-Item -ItemType Directory -Force -Path dashboards | Out-Null
New-Item -ItemType Directory -Force -Path alerts | Out-Null

Write-Host "Step 2: Validating dashboard JSON files..." -ForegroundColor Cyan
$dashboardFiles = Get-ChildItem -Path dashboards -Filter *.json
foreach ($dashboard in $dashboardFiles) {
    try {
        $null = Get-Content $dashboard.FullName | ConvertFrom-Json
        Write-Host "  ✓ $($dashboard.Name)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ $($dashboard.Name): Invalid JSON" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Step 3: Validating alert YAML files..." -ForegroundColor Cyan
$alertFiles = Get-ChildItem -Path alerts -Filter *.yml
foreach ($alert in $alertFiles) {
    Write-Host "  ✓ $($alert.Name)" -ForegroundColor Green
}

Write-Host "Step 4: Starting Docker containers..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check if Grafana is running
$grafanaRunning = docker ps --filter "name=utxoiq-grafana" --format "{{.Names}}"
if ($grafanaRunning) {
    Write-Host "  ✓ Grafana is running" -ForegroundColor Green
}
else {
    Write-Host "  ✗ Grafana failed to start" -ForegroundColor Red
    docker-compose logs grafana
    exit 1
}

# Check if Prometheus is running
$prometheusRunning = docker ps --filter "name=utxoiq-prometheus" --format "{{.Names}}"
if ($prometheusRunning) {
    Write-Host "  ✓ Prometheus is running" -ForegroundColor Green
}
else {
    Write-Host "  ✗ Prometheus failed to start" -ForegroundColor Red
    docker-compose logs prometheus
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "Setup Complete!" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Access your dashboards:" -ForegroundColor Cyan
Write-Host "  Grafana:    http://localhost:3000" -ForegroundColor White
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host ""
Write-Host "Grafana credentials:" -ForegroundColor Cyan
Write-Host "  Username: $GRAFANA_ADMIN_USER" -ForegroundColor White
Write-Host "  Password: $GRAFANA_ADMIN_PASSWORD" -ForegroundColor White
Write-Host ""
Write-Host "Available dashboards:" -ForegroundColor Cyan
Write-Host "  - utxoIQ - Performance Monitoring" -ForegroundColor White
Write-Host "  - utxoIQ - Cost Tracking & Analytics" -ForegroundColor White
Write-Host "  - utxoIQ - Accuracy & Feedback" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "To stop services:" -ForegroundColor Cyan
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
