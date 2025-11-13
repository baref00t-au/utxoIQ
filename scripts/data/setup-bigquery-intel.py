#!/usr/bin/env python3
"""
Set up BigQuery intel dataset and insights table with correct schema.
"""
from google.cloud import bigquery

PROJECT_ID = "utxoiq-dev"
DATASET_ID = "intel"
TABLE_ID = "insights"

def main():
    print("=" * 60)
    print("Setting up BigQuery Intel Dataset")
    print("=" * 60)
    print()
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create dataset
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    
    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"✅ Dataset {dataset_ref} ready")
    except Exception as e:
        print(f"⚠️  Dataset issue: {e}")
    
    # Delete existing table if it exists
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    try:
        client.delete_table(table_ref)
        print(f"🗑️  Deleted existing table {table_ref}")
    except Exception:
        pass
    
    # Create table with correct schema
    schema = [
        bigquery.SchemaField("insight_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("signal_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("headline", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("summary", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("confidence", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("block_height", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("evidence_blocks", "INTEGER", mode="REPEATED"),
        bigquery.SchemaField("evidence_txids", "STRING", mode="REPEATED"),
        bigquery.SchemaField("chart_url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("confidence_factors", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("confidence_explanation", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("supporting_evidence", "STRING", mode="REPEATED"),
        bigquery.SchemaField("accuracy_rating", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("is_predictive", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("model_version", "STRING", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table)
    
    print(f"✅ Created table {table_ref}")
    print()
    print("Table schema:")
    for field in schema:
        print(f"  - {field.name}: {field.field_type}")
    
    print()
    print("=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print()
    print("Next: Run scripts/quick-seed-insights.py to add sample data")

if __name__ == "__main__":
    main()
