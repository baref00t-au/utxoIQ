#!/bin/bash
# Create BigQuery dataset and tables for hybrid approach

set -e

PROJECT_ID="utxoiq-dev"
DATASET_ID="btc"
LOCATION="us-central1"

echo "Creating BigQuery dataset: ${PROJECT_ID}:${DATASET_ID}"

# Create dataset
bq mk \
  --dataset \
  --location=${LOCATION} \
  --description="Bitcoin blockchain data (real-time 24h buffer)" \
  ${PROJECT_ID}:${DATASET_ID}

echo "Creating blocks table..."
bq mk \
  --table \
  --time_partitioning_field=timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=number,hash \
  --description="Bitcoin blocks (last 24 hours)" \
  ${PROJECT_ID}:${DATASET_ID}.blocks \
  infrastructure/bigquery/schemas/blocks.json

echo "Creating transactions table..."
bq mk \
  --table \
  --time_partitioning_field=block_timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=block_number,hash \
  --description="Bitcoin transactions (last 24 hours)" \
  ${PROJECT_ID}:${DATASET_ID}.transactions \
  infrastructure/bigquery/schemas/transactions.json

echo "Creating inputs table..."
bq mk \
  --table \
  --time_partitioning_field=block_timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=transaction_hash \
  --description="Bitcoin transaction inputs (last 24 hours)" \
  ${PROJECT_ID}:${DATASET_ID}.inputs \
  infrastructure/bigquery/schemas/inputs.json

echo "Creating outputs table..."
bq mk \
  --table \
  --time_partitioning_field=block_timestamp \
  --time_partitioning_type=DAY \
  --clustering_fields=transaction_hash \
  --description="Bitcoin transaction outputs (last 24 hours)" \
  ${PROJECT_ID}:${DATASET_ID}.outputs \
  infrastructure/bigquery/schemas/outputs.json

echo "Dataset and tables created successfully!"
