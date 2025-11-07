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
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'data-ingestion', 'src'))

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from bitcoin_rpc import BitcoinRPCClient, BlockDataNormalizer

# Use mock Pub/Sub for local development (Python 3.14 compatibility)
try:
    from pubsub_streamer import PubSubStreamer
except (ImportError, TypeError) as e:
    logger.warning(f"Could not import real Pub/Sub client: {e}")
    logger.info("Using mock Pub/Sub streamer for local development")
    from pubsub_streamer_mock import PubSubStreamer


class BlockBackfiller:
    """Backfill historical blocks"""
    
    def __init__(self, batch_size: int = 100):
        self.rpc_client = BitcoinRPCClient()
        self.pubsub_streamer = PubSubStreamer()
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
            
            self._print_summary(start_height, end_height)
            
        except KeyboardInterrupt:
            logger.info("\nBackfill interrupted by user")
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
                
                # Normalize and publish block
                normalized_block = self.normalizer.normalize_block(raw_block)
                self.pubsub_streamer.publish_block(normalized_block)
                
                # Process transactions
                transactions = []
                for tx in raw_block.get('tx', []):
                    normalized_tx = self.normalizer.normalize_transaction(tx, height)
                    transactions.append(normalized_tx)
                
                if transactions:
                    self.pubsub_streamer.publish_transactions(transactions, height)
                
                self.blocks_processed += 1
                self.transactions_processed += len(transactions)
                
                # Log every 100 blocks
                if self.blocks_processed % 100 == 0:
                    logger.debug(f"Processed block {height} ({len(transactions)} txs)")
                
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
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Determine block range
    backfiller = BlockBackfiller(batch_size=args.batch_size)
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
    print(f"\nBackfill Configuration:")
    print(f"  Start height: {start_height:,}")
    print(f"  End height: {end_height:,}")
    print(f"  Total blocks: {total_blocks:,}")
    print(f"  Batch size: {args.batch_size}")
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
