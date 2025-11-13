#!/bin/bash
# Test queries to verify hybrid dataset is working correctly

set -e

PROJECT_ID="utxoiq-dev"
DATASET_ID="btc"

echo "Testing hybrid BigQuery setup..."
echo ""

# Test 1: Recent blocks (should use custom dataset)
echo "Test 1: Querying recent blocks (last 1 hour)..."
bq query --use_legacy_sql=false --format=pretty <<EOF
SELECT 
  number,
  hash,
  timestamp,
  transaction_count
FROM \`${PROJECT_ID}.${DATASET_ID}.blocks_unified\`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY number DESC
LIMIT 10;
EOF

echo ""
echo "Test 2: Historical blocks (should use public dataset)..."
bq query --use_legacy_sql=false --format=pretty <<EOF
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as block_count,
  AVG(transaction_count) as avg_tx_count
FROM \`${PROJECT_ID}.${DATASET_ID}.blocks_unified\`
WHERE timestamp BETWEEN '2024-01-01' AND '2024-01-07'
GROUP BY date
ORDER BY date;
EOF

echo ""
echo "Test 3: Recent transactions (last 1 hour)..."
bq query --use_legacy_sql=false --format=pretty <<EOF
SELECT 
  hash,
  block_number,
  block_timestamp,
  input_count,
  output_count,
  fee
FROM \`${PROJECT_ID}.${DATASET_ID}.transactions_unified\`
WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY block_number DESC
LIMIT 10;
EOF

echo ""
echo "Test 4: Cross-dataset query (24h boundary)..."
bq query --use_legacy_sql=false --format=pretty <<EOF
SELECT 
  CASE 
    WHEN timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR) 
    THEN 'Custom Dataset'
    ELSE 'Public Dataset'
  END as source,
  COUNT(*) as block_count
FROM \`${PROJECT_ID}.${DATASET_ID}.blocks_unified\`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
GROUP BY source;
EOF

echo ""
echo "All tests completed!"
