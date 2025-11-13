#!/usr/bin/env python3
"""
Real-time Bitcoin block monitoring service
Watches for new blocks and processes them automatically
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

class BlockMonitor:
    """Monitor Bitcoin blockchain for new blocks, transactions, and UTXOs"""
    
    def __init__(self):
        self.rpc = BitcoinRPCClient()
        self.bq = BigQueryClient()
        self.last_height = None
        self.blocks_processed = 0
        self.transactions_processed = 0
        self.utxos_processed = 0
        
    def get_last_processed_height(self):
        """Get the last block height we processed from BigQuery"""
        try:
            query = """
                SELECT MAX(height) as max_height 
                FROM `utxoiq-dev.btc.blocks`
            """
            result = self.bq.client.query(query).result()
            for row in result:
                return row.max_height if row.max_height else 0
        except Exception as e:
            print(f"⚠️  Could not get last height from BigQuery: {e}")
            return None
    
    def process_block(self, height):
        """Fetch and process a single block with transactions and UTXOs"""
        try:
            # Load and execute the backfill-full script's logic
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "backfill_full",
                os.path.join(os.path.dirname(__file__), "backfill-full.py")
            )
            backfill_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backfill_module)
            
            # Use the full backfiller to process this block
            backfiller = backfill_module.FullBackfiller(batch_size=1)
            success = backfiller.process_block(height)
            
            if success:
                backfiller.flush_batches()
                
                self.blocks_processed += 1
                self.transactions_processed += backfiller.transactions_processed
                self.utxos_processed += backfiller.utxos_processed
                
                print(f"✅ Block {height:,} | "
                      f"{backfiller.transactions_processed} txs | "
                      f"{backfiller.utxos_processed} UTXOs")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error processing block {height}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start(self):
        """Start monitoring for new blocks"""
        print("🚀 Starting Bitcoin Block Monitor\n")
        
        # Get current blockchain height
        current_height = self.rpc.get_block_count()
        print(f"📊 Current blockchain height: {current_height:,}")
        
        # Get last processed height from BigQuery
        last_processed = self.get_last_processed_height()
        
        if last_processed:
            print(f"📦 Last processed block: {last_processed:,}")
            self.last_height = last_processed
            
            # Catch up on any missed blocks
            if current_height > last_processed:
                missed = current_height - last_processed
                print(f"⚡ Catching up on {missed} missed blocks...\n")
                
                for height in range(last_processed + 1, current_height + 1):
                    self.process_block(height)
                
                print(f"\n✅ Caught up! Now monitoring for new blocks...\n")
        else:
            print(f"📦 No blocks in BigQuery yet")
            print(f"💡 Processing current block to start...\n")
            self.process_block(current_height)
        
        self.last_height = current_height
        
        # Monitor for new blocks
        print(f"👀 Watching for new blocks (checking every 30 seconds)...")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                time.sleep(30)  # Check every 30 seconds
                
                current_height = self.rpc.get_block_count()
                
                if current_height > self.last_height:
                    # New block(s) found!
                    new_blocks = current_height - self.last_height
                    
                    print(f"\n🔔 {new_blocks} new block(s) detected!")
                    
                    for height in range(self.last_height + 1, current_height + 1):
                        self.process_block(height)
                    
                    self.last_height = current_height
                    print(f"\n👀 Watching for new blocks...")
                    
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Monitor stopped")
            print(f"📊 Summary:")
            print(f"   Blocks: {self.blocks_processed}")
            print(f"   Transactions: {self.transactions_processed:,}")
            print(f"   UTXOs: {self.utxos_processed:,}")

def main():
    monitor = BlockMonitor()
    monitor.start()

if __name__ == '__main__':
    main()
