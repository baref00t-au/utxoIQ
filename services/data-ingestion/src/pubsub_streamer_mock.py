"""
Mock Pub/Sub streamer for local development
Logs data instead of publishing to Pub/Sub
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PubSubStreamer:
    """Mock streamer that logs data instead of publishing"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID', 'utxoiq-local')
        logger.info("Using MOCK Pub/Sub streamer (local development mode)")
        logger.info("Data will be logged instead of published to Pub/Sub")
    
    def publish_block(self, block_data: Dict) -> str:
        """Log block data instead of publishing"""
        logger.info(f"[MOCK] Would publish block {block_data.get('height')} "
                   f"(hash: {block_data.get('block_hash', '')[:16]}...)")
        return f"mock_msg_{block_data.get('height')}"
    
    def publish_transactions(self, transactions: list, block_height: int) -> list:
        """Log transaction data instead of publishing"""
        logger.info(f"[MOCK] Would publish {len(transactions)} transactions for block {block_height}")
        return [f"mock_tx_{i}" for i in range(len(transactions))]
    
    def publish_mempool_snapshot(self, mempool_data: Dict) -> str:
        """Log mempool snapshot instead of publishing"""
        logger.info(f"[MOCK] Would publish mempool snapshot: "
                   f"{mempool_data.get('size', 0)} txs, "
                   f"{mempool_data.get('avg_fee_rate', 0):.2f} sat/byte")
        return "mock_mempool_msg"
    
    def publish_anomaly_alert(self, anomaly_data: Dict) -> str:
        """Log anomaly alert instead of publishing"""
        logger.warning(f"[MOCK] Would publish anomaly: {anomaly_data.get('type')} - "
                      f"{anomaly_data.get('description', '')}")
        return "mock_anomaly_msg"
