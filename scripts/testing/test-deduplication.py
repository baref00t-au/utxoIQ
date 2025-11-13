#!/usr/bin/env python3
"""
Test deduplication behavior of unified views.
"""

from google.cloud import bigquery
from datetime import datetime


def main():
    PROJECT_ID = "utxoiq-dev"
    DATASET_ID = "btc"
    
    print("="*60)
    print("Testing Deduplication Behavior")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Test 1: Check custom dataset size
    print("\nTest 1: Custom dataset size")
    print("-"*60)
    query = f"""
    SELECT 
      COUNT(*) as block_count,
      MIN(timestamp) as oldest_block,
      MAX(timestamp) as newest_block,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MIN(timestamp), HOUR) as oldest_age_hours,
      TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), HOUR) as span_hours
    FROM `{PROJECT_ID}.{DATASET_ID}.blocks`
    """
    
    results = list(client.query(query).result())
    if results and results[0]['block_count'] > 0:
        row = results[0]
        print(f"  Blocks in custom dataset: {row['block_count']}")
        print(f"  Oldest block: {row['oldest_block']}")
        print(f"  Newest block: {row['newest_block']}")
        print(f"  Oldest age: {row['oldest_age_hours']:.1f} hours")
        print(f"  Time span: {row['span_hours']:.1f} hours")
        
        if row['oldest_age_hours'] > 2:
            print(f"  ⚠️  WARNING: Oldest block is {row['oldest_age_hours']:.1f}h old (should be < 2h)")
            print(f"      Cleanup may have failed. Run: curl -X POST .../cleanup?hours=2")
        else:
            print(f"  ✓ Custom dataset size is healthy")
    else:
        print("  Custom dataset is empty (no blocks yet)")
    
    # Test 2: Check for duplicates in unified view
    print("\nTest 2: Duplicate detection")
    print("-"*60)
    query = f"""
    SELECT 
      `hash`,
      COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
    GROUP BY `hash`
    HAVING COUNT(*) > 1
    LIMIT 10
    """
    
    results = list(client.query(query).result())
    if results:
        print(f"  ✗ DUPLICATES FOUND: {len(results)} blocks appear multiple times")
        for row in results[:5]:
            print(f"    - {row['hash']}: {row['count']} times")
        print("\n  This indicates deduplication is not working correctly!")
    else:
        print("  ✓ No duplicates found - deduplication working correctly")
    
    # Test 3: Query performance comparison
    print("\nTest 3: Query performance")
    print("-"*60)
    
    # Query with deduplication
    query_dedup = f"""
    SELECT COUNT(*) as count
    FROM `{PROJECT_ID}.{DATASET_ID}.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
    """
    
    job = client.query(query_dedup)
    results = list(job.result())
    
    print(f"  Blocks in last 2 hours: {results[0]['count']}")
    print(f"  Bytes processed: {job.total_bytes_processed:,}")
    print(f"  Bytes billed: {job.total_bytes_billed:,}")
    print(f"  Query cost: ${job.total_bytes_billed / 1024**4 * 5:.4f}")
    
    # Test 4: Coverage check
    print("\nTest 4: Coverage check")
    print("-"*60)
    query = f"""
    WITH time_buckets AS (
      SELECT 
        TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
        COUNT(*) as blocks
      FROM `{PROJECT_ID}.{DATASET_ID}.blocks_unified`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      GROUP BY hour
      ORDER BY hour DESC
    )
    SELECT 
      hour,
      blocks,
      CASE 
        WHEN blocks < 3 THEN '⚠️  Low'
        WHEN blocks > 10 THEN '⚠️  High'
        ELSE '✓ Normal'
      END as status
    FROM time_buckets
    LIMIT 24
    """
    
    results = list(client.query(query).result())
    print(f"  Hourly block distribution (last 24 hours):")
    for row in results[:12]:  # Show last 12 hours
        print(f"    {row['hour']}: {row['blocks']:3d} blocks {row['status']}")
    
    # Test 5: Recommend cleanup if needed
    print("\nTest 5: Cleanup recommendation")
    print("-"*60)
    query = f"""
    SELECT 
      COUNT(*) as total_blocks,
      TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MIN(timestamp), HOUR) as oldest_age_hours
    FROM `{PROJECT_ID}.{DATASET_ID}.blocks`
    """
    
    results = list(client.query(query).result())
    if results and results[0]['total_blocks'] > 0:
        row = results[0]
        if row['oldest_age_hours'] > 2:
            print(f"  ⚠️  CLEANUP RECOMMENDED")
            print(f"     Custom dataset has {row['total_blocks']} blocks")
            print(f"     Oldest block is {row['oldest_age_hours']:.1f} hours old")
            print(f"\n  Run cleanup:")
            print(f"     curl -X POST https://feature-engine-xxx.run.app/cleanup?hours=2")
        else:
            print(f"  ✓ No cleanup needed")
            print(f"     Custom dataset: {row['total_blocks']} blocks")
            print(f"     Oldest age: {row['oldest_age_hours']:.1f} hours")
    else:
        print("  ℹ️  Custom dataset is empty")
    
    print("\n" + "="*60)
    print("Deduplication Test Complete")
    print("="*60)


if __name__ == "__main__":
    main()
