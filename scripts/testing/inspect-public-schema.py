#!/usr/bin/env python3
"""
Inspect the public BigQuery Bitcoin dataset schema.
"""

from google.cloud import bigquery
import json


def inspect_table_schema(table_ref: str):
    """Inspect and print table schema."""
    client = bigquery.Client()
    
    try:
        table = client.get_table(table_ref)
        
        print(f"\n{'='*60}")
        print(f"Table: {table_ref}")
        print(f"{'='*60}")
        print(f"Rows: {table.num_rows:,}")
        print(f"Size: {table.num_bytes / 1024 / 1024 / 1024:.2f} GB")
        print(f"\nSchema ({len(table.schema)} fields):")
        print(f"{'='*60}")
        
        for field in table.schema:
            mode = field.mode or "NULLABLE"
            print(f"  {field.name:30} {field.field_type:15} {mode:10}")
            if field.description:
                print(f"    → {field.description}")
        
        # Export schema to JSON
        schema_json = [
            {
                'name': field.name,
                'type': field.field_type,
                'mode': field.mode or 'NULLABLE',
                'description': field.description or ''
            }
            for field in table.schema
        ]
        
        return schema_json
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def main():
    """Main inspection function."""
    tables = {
        'blocks': 'bigquery-public-data.crypto_bitcoin.blocks',
        'transactions': 'bigquery-public-data.crypto_bitcoin.transactions',
        'inputs': 'bigquery-public-data.crypto_bitcoin.inputs',
        'outputs': 'bigquery-public-data.crypto_bitcoin.outputs'
    }
    
    print("Inspecting BigQuery Public Bitcoin Dataset")
    print("="*60)
    
    for table_name, table_ref in tables.items():
        schema = inspect_table_schema(table_ref)
        
        if schema:
            # Save to file
            output_file = f"temp/public_{table_name}_schema.json"
            with open(output_file, 'w') as f:
                json.dump(schema, f, indent=2)
            print(f"\n✓ Saved schema to {output_file}")
    
    print("\n" + "="*60)
    print("Inspection complete!")
    print("="*60)


if __name__ == "__main__":
    main()
