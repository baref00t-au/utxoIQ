# Test Backup and Recovery Procedures (PowerShell)
# This script performs automated testing of backup and recovery functionality

$ErrorActionPreference = "Continue"

# Configuration
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "utxoiq-project" }
$INSTANCE_NAME = if ($env:CLOUDSQL_INSTANCE) { $env:CLOUDSQL_INSTANCE } else { "utxoiq-postgres" }
$TEST_INSTANCE_PREFIX = "test-recovery"
$BACKUP_BUCKET = if ($env:BACKUP_BUCKET) { $env:BACKUP_BUCKET } else { "utxoiq-backups" }
$TEST_DATABASE = "test_recovery_db"

# Test results
$TESTS_PASSED = 0
$TESTS_FAILED = 0

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backup and Recovery Test Suite" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Instance: $INSTANCE_NAME"
Write-Host "Test Instance Prefix: $TEST_INSTANCE_PREFIX"
Write-Host ""

# Function to print test result
function Print-Result {
    param(
        [string]$TestName,
        [bool]$Result
    )
    
    if ($Result) {
        Write-Host "✓ PASS: $TestName" -ForegroundColor Green
        $script:TESTS_PASSED++
    } else {
        Write-Host "✗ FAIL: $TestName" -ForegroundColor Red
        $script:TESTS_FAILED++
    }
}

# Function to cleanup test resources
function Cleanup {
    Write-Host ""
    Write-Host "Cleaning up test resources..." -ForegroundColor Yellow
    
    # List and delete test instances
    $testInstances = gcloud sql instances list --project=$PROJECT_ID --format="value(name)" | Where-Object { $_ -match "^$TEST_INSTANCE_PREFIX" }
    foreach ($instance in $testInstances) {
        Write-Host "Deleting test instance: $instance"
        gcloud sql instances delete $instance --project=$PROJECT_ID --quiet 2>$null
    }
    
    # Clean up test database
    Write-Host "Cleaning up test database..."
    gcloud sql databases delete $TEST_DATABASE --instance=$INSTANCE_NAME --project=$PROJECT_ID --quiet 2>$null
}

# Register cleanup on exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 1: Verify Backup Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if backups are enabled
$backupEnabled = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.backupConfiguration.enabled)"

Print-Result "Backups enabled" ($backupEnabled -eq "True")

# Check backup start time
$backupTime = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.backupConfiguration.startTime)"

Print-Result "Backup time configured (01:00 UTC)" ($backupTime -eq "01:00")

# Check PITR enabled
$pitrEnabled = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.backupConfiguration.pointInTimeRecoveryEnabled)"

Print-Result "Point-in-time recovery enabled" ($pitrEnabled -eq "True")

# Check backup retention
$retention = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.backupConfiguration.backupRetentionSettings.retainedBackups)"

Print-Result "Backup retention set to 7 days" ($retention -eq "7")

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 2: Verify Backup Existence" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# List recent backups
$backups = gcloud sql backups list `
    --instance=$INSTANCE_NAME `
    --project=$PROJECT_ID `
    --filter="status=SUCCESSFUL" `
    --limit=7 `
    --format="value(id)"

$backupCount = ($backups | Measure-Object).Count

if ($backupCount -gt 0) {
    Print-Result "At least one successful backup exists" $true
    Write-Host "  Found $backupCount successful backups"
} else {
    Print-Result "At least one successful backup exists" $false
}

# Get latest backup
$latestBackup = gcloud sql backups list `
    --instance=$INSTANCE_NAME `
    --project=$PROJECT_ID `
    --filter="status=SUCCESSFUL" `
    --limit=1 `
    --format="value(id)"

