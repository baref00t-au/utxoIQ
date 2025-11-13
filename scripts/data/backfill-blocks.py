#!/usr/bin/env python3
"""
Backfill script for processing historical Bitcoin blocks
Processes blocks in batches with progress tracking
"""

import os
import sys
import time
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from bitcoin_rpc import BitcoinRPCClient, BlockDataNormalizer
from bigquery_writer import BigQueryWriter
from bigquery_client import BigQueryClient


class BigQueryStorage:
    """Store blocks and transactions to BigQuery"""
    
    def __init__(self):
        self.bq_client = BigQueryClient()
        self.blocks_buffer = []
        self.transactions_buffer = []
        self.buffer_size = 100  # Stream every 100 blocks
        
        # Verify tables exist
        if not self.bq_client.check_tables_exist():
            raise RuntimeError("BigQuery tables not found. Run setup-bigquery.py first.")
        
        logger.info(f"Streaming data to BigQuery: {self.bq_client.project_id}")
    
    def save_block(self, block_data: dict):
        """Buffer block data for streaming"""
        self.blocks_buffer.append(block_data)
        
        # Flush if buffer is full
        if len(self.blocks_buffer) >= self.buffer_size:
            self.flush_blocks()
    
    def save_transactions(self, transactions: list, block_height: int):
        """Buffer transactions for streaming"""
        if not transactions:
            return
        
        self.transactions_buffer.extend(transactions)
        
        # Flush if buffer is full
        if len(self.transactions_buffer) >= self.buffer_size * 10:  # Larger buffer for txs
            self.flush_transactions()
    
    def flush_blocks(self):
        """Flush blocks buffer to BigQuery"""
        if not self.blocks_buffer:
            return
        
        try:
            count = self.bq_client.stream_blocks(self.blocks_buffer)
            logger.info(f"Streamed {count} blocks to BigQuery")
            self.blocks_buffer = []
        except Exception as e:
            logger.error(f"Failed to stream blocks: {str(e)}")
            # Keep buffer for retry
    
    def flush_transactions(self):
        """Flush transactions buffer to BigQuery"""
        if not self.transactions_buffer:
            return
        
        try:
            count = self.bq_client.stream_transactions(self.transactions_buffer)
            logger.info(f"Streamed {count} transactions to BigQuery")
            self.transactions_buffer = []
        except Exception as e:
            logger.error(f"Failed to stream transactions: {str(e)}")
            # Keep buffer for retry
    
    def flush_all(self):
        """Flush all buffers"""
        self.flush_blocks()
        self.flush_transactions()


class FileStorage:
    """Store blocks and transactions to local files"""
    
    def __init__(self, output_dir: str = "data/backfill"):
        self.output_dir = Path(output_dir)
        self.blocks_dir = self.output_dir / "blocks"
        self.transactions_dir = self.output_dir / "transactions"
        
        # Create directories
        self.blocks_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Storing data to: {self.output_dir.absolute()}")
    
    def save_block(self, block_data: dict):
        """Save block data to JSON file"""
        block_height = block_data.get('height')
        # Group blocks in subdirectories by 10k blocks
        subdir = self.blocks_dir / f"{(block_height // 10000) * 10000:07d}"
        subdir.mkdir(exist_ok=True)
        
        filepath = subdir / f"block_{block_height:07d}.json"
        with open(filepath, 'w') as f:
            json.dump(block_data, f, indent=2)
    
    def save_transactions(self, transactions: list, block_height: int):
        """Save transactions to JSON file"""
        if not transactions:
            return
        
        # Group transactions in subdirectories by 10k blocks
        subdir = self.transactions_dir / f"{(block_height // 10000) * 10000:07d}"
        subdir.mkdir(exist_ok=True)
        
        filepath = subdir / f"txs_{block_height:07d}.json"
        with open(filepath, 'w') as f:
            json.dump(transactions, f, indent=2)


