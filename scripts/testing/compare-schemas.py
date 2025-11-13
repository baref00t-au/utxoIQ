#!/usr/bin/env python3
"""
Compare blockchain-etl schema with current schema to identify differences.
"""

import json
import sys
from typing import Dict, List, Set


def load_schema(filepath: str) -> List[Dict]:
    """Load BigQuery schema from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def schema_to_dict(schema: List[Dict]) -> Dict[str, Dict]:
    """Convert schema list to dictionary keyed by field name."""
    return {field['name']: field for field in schema}


def compare_schemas(
    blockchain_etl_schema: List[Dict],
    current_schema: List[Dict],
    table_name: str
):
    """Compare two schemas and print differences."""
    etl_dict = schema_to_dict(blockchain_etl_schema)
    current_dict = schema_to_dict(current_schema)
    
    etl_fields = set(etl_dict.keys())
    current_fields = set(current_dict.keys())
    
    print(f"\n{'='*60}")
    print(f"Schema Comparison: {table_name}")
    print(f"{'='*60}")
    
    # Fields only in blockchain-etl
    only_in_etl = etl_fields - current_fields
    if only_in_etl:
        print(f"\n✓ Fields to ADD (in blockchain-etl, not in current):")
        for field in sorted(only_in_etl):
            field_info = etl_dict[field]
            print(f"  - {field} ({field_info['type']}, {field_info['mode']})")
    
    # Fields only in current
    only_in_current = current_fields - etl_fields
    if only_in_current:
        print(f"\n✗ Fields to REMOVE (in current, not in blockchain-etl):")
        for field in sorted(only_in_current):
            field_info = current_dict[field]
            print(f"  - {field} ({field_info['type']}, {field_info['mode']})")
    
    # Fields in both but with differences
    common_fields = etl_fields & current_fields
    differences = []
    
    for field in sorted(common_fields):
        etl_field = etl_dict[field]
        current_field = current_dict[field]
        
        diffs = []
        if etl_field['type'] != current_field['type']:
            diffs.append(f"type: {current_field['type']} → {etl_field['type']}")
        
        if etl_field['mode'] != current_field['mode']:
            diffs.append(f"mode: {current_field['mode']} → {etl_field['mode']}")
        
        if diffs:
            differences.append((field, diffs))
    
    if differences:
        print(f"\n⚠ Fields with DIFFERENCES:")
        for field, diffs in differences:
            print(f"  - {field}:")
            for diff in diffs:
                print(f"      {diff}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Fields to add:    {len(only_in_etl)}")
    print(f"  Fields to remove: {len(only_in_current)}")
    print(f"  Fields to modify: {len(differences)}")
    print(f"  Fields unchanged: {len(common_fields) - len(differences)}")
    print(f"{'='*60}")


def main():
    """Main comparison function."""
    tables = ['blocks', 'transactions', 'inputs', 'outputs']
    
    print("BigQuery Schema Comparison Tool")
    print("Comparing blockchain-etl schema with current schema")
    
    for table in tables:
        etl_schema_path = f"infrastructure/bigquery/schemas/{table}.json"
        current_schema_path = f"temp/current_{table}_schema.json"
        
        try:
            etl_schema = load_schema(etl_schema_path)
            
            try:
                current_schema = load_schema(current_schema_path)
                compare_schemas(etl_schema, current_schema, table)
            except FileNotFoundError:
                print(f"\n⚠ Current schema not found: {current_schema_path}")
                print(f"  Run: bq show --schema --format=prettyjson utxoiq-dev:btc.{table} > {current_schema_path}")
                
        except FileNotFoundError:
            print(f"\n✗ blockchain-etl schema not found: {etl_schema_path}")
    
    print("\n")


if __name__ == "__main__":
    main()
