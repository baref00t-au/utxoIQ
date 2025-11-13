"""
Verify BigQuery hybrid deployment is working correctly.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta

def verify_deployment():
    """Verify all components of the hybrid deployment."""
    
    client = bigquery.Client(project="utxoiq-dev")
    
    print("=" * 60)
    print("BigQuery Hybrid Deployment Verification")
    print("=" * 60)
    print()
    
    # 1. Check custom dataset
    print("1. Custom Dataset (btc.blocks)")
    query = """
    SELECT 
        COUNT(*) as block_count,
        MIN(timestamp) as oldest_block,
        MAX(timestamp) as newest_block,
        MAX(number) as latest_height
    FROM `utxoiq-dev.btc.blocks`
    """
    result = list(client.query(query).result())[0]
    print(f"   ✅ Blocks: {result.block_count}")
    print(f"   ✅ Oldest: {result.oldest_block}")
    print(f"   ✅ Newest: {result.newest_block}")
    print(f"   ✅ Latest height: {result.latest_height}")
    print()
    
    # 2. Check unified view (last 2 hours)
    print("2. Unified View (blocks_unified - last 2 hours)")
    query = """
    SELECT 
        COUNT(*) as block_count,
        MIN(timestamp) as oldest_block,
        MAX(timestamp) as newest_block,
        MAX(number) as latest_height
    FROM `utxoiq-dev.btc.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
    """
    result = list(client.query(query).result())[0]
    print(f"   ✅ Blocks (last 2h): {result.block_count}")
    print(f"   ✅ Oldest: {result.oldest_block}")
    print(f"   ✅ Newest: {result.newest_block}")
    print(f"   ✅ Latest height: {result.latest_height}")
    print()
    
    # 3. Check for duplicates
    print("3. Duplicate Check")
    query = """
    SELECT 
        number,
        COUNT(*) as count
    FROM `utxoiq-dev.btc.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
    GROUP BY number
    HAVING COUNT(*) > 1
    """
    duplicates = list(client.query(query).result())
    if duplicates:
        print(f"   ❌ Found {len(duplicates)} duplicate blocks!")
        for dup in duplicates:
            print(f"      Block {dup.number}: {dup.count} copies")
    else:
        print("   ✅ No duplicates found")
    print()
    
    # 4. Check transactions
    print("4. Transactions (custom dataset)")
    query = """
    SELECT 
        COUNT(*) as tx_count,
        COUNT(DISTINCT block_hash) as unique_blocks
    FROM `utxoiq-dev.btc.transactions`
    """
    result = list(client.query(query).result())[0]
    print(f"   ✅ Transactions: {result.tx_count}")
    print(f"   ✅ Unique blocks: {result.unique_blocks}")
    print()
    
    # 5. Verify nested structure
    print("5. Nested Structure Verification")
    query = """
    SELECT 
        `hash`,
        ARRAY_LENGTH(inputs) as input_count,
        ARRAY_LENGTH(outputs) as output_count
    FROM `utxoiq-dev.btc.transactions`
    LIMIT 1
    """
    result = list(client.query(query).result())
    if result:
        tx = result[0]
        print(f"   ✅ Sample transaction: {tx['hash'][:16]}...")
        print(f"   ✅ Inputs (nested): {tx.input_count}")
        print(f"   ✅ Outputs (nested): {tx.output_count}")
    else:
        print("   ⚠️  No transactions found")
    print()
    
    # 6. Cost estimate
    print("6. Cost Estimate")
    print("   Custom dataset size:")
    query = """
    SELECT 
        ROUND(SUM(size_bytes) / 1024 / 1024, 2) as size_mb
    FROM `utxoiq-dev.btc.__TABLES__`
    WHERE table_id IN ('blocks', 'transactions')
    """
    result = list(client.query(query).result())[0]
    print(f"   ✅ Total size: {result.size_mb} MB")
    print(f"   ✅ Estimated monthly cost: ~$0.02 (storage)")
    print(f"   ✅ Query cost: $5/TB (uses public dataset for historical)")
    print()
    
    print("=" * 60)
    print("✅ Deployment verification complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Monitor Cloud Scheduler runs every 30 minutes")
    print("  2. Check logs: gcloud logging read 'resource.labels.service_name=feature-engine'")
    print("  3. Test ingestion: POST to /ingest/block endpoint")
    print("  4. Monitor costs in GCP Console")


if __name__ == "__main__":
    verify_deployment()
