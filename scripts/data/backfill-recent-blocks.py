#!/usr/bin/env python3
"""
Backfill recent blocks (last 24 hours) into custom BigQuery dataset.
Run this after setting up the hybrid dataset to populate initial data.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Add service path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'feature-engine', 'src'))

# Import only what we need to avoid numpy issues
from google.cloud import bigquery
import logging

# Import our modules directly
from adapters.bigquery_adapter import BigQueryAdapter

# Import processor module directly to avoid __init__.py imports
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bitcoin_block_processor",
    os.path.join(os.path.dirname(__file__), '..', 'services', 'feature-engine', 'src', 'processors', 'bitcoin_block_processor.py')
)
bitcoin_block_processor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bitcoin_block_processor)
BitcoinBlockProcessor = bitcoin_block_processor.BitcoinBlockProcessor

logging.basicConfig(level=logging.INFO)

try:
    from bitcoinrpc.authproxy import AuthServiceProxy
except ImportError:
    print("Error: python-bitcoinrpc not installed")
    print("Install with: pip install python-bitcoinrpc")
    sys.exit(1)


def backfill_blocks(
    rpc_url: str,
    start_height: Optional[int] = None,
    end_height: Optional[int] = None
):
    """
    Backfill blocks into BigQuery custom dataset.
    
    Args:
        rpc_url: Bitcoin Core RPC URL (e.g., http://user:pass@localhost:8332)
        start_height: Starting block height (default: current - 144)
        end_height: Ending block height (default: current)
    """
    print("Connecting to Bitcoin Core...")
    rpc = AuthServiceProxy(rpc_url)
    
    # Get current block height
    current_height = rpc.getblockcount()
    print(f"Current block height: {current_height}")
    
    # Default to last 144 blocks (approximately 24 hours)
    if start_height is None:
        start_height = current_height - 144
    
    if end_height is None:
        end_height = current_height
    
    print(f"Backfilling blocks {start_height} to {end_height}")
    print(f"Total blocks: {end_height - start_height + 1}")
    
    # Initialize adapters
    bq_adapter = BigQueryAdapter()
    processor = BitcoinBlockProcessor()
    
    # Track statistics
    blocks_inserted = 0
    blocks_skipped = 0
    errors = 0
    
    # Process blocks
    for height in range(start_height, end_height + 1):
        try:
            # Get block data
            block_hash = rpc.getblockhash(height)
            block_data = rpc.getblock(block_hash, 2)  # Verbosity 2 includes transactions
            
            # Process block
            processed_block = processor.process_block(block_data)
            
            # Check if should ingest
            if not bq_adapter.should_ingest_block(processed_block['timestamp']):
                blocks_skipped += 1
                print(f"[SKIP] Block {height} (too old: {processed_block['timestamp']})")
                continue
            
            # Insert block
            bq_adapter.insert_block(processed_block)
            
            # Process transactions
            if 'tx' in block_data:
                transactions = []
                all_inputs = []
                all_outputs = []
                
                for tx_data in block_data['tx']:
                    # Process transaction
                    tx = processor.process_transaction(
                        tx_data,
                        processed_block['hash'],
                        processed_block['number'],
                        processed_block['timestamp']
                    )
                    transactions.append(tx)
                    
                    # Process inputs and outputs
                    inputs = processor.process_inputs(
                        tx_data,
                        processed_block['timestamp']
                    )
                    outputs = processor.process_outputs(
                        tx_data,
                        processed_block['timestamp']
                    )
                    
                    all_inputs.extend(inputs)
                    all_outputs.extend(outputs)
                
                # Batch insert
                bq_adapter.insert_transactions(transactions)
                bq_adapter.insert_inputs(all_inputs)
                bq_adapter.insert_outputs(all_outputs)
            
            blocks_inserted += 1
            print(f"[OK] Backfilled block {height} ({processed_block['transaction_count']} txs)")
            
        except Exception as e:
            errors += 1
            print(f"[ERROR] Block {height}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary
    print("\n" + "="*60)
    print("Backfill Summary")
    print("="*60)
    print(f"Blocks inserted: {blocks_inserted}")
    print(f"Blocks skipped:  {blocks_skipped}")
    print(f"Errors:          {errors}")
    print(f"Success rate:    {blocks_inserted / (end_height - start_height + 1) * 100:.1f}%")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Backfill recent Bitcoin blocks into BigQuery"
    )
    parser.add_argument(
        "--rpc-url",
        default="http://user:pass@localhost:8332",
        help="Bitcoin Core RPC URL"
    )
    parser.add_argument(
        "--start-height",
        type=int,
        help="Starting block height (default: current - 144)"
    )
    parser.add_argument(
        "--end-height",
        type=int,
        help="Ending block height (default: current)"
    )
    
    args = parser.parse_args()
    
    try:
        backfill_blocks(
            rpc_url=args.rpc_url,
            start_height=args.start_height,
            end_height=args.end_height
        )
    except KeyboardInterrupt:
        print("\n\nBackfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        sys.exit(1)
