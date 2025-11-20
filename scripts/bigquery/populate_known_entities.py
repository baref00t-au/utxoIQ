#!/usr/bin/env python3
"""
Populate btc.known_entities table with exchange, mining pool, and treasury company data.

This script populates the BigQuery btc.known_entities table with:
- Exchange entities (Coinbase, Kraken, Binance, Gemini, Bitstamp)
- Mining pool entities (Foundry USA, AntPool, F2Pool, ViaBTC, Binance Pool)
- Treasury company entities (MicroStrategy, Tesla, Block, Marathon, Riot)

Usage:
    python scripts/bigquery/populate_known_entities.py [--project PROJECT_ID] [--dry-run]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
except ImportError:
    print("Error: google-cloud-bigquery not installed")
    print("Install with: pip install google-cloud-bigquery")
    sys.exit(1)


# Exchange entities with known addresses
EXCHANGES = [
    {
        "entity_id": "coinbase_001",
        "entity_name": "Coinbase",
        "entity_type": "exchange",
        "addresses": [
            "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97",
            "3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5",
            "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h",
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Example address
        ],
        "metadata": {}
    },
    {
        "entity_id": "kraken_001",
        "entity_name": "Kraken",
        "entity_type": "exchange",
        "addresses": [
            "bc1qj0yrqa7gcgqv3h2p7w5c8qwz9v8qgqxqz9v8qg",
            "3BMEX8FTXqvjqjqjqjqjqjqjqjqjqjqjqj",
            "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        ],
        "metadata": {}
    },
    {
        "entity_id": "binance_001",
        "entity_name": "Binance",
        "entity_type": "exchange",
        "addresses": [
            "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h",
            "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
            "bc1qjasf9z3h7w3jkqvxvqxvqxvqxvqxvqxvqxvqxv",
        ],
        "metadata": {}
    },
    {
        "entity_id": "gemini_001",
        "entity_name": "Gemini",
        "entity_type": "exchange",
        "addresses": [
            "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrp",
            "3JZq4atUahhuA9rLhXLMhhTo133J9rF97j",
        ],
        "metadata": {}
    },
    {
        "entity_id": "bitstamp_001",
        "entity_name": "Bitstamp",
        "entity_type": "exchange",
        "addresses": [
            "3BMEX2VJD5v8zrVqzqzqzqzqzqzqzqzqzq",
            "bc1qjh0akslml073gn48r5l4z7rq0xmfs5k0u7s8p7",
        ],
        "metadata": {}
    },
]

# Mining pool entities with known addresses
MINING_POOLS = [
    {
        "entity_id": "foundry_usa_001",
        "entity_name": "Foundry USA",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qxhmdufsvnuaaaehg6gvggvglhfhgfhgfhgfhgfh",
            "3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5",
        ],
        "metadata": {
            "pool_identifier": "Foundry USA Pool",
            "website": "https://foundrydigital.com"
        }
    },
    {
        "entity_id": "antpool_001",
        "entity_name": "AntPool",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qjl8uwezzlech723lpnyuza0h2cdkvxvh54v3dn",
            "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
        ],
        "metadata": {
            "pool_identifier": "AntPool",
            "website": "https://www.antpool.com"
        }
    },
    {
        "entity_id": "f2pool_001",
        "entity_name": "F2Pool",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qjh0akslml073gn48r5l4z7rq0xmfs5k0u7s8p7",
            "1KFHE7w8BhaENAswwryaoccDb6qcT6DbYY",
        ],
        "metadata": {
            "pool_identifier": "F2Pool",
            "website": "https://www.f2pool.com"
        }
    },
    {
        "entity_id": "viabtc_001",
        "entity_name": "ViaBTC",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "3NA8hsjfdgVkmmVS9moHmkZsVCoLxUkvvv",
        ],
        "metadata": {
            "pool_identifier": "ViaBTC",
            "website": "https://www.viabtc.com"
        }
    },
    {
        "entity_id": "binance_pool_001",
        "entity_name": "Binance Pool",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qjasf9z3h7w3jkqvxvqxvqxvqxvqxvqxvqxvqxv",
            "3NA8hsjfdgVkmmVS9moHmkZsVCoLxUkvvv",
        ],
        "metadata": {
            "pool_identifier": "Binance Pool",
            "website": "https://pool.binance.com"
        }
    },
]

# Treasury company entities with known addresses and holdings
TREASURY_COMPANIES = [
    {
        "entity_id": "microstrategy_001",
        "entity_name": "MicroStrategy",
        "entity_type": "treasury",
        "addresses": [
            "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrp",
            "3FZbgi29cpjq2GjdwV8eyHuJJnkLtktZc5",
            "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h",
        ],
        "metadata": {
            "ticker": "MSTR",
            "known_holdings_btc": 152800,
            "company_type": "business_intelligence",
            "public_company": True
        }
    },
    {
        "entity_id": "tesla_001",
        "entity_name": "Tesla",
        "entity_type": "treasury",
        "addresses": [
            "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
        ],
        "metadata": {
            "ticker": "TSLA",
            "known_holdings_btc": 9720,
            "company_type": "automotive",
            "public_company": True
        }
    },
    {
        "entity_id": "block_001",
        "entity_name": "Block",
        "entity_type": "treasury",
        "addresses": [
            "bc1qjh0akslml073gn48r5l4z7rq0xmfs5k0u7s8p7",
            "1KFHE7w8BhaENAswwryaoccDb6qcT6DbYY",
        ],
        "metadata": {
            "ticker": "SQ",
            "known_holdings_btc": 8027,
            "company_type": "fintech",
            "public_company": True
        }
    },
    {
        "entity_id": "marathon_001",
        "entity_name": "Marathon Digital",
        "entity_type": "treasury",
        "addresses": [
            "bc1qjasf9z3h7w3jkqvxvqxvqxvqxvqxvqxvqxvqxv",
            "3NA8hsjfdgVkmmVS9moHmkZsVCoLxUkvvv",
        ],
        "metadata": {
            "ticker": "MARA",
            "known_holdings_btc": 26842,
            "company_type": "bitcoin_mining",
            "public_company": True
        }
    },
    {
        "entity_id": "riot_001",
        "entity_name": "Riot Platforms",
        "entity_type": "treasury",
        "addresses": [
            "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h",
            "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo",
        ],
        "metadata": {
            "ticker": "RIOT",
            "known_holdings_btc": 9334,
            "company_type": "bitcoin_mining",
            "public_company": True
        }
    },
]


def create_table_if_not_exists(client: bigquery.Client, project_id: str) -> None:
    """Create the btc.known_entities table if it doesn't exist."""
    table_id = f"{project_id}.btc.known_entities"
    
    schema = [
        bigquery.SchemaField("entity_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entity_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entity_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("addresses", "STRING", mode="REPEATED"),
        bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.clustering_fields = ["entity_type", "entity_name"]
    table.description = "Known blockchain entities including exchanges, mining pools, and treasury companies"
    
    try:
        client.get_table(table_id)
        print(f"[OK] Table {table_id} already exists")
    except NotFound:
        table = client.create_table(table)
        print(f"[OK] Created table {table_id}")


def prepare_entity_rows(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prepare entity data for BigQuery insertion."""
    rows = []
    current_time = datetime.now(timezone.utc).isoformat()
    
    for entity in entities:
        row = {
            "entity_id": entity["entity_id"],
            "entity_name": entity["entity_name"],
            "entity_type": entity["entity_type"],
            "addresses": entity["addresses"],
            "metadata": json.dumps(entity["metadata"]) if entity["metadata"] else None,
            "updated_at": current_time,
        }
        rows.append(row)
    
    return rows


def insert_entities(
    client: bigquery.Client,
    project_id: str,
    entities: List[Dict[str, Any]],
    entity_type_name: str,
    dry_run: bool = False
) -> None:
    """Insert entities into the btc.known_entities table."""
    table_id = f"{project_id}.btc.known_entities"
    rows = prepare_entity_rows(entities)
    
    if dry_run:
        print(f"\n[DRY RUN] Would insert {len(rows)} {entity_type_name}:")
        for row in rows:
            print(f"  - {row['entity_name']} ({row['entity_id']})")
            print(f"    Type: {row['entity_type']}")
            print(f"    Addresses: {len(row['addresses'])} addresses")
            if row['metadata']:
                metadata = json.loads(row['metadata'])
                print(f"    Metadata: {metadata}")
        return
    
    print(f"\nInserting {len(rows)} {entity_type_name}...")
    errors = client.insert_rows_json(table_id, rows)
    
    if errors:
        print(f"[ERROR] Errors occurred while inserting {entity_type_name}:")
        for error in errors:
            print(f"  {error}")
    else:
        print(f"[OK] Successfully inserted {len(rows)} {entity_type_name}")


def clear_existing_data(
    client: bigquery.Client,
    project_id: str,
    dry_run: bool = False
) -> None:
    """Clear existing data from the table (optional)."""
    table_id = f"{project_id}.btc.known_entities"
    
    if dry_run:
        print("\n[DRY RUN] Would clear existing data from table")
        return
    
    query = f"DELETE FROM `{table_id}` WHERE TRUE"
    
    print("\nClearing existing data...")
    job = client.query(query)
    job.result()
    print("[OK] Cleared existing data")


def verify_data(client: bigquery.Client, project_id: str) -> None:
    """Verify the inserted data."""
    table_id = f"{project_id}.btc.known_entities"
    
    query = f"""
    SELECT 
        entity_type,
        COUNT(*) as count
    FROM `{table_id}`
    GROUP BY entity_type
    ORDER BY entity_type
    """
    
    print("\nVerifying inserted data...")
    results = client.query(query).result()
    
    print("\nEntity counts by type:")
    for row in results:
        print(f"  {row.entity_type}: {row.count}")
    
    # Show sample entities
    sample_query = f"""
    SELECT 
        entity_name,
        entity_type,
        ARRAY_LENGTH(addresses) as address_count,
        metadata
    FROM `{table_id}`
    ORDER BY entity_type, entity_name
    LIMIT 10
    """
    
    print("\nSample entities:")
    results = client.query(sample_query).result()
    for row in results:
        print(f"  {row.entity_name} ({row.entity_type})")
        print(f"    Addresses: {row.address_count}")
        if row.metadata:
            print(f"    Metadata: {row.metadata}")


def main():
    parser = argparse.ArgumentParser(
        description="Populate btc.known_entities table with exchange, mining pool, and treasury data"
    )
    parser.add_argument(
        "--project",
        help="GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)",
        default=None
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be inserted without actually inserting"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before inserting (use with caution)"
    )
    
    args = parser.parse_args()
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=args.project)
        project_id = client.project
        print(f"Using GCP project: {project_id}")
    except Exception as e:
        print(f"Error initializing BigQuery client: {e}")
        print("Make sure you have authenticated with: gcloud auth application-default login")
        sys.exit(1)
    
    # Create table if needed
    if not args.dry_run:
        create_table_if_not_exists(client, project_id)
    
    # Clear existing data if requested
    if args.clear:
        clear_existing_data(client, project_id, args.dry_run)
    
    # Insert entities
    insert_entities(client, project_id, EXCHANGES, "exchanges", args.dry_run)
    insert_entities(client, project_id, MINING_POOLS, "mining pools", args.dry_run)
    insert_entities(client, project_id, TREASURY_COMPANIES, "treasury companies", args.dry_run)
    
    # Verify data
    if not args.dry_run:
        verify_data(client, project_id)
    
    print("\n[OK] Done!")
    print("\nNote: The addresses in this script are examples. Update them with real addresses")
    print("from public sources like blockchain explorers and company disclosures.")


if __name__ == "__main__":
    main()
