#!/bin/bash
# Clean up data older than 48 hours from custom dataset
# Run this as a Cloud Scheduler job every 6 hours

set -e

PROJECT_ID="utxoiq-dev"
DATASET_ID="btc"

echo "Cleaning up old data from ${PROJECT_ID}:${DATASET_ID}..."

# Delete old blocks
echo "Deleting blocks older than 48 hours..."
bq query --use_legacy_sql=false <<EOF
DELETE FROM \`${PROJECT_ID}.${DATASET_ID}.blocks\`
WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
EOF

# Delete old transactions
echo "Deleting transactions older than 48 hours..."
bq query --use_legacy_sql=false <<EOF
DELETE FROM \`${PROJECT_ID}.${DATASET_ID}.transactions\`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
EOF

# Delete old inputs
echo "Deleting inputs older than 48 hours..."
bq query --use_legacy_sql=false <<EOF
DELETE FROM \`${PROJECT_ID}.${DATASET_ID}.inputs\`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
EOF

# Delete old outputs
echo "Deleting outputs older than 48 hours..."
bq query --use_legacy_sql=false <<EOF
DELETE FROM \`${PROJECT_ID}.${DATASET_ID}.outputs\`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
EOF

echo "Cleanup completed successfully!"
