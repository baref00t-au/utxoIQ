#!/bin/bash
# Deploy alert evaluator Cloud Function and set up Cloud Scheduler

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-prod}"
REGION="${GCP_REGION:-us-central1}"
FUNCTION_NAME="alert-evaluator"
SCHEDULER_JOB_NAME="alert-evaluation-job"
SCHEDULER_SCHEDULE="* * * * *"  # Every minute
FUNCTION_DIR="alert-evaluator-function"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying Alert Evaluator Cloud Function${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Warning: DATABASE_URL not set${NC}"
    echo "Please set DATABASE_URL environment variable"
    exit 1
fi

# Navigate to function directory
cd "$(dirname "$0")/$FUNCTION_DIR"

echo -e "${GREEN}Step 1: Deploying Cloud Function${NC}"

# Deploy Cloud Function
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=. \
    --entry-point=evaluate_alerts \
    --trigger-http \
    --allow-unauthenticated=false \
    --timeout=540s \
    --memory=512MB \
    --max-instances=10 \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,SENDGRID_API_KEY=$SENDGRID_API_KEY,SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL,TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN,TWILIO_FROM_NUMBER=$TWILIO_FROM_NUMBER,ALERT_EMAIL_RECIPIENTS=$ALERT_EMAIL_RECIPIENTS,ALERT_SMS_RECIPIENTS=$ALERT_SMS_RECIPIENTS" \
    --project=$PROJECT_ID

echo -e "${GREEN}Cloud Function deployed successfully${NC}"
echo ""

# Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --gen2 \
    --format="value(serviceConfig.uri)")

echo "Function URL: $FUNCTION_URL"
echo ""

# Check if Cloud Scheduler job exists
echo -e "${GREEN}Step 2: Setting up Cloud Scheduler${NC}"

if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID &> /dev/null; then
    
    echo "Updating existing Cloud Scheduler job..."
    
    gcloud scheduler jobs update http $SCHEDULER_JOB_NAME \
        --location=$REGION \
        --schedule="$SCHEDULER_SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --project=$PROJECT_ID
else
    echo "Creating new Cloud Scheduler job..."
    
    gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
        --location=$REGION \
        --schedule="$SCHEDULER_SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --oidc-service-account-email="${PROJECT_ID}@appspot.gserviceaccount.com" \
        --project=$PROJECT_ID
fi

echo -e "${GREEN}Cloud Scheduler job configured successfully${NC}"
echo ""

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Alert evaluator will run every 60 seconds"
echo "Function: $FUNCTION_URL"
echo "Scheduler job: $SCHEDULER_JOB_NAME"
echo ""
echo "To manually trigger the function:"
echo "  gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION --project=$PROJECT_ID"
echo ""
echo "To view logs:"
echo "  gcloud functions logs read $FUNCTION_NAME --region=$REGION --project=$PROJECT_ID --gen2"
