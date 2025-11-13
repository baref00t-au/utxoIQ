#!/usr/bin/env python3
"""
Drop and recreate BigQuery tables with updated schema.
"""

from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def main():
    PROJECT_ID = "utxoiq-dev"
    DATASET_ID = "btc"
    
    client = bigquery.Client(project=PROJECT_ID)
    
    tables = ['blocks', 'transactions', 'inputs', 'outputs']
    
    print("Dropping existing tables...")
    for table_id in tables:
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
        try:
            client.delete_table(table_ref)
            print(f"✓ Dropped {table_ref}")
        except NotFound:
            print(f"  Table {table_ref} doesn't exist")
    
    print("\nNow run: python scripts/setup-bigquery-hybrid.py")


if __name__ == "__main__":
    main()
