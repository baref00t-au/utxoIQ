#!/bin/bash
# Setup Cloud Scheduler job for database metrics publishing

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-project}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_URL="${API_SERVICE_URL:-https://utxoiq-api-xxxxx.run.app}"
SERVICE_ACCOUNT="${SCHEDULER_SA:-scheduler@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "Setting up Cloud Scheduler for database metrics publishing"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service URL: $SERVICE_URL"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID"

# Create service account if it doesn't exist
echo "Checking service account..."
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" &> /dev/null; then
    echo "Creating service account: $SERVICE_ACCOUNT"
    gcloud iam service-accounts create scheduler \
        --display-name="Cloud Scheduler Service Account" \
        --description="Service account for Cloud Scheduler jobs"
else
    echo "Service account already exists: $SERVICE_ACCOUNT"
fi

# Grant Cloud Run Invoker role to service account
echo "Granting Cloud Run Invoker role..."
gcloud run services add-iam-policy-binding utxoiq-api \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker" \
    --region="$REGION" \
    --quiet || true

# Delete existing job if it exists
echo "Checking for existing scheduler job..."
if gcloud scheduler jobs describe database-metrics-publisher --location="$REGION" &> /dev/null; then
    echo "Deleting existing job..."
    gcloud scheduler jobs delete database-metrics-publisher \
        --location="$REGION" \
        --quiet
fi

# Create Cloud Scheduler job
echo "Creating Cloud Scheduler job..."
gcloud scheduler jobs create http database-metrics-publisher \
    --location="$REGION" \
    --schedule="* * * * *" \
    --uri="${SERVICE_URL}/api/v1/monitoring/database/publish-metrics" \
    --http-method=POST \
    --oidc-service-account-email="$SERVICE_ACCOUNT" \
    --oidc-token-audience="$SERVICE_URL" \
    --attempt-deadline="30s" \
    --max-retry-attempts=3 \
    --max-retry-duration="60s" \
    --min-backoff="5s" \
    --max-backoff="30s" \
    --description="Publish database metrics to Cloud Monitoring every minute"

echo ""
echo "Cloud Scheduler job created successfully!"
echo ""
echo "To view the job:"
echo "  gcloud scheduler jobs describe database-metrics-publisher --location=$REGION"
echo ""
echo "To manually trigger the job:"
echo "  gcloud scheduler jobs run database-metrics-publisher --location=$REGION"
echo ""
echo "To view job execution logs:"
echo "  gcloud logging read 'resource.type=cloud_scheduler_job AND resource.labels.job_id=database-metrics-publisher' --limit=10"
