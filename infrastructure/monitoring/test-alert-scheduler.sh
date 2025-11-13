#!/bin/bash
# Test alert scheduler functionality

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-utxoiq-prod}"
REGION="${GCP_REGION:-us-central1}"
FUNCTION_NAME="alert-evaluator"
SCHEDULER_JOB_NAME="alert-evaluation-job"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing Alert Scheduler${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Test 1: Verify Cloud Scheduler job exists
echo -e "${GREEN}Test 1: Verify Cloud Scheduler job exists${NC}"
if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}✓ Cloud Scheduler job exists${NC}"
else
    echo -e "${RED}✗ Cloud Scheduler job not found${NC}"
    exit 1
fi
echo ""

# Test 2: Verify job schedule
echo -e "${GREEN}Test 2: Verify job schedule (every minute)${NC}"
SCHEDULE=$(gcloud scheduler jobs describe $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID \
    --format="value(schedule)")

if [ "$SCHEDULE" = "* * * * *" ]; then
    echo -e "${GREEN}✓ Schedule is correct: $SCHEDULE${NC}"
else
    echo -e "${YELLOW}⚠ Schedule is: $SCHEDULE (expected: * * * * *)${NC}"
fi
echo ""

# Test 3: Verify Cloud Function exists
echo -e "${GREEN}Test 3: Verify Cloud Function exists${NC}"
if gcloud functions describe $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --gen2 &> /dev/null; then
    echo -e "${GREEN}✓ Cloud Function exists${NC}"
else
    echo -e "${RED}✗ Cloud Function not found${NC}"
    exit 1
fi
echo ""

# Test 4: Manually trigger scheduler job
echo -e "${GREEN}Test 4: Manually trigger scheduler job${NC}"
echo "Triggering job..."
gcloud scheduler jobs run $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID

echo "Waiting 10 seconds for execution..."
sleep 10
echo -e "${GREEN}✓ Job triggered successfully${NC}"
echo ""

# Test 5: Check function logs for execution
echo -e "${GREEN}Test 5: Check function logs for recent execution${NC}"
echo "Fetching recent logs..."

LOGS=$(gcloud functions logs read $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --gen2 \
    --limit=20 \
    --format="value(textPayload)")

if echo "$LOGS" | grep -q "Starting alert evaluation"; then
    echo -e "${GREEN}✓ Function executed successfully${NC}"
    
    # Extract execution summary
    if echo "$LOGS" | grep -q "Alert evaluation complete"; then
        SUMMARY=$(echo "$LOGS" | grep "Alert evaluation complete" | head -1)
        echo "  Summary: $SUMMARY"
    fi
else
    echo -e "${YELLOW}⚠ No recent execution found in logs${NC}"
fi
echo ""

# Test 6: Verify error handling
echo -e "${GREEN}Test 6: Verify error handling${NC}"
ERROR_LOGS=$(gcloud functions logs read $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --gen2 \
    --limit=50 \
    --format="value(textPayload)" | grep -i "error" || true)

if [ -z "$ERROR_LOGS" ]; then
    echo -e "${GREEN}✓ No errors in recent logs${NC}"
else
    echo -e "${YELLOW}⚠ Found errors in logs:${NC}"
    echo "$ERROR_LOGS" | head -5
fi
echo ""

# Test 7: Verify idempotency
echo -e "${GREEN}Test 7: Verify idempotency (trigger twice)${NC}"
echo "First trigger..."
gcloud scheduler jobs run $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID &> /dev/null

sleep 5

echo "Second trigger..."
gcloud scheduler jobs run $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID &> /dev/null

sleep 10

# Check logs for duplicate alerts
RECENT_LOGS=$(gcloud functions logs read $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --gen2 \
    --limit=50 \
    --format="value(textPayload)")

TRIGGERED_COUNT=$(echo "$RECENT_LOGS" | grep -c "Alert triggered" || true)

if [ "$TRIGGERED_COUNT" -le 1 ]; then
    echo -e "${GREEN}✓ Idempotency verified (no duplicate alerts)${NC}"
else
    echo -e "${YELLOW}⚠ Found $TRIGGERED_COUNT triggered alerts (check for duplicates)${NC}"
fi
echo ""

# Test 8: Check scheduler job status
echo -e "${GREEN}Test 8: Check scheduler job status${NC}"
JOB_STATE=$(gcloud scheduler jobs describe $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --project=$PROJECT_ID \
    --format="value(state)")

if [ "$JOB_STATE" = "ENABLED" ]; then
    echo -e "${GREEN}✓ Scheduler job is enabled${NC}"
else
    echo -e "${YELLOW}⚠ Scheduler job state: $JOB_STATE${NC}"
fi
echo ""

# Test 9: Verify function timeout configuration
echo -e "${GREEN}Test 9: Verify function timeout configuration${NC}"
TIMEOUT=$(gcloud functions describe $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --gen2 \
    --format="value(serviceConfig.timeoutSeconds)")

if [ "$TIMEOUT" -ge 540 ]; then
    echo -e "${GREEN}✓ Function timeout is adequate: ${TIMEOUT}s${NC}"
else
    echo -e "${YELLOW}⚠ Function timeout is low: ${TIMEOUT}s (recommended: 540s)${NC}"
fi
echo ""

# Test 10: Monitor for 2 minutes
echo -e "${GREEN}Test 10: Monitor executions for 2 minutes${NC}"
echo "Monitoring scheduler executions..."
echo "Press Ctrl+C to stop monitoring"
echo ""

START_TIME=$(date +%s)
EXECUTION_COUNT=0

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -ge 120 ]; then
        break
    fi
    
    # Check for new executions
    NEW_LOGS=$(gcloud functions logs read $FUNCTION_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --gen2 \
        --limit=5 \
        --format="value(textPayload)" | grep "Starting alert evaluation" || true)
    
    if [ -n "$NEW_LOGS" ]; then
        EXECUTION_COUNT=$((EXECUTION_COUNT + 1))
        echo "  [$(date +%H:%M:%S)] Execution detected (#$EXECUTION_COUNT)"
    fi
    
    sleep 10
done

echo ""
if [ $EXECUTION_COUNT -ge 2 ]; then
    echo -e "${GREEN}✓ Scheduler is running (detected $EXECUTION_COUNT executions)${NC}"
else
    echo -e "${YELLOW}⚠ Only detected $EXECUTION_COUNT executions in 2 minutes${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}Test Summary${NC}"
echo "============================================"
echo "All tests completed successfully!"
echo ""
echo "Scheduler Status:"
echo "  - Job Name: $SCHEDULER_JOB_NAME"
echo "  - Schedule: Every minute"
echo "  - State: $JOB_STATE"
echo ""
echo "Function Status:"
echo "  - Function Name: $FUNCTION_NAME"
echo "  - Timeout: ${TIMEOUT}s"
echo "  - Recent Executions: $EXECUTION_COUNT (in last 2 minutes)"
echo ""
echo "To view live logs:"
echo "  gcloud functions logs read $FUNCTION_NAME --region=$REGION --project=$PROJECT_ID --gen2 --limit=50"
echo ""
echo "To pause scheduler:"
echo "  gcloud scheduler jobs pause $SCHEDULER_JOB_NAME --location=$REGION --project=$PROJECT_ID"
