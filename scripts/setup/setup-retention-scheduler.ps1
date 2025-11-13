# Setup script for Cloud Scheduler retention job (PowerShell)
# This script creates the Cloud Scheduler job for daily data retention

param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = "us-central1",
    [string]$ServiceName = "utxoiq-api",
    [string]$JobName = "retention-job",
    [string]$Schedule = "0 2 * * *",
    [string]$TimeZone = "UTC",
    [string]$Timeout = "1800s"
)

$ErrorActionPreference = "Stop"

if (-not $ProjectId) {
    $ProjectId = "utxoiq-project"
}

$ServiceAccount = "cloud-scheduler@$ProjectId.iam.gserviceaccount.com"

Write-Host "Setting up Cloud Scheduler retention job..." -ForegroundColor Green
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host "Schedule: $Schedule ($TimeZone)"
Write-Host ""

# Get Cloud Run service URL
Write-Host "Retrieving Cloud Run service URL..."
$ServiceUrl = gcloud run services describe $ServiceName `
    --platform managed `
    --region $Region `
    --project $ProjectId `
    --format "value(status.url)" 2>$null

if (-not $ServiceUrl) {
    Write-Host "Error: Could not find Cloud Run service $ServiceName" -ForegroundColor Red
    exit 1
}

Write-Host "Service URL: $ServiceUrl"
Write-Host ""

# Create service account if it doesn't exist
Write-Host "Checking service account..."
$saExists = gcloud iam service-accounts describe $ServiceAccount --project $ProjectId 2>$null
if (-not $saExists) {
    Write-Host "Creating service account $ServiceAccount..."
    gcloud iam service-accounts create cloud-scheduler `
        --display-name "Cloud Scheduler Service Account" `
        --project $ProjectId
} else {
    Write-Host "Service account $ServiceAccount already exists"
}

# Grant Cloud Run Invoker role to service account
Write-Host "Granting Cloud Run Invoker role..."
gcloud run services add-iam-policy-binding $ServiceName `
    --member="serviceAccount:$ServiceAccount" `
    --role="roles/run.invoker" `
    --region $Region `
    --project $ProjectId

# Delete existing job if it exists
Write-Host "Checking for existing job..."
$jobExists = gcloud scheduler jobs describe $JobName --location $Region --project $ProjectId 2>$null
if ($jobExists) {
    Write-Host "Deleting existing job $JobName..."
    gcloud scheduler jobs delete $JobName `
        --location $Region `
        --project $ProjectId `
        --quiet
}

# Create Cloud Scheduler job
Write-Host "Creating Cloud Scheduler job $JobName..."
gcloud scheduler jobs create http $JobName `
    --location $Region `
    --schedule $Schedule `
    --uri "$ServiceUrl/api/v1/monitoring/retention/run" `
    --http-method POST `
    --oidc-service-account-email $ServiceAccount `
    --oidc-token-audience $ServiceUrl `
    --time-zone $TimeZone `
    --attempt-deadline $Timeout `
    --max-retry-attempts 3 `
    --min-backoff-duration 60s `
    --max-backoff-duration 300s `
    --project $ProjectId

Write-Host ""
Write-Host "✓ Cloud Scheduler retention job created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Job details:"
Write-Host "  Name: $JobName"
Write-Host "  Schedule: $Schedule ($TimeZone)"
Write-Host "  Endpoint: $ServiceUrl/api/v1/monitoring/retention/run"
Write-Host "  Timeout: $Timeout"
Write-Host ""
Write-Host "To manually trigger the job:"
Write-Host "  gcloud scheduler jobs run $JobName --location $Region --project $ProjectId"
Write-Host ""
Write-Host "To view job logs:"
Write-Host "  gcloud logging read `"resource.type=cloud_scheduler_job AND resource.labels.job_id=$JobName`" --limit 50 --project $ProjectId"
Write-Host ""
Write-Host "To delete the job:"
Write-Host "  gcloud scheduler jobs delete $JobName --location $Region --project $ProjectId"
