#!/bin/bash

# BigQuery Cost Monitoring and Budget Alert Setup
# Sets up budget alerts and cost tracking for BigQuery usage

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"utxoiq-project"}
BILLING_ACCOUNT_ID=${GCP_BILLING_ACCOUNT_ID}
ALERT_EMAIL=${ALERT_EMAIL:-"alerts@utxoiq.com"}

# Budget thresholds (in USD)
DAILY_BUDGET=${DAILY_BIGQUERY_BUDGET:-100}
MONTHLY_BUDGET=${MONTHLY_BIGQUERY_BUDGET:-3000}

echo "Setting up BigQuery cost monitoring for project: $PROJECT_ID"

# ============================================================================
# 1. Create Budget Alerts
# ============================================================================

if [ -z "$BILLING_ACCOUNT_ID" ]; then
  echo "Warning: GCP_BILLING_ACCOUNT_ID not set. Skipping budget alert creation."
  echo "To create budget alerts, set GCP_BILLING_ACCOUNT_ID environment variable."
else
  echo "Creating monthly BigQuery budget alert..."
  
  # Create budget for BigQuery service
  gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT_ID \
    --display-name="BigQuery Monthly Budget" \
    --budget-amount=${MONTHLY_BUDGET}USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=75 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100 \
    --filter-projects=$PROJECT_ID \
    --filter-services=services/24E6-581D-38E5 \
    --all-updates-rule-pubsub-topic=projects/$PROJECT_ID/topics/bigquery-budget-alerts \
    || echo "Budget already exists or failed to create"

  echo "Budget alert created with thresholds at 50%, 75%, 90%, and 100%"
fi

# ============================================================================
# 2. Create Pub/Sub Topic for Budget Alerts
# ============================================================================

echo "Creating Pub/Sub topic for budget alerts..."
gcloud pubsub topics create bigquery-budget-alerts \
  --project=$PROJECT_ID \
  || echo "Topic already exists"

# Create subscription for budget alerts
gcloud pubsub subscriptions create bigquery-budget-alerts-sub \
  --topic=bigquery-budget-alerts \
  --project=$PROJECT_ID \
  || echo "Subscription already exists"

# ============================================================================
# 3. Set up Log-based Metrics for Query Costs
# ============================================================================

echo "Creating log-based metric for BigQuery query costs..."

# Metric for total bytes processed
gcloud logging metrics create bigquery_bytes_processed \
  --project=$PROJECT_ID \
  --description="Total bytes processed by BigQuery queries" \
  --log-filter='resource.type="bigquery_project"
protoPayload.methodName="jobservice.jobcompleted"
protoPayload.serviceData.jobCompletedEvent.job.jobStatistics.totalBilledBytes>0' \
  --value-extractor='EXTRACT(protoPayload.serviceData.jobCompletedEvent.job.jobStatistics.totalBilledBytes)' \
  || echo "Metric already exists"

# Metric for query count
gcloud logging metrics create bigquery_query_count \
  --project=$PROJECT_ID \
  --description="Count of BigQuery queries executed" \
  --log-filter='resource.type="bigquery_project"
protoPayload.methodName="jobservice.jobcompleted"
protoPayload.serviceData.jobCompletedEvent.job.jobConfiguration.query.query!=""' \
  || echo "Metric already exists"

# ============================================================================
# 4. Create Monitoring Alert Policies
# ============================================================================

echo "Creating monitoring alert policies..."

