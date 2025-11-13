# Install block monitor as Windows Task Scheduler task
# This will run the monitor automatically on startup without requiring NSSM

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$TaskName = "utxoIQ-BlockMonitor"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$BatchFile = Join-Path $ScriptDir "run-block-monitor.bat"
$LogDir = Join-Path $ProjectDir "logs"

# Create logs directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

function Install-Task {
    Write-Host "Installing utxoIQ Block Monitor as scheduled task..." -ForegroundColor Cyan
    
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Task already exists. Uninstalling first..." -ForegroundColor Yellow
        Uninstall-Task
    }
    
    # Create task action
    $action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory $ProjectDir
    
    # Create task trigger (at startup)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    
    # Create task settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 999 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Days 365)
    
    # Create task principal (run as current user)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    # Register the task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Monitors Bitcoin blockchain and sends blocks to utxoIQ ingestion service" `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "✅ Task installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Name: $TaskName"
    Write-Host "Trigger: At system startup"
    Write-Host "Logs: $LogDir"
    Write-Host ""
    Write-Host "To start the task now:"
    Write-Host "  .\scripts\install-task-scheduler.ps1 -Start"
    Write-Host ""
    Write-Host "Or use Task Scheduler GUI:"
    Write-Host "  taskschd.msc"
}

function Uninstall-Task {
    Write-Host "Uninstalling utxoIQ Block Monitor task..." -ForegroundColor Cyan
    
    # Stop task if running
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # Remove task
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    
    Write-Host "✅ Task uninstalled successfully!" -ForegroundColor Green
}

function Start-MonitorTask {
    Write-Host "Starting utxoIQ Block Monitor task..." -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "ERROR: Task is not installed." -ForegroundColor Red
        Write-Host "Run: .\scripts\install-task-scheduler.ps1 -Install"
        return
    }
    
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
    
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    if ($taskInfo.LastTaskResult -eq 267009) {
        Write-Host "✅ Task started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "The monitor is now running in the background."
        Write-Host ""
        Write-Host "To check if it's working:"
        Write-Host "  1. Check Cloud Run status:"
        Write-Host "     curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status"
        Write-Host "  2. Look for increasing block_count"
    } else {
        Write-Host "Task started. Status: $($taskInfo.LastTaskResult)" -ForegroundColor Yellow
    }
}

function Stop-MonitorTask {
    Write-Host "Stopping utxoIQ Block Monitor task..." -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "ERROR: Task is not installed." -ForegroundColor Red
        return
    }
    
    Stop-ScheduledTask -TaskName $TaskName
    
    # Also kill any running python processes for the monitor
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*block-monitor.py*"
    } | Stop-Process -Force
    
    Write-Host "✅ Task stopped successfully!" -ForegroundColor Green
}

function Get-TaskStatus {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "utxoIQ Block Monitor Task Status" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $task) {
        Write-Host "Status: NOT INSTALLED" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To install:"
        Write-Host "  .\scripts\install-task-scheduler.ps1 -Install"
    } else {
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        
        Write-Host "Status: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Running') { 'Green' } else { 'Yellow' })
        Write-Host "Last Run: $($taskInfo.LastRunTime)"
        Write-Host "Last Result: $($taskInfo.LastTaskResult)"
        Write-Host "Next Run: $($taskInfo.NextRunTime)"
        Write-Host ""
        
        # Check if process is actually running
        $runningProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*block-monitor.py*"
        }
        
        if ($runningProcess) {
            Write-Host "Monitor Process: RUNNING (PID: $($runningProcess.Id))" -ForegroundColor Green
        } else {
            Write-Host "Monitor Process: NOT RUNNING" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Check Cloud Run status:"
        Write-Host "  curl https://utxoiq-ingestion-544291059247.us-central1.run.app/status"
    }
    
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  Start:     .\scripts\install-task-scheduler.ps1 -Start"
    Write-Host "  Stop:      .\scripts\install-task-scheduler.ps1 -Stop"
    Write-Host "  Uninstall: .\scripts\install-task-scheduler.ps1 -Uninstall"
}

# Main execution
if ($Install) {
    Install-Task
} elseif ($Uninstall) {
    Uninstall-Task
} elseif ($Start) {
    Start-MonitorTask
} elseif ($Stop) {
    Stop-MonitorTask
} elseif ($Status) {
    Get-TaskStatus
} else {
    Write-Host "utxoIQ Block Monitor Task Scheduler Manager" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\scripts\install-task-scheduler.ps1 -Install    # Install as scheduled task"
    Write-Host "  .\scripts\install-task-scheduler.ps1 -Start      # Start the task"
    Write-Host "  .\scripts\install-task-scheduler.ps1 -Stop       # Stop the task"
    Write-Host "  .\scripts\install-task-scheduler.ps1 -Status     # Check task status"
    Write-Host "  .\scripts\install-task-scheduler.ps1 -Uninstall  # Remove the task"
    Write-Host ""
    Write-Host "For manual testing (no task):"
    Write-Host "  .\scripts\run-block-monitor.bat"
    Write-Host ""
    Write-Host "Note: Uses Windows Task Scheduler (no additional software required)"
}
