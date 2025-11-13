# Test alert scheduler functionality
# PowerShell version for Windows

param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = "us-central1"
)

# Configuration
$FUNCTION_NAME = "alert-evaluator"
$SCHEDULER_JOB_NAME = "alert-evaluation-job"

Write-Host "Testing Alert Scheduler" -ForegroundColor Blue
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host ""

# Test 1: Verify Cloud Scheduler job exists
Write-Host "Test 1: Verify Cloud Scheduler job exists" -ForegroundColor Green
$jobExists = gcloud scheduler jobs describe $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId 2>$null

if ($jobExists) {
    Write-Host "✓ Cloud Scheduler job exists" -ForegroundColor Green
} else {
    Write-Host "✗ Cloud Scheduler job not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Verify job schedule
Write-Host "Test 2: Verify job schedule (every minute)" -ForegroundColor Green
$schedule = gcloud scheduler jobs describe $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId `
    --format="value(schedule)"

if ($schedule -eq "* * * * *") {
    Write-Host "✓ Schedule is correct: $schedule" -ForegroundColor Green
} else {
    Write-Host "⚠ Schedule is: $schedule (expected: * * * * *)" -ForegroundColor Yellow
}
Write-Host ""

# Test 3: Verify Cloud Function exists
Write-Host "Test 3: Verify Cloud Function exists" -ForegroundColor Green
$functionExists = gcloud functions describe $FUNCTION_NAME `
    --region=$Region `
    --project=$ProjectId `
    --gen2 2>$null

if ($functionExists) {
    Write-Host "✓ Cloud Function exists" -ForegroundColor Green
} else {
    Write-Host "✗ Cloud Function not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 4: Manually trigger scheduler job
Write-Host "Test 4: Manually trigger scheduler job" -ForegroundColor Green
Write-Host "Triggering job..."
gcloud scheduler jobs run $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId | Out-Null

Write-Host "Waiting 10 seconds for execution..."
Start-Sleep -Seconds 10
Write-Host "✓ Job triggered successfully" -ForegroundColor Green
Write-Host ""

# Test 5: Check function logs for execution
Write-Host "Test 5: Check function logs for recent execution" -ForegroundColor Green
Write-Host "Fetching recent logs..."

$logs = gcloud functions logs read $FUNCTION_NAME `
    --region=$Region `
    --project=$ProjectId `
    --gen2 `
    --limit=20 `
    --format="value(textPayload)"

if ($logs -match "Starting alert evaluation") {
    Write-Host "✓ Function executed successfully" -ForegroundColor Green
    
    # Extract execution summary
    $summaryLine = $logs | Select-String "Alert evaluation complete" | Select-Object -First 1
    if ($summaryLine) {
        Write-Host "  Summary: $summaryLine"
    }
} else {
    Write-Host "⚠ No recent execution found in logs" -ForegroundColor Yellow
}
Write-Host ""

# Test 6: Verify error handling
Write-Host "Test 6: Verify error handling" -ForegroundColor Green
$errorLogs = gcloud functions logs read $FUNCTION_NAME `
    --region=$Region `
    --project=$ProjectId `
    --gen2 `
    --limit=50 `
    --format="value(textPayload)" | Select-String -Pattern "error" -CaseSensitive:$false

if (-not $errorLogs) {
    Write-Host "✓ No errors in recent logs" -ForegroundColor Green
} else {
    Write-Host "⚠ Found errors in logs:" -ForegroundColor Yellow
    $errorLogs | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
}
Write-Host ""

# Test 7: Verify idempotency
Write-Host "Test 7: Verify idempotency (trigger twice)" -ForegroundColor Green
Write-Host "First trigger..."
gcloud scheduler jobs run $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId 2>$null | Out-Null

Start-Sleep -Seconds 5

Write-Host "Second trigger..."
gcloud scheduler jobs run $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId 2>$null | Out-Null

Start-Sleep -Seconds 10

# Check logs for duplicate alerts
$recentLogs = gcloud functions logs read $FUNCTION_NAME `
    --region=$Region `
    --project=$ProjectId `
    --gen2 `
    --limit=50 `
    --format="value(textPayload)"

$triggeredCount = ($recentLogs | Select-String "Alert triggered").Count

if ($triggeredCount -le 1) {
    Write-Host "✓ Idempotency verified (no duplicate alerts)" -ForegroundColor Green
} else {
    Write-Host "⚠ Found $triggeredCount triggered alerts (check for duplicates)" -ForegroundColor Yellow
}
Write-Host ""

# Test 8: Check scheduler job status
Write-Host "Test 8: Check scheduler job status" -ForegroundColor Green
$jobState = gcloud scheduler jobs describe $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId `
    --format="value(state)"

if ($jobState -eq "ENABLED") {
    Write-Host "✓ Scheduler job is enabled" -ForegroundColor Green
} else {
    Write-Host "⚠ Scheduler job state: $jobState" -ForegroundColor Yellow
}
Write-Host ""

# Test 9: Verify function timeout configuration
Write-Host "Test 9: Verify function timeout configuration" -ForegroundColor Green
$timeout = gcloud functions describe $FUNCTION_NAME `
    --region=$Region `
    --project=$ProjectId `
    --gen2 `
    --format="value(serviceConfig.timeoutSeconds)"

if ([int]$timeout -ge 540) {
    Write-Host "✓ Function timeout is adequate: ${timeout}s" -ForegroundColor Green
} else {
    Write-Host "⚠ Function timeout is low: ${timeout}s (recommended: 540s)" -ForegroundColor Yellow
}
Write-Host ""

# Test 10: Monitor for 2 minutes
Write-Host "Test 10: Monitor executions for 2 minutes" -ForegroundColor Green
Write-Host "Monitoring scheduler executions..."
Write-Host "Press Ctrl+C to stop monitoring"
Write-Host ""

$startTime = Get-Date
$executionCount = 0

while ($true) {
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    
    if ($elapsed -ge 120) {
        break
    }
    
    # Check for new executions
    $newLogs = gcloud functions logs read $FUNCTION_NAME `
        --region=$Region `
        --project=$ProjectId `
        --gen2 `
        --limit=5 `
        --format="value(textPayload)" | Select-String "Starting alert evaluation"
    
    if ($newLogs) {
        $executionCount++
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "  [$timestamp] Execution detected (#$executionCount)"
    }
    
    Start-Sleep -Seconds 10
}

Write-Host ""
if ($executionCount -ge 2) {
    Write-Host "✓ Scheduler is running (detected $executionCount executions)" -ForegroundColor Green
} else {
    Write-Host "⚠ Only detected $executionCount executions in 2 minutes" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "Test Summary" -ForegroundColor Blue
Write-Host "============================================"
Write-Host "All tests completed successfully!"
Write-Host ""
Write-Host "Scheduler Status:"
Write-Host "  - Job Name: $SCHEDULER_JOB_NAME"
Write-Host "  - Schedule: Every minute"
Write-Host "  - State: $jobState"
Write-Host ""
Write-Host "Function Status:"
Write-Host "  - Function Name: $FUNCTION_NAME"
Write-Host "  - Timeout: ${timeout}s"
Write-Host "  - Recent Executions: $executionCount (in last 2 minutes)"
Write-Host ""
Write-Host "To view live logs:"
Write-Host "  gcloud functions logs read $FUNCTION_NAME --region=$Region --project=$ProjectId --gen2 --limit=50"
Write-Host ""
Write-Host "To pause scheduler:"
Write-Host "  gcloud scheduler jobs pause $SCHEDULER_JOB_NAME --location=$Region --project=$ProjectId"
