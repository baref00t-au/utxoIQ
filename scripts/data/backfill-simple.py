#!/usr/bin/env python3
"""
Simple backfill script that writes directly to BigQuery
Compatible with Python 3.12 and BigQuery free tier
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

from dotenv import load_dotenv
load_dotenv()

from bitcoin_rpc import BitcoinRPCClient
from bigquery_client import BigQueryClient

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Backfill Bitcoin blocks to BigQuery')
    parser.add_argument('--start', type=int, required=True, help='Starting block height')
    parser.add_argument('--end', type=int, help='Ending block height (default: current tip)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size (default: 100)')
    args = parser.parse_args()
    
    print("🚀 Starting BigQuery Backfill\n")
    
    # Initialize clients
    rpc = BitcoinRPCClient()
    bq = BigQueryClient()
    
    current_height = rpc.get_block_count()
    end_height = args.end if args.end else current_height
    
    print(f"📊 Configuration:")
    print(f"   Start: {args.start:,}")
    print(f"   End: {end_height:,}")
    print(f"   Total: {end_height - args.start + 1:,} blocks")
    print(f"   Batch size: {args.batch_size}\n")
    
    response = input("Proceed? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled")
        return
    
    start_time = time.time()
    blocks_processed = 0
    batch = []
    
    for height in range(args.start, end_height + 1):
        try:
            # Fetch block
            block_hash = rpc.get_block_hash(height)
            block_data = rpc.get_block(block_hash, verbosity=2)
            
            # Prepare for BigQuery
            block_row = {
                "block_hash": block_data.get("hash"),
                "height": block_data.get("height"),
                "timestamp": datetime.fromtimestamp(block_data.get("time")).isoformat(),
                "size": block_data.get("size"),
                "tx_count": len(block_data.get("tx", [])),
                "fees_total": 0,  # Calculate if needed
            }
            
            batch.append(block_row)
            blocks_processed += 1
            
            # Write batch when full
            if len(batch) >= args.batch_size:
                bq.stream_blocks(batch)
                elapsed = time.time() - start_time
                rate = blocks_processed / elapsed if elapsed > 0 else 0
                progress = (blocks_processed / (end_height - args.start + 1)) * 100
                print(f"Progress: {progress:.1f}% | Blocks: {blocks_processed:,} | Rate: {rate:.1f}/sec")
                batch = []
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error at block {height}: {e}")
            continue
    
    # Write remaining batch
    if batch:
        bq.stream_blocks(batch)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Complete!")
    print(f"   Blocks processed: {blocks_processed:,}")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"   Rate: {blocks_processed/elapsed:.1f} blocks/sec")

if __name__ == '__main__':
    main()
