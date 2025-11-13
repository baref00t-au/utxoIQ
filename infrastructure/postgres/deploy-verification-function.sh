#!/bin/bash
# Deploy backup verification Cloud Function

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-project}"
FUNCTION_NAME="backup-verification"
REGION="${PRIMARY_REGION:-us-central1}"
INSTANCE_NAME="${CLOUDSQL_INSTANCE:-utxoiq-postgres}"
BACKUP_BUCKET="${BACKUP_BUCKET:-utxoiq-backups}"

echo "=== Deploying Backup Verification Function ==="
echo "Project: $PROJECT_ID"
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""

# Deploy Cloud Function
gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source=. \
    --entry-point=verify_backup \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,CLOUDSQL_INSTANCE=$INSTANCE_NAME,BACKUP_BUCKET=$BACKUP_BUCKET" \
    --memory=512MB \
    --timeout=540s \
    --max-instances=1 \
    --service-account="backup-verification@${PROJECT_ID}.iam.gserviceaccount.com"

echo ""
echo "Function deployed successfully"

# Get function URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --region="$REGION" \
    --format="value(serviceConfig.uri)")

echo "Function URL: $FUNCTION_URL"

# Create Cloud Scheduler job
echo ""
echo "Creating Cloud Scheduler job..."

gcloud scheduler jobs create http backup-verification-weekly \
    --location="$REGION" \
    --schedule="0 3 * * 0" \
    --time-zone="UTC" \
    --uri="$FUNCTION_URL" \
    --http-method=POST \
    --oidc-service-account-email="backup-verification@${PROJECT_ID}.iam.gserviceaccount.com" \
    --oidc-token-audience="$FUNCTION_URL" \
    --max-retry-attempts=3 \
    --max-backoff=1h \
    --min-backoff=5s \
    || echo "Scheduler job may already exist"

echo ""
echo "=== Deployment Complete ==="
echo "Backup verification will run weekly on Sunday at 03:00 UTC"
