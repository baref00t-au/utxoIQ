# Deploy alert evaluator Cloud Function and set up Cloud Scheduler
# PowerShell version for Windows

param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = "us-central1"
)

# Configuration
$FUNCTION_NAME = "alert-evaluator"
$SCHEDULER_JOB_NAME = "alert-evaluation-job"
$SCHEDULER_SCHEDULE = "* * * * *"  # Every minute
$FUNCTION_DIR = "alert-evaluator-function"

Write-Host "Deploying Alert Evaluator Cloud Function" -ForegroundColor Green
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not installed" -ForegroundColor Red
    exit 1
}

# Check if required environment variables are set
if (-not $env:DATABASE_URL) {
    Write-Host "Warning: DATABASE_URL not set" -ForegroundColor Yellow
    Write-Host "Please set DATABASE_URL environment variable"
    exit 1
}

# Navigate to function directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\$FUNCTION_DIR"

Write-Host "Step 1: Deploying Cloud Function" -ForegroundColor Green

# Build environment variables string
$envVars = "GCP_PROJECT_ID=$ProjectId,DATABASE_URL=$env:DATABASE_URL"
if ($env:REDIS_URL) { $envVars += ",REDIS_URL=$env:REDIS_URL" }
if ($env:SENDGRID_API_KEY) { $envVars += ",SENDGRID_API_KEY=$env:SENDGRID_API_KEY" }
if ($env:SLACK_WEBHOOK_URL) { $envVars += ",SLACK_WEBHOOK_URL=$env:SLACK_WEBHOOK_URL" }
if ($env:TWILIO_ACCOUNT_SID) { $envVars += ",TWILIO_ACCOUNT_SID=$env:TWILIO_ACCOUNT_SID" }
if ($env:TWILIO_AUTH_TOKEN) { $envVars += ",TWILIO_AUTH_TOKEN=$env:TWILIO_AUTH_TOKEN" }
if ($env:TWILIO_FROM_NUMBER) { $envVars += ",TWILIO_FROM_NUMBER=$env:TWILIO_FROM_NUMBER" }
if ($env:ALERT_EMAIL_RECIPIENTS) { $envVars += ",ALERT_EMAIL_RECIPIENTS=$env:ALERT_EMAIL_RECIPIENTS" }
if ($env:ALERT_SMS_RECIPIENTS) { $envVars += ",ALERT_SMS_RECIPIENTS=$env:ALERT_SMS_RECIPIENTS" }

# Deploy Cloud Function
gcloud functions deploy $FUNCTION_NAME `
    --gen2 `
    --runtime=python312 `
    --region=$Region `
    --source=. `
    --entry-point=evaluate_alerts `
    --trigger-http `
    --allow-unauthenticated=false `
    --timeout=540s `
    --memory=512MB `
    --max-instances=10 `
    --set-env-vars="$envVars" `
    --project=$ProjectId

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error deploying Cloud Function" -ForegroundColor Red
    exit 1
}

Write-Host "Cloud Function deployed successfully" -ForegroundColor Green
Write-Host ""

# Get function URL
$FUNCTION_URL = gcloud functions describe $FUNCTION_NAME `
    --region=$Region `
    --project=$ProjectId `
    --gen2 `
    --format="value(serviceConfig.uri)"

Write-Host "Function URL: $FUNCTION_URL"
Write-Host ""

# Check if Cloud Scheduler job exists
Write-Host "Step 2: Setting up Cloud Scheduler" -ForegroundColor Green

$jobExists = gcloud scheduler jobs describe $SCHEDULER_JOB_NAME `
    --location=$Region `
    --project=$ProjectId 2>$null

if ($jobExists) {
    Write-Host "Updating existing Cloud Scheduler job..."
    
    gcloud scheduler jobs update http $SCHEDULER_JOB_NAME `
        --location=$Region `
        --schedule="$SCHEDULER_SCHEDULE" `
        --uri="$FUNCTION_URL" `
        --http-method=POST `
        --oidc-service-account-email="${ProjectId}@appspot.gserviceaccount.com" `
        --project=$ProjectId
} else {
    Write-Host "Creating new Cloud Scheduler job..."
    
    gcloud scheduler jobs create http $SCHEDULER_JOB_NAME `
        --location=$Region `
        --schedule="$SCHEDULER_SCHEDULE" `
        --uri="$FUNCTION_URL" `
        --http-method=POST `
        --oidc-service-account-email="${ProjectId}@appspot.gserviceaccount.com" `
        --project=$ProjectId
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error configuring Cloud Scheduler" -ForegroundColor Red
    exit 1
}

Write-Host "Cloud Scheduler job configured successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Alert evaluator will run every 60 seconds"
Write-Host "Function: $FUNCTION_URL"
Write-Host "Scheduler job: $SCHEDULER_JOB_NAME"
Write-Host ""
Write-Host "To manually trigger the function:"
Write-Host "  gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$Region --project=$ProjectId"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  gcloud functions logs read $FUNCTION_NAME --region=$Region --project=$ProjectId --gen2"
