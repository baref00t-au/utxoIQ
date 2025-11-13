"""
Populate btc.known_entities table with treasury companies, exchanges, and mining pools.

This script inserts known blockchain entities into BigQuery for use in signal processing.
Treasury companies include public companies with disclosed Bitcoin holdings.
"""

import os
import sys
from datetime import datetime
from google.cloud import bigquery
from typing import List, Dict, Any


# Treasury companies with known Bitcoin holdings (as of 2024)
TREASURY_ENTITIES = [
    {
        "entity_id": "microstrategy_001",
        "entity_name": "MicroStrategy",
        "entity_type": "treasury",
        "addresses": [
            # MicroStrategy known addresses (examples - would need real addresses)
            "bc1qmicrostrategy1",
            "bc1qmicrostrategy2"
        ],
        "metadata": {
            "ticker": "MSTR",
            "known_holdings_btc": 152800,
            "company_type": "business_intelligence",
            "public": True
        }
    },
    {
        "entity_id": "tesla_001",
        "entity_name": "Tesla",
        "entity_type": "treasury",
        "addresses": [
            "bc1qtesla1",
            "bc1qtesla2"
        ],
        "metadata": {
            "ticker": "TSLA",
            "known_holdings_btc": 9720,
            "company_type": "automotive",
            "public": True
        }
    },
    {
        "entity_id": "block_001",
        "entity_name": "Block",
        "entity_type": "treasury",
        "addresses": [
            "bc1qblock1",
            "bc1qblock2"
        ],
        "metadata": {
            "ticker": "SQ",
            "known_holdings_btc": 8027,
            "company_type": "fintech",
            "public": True
        }
    },
    {
        "entity_id": "marathon_001",
        "entity_name": "Marathon Digital",
        "entity_type": "treasury",
        "addresses": [
            "bc1qmarathon1",
            "bc1qmarathon2"
        ],
        "metadata": {
            "ticker": "MARA",
            "known_holdings_btc": 26842,
            "company_type": "mining",
            "public": True
        }
    },
    {
        "entity_id": "riot_001",
        "entity_name": "Riot Platforms",
        "entity_type": "treasury",
        "addresses": [
            "bc1qriot1",
            "bc1qriot2"
        ],
        "metadata": {
            "ticker": "RIOT",
            "known_holdings_btc": 9334,
            "company_type": "mining",
            "public": True
        }
    },
    {
        "entity_id": "coinbase_treasury_001",
        "entity_name": "Coinbase",
        "entity_type": "treasury",
        "addresses": [
            "bc1qcoinbase_corp1",
            "bc1qcoinbase_corp2"
        ],
        "metadata": {
            "ticker": "COIN",
            "known_holdings_btc": 9000,
            "company_type": "exchange",
            "public": True
        }
    },
    {
        "entity_id": "galaxy_001",
        "entity_name": "Galaxy Digital",
        "entity_type": "treasury",
        "addresses": [
            "bc1qgalaxy1",
            "bc1qgalaxy2"
        ],
        "metadata": {
            "ticker": "GLXY",
            "known_holdings_btc": 15449,
            "company_type": "investment",
            "public": True
        }
    },
    {
        "entity_id": "hut8_001",
        "entity_name": "Hut 8 Mining",
        "entity_type": "treasury",
        "addresses": [
            "bc1qhut8_1",
            "bc1qhut8_2"
        ],
        "metadata": {
            "ticker": "HUT",
            "known_holdings_btc": 9102,
            "company_type": "mining",
            "public": True
        }
    }
]

# Major exchanges (examples - would need real addresses)
EXCHANGE_ENTITIES = [
    {
        "entity_id": "coinbase_001",
        "entity_name": "Coinbase",
        "entity_type": "exchange",
        "addresses": [
            "bc1qcoinbase1",
            "bc1qcoinbase2",
            "3CoinbaseAddr1"
        ],
        "metadata": {
            "country": "USA",
            "founded": 2012
        }
    },
    {
        "entity_id": "kraken_001",
        "entity_name": "Kraken",
        "entity_type": "exchange",
        "addresses": [
            "bc1qkraken1",
            "bc1qkraken2"
        ],
        "metadata": {
            "country": "USA",
            "founded": 2011
        }
    },
    {
        "entity_id": "binance_001",
        "entity_name": "Binance",
        "entity_type": "exchange",
        "addresses": [
            "bc1qbinance1",
            "bc1qbinance2"
        ],
        "metadata": {
            "country": "Global",
            "founded": 2017
        }
    },
    {
        "entity_id": "gemini_001",
        "entity_name": "Gemini",
        "entity_type": "exchange",
        "addresses": [
            "bc1qgemini1",
            "bc1qgemini2"
        ],
        "metadata": {
            "country": "USA",
            "founded": 2014
        }
    },
    {
        "entity_id": "bitstamp_001",
        "entity_name": "Bitstamp",
        "entity_type": "exchange",
        "addresses": [
            "bc1qbitstamp1",
            "bc1qbitstamp2"
        ],
        "metadata": {
            "country": "Luxembourg",
            "founded": 2011
        }
    }
]

