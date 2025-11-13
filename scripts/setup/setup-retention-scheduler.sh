#!/bin/bash
# Setup script for Cloud Scheduler retention job
# This script creates the Cloud Scheduler job for daily data retention

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-project}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="utxoiq-api"
SERVICE_ACCOUNT="cloud-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"
JOB_NAME="retention-job"
SCHEDULE="0 2 * * *"  # Daily at 02:00 UTC
TIME_ZONE="UTC"
TIMEOUT="1800s"  # 30 minutes

echo "Setting up Cloud Scheduler retention job..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Schedule: ${SCHEDULE} (${TIME_ZONE})"

# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)')

if [ -z "$SERVICE_URL" ]; then
  echo "Error: Could not find Cloud Run service ${SERVICE_NAME}"
  exit 1
fi

echo "Service URL: ${SERVICE_URL}"

# Create service account if it doesn't exist
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project ${PROJECT_ID} &>/dev/null; then
  echo "Creating service account ${SERVICE_ACCOUNT}..."
  gcloud iam service-accounts create cloud-scheduler \
    --display-name "Cloud Scheduler Service Account" \
    --project ${PROJECT_ID}
else
  echo "Service account ${SERVICE_ACCOUNT} already exists"
fi

# Grant Cloud Run Invoker role to service account
echo "Granting Cloud Run Invoker role..."
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker" \
  --region ${REGION} \
  --project ${PROJECT_ID}

# Delete existing job if it exists
if gcloud scheduler jobs describe ${JOB_NAME} --location ${REGION} --project ${PROJECT_ID} &>/dev/null; then
  echo "Deleting existing job ${JOB_NAME}..."
  gcloud scheduler jobs delete ${JOB_NAME} \
    --location ${REGION} \
    --project ${PROJECT_ID} \
    --quiet
fi

# Create Cloud Scheduler job
echo "Creating Cloud Scheduler job ${JOB_NAME}..."
gcloud scheduler jobs create http ${JOB_NAME} \
  --location ${REGION} \
  --schedule "${SCHEDULE}" \
  --uri "${SERVICE_URL}/api/v1/monitoring/retention/run" \
  --http-method POST \
  --oidc-service-account-email ${SERVICE_ACCOUNT} \
  --oidc-token-audience "${SERVICE_URL}" \
  --time-zone "${TIME_ZONE}" \
  --attempt-deadline ${TIMEOUT} \
  --max-retry-attempts 3 \
  --min-backoff-duration 60s \
  --max-backoff-duration 300s \
  --project ${PROJECT_ID}

echo ""
echo "✓ Cloud Scheduler retention job created successfully!"
echo ""
echo "Job details:"
echo "  Name: ${JOB_NAME}"
echo "  Schedule: ${SCHEDULE} (${TIME_ZONE})"
echo "  Endpoint: ${SERVICE_URL}/api/v1/monitoring/retention/run"
echo "  Timeout: ${TIMEOUT}"
echo ""
echo "To manually trigger the job:"
echo "  gcloud scheduler jobs run ${JOB_NAME} --location ${REGION} --project ${PROJECT_ID}"
echo ""
echo "To view job logs:"
echo "  gcloud logging read \"resource.type=cloud_scheduler_job AND resource.labels.job_id=${JOB_NAME}\" --limit 50 --project ${PROJECT_ID}"
echo ""
echo "To delete the job:"
echo "  gcloud scheduler jobs delete ${JOB_NAME} --location ${REGION} --project ${PROJECT_ID}"
