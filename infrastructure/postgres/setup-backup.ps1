# Cloud SQL Backup Setup Script (PowerShell)
# Configures automated backups for Cloud SQL PostgreSQL instance

$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "utxoiq-project" }
$INSTANCE_NAME = if ($env:CLOUDSQL_INSTANCE) { $env:CLOUDSQL_INSTANCE } else { "utxoiq-postgres" }
$PRIMARY_REGION = if ($env:PRIMARY_REGION) { $env:PRIMARY_REGION } else { "us-central1" }
$BACKUP_REGION = if ($env:BACKUP_REGION) { $env:BACKUP_REGION } else { "us-east1" }
$BACKUP_BUCKET = if ($env:BACKUP_BUCKET) { $env:BACKUP_BUCKET } else { "utxoiq-backups" }

Write-Host "=== Cloud SQL Backup Configuration ===" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Instance: $INSTANCE_NAME"
Write-Host "Primary Region: $PRIMARY_REGION"
Write-Host "Backup Region: $BACKUP_REGION"
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not installed" -ForegroundColor Red
    exit 1
}

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Create backup bucket if it doesn't exist
Write-Host "Creating backup bucket..." -ForegroundColor Yellow
$bucketExists = gsutil ls "gs://$BACKUP_BUCKET" 2>$null
if (-not $bucketExists) {
    gsutil mb -p $PROJECT_ID -l $BACKUP_REGION "gs://$BACKUP_BUCKET"
    Write-Host "Backup bucket created: gs://$BACKUP_BUCKET" -ForegroundColor Green
} else {
    Write-Host "Backup bucket already exists: gs://$BACKUP_BUCKET" -ForegroundColor Green
}

# Enable versioning on backup bucket
Write-Host "Enabling versioning on backup bucket..." -ForegroundColor Yellow
gsutil versioning set on "gs://$BACKUP_BUCKET"

# Set lifecycle policy for backup bucket
Write-Host "Setting lifecycle policy for backup bucket..." -ForegroundColor Yellow
$lifecycleJson = @"
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 30,
          "isLive": false
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {
          "age": 7,
          "matchesStorageClass": ["STANDARD"]
        }
      }
    ]
  }
}
"@
$lifecycleJson | Out-File -FilePath "$env:TEMP\backup-lifecycle.json" -Encoding UTF8
gsutil lifecycle set "$env:TEMP\backup-lifecycle.json" "gs://$BACKUP_BUCKET"
Remove-Item "$env:TEMP\backup-lifecycle.json"

# Configure automated backups
Write-Host "Configuring automated backups..." -ForegroundColor Yellow
gcloud sql instances patch $INSTANCE_NAME `
    --backup-start-time=01:00 `
    --enable-bin-log `
    --retained-backups-count=7 `
    --retained-transaction-log-days=7 `
    --backup-location=$BACKUP_REGION `
    --quiet

Write-Host "Automated backups configured successfully" -ForegroundColor Green

# Enable point-in-time recovery
Write-Host "Enabling point-in-time recovery..." -ForegroundColor Yellow
gcloud sql instances patch $INSTANCE_NAME `
    --enable-point-in-time-recovery `
    --quiet

Write-Host "Point-in-time recovery enabled" -ForegroundColor Green

# Configure high availability
Write-Host "Configuring high availability..." -ForegroundColor Yellow
gcloud sql instances patch $INSTANCE_NAME `
    --availability-type=REGIONAL `
    --quiet

Write-Host "High availability configured" -ForegroundColor Green

# Set maintenance window
Write-Host "Setting maintenance window..." -ForegroundColor Yellow
gcloud sql instances patch $INSTANCE_NAME `
    --maintenance-window-day=SUN `
    --maintenance-window-hour=2 `
    --quiet

Write-Host "Maintenance window set to Sunday 02:00 UTC" -ForegroundColor Green

# Verify configuration
Write-Host ""
Write-Host "=== Verifying Backup Configuration ===" -ForegroundColor Cyan
gcloud sql instances describe $INSTANCE_NAME `
    --format="table(
        settings.backupConfiguration.enabled,
        settings.backupConfiguration.startTime,
        settings.backupConfiguration.backupRetentionSettings.retainedBackups,
        settings.backupConfiguration.pointInTimeRecoveryEnabled,
        settings.backupConfiguration.location,
        settings.availabilityType
    )"

Write-Host ""
Write-Host "=== Backup Configuration Complete ===" -ForegroundColor Green
Write-Host "Backups will run daily at 01:00 UTC"
Write-Host "7 daily backups will be retained"
Write-Host "Point-in-time recovery is enabled"
Write-Host "Backups are stored in: $BACKUP_REGION"
Write-Host "Backup bucket: gs://$BACKUP_BUCKET"
