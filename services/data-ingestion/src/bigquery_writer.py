"""
Direct BigQuery writer for blockchain data
Bypasses Pub/Sub for simpler local development
"""

import os
from google.cloud import bigquery
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BigQueryWriter:
    """Write blockchain data directly to BigQuery"""
    
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID', 'utxoiq-dev')
        self.client = bigquery.Client(project=self.project_id)
        self.blocks_table = f"{self.project_id}.btc.blocks"
        
        logger.info(f"BigQuery writer initialized for project: {self.project_id}")
    
    def write_block(self, block_data: dict):
        """Write a single block to BigQuery"""
        try:
            # Prepare row for BigQuery
            row = {
                "height": block_data.get("height"),
                "hash": block_data.get("hash"),
                "timestamp": datetime.fromtimestamp(block_data.get("time")).isoformat(),
                "size": block_data.get("size"),
                "weight": block_data.get("weight"),
                "tx_count": block_data.get("tx_count", len(block_data.get("tx", []))),
                "difficulty": block_data.get("difficulty"),
                "nonce": block_data.get("nonce"),
                "version": block_data.get("version"),
                "merkle_root": block_data.get("merkleroot"),
                "previous_block_hash": block_data.get("previousblockhash"),
                "next_block_hash": block_data.get("nextblockhash"),
            }
            
            # Insert row
            errors = self.client.insert_rows_json(self.blocks_table, [row])
            
            if errors:
                logger.error(f"Failed to insert block {block_data.get('height')}: {errors}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing block to BigQuery: {e}")
            return False
    
    def write_blocks_batch(self, blocks: list):
        """Write multiple blocks to BigQuery in a batch"""
        try:
            rows = []
            for block_data in blocks:
                row = {
                    "height": block_data.get("height"),
                    "hash": block_data.get("hash"),
                    "timestamp": datetime.fromtimestamp(block_data.get("time")).isoformat(),
                    "size": block_data.get("size"),
                    "weight": block_data.get("weight"),
                    "tx_count": block_data.get("tx_count", len(block_data.get("tx", []))),
                    "difficulty": block_data.get("difficulty"),
                    "nonce": block_data.get("nonce"),
                    "version": block_data.get("version"),
                    "merkle_root": block_data.get("merkleroot"),
                    "previous_block_hash": block_data.get("previousblockhash"),
                    "next_block_hash": block_data.get("nextblockhash"),
                }
                rows.append(row)
            
            # Insert all rows
            errors = self.client.insert_rows_json(self.blocks_table, rows)
            
            if errors:
                logger.error(f"Failed to insert batch: {errors}")
                return False
            
            logger.info(f"Successfully inserted {len(rows)} blocks to BigQuery")
            return True
            
        except Exception as e:
            logger.error(f"Error writing batch to BigQuery: {e}")
            return False
