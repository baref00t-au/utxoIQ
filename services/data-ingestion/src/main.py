"""
Main data ingestion service for utxoIQ platform
Monitors Bitcoin blockchain and streams data to Cloud Pub/Sub
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Load .env FIRST before any other imports that use environment variables
from dotenv import load_dotenv
load_dotenv()  # This will look for .env in current directory or parent directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Now import modules that use environment variables
from bitcoin_rpc import BitcoinRPCClient, BlockDataNormalizer, MempoolAnalyzer, ReorgDetector

# Use mock Pub/Sub for local development (Python 3.14 compatibility)
try:
    from pubsub_streamer import PubSubStreamer
except (ImportError, TypeError) as e:
    logger.warning(f"Could not import real Pub/Sub client: {e}")
    logger.info("Using mock Pub/Sub streamer for local development")
    from pubsub_streamer_mock import PubSubStreamer


class BlockchainIngestionService:
    """Main service for ingesting blockchain data"""
    
    def __init__(self, start_height: int = None):
        self.rpc_client = BitcoinRPCClient()
        self.pubsub_streamer = PubSubStreamer()
        self.normalizer = BlockDataNormalizer()
        self.mempool_analyzer = MempoolAnalyzer()
        self.reorg_detector = ReorgDetector()
        
        self.start_height = start_height
        self.last_processed_height = 0
        self.poll_interval = int(os.getenv('BLOCK_POLL_INTERVAL', '10'))  # seconds
        self.mempool_poll_interval = int(os.getenv('MEMPOOL_POLL_INTERVAL', '60'))  # seconds
        self.last_mempool_check = 0
    
    def start(self):
        """Start the ingestion service"""
        logger.info("Starting blockchain ingestion service...")
        
        try:
            # Get initial blockchain state
            blockchain_info = self.rpc_client.get_blockchain_info()
            
            # Determine starting height
            if self.start_height is not None:
                self.last_processed_height = self.start_height - 1
                logger.info(f"Starting from configured height: {self.start_height}")
            else:
                # Default: start from current tip
                self.last_processed_height = blockchain_info['blocks']
                logger.info(f"Starting from current block height: {self.last_processed_height}")
            
            # Main processing loop
            while True:
                try:
                    self._process_new_blocks()
                    self._process_mempool()
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Shutting down gracefully...")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {str(e)}", exc_info=True)
                    time.sleep(self.poll_interval)
                    
        except Exception as e:
            logger.error(f"Failed to start ingestion service: {str(e)}", exc_info=True)
            raise
    
    def _process_new_blocks(self):
        """Check for and process new blocks"""
        try:
            current_height = self.rpc_client.get_block_count()
            
            # Process any new blocks
            while self.last_processed_height < current_height:
                next_height = self.last_processed_height + 1
                
                try:
                    # Get block data
                    block_hash = self.rpc_client.get_block_hash(next_height)
                    raw_block = self.rpc_client.get_block(block_hash, verbosity=2)
                    
                    # Check for reorg
                    reorg_info = self.reorg_detector.check_for_reorg(raw_block)
                    if reorg_info and reorg_info['depth'] > 1:
                        logger.warning(f"Blockchain reorg detected: {reorg_info}")
                        self._handle_reorg(reorg_info)
                    
                    # Normalize and publish block data
                    normalized_block = self.normalizer.normalize_block(raw_block)
                    self.pubsub_streamer.publish_block(normalized_block)
                    
                    # Process transactions
                    transactions = []
                    for tx in raw_block.get('tx', []):
                        normalized_tx = self.normalizer.normalize_transaction(tx, next_height)
                        transactions.append(normalized_tx)
                    
                    if transactions:
                        self.pubsub_streamer.publish_transactions(transactions, next_height)
                    
                    self.last_processed_height = next_height
                    logger.info(f"Processed block {next_height} ({len(transactions)} transactions)")
                    
                except Exception as e:
                    logger.error(f"Error processing block {next_height}: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Error checking for new blocks: {str(e)}")
    
    def _process_mempool(self):
        """Process mempool data and detect anomalies"""
        current_time = time.time()
        
        # Only check mempool at specified interval
        if current_time - self.last_mempool_check < self.mempool_poll_interval:
            return
        
        try:
            # Get mempool info
            mempool_info = self.rpc_client.get_mempool_info()
            
            # Analyze for anomalies
            analysis = self.mempool_analyzer.analyze_mempool(mempool_info)
            
            # Publish mempool snapshot
            snapshot_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'size': analysis['current_size'],
                'bytes': analysis['current_bytes'],
                'avg_fee_rate': analysis['avg_fee_rate'],
                'block_height': self.last_processed_height
            }
            self.pubsub_streamer.publish_mempool_snapshot(snapshot_data)
            
            # Publish anomaly alerts if detected
            if analysis['anomalies']:
                for anomaly in analysis['anomalies']:
                    anomaly['timestamp'] = datetime.utcnow().isoformat()
                    anomaly['block_height'] = self.last_processed_height
                    self.pubsub_streamer.publish_anomaly_alert(anomaly)
                    logger.warning(f"Anomaly detected: {anomaly['description']}")
            
            self.last_mempool_check = current_time
            
        except Exception as e:
            logger.error(f"Error processing mempool: {str(e)}")
    
    def _handle_reorg(self, reorg_info: dict):
        """Handle blockchain reorganization"""
        logger.warning(f"Handling reorg of depth {reorg_info['depth']}")
        
        # Publish reorg alert
        reorg_alert = {
            'type': 'blockchain_reorg',
            'severity': 'critical' if reorg_info['depth'] > 3 else 'high',
            'description': f"Blockchain reorganization detected at height {reorg_info['height']}, depth: {reorg_info['depth']}",
            'depth': reorg_info['depth'],
            'old_tip': reorg_info['old_tip'],
            'new_tip': reorg_info['new_tip'],
            'height': reorg_info['height'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            self.pubsub_streamer.publish_anomaly_alert(reorg_alert)
        except Exception as e:
            logger.error(f"Failed to publish reorg alert: {str(e)}")
        
        # Reprocess affected blocks
        reprocess_from = reorg_info['height'] - reorg_info['depth']
        if reprocess_from > 0:
            self.last_processed_height = reprocess_from - 1
            logger.info(f"Will reprocess blocks from height {reprocess_from}")


def main():
    """Entry point for the ingestion service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bitcoin blockchain ingestion service')
    parser.add_argument(
        '--start-height',
        type=int,
        help='Block height to start processing from (default: current tip)'
    )
    parser.add_argument(
        '--from-genesis',
        action='store_true',
        help='Start processing from genesis block (height 0)'
    )
    
    args = parser.parse_args()
    
    # Determine start height
    start_height = None
    if args.from_genesis:
        start_height = 0
        logger.info("Starting from genesis block (height 0)")
    elif args.start_height is not None:
        start_height = args.start_height
        logger.info(f"Starting from block height: {start_height}")
    
    logger.info("Initializing blockchain ingestion service...")
    
    service = BlockchainIngestionService(start_height=start_height)
    service.start()


if __name__ == '__main__':
    main()