# Major mining pools (examples - would need real addresses)
MINING_POOL_ENTITIES = [
    {
        "entity_id": "foundry_001",
        "entity_name": "Foundry USA",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qfoundry1",
            "bc1qfoundry2"
        ],
        "metadata": {
            "country": "USA",
            "hash_rate_share_pct": 28.5
        }
    },
    {
        "entity_id": "antpool_001",
        "entity_name": "AntPool",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qantpool1",
            "bc1qantpool2"
        ],
        "metadata": {
            "country": "China",
            "hash_rate_share_pct": 25.3
        }
    },
    {
        "entity_id": "f2pool_001",
        "entity_name": "F2Pool",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qf2pool1",
            "bc1qf2pool2"
        ],
        "metadata": {
            "country": "China",
            "hash_rate_share_pct": 15.2
        }
    },
    {
        "entity_id": "viabtc_001",
        "entity_name": "ViaBTC",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qviabtc1",
            "bc1qviabtc2"
        ],
        "metadata": {
            "country": "China",
            "hash_rate_share_pct": 12.1
        }
    },
    {
        "entity_id": "binance_pool_001",
        "entity_name": "Binance Pool",
        "entity_type": "mining_pool",
        "addresses": [
            "bc1qbinancepool1",
            "bc1qbinancepool2"
        ],
        "metadata": {
            "country": "Global",
            "hash_rate_share_pct": 10.8
        }
    }
]


def populate_entities(project_id: str, dry_run: bool = False) -> None:
    """
    Populate btc.known_entities table with treasury companies, exchanges, and mining pools.
    
    Args:
        project_id: GCP project ID
        dry_run: If True, print entities without inserting
    """
    # Combine all entities
    all_entities = TREASURY_ENTITIES + EXCHANGE_ENTITIES + MINING_POOL_ENTITIES
    
    # Add updated_at timestamp
    current_time = datetime.utcnow()
    for entity in all_entities:
        entity["updated_at"] = current_time.isoformat()
    
    if dry_run:
        print("DRY RUN - Would insert the following entities:")
        print("=" * 80)
        for entity in all_entities:
            print(f"\n{entity['entity_name']} ({entity['entity_type']})")
            print(f"  ID: {entity['entity_id']}")
            print(f"  Addresses: {len(entity['addresses'])} addresses")
            if entity['entity_type'] == 'treasury':
                ticker = entity['metadata'].get('ticker', 'N/A')
                holdings = entity['metadata'].get('known_holdings_btc', 0)
                print(f"  Ticker: {ticker}")
                print(f"  Holdings: {holdings:,.0f} BTC")
        print("\n" + "=" * 80)
        print(f"Total entities: {len(all_entities)}")
        return
    
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.btc.known_entities"
    
    print(f"Inserting {len(all_entities)} entities into {table_id}...")
    
    # Insert entities
    errors = client.insert_rows_json(table_id, all_entities)
    
    if errors:
        print(f"Errors occurred while inserting rows:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print(f"✓ Successfully inserted {len(all_entities)} entities")
        
        # Print summary
        treasury_count = len(TREASURY_ENTITIES)
        exchange_count = len(EXCHANGE_ENTITIES)
        pool_count = len(MINING_POOL_ENTITIES)
        
        print(f"\nSummary:")
        print(f"  Treasury companies: {treasury_count}")
        print(f"  Exchanges: {exchange_count}")
        print(f"  Mining pools: {pool_count}")
        print(f"  Total: {len(all_entities)}")
        
        # Print treasury holdings
        total_holdings = sum(e['metadata']['known_holdings_btc'] for e in TREASURY_ENTITIES)
        print(f"\nTotal treasury holdings: {total_holdings:,.0f} BTC")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Populate btc.known_entities table with treasury companies, exchanges, and mining pools"
    )
    parser.add_argument(
        "--project-id",
        default=os.getenv("GCP_PROJECT_ID"),
        help="GCP project ID (default: GCP_PROJECT_ID env var)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print entities without inserting"
    )
    
    args = parser.parse_args()
    
    if not args.project_id:
        print("Error: Project ID not provided")
        print("Use --project-id or set GCP_PROJECT_ID environment variable")
        sys.exit(1)
    
    print(f"Project ID: {args.project_id}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    populate_entities(args.project_id, args.dry_run)


if __name__ == "__main__":
    main()