# Alert for daily BigQuery costs exceeding threshold
cat > /tmp/bigquery_daily_cost_alert.json <<EOF
{
  "displayName": "BigQuery Daily Cost Alert",
  "documentation": {
    "content": "BigQuery daily costs have exceeded ${DAILY_BUDGET} USD. Review query patterns and optimize expensive queries.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "BigQuery bytes processed exceeds daily threshold",
      "conditionThreshold": {
        "filter": "resource.type=\"bigquery_project\" AND metric.type=\"logging.googleapis.com/user/bigquery_bytes_processed\"",
        "aggregations": [
          {
            "alignmentPeriod": "86400s",
            "perSeriesAligner": "ALIGN_SUM"
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": $(echo "$DAILY_BUDGET * 200000000000" | bc),
        "duration": "0s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [],
  "alertStrategy": {
    "autoClose": "86400s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/bigquery_daily_cost_alert.json \
  --project=$PROJECT_ID \
  || echo "Alert policy already exists or failed to create"

# ============================================================================
# 5. Create Cost Analysis Scheduled Query
# ============================================================================

echo "Creating scheduled query for cost analysis..."

# Create a scheduled query to track daily costs
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  --destination_table=intel.bigquery_cost_tracking \
  --replace \
  --schedule='every 24 hours' \
  --display_name='BigQuery Daily Cost Tracking' \
"
CREATE TABLE IF NOT EXISTS \`$PROJECT_ID.intel.bigquery_cost_tracking\` (
  query_date DATE,
  user_email STRING,
  query_count INT64,
  total_tb_processed FLOAT64,
  estimated_cost_usd FLOAT64,
  avg_query_cost_usd FLOAT64
)
PARTITION BY query_date
CLUSTER BY user_email;

INSERT INTO \`$PROJECT_ID.intel.bigquery_cost_tracking\`
SELECT
  DATE(creation_time) as query_date,
  user_email,
  COUNT(*) as query_count,
  SUM(total_bytes_processed) / POW(10, 12) as total_tb_processed,
  SUM(total_bytes_processed) / POW(10, 12) * 5 as estimated_cost_usd,
  AVG(total_bytes_processed) / POW(10, 12) * 5 as avg_query_cost_usd
FROM \`$PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE 
  DATE(creation_time) = CURRENT_DATE() - 1
  AND job_type = 'QUERY'
  AND state = 'DONE'
GROUP BY query_date, user_email;
" || echo "Scheduled query already exists"

# ============================================================================
# 6. Create Query Optimization Recommendations View
# ============================================================================

echo "Creating query optimization recommendations view..."

bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
"
CREATE OR REPLACE VIEW \`$PROJECT_ID.intel.query_optimization_recommendations\` AS
SELECT
  user_email,
  query,
  creation_time,
  total_bytes_processed / POW(10, 9) as gb_processed,
  total_bytes_processed / POW(10, 12) * 5 as estimated_cost_usd,
  total_slot_ms / 1000 as total_seconds,
  CASE
    WHEN query LIKE '%SELECT *%' THEN 'Avoid SELECT * - specify columns'
    WHEN query NOT LIKE '%WHERE%' THEN 'Add WHERE clause with partition filter'
    WHEN total_bytes_processed > POW(10, 11) THEN 'Query scans > 100GB - optimize filters'
    ELSE 'Query looks optimized'
  END as recommendation
FROM \`$PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT\`
WHERE 
  creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
  AND total_bytes_processed > POW(10, 10)  -- > 10 GB
ORDER BY total_bytes_processed DESC;
"

echo ""
echo "============================================================================"
echo "BigQuery Cost Monitoring Setup Complete!"
echo "============================================================================"
echo ""
echo "Budget Configuration:"
echo "  - Monthly Budget: \$${MONTHLY_BUDGET} USD"
echo "  - Daily Budget: \$${DAILY_BUDGET} USD"
echo "  - Alert Thresholds: 50%, 75%, 90%, 100%"
echo ""
echo "Monitoring Components Created:"
echo "  ✓ Pub/Sub topic: bigquery-budget-alerts"
echo "  ✓ Log-based metrics: bigquery_bytes_processed, bigquery_query_count"
echo "  ✓ Alert policy: BigQuery Daily Cost Alert"
echo "  ✓ Scheduled query: BigQuery Daily Cost Tracking"
echo "  ✓ View: intel.query_optimization_recommendations"
echo ""
echo "Cost Tracking Table:"
echo "  - intel.bigquery_cost_tracking (updated daily)"
echo ""
echo "To view current costs, run:"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.intel.bigquery_cost_tracking\` ORDER BY query_date DESC LIMIT 30'"
echo ""
echo "To view optimization recommendations, run:"
echo "  bq query --use_legacy_sql=false 'SELECT * FROM \`$PROJECT_ID.intel.query_optimization_recommendations\` LIMIT 20'"
echo ""

# Clean up temp files
rm -f /tmp/bigquery_daily_cost_alert.json
