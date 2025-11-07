"""
Cloud Pub/Sub streaming service for blockchain data
Publishes normalized blockchain data to Pub/Sub topics
"""

import os
import json
import logging
from typing import Dict, Any
from google.cloud import pubsub_v1
from google.api_core import retry

logger = logging.getLogger(__name__)


class PubSubStreamer:
    """Streams blockchain data to Cloud Pub/Sub topics"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.publisher = pubsub_v1.PublisherClient()
        
        # Topic paths
        self.blocks_topic = self.publisher.topic_path(
            self.project_id,
            os.getenv('PUBSUB_TOPIC_BLOCKS', 'btc.blocks')
        )
        self.transactions_topic = self.publisher.topic_path(
            self.project_id,
            os.getenv('PUBSUB_TOPIC_TRANSACTIONS', 'btc.transactions')
        )
        self.mempool_topic = self.publisher.topic_path(
            self.project_id,
            os.getenv('PUBSUB_TOPIC_MEMPOOL', 'btc.mempool')
        )
        
        # Ensure topics exist
        self._ensure_topics_exist()
    
    def _ensure_topics_exist(self):
        """Create topics if they don't exist"""
        topics = [
            self.blocks_topic,
            self.transactions_topic,
            self.mempool_topic
        ]
        
        for topic_path in topics:
            try:
                self.publisher.get_topic(request={"topic": topic_path})
                logger.info(f"Topic exists: {topic_path}")
            except Exception:
                try:
                    self.publisher.create_topic(request={"name": topic_path})
                    logger.info(f"Created topic: {topic_path}")
                except Exception as e:
                    logger.error(f"Failed to create topic {topic_path}: {str(e)}")
    
    def publish_block(self, block_data: Dict) -> str:
        """Publish block data to Pub/Sub"""
        try:
            message_data = json.dumps(block_data).encode('utf-8')
            
            # Add attributes for filtering
            attributes = {
                'block_height': str(block_data.get('height', 0)),
                'block_hash': block_data.get('block_hash', ''),
                'data_type': 'block'
            }
            
            future = self.publisher.publish(
                self.blocks_topic,
                message_data,
                **attributes
            )
            
            message_id = future.result(timeout=10)
            logger.info(f"Published block {block_data.get('height')} to Pub/Sub: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish block: {str(e)}")
            raise
    
    def publish_transactions(self, transactions: list, block_height: int) -> list:
        """Publish multiple transactions to Pub/Sub"""
        message_ids = []
        
        for tx in transactions:
            try:
                message_data = json.dumps(tx).encode('utf-8')
                
                attributes = {
                    'block_height': str(block_height),
                    'tx_hash': tx.get('tx_hash', ''),
                    'data_type': 'transaction'
                }
                
                future = self.publisher.publish(
                    self.transactions_topic,
                    message_data,
                    **attributes
                )
                
                message_id = future.result(timeout=10)
                message_ids.append(message_id)
                
            except Exception as e:
                logger.error(f"Failed to publish transaction: {str(e)}")
        
        logger.info(f"Published {len(message_ids)} transactions for block {block_height}")
        return message_ids
    
    def publish_mempool_snapshot(self, mempool_data: Dict) -> str:
        """Publish mempool snapshot to Pub/Sub"""
        try:
            message_data = json.dumps(mempool_data).encode('utf-8')
            
            attributes = {
                'snapshot_time': str(mempool_data.get('timestamp', 0)),
                'data_type': 'mempool'
            }
            
            future = self.publisher.publish(
                self.mempool_topic,
                message_data,
                **attributes
            )
            
            message_id = future.result(timeout=10)
            logger.info(f"Published mempool snapshot to Pub/Sub: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish mempool snapshot: {str(e)}")
            raise
    
    def publish_anomaly_alert(self, anomaly_data: Dict) -> str:
        """Publish anomaly detection alert"""
        try:
            # Add anomaly flag to mempool data
            anomaly_data['is_anomaly'] = True
            message_data = json.dumps(anomaly_data).encode('utf-8')
            
            attributes = {
                'anomaly_type': anomaly_data.get('type', 'unknown'),
                'severity': anomaly_data.get('severity', 'medium'),
                'data_type': 'anomaly'
            }
            
            future = self.publisher.publish(
                self.mempool_topic,
                message_data,
                **attributes
            )
            
            message_id = future.result(timeout=10)
            logger.warning(f"Published anomaly alert: {anomaly_data.get('type')} - {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish anomaly alert: {str(e)}")
            raise
