#!/bin/bash
# Create unified views that combine public and custom datasets

set -e

PROJECT_ID="utxoiq-dev"
DATASET_ID="btc"

echo "Creating unified views..."

# Blocks unified view
echo "Creating blocks_unified view..."
bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.blocks_unified\` AS
SELECT * FROM \`bigquery-public-data.crypto_bitcoin.blocks\`
WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}.blocks\`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
EOF

# Transactions unified view
echo "Creating transactions_unified view..."
bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.transactions_unified\` AS
SELECT * FROM \`bigquery-public-data.crypto_bitcoin.transactions\`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}.transactions\`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
EOF

# Inputs unified view
echo "Creating inputs_unified view..."
bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.inputs_unified\` AS
SELECT * FROM \`bigquery-public-data.crypto_bitcoin.inputs\`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}.inputs\`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
EOF

# Outputs unified view
echo "Creating outputs_unified view..."
bq query --use_legacy_sql=false <<EOF
CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET_ID}.outputs_unified\` AS
SELECT * FROM \`bigquery-public-data.crypto_bitcoin.outputs\`
WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
UNION ALL
SELECT * FROM \`${PROJECT_ID}.${DATASET_ID}.outputs\`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR);
EOF

echo "Unified views created successfully!"
echo ""
echo "You can now query using:"
echo "  - ${PROJECT_ID}.${DATASET_ID}.blocks_unified"
echo "  - ${PROJECT_ID}.${DATASET_ID}.transactions_unified"
echo "  - ${PROJECT_ID}.${DATASET_ID}.inputs_unified"
echo "  - ${PROJECT_ID}.${DATASET_ID}.outputs_unified"
