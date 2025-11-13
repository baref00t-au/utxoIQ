# Install block monitor as Windows service using NSSM
# This will run the monitor in the background automatically on startup

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$ServiceName = "utxoIQ-BlockMonitor"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$VenvPython = Join-Path $ProjectDir "venv312\Scripts\python.exe"
$MonitorScript = Join-Path $ScriptDir "block-monitor.py"
$LogDir = Join-Path $ProjectDir "logs"

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Get Bitcoin RPC password from .env
$EnvFile = Join-Path $ProjectDir ".env"
$BitcoinPassword = (Get-Content $EnvFile | Select-String "BITCOIN_RPC_PASSWORD" | ForEach-Object { $_ -replace "BITCOIN_RPC_PASSWORD=", "" })

$RpcUrl = "http://umbrel:$BitcoinPassword@umbrel.local:8332"
$FeatureEngineUrl = "https://utxoiq-ingestion-544291059247.us-central1.run.app"
$PollInterval = "10"

function Test-NSSMInstalled {
    try {
        $null = Get-Command nssm -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Install-Service {
    Write-Host "Installing utxoIQ Block Monitor as Windows service..." -ForegroundColor Cyan
    
    if (-not (Test-NSSMInstalled)) {
        Write-Host "ERROR: NSSM is not installed." -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install NSSM first:"
        Write-Host "  1. Download from: https://nssm.cc/download"
        Write-Host "  2. Extract nssm.exe to C:\Windows\System32\"
        Write-Host "  OR install via Chocolatey: choco install nssm"
        return
    }
    
    # Check if service already exists
    $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existingService) {
        Write-Host "Service already exists. Uninstalling first..." -ForegroundColor Yellow
        Uninstall-Service
    }
    
    # Install service
    $args = @(
        "--rpc-url", $RpcUrl,
        "--feature-engine-url", $FeatureEngineUrl,
        "--poll-interval", $PollInterval
    )
    
    nssm install $ServiceName $VenvPython $MonitorScript $args
    
    # Configure service
    nssm set $ServiceName AppDirectory $ProjectDir
    nssm set $ServiceName DisplayName "utxoIQ Block Monitor"
    nssm set $ServiceName Description "Monitors Bitcoin blockchain and sends blocks to utxoIQ ingestion service"
    nssm set $ServiceName Start SERVICE_AUTO_START
    
    # Set up logging
    $StdoutLog = Join-Path $LogDir "block-monitor-stdout.log"
    $StderrLog = Join-Path $LogDir "block-monitor-stderr.log"
    nssm set $ServiceName AppStdout $StdoutLog
    nssm set $ServiceName AppStderr $StderrLog
    nssm set $ServiceName AppStdoutCreationDisposition 4  # Append
    nssm set $ServiceName AppStderrCreationDisposition 4  # Append
    
    # Set restart policy
    nssm set $ServiceName AppExit Default Restart
    nssm set $ServiceName AppRestartDelay 5000  # 5 seconds
    
    Write-Host ""
    Write-Host "✅ Service installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service Name: $ServiceName"
    Write-Host "Logs: $LogDir"
    Write-Host ""
    Write-Host "To start the service:"
    Write-Host "  .\scripts\install-monitor-service.ps1 -Start"
    Write-Host ""
    Write-Host "Or use Windows Services:"
    Write-Host "  services.msc"
}

function Uninstall-Service {
    Write-Host "Uninstalling utxoIQ Block Monitor service..." -ForegroundColor Cyan
    
    # Stop service if running
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq 'Running') {
        Write-Host "Stopping service..." -ForegroundColor Yellow
        nssm stop $ServiceName
        Start-Sleep -Seconds 2
    }
    
    # Remove service
    nssm remove $ServiceName confirm
    
    Write-Host "✅ Service uninstalled successfully!" -ForegroundColor Green
}

function Start-MonitorService {
    Write-Host "Starting utxoIQ Block Monitor service..." -ForegroundColor Cyan
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "ERROR: Service is not installed." -ForegroundColor Red
        Write-Host "Run: .\scripts\install-monitor-service.ps1 -Install"
        return
    }
    
    Start-Service -Name $ServiceName
    Start-Sleep -Seconds 2
    
    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq 'Running') {
        Write-Host "✅ Service started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Check logs:"
        Write-Host "  Get-Content $LogDir\block-monitor-stdout.log -Tail 20 -Wait"
    } else {
        Write-Host "❌ Service failed to start. Check logs:" -ForegroundColor Red
        Write-Host "  Get-Content $LogDir\block-monitor-stderr.log"
    }
}

function Stop-MonitorService {
    Write-Host "Stopping utxoIQ Block Monitor service..." -ForegroundColor Cyan
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "ERROR: Service is not installed." -ForegroundColor Red
        return
    }
    
    Stop-Service -Name $ServiceName
    Write-Host "✅ Service stopped successfully!" -ForegroundColor Green
}

function Get-ServiceStatus {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "utxoIQ Block Monitor Service Status" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $service) {
        Write-Host "Status: NOT INSTALLED" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To install:"
        Write-Host "  .\scripts\install-monitor-service.ps1 -Install"
    } else {
        Write-Host "Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Yellow' })
        Write-Host "Display Name: $($service.DisplayName)"
        Write-Host "Start Type: $($service.StartType)"
        Write-Host ""
        Write-Host "Logs:"
        Write-Host "  Stdout: $LogDir\block-monitor-stdout.log"
        Write-Host "  Stderr: $LogDir\block-monitor-stderr.log"
        Write-Host ""
        
        if ($service.Status -eq 'Running') {
            Write-Host "Recent log entries:" -ForegroundColor Cyan
            $logFile = Join-Path $LogDir "block-monitor-stdout.log"
            if (Test-Path $logFile) {
                Get-Content $logFile -Tail 10
            }
        }
    }
    
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  Start:     .\scripts\install-monitor-service.ps1 -Start"
    Write-Host "  Stop:      .\scripts\install-monitor-service.ps1 -Stop"
    Write-Host "  Uninstall: .\scripts\install-monitor-service.ps1 -Uninstall"
}

# Main execution
if ($Install) {
    Install-Service
} elseif ($Uninstall) {
    Uninstall-Service
} elseif ($Start) {
    Start-MonitorService
} elseif ($Stop) {
    Stop-MonitorService
} elseif ($Status) {
    Get-ServiceStatus
} else {
    Write-Host "utxoIQ Block Monitor Service Manager" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\scripts\install-monitor-service.ps1 -Install    # Install as Windows service"
    Write-Host "  .\scripts\install-monitor-service.ps1 -Start      # Start the service"
    Write-Host "  .\scripts\install-monitor-service.ps1 -Stop       # Stop the service"
    Write-Host "  .\scripts\install-monitor-service.ps1 -Status     # Check service status"
    Write-Host "  .\scripts\install-monitor-service.ps1 -Uninstall  # Remove the service"
    Write-Host ""
    Write-Host "For manual testing (no service):"
    Write-Host "  .\scripts\run-block-monitor.bat"
}
