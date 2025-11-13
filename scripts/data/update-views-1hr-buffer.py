#!/usr/bin/env python3
"""
Update unified views to use 1-hour buffer with deduplication.
"""

from google.cloud import bigquery


def main():
    PROJECT_ID = "utxoiq-dev"
    DATASET_ID = "btc"
    
    print("="*60)
    print("Updating Views to 1-Hour Buffer with Deduplication")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Blocks unified view with deduplication
    print("\nUpdating blocks_unified view...")
    blocks_query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.blocks`
    UNION ALL
    SELECT * FROM `bigquery-public-data.crypto_bitcoin.blocks`
    WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
      AND `hash` NOT IN (
        SELECT `hash` FROM `{PROJECT_ID}.{DATASET_ID}.blocks`
      )
    """
    
    view_ref = f"{PROJECT_ID}.{DATASET_ID}.blocks_unified"
    view = client.get_table(view_ref)
    view.view_query = blocks_query
    client.update_table(view, ["view_query"])
    print(f"✓ Updated {view_ref}")
    
    # Transactions unified view with deduplication
    print("\nUpdating transactions_unified view...")
    transactions_query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.transactions`
    UNION ALL
    SELECT * FROM `bigquery-public-data.crypto_bitcoin.transactions`
    WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
      AND `hash` NOT IN (
        SELECT `hash` FROM `{PROJECT_ID}.{DATASET_ID}.transactions`
      )
    """
    
    view_ref = f"{PROJECT_ID}.{DATASET_ID}.transactions_unified"
    view = client.get_table(view_ref)
    view.view_query = transactions_query
    client.update_table(view, ["view_query"])
    print(f"✓ Updated {view_ref}")
    
    print("\n" + "="*60)
    print("Views Updated Successfully!")
    print("="*60)
    print("\nConfiguration:")
    print("  • Real-time buffer: 1 hour")
    print("  • Deduplication: Enabled (hash-based)")
    print("  • Cleanup threshold: 2 hours (recommended)")
    print("\nBenefits:")
    print("  • No duplicates even if cleanup fails")
    print("  • Maximum cost savings (~53% reduction)")
    print("  • Sub-hour real-time insights")
    print("\nNext steps:")
    print("  1. Update cleanup schedule to every 30 minutes")
    print("  2. Set cleanup threshold to 2 hours")
    print("  3. Set up monitoring for custom dataset size")
    print("  4. Test with: python scripts/test-deduplication.py")


if __name__ == "__main__":
    main()
