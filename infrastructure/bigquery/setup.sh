#!/bin/bash

# BigQuery setup script for utxoIQ platform
# Creates datasets and tables with partitioning and clustering

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"utxoiq-project"}
LOCATION=${GCP_LOCATION:-"US"}

echo "Setting up BigQuery datasets and tables for project: $PROJECT_ID"

# Create btc dataset for raw blockchain data
echo "Creating btc dataset..."
bq mk --dataset \
  --location=$LOCATION \
  --description="Raw Bitcoin blockchain data" \
  $PROJECT_ID:btc || echo "Dataset btc already exists"

# Create intel dataset for processed intelligence
echo "Creating intel dataset..."
bq mk --dataset \
  --location=$LOCATION \
  --description="Processed blockchain intelligence and insights" \
  $PROJECT_ID:intel || echo "Dataset intel already exists"

# Create btc.blocks table
echo "Creating btc.blocks table..."
bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=height \
  --description="Bitcoin block data" \
  $PROJECT_ID:btc.blocks \
  ./schemas/btc_blocks.json || echo "Table btc.blocks already exists"

# Create intel.signals table with partitioning and clustering
echo "Creating intel.signals table..."
bq mk --table \
  --time_partitioning_field=processed_at \
  --time_partitioning_type=DAY \
  --clustering_fields=type,block_height \
  --description="Blockchain signals with partitioning by timestamp" \
  $PROJECT_ID:intel.signals \
  ./schemas/intel_signals.json || echo "Table intel.signals already exists"

# Create intel.insights table with clustering
echo "Creating intel.insights table..."
bq mk --table \
  --time_partitioning_field=created_at \
  --time_partitioning_type=DAY \
  --clustering_fields=signal_type,confidence \
  --description="AI-generated insights with clustering by signal_type" \
  $PROJECT_ID:intel.insights \
  ./schemas/intel_insights.json || echo "Table intel.insights already exists"

# Create intel.user_feedback table
echo "Creating intel.user_feedback table..."
bq mk --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=insight_id,user_id \
  --description="User feedback for insights" \
  $PROJECT_ID:intel.user_feedback \
  ./schemas/intel_user_feedback.json || echo "Table intel.user_feedback already exists"

echo "BigQuery setup complete!"
echo ""
echo "Datasets created:"
echo "  - $PROJECT_ID:btc (raw blockchain data)"
echo "  - $PROJECT_ID:intel (processed intelligence)"
echo ""
echo "Tables created with partitioning and clustering:"
echo "  - btc.blocks (partitioned by timestamp, clustered by height)"
echo "  - intel.signals (partitioned by processed_at, clustered by type, block_height)"
echo "  - intel.insights (partitioned by created_at, clustered by signal_type, confidence)"
echo "  - intel.user_feedback (partitioned by timestamp, clustered by insight_id, user_id)"
