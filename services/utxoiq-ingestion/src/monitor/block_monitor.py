"""
Bitcoin block monitor that polls Bitcoin Core and ingests blocks locally.
"""

import os
import time
import logging
import json
from decimal import Decimal
from datetime import datetime
from threading import Thread
from typing import Optional

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from Bitcoin RPC."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class BlockMonitor:
    """Monitor Bitcoin Core for new blocks with mempool.space fallback."""
    
    def __init__(
        self,
        rpc_client,
        block_processor,
        bigquery_adapter,
        poll_interval: int = 10,
        mempool_api_url: str = "https://mempool.space/api"
    ):
        """
        Initialize block monitor.
        
        Args:
            rpc_client: Bitcoin RPC client
            block_processor: Block processor instance
            bigquery_adapter: BigQuery adapter instance
            poll_interval: Seconds between checks (default: 10)
            mempool_api_url: mempool.space API URL for fallback
        """
        self.rpc = rpc_client
        self.block_processor = block_processor
        self.bq_adapter = bigquery_adapter
        self.poll_interval = poll_interval
        self.mempool_api_url = mempool_api_url.rstrip('/')
        self.last_processed_height: Optional[int] = None
        self.running = False
        self.thread: Optional[Thread] = None
        self.consecutive_failures = 0
        self.max_failures = 3
        self.using_fallback = False
        
        # Separate session for mempool.space (no Tor proxy)
        import requests
        self.mempool_session = requests.Session()
    
    def get_current_height(self) -> int:
        """Get current blockchain height with fallback to mempool.space."""
        try:
            height = self.rpc.getblockcount()
            self.consecutive_failures = 0
            if self.using_fallback:
                logger.info("✅ Umbrel connection restored, switching back from fallback")
                self.using_fallback = False
            return height
        except Exception as e:
            self.consecutive_failures += 1
            logger.warning(f"⚠️  Umbrel RPC failed ({self.consecutive_failures}/{self.max_failures}): {e}")
            
            if self.consecutive_failures >= self.max_failures:
                if not self.using_fallback:
                    logger.warning("🔄 Switching to mempool.space fallback")
                    self.using_fallback = True
                
                # Fallback to mempool.space
                try:
                    response = self.mempool_session.get(
                        f"{self.mempool_api_url}/blocks/tip/height",
                        timeout=10
                    )
                    response.raise_for_status()
                    return int(response.text)
                except Exception as fallback_error:
                    logger.error(f"❌ mempool.space fallback also failed: {fallback_error}")
                    raise
            else:
                raise
    
    def get_block_data(self, height: int) -> dict:
        """
        Get full block data including transactions with fallback to mempool.space.
        
        Args:
            height: Block height
            
        Returns:
            Block data with transactions
        """
        try:
            block_hash = self.rpc.getblockhash(height)
            # verbosity=2 includes full transaction data
            block_data = self.rpc.getblock(block_hash, 2)
            return block_data
        except Exception as e:
            if self.using_fallback:
                logger.info(f"🔄 Fetching block {height} from mempool.space")
                # Get block hash from mempool.space
                response = self.mempool_session.get(
                    f"{self.mempool_api_url}/block-height/{height}",
                    timeout=10
                )
                response.raise_for_status()
                block_hash = response.text
                
                # Get full block data
                response = self.mempool_session.get(
                    f"{self.mempool_api_url}/block/{block_hash}",
                    timeout=10
                )
                response.raise_for_status()
                block_data = response.json()
                
                # Note: mempool.space doesn't include full tx data by default
                logger.warning("⚠️  Using mempool.space data (limited transaction details)")
                return block_data
            else:
                raise
    
    def process_and_ingest_block(self, block_data: dict) -> bool:
        """
        Process and ingest block data.
        
        Args:
            block_data: Raw block data from Bitcoin Core
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Process block
            processed_block = self.block_processor.process_block(block_data)
            
            # Check if block should be ingested
            if not self.bq_adapter.should_ingest_block(processed_block['timestamp']):
                logger.info(
                    f"Block {processed_block['number']} skipped "
                    f"(older than {self.bq_adapter.realtime_hours} hours)"
                )
                return True  # Not an error, just skipped
            
            # Insert block
            self.bq_adapter.insert_block(processed_block)
            
            # Process and insert transactions if present
            if 'tx' in block_data:
                transactions = []
                
                for tx_data in block_data['tx']:
                    tx = self.block_processor.process_transaction(
                        tx_data,
                        processed_block['hash'],
                        processed_block['number'],
                        processed_block['timestamp']
                    )
                    transactions.append(tx)
                
                # Batch insert transactions
                if transactions:
                    self.bq_adapter.insert_transactions(transactions)
            
            logger.info(
                f"✅ Block {processed_block['number']} ingested "
                f"({processed_block['transaction_count']} transactions)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process block: {e}", exc_info=True)
            return False
    
    def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("=" * 60)
        logger.info("Bitcoin Block Monitor")
        logger.info("=" * 60)
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info(f"Realtime window: {self.bq_adapter.realtime_hours} hour(s)")
        logger.info("=" * 60)
        
        try:
            # Get initial state
            current_height = self.get_current_height()
            
            if self.last_processed_height is None:
                self.last_processed_height = current_height
                logger.info(f"Starting from current tip: {current_height}")
            else:
                logger.info(f"Resuming from height: {self.last_processed_height}")
            
            logger.info("Monitoring for new blocks...")
            logger.info("")
            
            # Main loop
            while self.running:
                try:
                    current_height = self.get_current_height()
                    
                    # Process any new blocks
                    while self.last_processed_height < current_height and self.running:
                        next_height = self.last_processed_height + 1
                        
                        logger.info(f"📦 New block detected: {next_height}")
                        
                        # Get block data
                        block_data = self.get_block_data(next_height)
                        
                        # Process and ingest
                        success = self.process_and_ingest_block(block_data)
                        
                        if success:
                            self.last_processed_height = next_height
                        else:
                            logger.warning(f"Retrying in {self.poll_interval}s...")
                            break
                    
                    # Wait before next check
                    time.sleep(self.poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error in monitor loop: {e}", exc_info=True)
                    time.sleep(self.poll_interval)
        
        except Exception as e:
            logger.error(f"Monitor loop failed: {e}", exc_info=True)
        finally:
            logger.info("Monitor loop stopped")
    
    def start(self):
        """Start the monitor in a background thread."""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self.thread = Thread(target=self.monitor_loop, daemon=True, name="BlockMonitor")
        self.thread.start()
        logger.info("Block monitor started")
    
    def stop(self):
        """Stop the monitor."""
        if not self.running:
            return
        
        logger.info("Stopping block monitor...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Block monitor stopped")
    
    def get_status(self) -> dict:
        """Get monitor status."""
        return {
            "running": self.running,
            "last_processed_height": self.last_processed_height,
            "poll_interval": self.poll_interval,
            "realtime_window_hours": self.bq_adapter.realtime_hours,
            "using_fallback": self.using_fallback,
            "consecutive_failures": self.consecutive_failures,
            "data_source": "mempool.space" if self.using_fallback else "umbrel"
        }
