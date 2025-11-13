"""
Real-time Bitcoin block monitor.
Polls Bitcoin Core for new blocks and sends them to feature-engine service.
"""

import os
import sys
import time
import logging
import requests
import json
from decimal import Decimal
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from Bitcoin RPC."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class BlockMonitor:
    """Monitor Bitcoin Core for new blocks and send to feature-engine."""
    
    def __init__(
        self,
        rpc_url: str,
        feature_engine_url: str,
        poll_interval: int = 10
    ):
        """
        Initialize block monitor.
        
        Args:
            rpc_url: Bitcoin Core RPC URL
            feature_engine_url: Feature engine service URL
            poll_interval: Seconds between checks (default: 10)
        """
        self.rpc = AuthServiceProxy(rpc_url)
        self.feature_engine_url = feature_engine_url.rstrip('/')
        self.poll_interval = poll_interval
        self.last_processed_height = None
        self.session = requests.Session()
    
    def get_last_ingested_height(self) -> int:
        """
        Get the last block height from the ingestion service.
        
        Returns:
            Last processed block height, or None if unavailable
        """
        try:
            response = self.session.get(
                f"{self.feature_engine_url}/status",
                timeout=10
            )
            response.raise_for_status()
            
            status = response.json()
            return status.get('latest_block_height')
            
        except Exception as e:
            logger.warning(f"Could not get last ingested height: {e}")
            return None
        
    def get_current_height(self) -> int:
        """Get current blockchain height."""
        return self.rpc.getblockcount()
    
    def get_block_data(self, height: int) -> dict:
        """
        Get full block data including transactions.
        
        Args:
            height: Block height
            
        Returns:
            Block data with transactions
        """
        block_hash = self.rpc.getblockhash(height)
        # verbosity=2 includes full transaction data
        block_data = self.rpc.getblock(block_hash, 2)
        return block_data
    
    def send_to_feature_engine(self, block_data: dict) -> bool:
        """
        Send block data to feature-engine service.
        
        Args:
            block_data: Block data from Bitcoin Core
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to JSON string with Decimal handling, then send
            json_data = json.dumps(block_data, cls=DecimalEncoder)
            
            response = requests.post(
                f"{self.feature_engine_url}/ingest/block",
                data=json_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Block {block_data['height']} ingested: {result['status']}")
            
            if result['status'] == 'skipped':
                logger.info(f"   Reason: {result['reason']}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send block {block_data['height']}: {e}")
            return False
    
    def start(self, start_height: int = None):
        """
        Start monitoring for new blocks.
        
        Args:
            start_height: Block height to start from (default: current tip)
        """
        logger.info("=" * 60)
        logger.info("Bitcoin Block Monitor")
        logger.info("=" * 60)
        logger.info(f"RPC: {self.rpc.url}")
        logger.info(f"Feature Engine: {self.feature_engine_url}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info("=" * 60)
        
        try:
            # Get initial state
            current_height = self.get_current_height()
            
            if start_height is not None:
                self.last_processed_height = start_height - 1
                logger.info(f"Starting from height: {start_height}")
            else:
                self.last_processed_height = current_height
                logger.info(f"Starting from current tip: {current_height}")
            
            logger.info("Monitoring for new blocks... (Ctrl+C to stop)")
            logger.info("")
            
            # Main loop
            while True:
                try:
                    current_height = self.get_current_height()
                    
                    # Process any new blocks
                    while self.last_processed_height < current_height:
                        next_height = self.last_processed_height + 1
                        
                        logger.info(f"📦 New block detected: {next_height}")
                        
                        # Get block data
                        block_data = self.get_block_data(next_height)
                        
                        # Send to feature-engine
                        success = self.send_to_feature_engine(block_data)
                        
                        if success:
                            self.last_processed_height = next_height
                            logger.info(f"   Transactions: {len(block_data.get('tx', []))}")
                            logger.info(f"   Timestamp: {datetime.fromtimestamp(block_data['time'])}")
                            logger.info("")
                        else:
                            logger.warning(f"   Retrying in {self.poll_interval}s...")
                            break
                    
                    # Wait before next check
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    logger.info("")
                    logger.info("Shutting down gracefully...")
                    break
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    time.sleep(self.poll_interval)
        
        except Exception as e:
            logger.error(f"Failed to start monitor: {e}", exc_info=True)
            raise


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Bitcoin Core for new blocks')
    parser.add_argument(
        '--rpc-url',
        default=os.getenv('BITCOIN_RPC_URL'),
        help='Bitcoin Core RPC URL (default: from BITCOIN_RPC_URL env var)'
    )
    parser.add_argument(
        '--feature-engine-url',
        default='https://feature-engine-544291059247.us-central1.run.app',
        help='Feature engine service URL'
    )
    parser.add_argument(
        '--start-height',
        type=int,
        help='Block height to start from (default: current tip)'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=10,
        help='Seconds between checks (default: 10)'
    )
    
    args = parser.parse_args()
    
    if not args.rpc_url:
        logger.error("Error: Bitcoin RPC URL not provided")
        logger.error("Set BITCOIN_RPC_URL environment variable or use --rpc-url")
        sys.exit(1)
    
    monitor = BlockMonitor(
        rpc_url=args.rpc_url,
        feature_engine_url=args.feature_engine_url,
        poll_interval=args.poll_interval
    )
    
    monitor.start(start_height=args.start_height)


if __name__ == '__main__':
    main()