class BlockBackfiller:
    """Backfill historical blocks"""
    
    def __init__(self, batch_size: int = 100, use_bigquery: bool = True):
        self.rpc_client = BitcoinRPCClient()
        self.use_bigquery = use_bigquery
        
        if use_bigquery:
            self.storage = BigQueryStorage()
        else:
            self.storage = FileStorage("data/backfill")
        
        self.normalizer = BlockDataNormalizer()
        self.batch_size = batch_size
        
        self.blocks_processed = 0
        self.transactions_processed = 0
        self.start_time = None
    
    def backfill(self, start_height: int, end_height: int = None):
        """
        Backfill blocks from start_height to end_height
        
        Args:
            start_height: First block to process
            end_height: Last block to process (None = current tip)
        """
        self.start_time = time.time()
        
        # Get current blockchain height
        current_height = self.rpc_client.get_block_count()
        
        if end_height is None:
            end_height = current_height
        
        # Validate range
        if start_height < 0:
            start_height = 0
        if end_height > current_height:
            end_height = current_height
        
        total_blocks = end_height - start_height + 1
        
        logger.info(f"Starting backfill from block {start_height} to {end_height}")
        logger.info(f"Total blocks to process: {total_blocks:,}")
        
        try:
            current = start_height
            
            while current <= end_height:
                batch_end = min(current + self.batch_size - 1, end_height)
                self._process_batch(current, batch_end)
                
                # Progress update
                progress = ((current - start_height + 1) / total_blocks) * 100
                elapsed = time.time() - self.start_time
                rate = self.blocks_processed / elapsed if elapsed > 0 else 0
                eta = (total_blocks - self.blocks_processed) / rate if rate > 0 else 0
                
                logger.info(
                    f"Progress: {progress:.1f}% | "
                    f"Blocks: {self.blocks_processed:,}/{total_blocks:,} | "
                    f"Rate: {rate:.1f} blocks/sec | "
                    f"ETA: {eta/60:.1f} min"
                )
                
                current = batch_end + 1
            
            # Flush any remaining data
            if hasattr(self.storage, 'flush_all'):
                logger.info("Flushing remaining data to BigQuery...")
                self.storage.flush_all()
            
            self._print_summary(start_height, end_height)
            
        except KeyboardInterrupt:
            logger.info("\nBackfill interrupted by user")
            # Flush any remaining data
            if hasattr(self.storage, 'flush_all'):
                logger.info("Flushing remaining data to BigQuery...")
                self.storage.flush_all()
            self._print_summary(start_height, current - 1)
        except Exception as e:
            logger.error(f"Backfill failed: {str(e)}", exc_info=True)
            raise
    
    def _process_batch(self, start: int, end: int):
        """Process a batch of blocks"""
        for height in range(start, end + 1):
            try:
                # Get block data
                block_hash = self.rpc_client.get_block_hash(height)
                raw_block = self.rpc_client.get_block(block_hash, verbosity=2)
                
                # Normalize and save block
                normalized_block = self.normalizer.normalize_block(raw_block)
                self.storage.save_block(normalized_block)
                
                # Process transactions
                transactions = []
                for tx in raw_block.get('tx', []):
                    normalized_tx = self.normalizer.normalize_transaction(tx, height)
                    transactions.append(normalized_tx)
                
                if transactions:
                    self.storage.save_transactions(transactions, height)
                
                self.blocks_processed += 1
                self.transactions_processed += len(transactions)
                
                # Log every 100 blocks
                if self.blocks_processed % 100 == 0:
                    logger.info(f"Saved block {height} ({len(transactions)} txs)")
                
            except Exception as e:
                logger.error(f"Error processing block {height}: {str(e)}")
                # Continue with next block
    
    def _print_summary(self, start_height: int, end_height: int):
        """Print backfill summary"""
        elapsed = time.time() - self.start_time
        rate = self.blocks_processed / elapsed if elapsed > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("Backfill Summary")
        logger.info("=" * 60)
        logger.info(f"Block range: {start_height:,} to {end_height:,}")
        logger.info(f"Blocks processed: {self.blocks_processed:,}")
        logger.info(f"Transactions processed: {self.transactions_processed:,}")
        logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
        logger.info(f"Average rate: {rate:.2f} blocks/sec")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Backfill historical Bitcoin blocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process last 1000 blocks
  python backfill-blocks.py --last 1000
  
  # Process specific range
  python backfill-blocks.py --start 800000 --end 801000
  
  # Process from genesis to block 10000
  python backfill-blocks.py --start 0 --end 10000
  
  # Process all blocks from genesis
  python backfill-blocks.py --from-genesis
        """
    )
    
    parser.add_argument(
        '--start',
        type=int,
        help='Starting block height'
    )
    parser.add_argument(
        '--end',
        type=int,
        help='Ending block height (default: current tip)'
    )
    parser.add_argument(
        '--last',
        type=int,
        help='Process last N blocks from current tip'
    )
    parser.add_argument(
        '--from-genesis',
        action='store_true',
        help='Process all blocks from genesis (height 0)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of blocks to process per batch (default: 100)'
    )
    parser.add_argument(
        '--use-files',
        action='store_true',
        help='Write to local files instead of BigQuery (default: stream to BigQuery)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Determine block range
    use_bigquery = not args.use_files
    backfiller = BlockBackfiller(batch_size=args.batch_size, use_bigquery=use_bigquery)
    rpc_client = BitcoinRPCClient()
    current_height = rpc_client.get_block_count()
    
    if args.from_genesis:
        start_height = 0
        end_height = current_height
    elif args.last:
        start_height = max(0, current_height - args.last + 1)
        end_height = current_height
    elif args.start is not None:
        start_height = args.start
        end_height = args.end if args.end is not None else current_height
    else:
        parser.error("Must specify --start, --last, or --from-genesis")
        return
    
    # Confirm with user
    total_blocks = end_height - start_height + 1
    storage_type = "local files" if args.use_files else "BigQuery"
    print(f"\nBackfill Configuration:")
    print(f"  Start height: {start_height:,}")
    print(f"  End height: {end_height:,}")
    print(f"  Total blocks: {total_blocks:,}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Storage: {storage_type}")
    print(f"  Current tip: {current_height:,}")
    
    if total_blocks > 10000:
        print(f"\n⚠️  Warning: Processing {total_blocks:,} blocks will take significant time!")
        print(f"  Estimated time: {(total_blocks / 10) / 60:.1f} hours at 10 blocks/sec")
    
    response = input("\nProceed with backfill? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Backfill cancelled")
        return
    
    # Start backfill
    backfiller.backfill(start_height, end_height)


if __name__ == '__main__':
    main()