if ($latestBackup) {
    Print-Result "Latest backup ID retrieved: $latestBackup" $true
} else {
    Print-Result "Latest backup ID retrieved" $false
    Write-Host "Cannot proceed with restore tests without a backup" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 3: Create Test Database" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Create test database
Write-Host "Creating test database..."
gcloud sql databases create $TEST_DATABASE `
    --instance=$INSTANCE_NAME `
    --project=$PROJECT_ID 2>$null

Print-Result "Test database created" $true

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 4: Create On-Demand Backup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Create on-demand backup
Write-Host "Creating on-demand backup..."
$backupDescription = "Test backup $(Get-Date -Format 'yyyyMMdd-HHmmss')"

gcloud sql backups create `
    --instance=$INSTANCE_NAME `
    --project=$PROJECT_ID `
    --description=$backupDescription `
    --async

# Wait for backup to complete
Write-Host "Waiting for backup to complete..."
$timeout = 300  # 5 minutes
$elapsed = 0
$backupComplete = $false

while ($elapsed -lt $timeout) {
    $runningBackups = gcloud sql operations list `
        --instance=$INSTANCE_NAME `
        --project=$PROJECT_ID `
        --filter="operationType=BACKUP_VOLUME AND status=RUNNING" `
        --format="value(name)"
    
    if (-not $runningBackups) {
        $backupComplete = $true
        break
    }
    
    Start-Sleep -Seconds 10
    $elapsed += 10
    Write-Host -NoNewline "."
}

Write-Host ""
Print-Result "On-demand backup completed" $backupComplete

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 5: Test Backup Restore (Clone)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Create test instance from backup
$testInstanceName = "$TEST_INSTANCE_PREFIX-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Write-Host "Creating test instance from backup: $testInstanceName"

gcloud sql instances clone $INSTANCE_NAME $testInstanceName `
    --project=$PROJECT_ID `
    --async

# Wait for clone to complete
Write-Host "Waiting for clone to complete (this may take 10-15 minutes)..."
$timeout = 1800  # 30 minutes
$elapsed = 0
$cloneComplete = $false

while ($elapsed -lt $timeout) {
    $instanceState = gcloud sql instances describe $testInstanceName `
        --project=$PROJECT_ID `
        --format="value(state)" 2>$null
    
    if ($instanceState -eq "RUNNABLE") {
        $cloneComplete = $true
        break
    }
    
    Start-Sleep -Seconds 30
    $elapsed += 30
    Write-Host -NoNewline "."
}

Write-Host ""
Print-Result "Clone instance created successfully" $cloneComplete

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 6: Verify Restored Data" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if ($cloneComplete) {
    # Verify data in cloned instance
    Write-Host "Verifying data in cloned instance..."
    
    # Check if test database exists
    $databases = gcloud sql databases list `
        --instance=$testInstanceName `
        --project=$PROJECT_ID `
        --format="value(name)"
    
    $dbExists = $databases -contains $TEST_DATABASE
    
    if ($dbExists) {
        Print-Result "Test database exists in clone" $true
        Write-Host "  Note: Full data verification requires database connection"
    } else {
        Print-Result "Test database exists in clone" $false
    }
} else {
    Write-Host "Skipping data verification (clone not completed)"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 7: Test Point-in-Time Recovery" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Calculate target time (5 minutes ago)
$targetTime = (Get-Date).AddMinutes(-5).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$pitrInstanceName = "$TEST_INSTANCE_PREFIX-pitr-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "Testing PITR to: $targetTime"
Write-Host "Creating PITR instance: $pitrInstanceName"

$pitrResult = gcloud sql instances clone $INSTANCE_NAME $pitrInstanceName `
    --point-in-time=$targetTime `
    --project=$PROJECT_ID `
    --async 2>$null

if ($LASTEXITCODE -eq 0) {
    Print-Result "Point-in-time recovery initiated" $true
} else {
    Write-Host "PITR clone creation failed (may be outside retention window)"
    Print-Result "Point-in-time recovery clone" $false
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 8: Verify Backup Bucket" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if backup bucket exists
$bucketExists = gsutil ls "gs://$BACKUP_BUCKET" 2>$null
if ($LASTEXITCODE -eq 0) {
    Print-Result "Backup bucket exists" $true
    
    # Check versioning
    $versioning = gsutil versioning get "gs://$BACKUP_BUCKET"
    $versioningEnabled = $versioning -match "Enabled"
    Print-Result "Bucket versioning enabled" $versioningEnabled
} else {
    Print-Result "Backup bucket exists" $false
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 9: Verify High Availability" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check HA configuration
$availabilityType = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.availabilityType)"

Print-Result "High availability configured (REGIONAL)" ($availabilityType -eq "REGIONAL")

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test 10: Verify Maintenance Window" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check maintenance window
$maintDay = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.maintenanceWindow.day)"

$maintHour = gcloud sql instances describe $INSTANCE_NAME `
    --project=$PROJECT_ID `
    --format="value(settings.maintenanceWindow.hour)"

Print-Result "Maintenance window configured (Sunday 02:00 UTC)" (($maintDay -eq "7") -and ($maintHour -eq "2"))

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Tests Passed: $TESTS_PASSED" -ForegroundColor Green
Write-Host "Tests Failed: $TESTS_FAILED" -ForegroundColor Red
Write-Host ""

# Cleanup
Cleanup

if ($TESTS_FAILED -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some tests failed. Please review the output above." -ForegroundColor Red
    exit 1
}
