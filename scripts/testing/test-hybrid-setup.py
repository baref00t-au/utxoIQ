#!/usr/bin/env python3
"""
Test the hybrid BigQuery setup with sample queries.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta


def run_query(client: bigquery.Client, query: str, description: str):
    """Run a query and print results."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"{'='*60}")
    print(f"Query:\n{query}\n")
    
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        
        print(f"✓ Query successful!")
        print(f"  Rows returned: {len(results)}")
        print(f"  Bytes processed: {query_job.total_bytes_processed:,}")
        print(f"  Bytes billed: {query_job.total_bytes_billed:,}")
        
        if results:
            print(f"\nSample results (first 3 rows):")
            for i, row in enumerate(results[:3]):
                print(f"  Row {i+1}: {dict(row)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Query failed: {str(e)}")
        return False


def main():
    """Run test queries."""
    PROJECT_ID = "utxoiq-dev"
    DATASET_ID = "btc"
    
    print("="*60)
    print("BigQuery Hybrid Setup Tests")
    print("="*60)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Query public dataset directly
    query1 = """
    SELECT 
        number,
        `hash`,
        timestamp,
        transaction_count
    FROM `bigquery-public-data.crypto_bitcoin.blocks`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
      AND timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY number DESC
    LIMIT 5
    """
    if run_query(client, query1, "Query public dataset (historical blocks 24-48h ago)"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: Query custom dataset (should be empty for now)
    query2 = f"""
    SELECT 
        number,
        `hash`,
        timestamp,
        transaction_count
    FROM `{PROJECT_ID}.{DATASET_ID}.blocks`
    ORDER BY number DESC
    LIMIT 5
    """
    if run_query(client, query2, "Query custom dataset (real-time blocks)"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 3: Query unified view
    query3 = f"""
    SELECT 
        number,
        `hash`,
        timestamp,
        transaction_count
    FROM `{PROJECT_ID}.{DATASET_ID}.blocks_unified`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
    ORDER BY number DESC
    LIMIT 5
    """
    if run_query(client, query3, "Query unified view (combines both datasets)"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 4: Query transactions with nested fields
    query4 = """
    SELECT 
        `hash`,
        block_number,
        block_timestamp,
        input_count,
        output_count,
        fee,
        ARRAY_LENGTH(inputs) as inputs_array_length,
        ARRAY_LENGTH(outputs) as outputs_array_length
    FROM `bigquery-public-data.crypto_bitcoin.transactions`
    WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
      AND block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY block_number DESC
    LIMIT 5
    """
    if run_query(client, query4, "Query transactions with nested inputs/outputs"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 5: Unnest inputs from transactions
    query5 = """
    SELECT 
        t.`hash` as tx_hash,
        t.block_number,
        input.`index` as input_index,
        input.spent_transaction_hash,
        input.value
    FROM `bigquery-public-data.crypto_bitcoin.transactions` t,
    UNNEST(t.inputs) as input
    WHERE t.block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
      AND t.block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY t.block_number DESC
    LIMIT 5
    """
    if run_query(client, query5, "Unnest inputs from transactions"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Unnest outputs from transactions
    query6 = """
    SELECT 
        t.`hash` as tx_hash,
        t.block_number,
        output.`index` as output_index,
        output.`type`,
        output.value,
        output.addresses
    FROM `bigquery-public-data.crypto_bitcoin.transactions` t,
    UNNEST(t.outputs) as output
    WHERE t.block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
      AND t.block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY t.block_number DESC
    LIMIT 5
    """
    if run_query(client, query6, "Unnest outputs from transactions"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 7: Check data freshness
    query7 = """
    SELECT 
        MAX(timestamp) as latest_block_time,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(timestamp), HOUR) as hours_behind,
        COUNT(*) as total_blocks
    FROM `bigquery-public-data.crypto_bitcoin.blocks`
    """
    if run_query(client, query7, "Check public dataset freshness"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print(f"Success rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
    print("="*60)
    
    if tests_failed == 0:
        print("\n✓ All tests passed! Hybrid setup is working correctly.")
        print("\nNext steps:")
        print("  1. Backfill recent blocks when Bitcoin Core is available")
        print("  2. Deploy feature-engine service for real-time ingestion")
        print("  3. Update application queries to use *_unified views")
    else:
        print(f"\n⚠ {tests_failed} test(s) failed. Review errors above.")


if __name__ == "__main__":
    main()
