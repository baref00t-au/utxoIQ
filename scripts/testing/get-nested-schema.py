#!/usr/bin/env python3
"""
Get the full nested schema including RECORD fields.
"""

from google.cloud import bigquery
import json


def schema_to_dict(field, indent=0):
    """Convert schema field to dictionary with nested fields."""
    result = {
        'name': field.name,
        'type': field.field_type,
        'mode': field.mode or 'NULLABLE',
        'description': field.description or ''
    }
    
    if field.field_type == 'RECORD' and field.fields:
        result['fields'] = [schema_to_dict(f, indent+1) for f in field.fields]
    
    return result


def main():
    client = bigquery.Client()
    
    # Get transactions table with nested fields
    table = client.get_table('bigquery-public-data.crypto_bitcoin.transactions')
    
    print(f"Transactions table schema:")
    print(f"Total fields: {len(table.schema)}")
    print()
    
    # Convert to JSON
    schema_json = [schema_to_dict(field) for field in table.schema]
    
    # Save to file
    with open('infrastructure/bigquery/schemas/transactions_nested.json', 'w') as f:
        json.dump(schema_json, f, indent=2)
    
    print("✓ Saved full nested schema to infrastructure/bigquery/schemas/transactions_nested.json")
    
    # Print nested fields
    for field in table.schema:
        if field.field_type == 'RECORD':
            print(f"\n{field.name} (RECORD, {field.mode}):")
            for nested in field.fields:
                print(f"  - {nested.name} ({nested.field_type}, {nested.mode})")


if __name__ == "__main__":
    main()
