#!/usr/bin/env python3
"""
Setup BigQuery hybrid dataset using Python API.
This script creates the dataset, tables, and unified views.
"""

import json
import sys
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict


def load_schema(filepath: str):
    """Load BigQuery schema from JSON file."""
    with open(filepath, 'r') as f:
        schema_json = json.load(f)
    
    # Convert to BigQuery SchemaField objects
    schema = []
    for field in schema_json:
        mode = field.get('mode', 'NULLABLE')
        field_type = field['type']
        
        if field_type == 'RECORD':
            # Handle nested fields
            nested_fields = [
                bigquery.SchemaField(
                    nf['name'],
                    nf['type'],
                    mode=nf.get('mode', 'NULLABLE'),
                    description=nf.get('description')
                )
                for nf in field.get('fields', [])
            ]
            schema_field = bigquery.SchemaField(
                field['name'],
                field_type,
                mode=mode,
                description=field.get('description'),
                fields=nested_fields
            )
        else:
            schema_field = bigquery.SchemaField(
                field['name'],
                field_type,
                mode=mode,
                description=field.get('description')
            )
        
        schema.append(schema_field)
    
    return schema


def create_dataset(client: bigquery.Client, project_id: str, dataset_id: str):
    """Create BigQuery dataset."""
    dataset_ref = f"{project_id}.{dataset_id}"
    
    try:
        client.get_dataset(dataset_ref)
        print(f"✓ Dataset {dataset_ref} already exists")
        return
    except NotFound:
        pass
    
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    dataset.description = "Bitcoin blockchain data (real-time 24h buffer)"
    
    dataset = client.create_dataset(dataset, timeout=30)
    print(f"✓ Created dataset {dataset_ref}")


def create_table(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    table_id: str,
    schema_file: str,
    partition_field: str,
    clustering_fields: list,
    description: str
):
    """Create BigQuery table with partitioning and clustering."""
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    try:
        client.get_table(table_ref)
        print(f"✓ Table {table_ref} already exists")
        return
    except NotFound:
        pass
    
    # Load schema
    schema = load_schema(schema_file)
    
    # Create table
    table = bigquery.Table(table_ref, schema=schema)
    table.description = description
    
    # Set partitioning
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field=partition_field
    )
    
    # Set clustering
    table.clustering_fields = clustering_fields
    
    table = client.create_table(table)
    print(f"✓ Created table {table_ref}")


def create_view(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    view_id: str,
    query: str,
    description: str
):
    """Create BigQuery view."""
    view_ref = f"{project_id}.{dataset_id}.{view_id}"
    
    try:
        client.get_table(view_ref)
        # Update existing view
        view = client.get_table(view_ref)
        view.view_query = query
        view.description = description
        client.update_table(view, ["view_query", "description"])
        print(f"✓ Updated view {view_ref}")
        return
    except NotFound:
        pass
    
    view = bigquery.Table(view_ref)
    view.view_query = query
    view.description = description
    
    view = client.create_table(view)
    print(f"✓ Created view {view_ref}")


def main():
    """Main setup function."""
    PROJECT_ID = "utxoiq-dev"
    DATASET_ID = "btc"
    
    print("="*60)
    print("BigQuery Hybrid Dataset Setup")
    print("="*60)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print("="*60)
    print()
    
    # Initialize client
    print("Initializing BigQuery client...")
    client = bigquery.Client(project=PROJECT_ID)
    print("✓ Client initialized")
    print()
    
    # Step 1: Create dataset
    print("Step 1: Creating dataset...")
    create_dataset(client, PROJECT_ID, DATASET_ID)
    print()
    
    # Step 2: Create tables
    print("Step 2: Creating tables...")
    
    # Blocks table
    create_table(
        client,
        PROJECT_ID,
        DATASET_ID,
        "blocks",
        "infrastructure/bigquery/schemas/blocks.json",
        "timestamp",
        ["number", "hash"],
        "Bitcoin blocks (last 24 hours)"
    )
    
    # Transactions table (with nested inputs/outputs to match public dataset)
    create_table(
        client,
        PROJECT_ID,
        DATASET_ID,
        "transactions",
        "infrastructure/bigquery/schemas/transactions_nested.json",
        "block_timestamp",
        ["block_number", "hash"],
        "Bitcoin transactions with nested inputs/outputs (last 24 hours)"
    )
    
    print()
    
    # Step 3: Create unified views
    print("Step 3: Creating unified views...")
    
    # Blocks unified view
    blocks_query = f"""
    SELECT * FROM `bigquery-public-data.crypto_bitcoin.blocks`
    WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    UNION ALL
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.blocks`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    """
    create_view(
        client,
        PROJECT_ID,
        DATASET_ID,
        "blocks_unified",
        blocks_query,
        "Unified view combining public and custom block data"
    )
    
    # Transactions unified view
    transactions_query = f"""
    SELECT * FROM `bigquery-public-data.crypto_bitcoin.transactions`
    WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    UNION ALL
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.transactions`
    WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    """
    create_view(
        client,
        PROJECT_ID,
        DATASET_ID,
        "transactions_unified",
        transactions_query,
        "Unified view combining public and custom transaction data"
    )
    
    print()
    print("="*60)
    print("Setup Complete!")
    print("="*60)
    print()
    print("Created resources:")
    print(f"  • Dataset: {PROJECT_ID}:{DATASET_ID}")
    print(f"  • Tables: blocks, transactions (with nested inputs/outputs)")
    print(f"  • Views: blocks_unified, transactions_unified")
    print()
    print("Next steps:")
    print("  1. Run backfill script to populate recent blocks")
    print("  2. Deploy feature-engine service for real-time ingestion")
    print("  3. Update application queries to use *_unified views")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
