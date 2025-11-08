#!/usr/bin/env python3
"""
BigQuery client for streaming blockchain data
"""

import os
import logging
from typing import List, Dict, Any
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

logger = logging.getLogger(__name__)


class BigQueryClient:
    """Client for streaming data to BigQuery"""
    
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'btc')
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set")
        
        self.client = bigquery.Client(project=self.project_id)
        self.blocks_table = f"{self.project_id}.{self.dataset_id}.blocks"
        self.transactions_table = f"{self.project_id}.{self.dataset_id}.transactions"
        
        logger.info(f"BigQuery client initialized for project: {self.project_id}")
    
    def stream_blocks(self, blocks: List[Dict[str, Any]]) -> int:
        """
        Load blocks to BigQuery using batch loading (free tier compatible)
        
        Args:
            blocks: List of normalized block dictionaries
            
        Returns:
            Number of blocks successfully inserted
        """
        if not blocks:
            return 0
        
        try:
            # Use load_table_from_json for batch loading (free tier)
            table = self.client.get_table(self.blocks_table)
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            )
            
            job = self.client.load_table_from_json(
                blocks,
                table,
                job_config=job_config
            )
            
            # Wait for the job to complete
            job.result()
            
            logger.debug(f"Successfully loaded {len(blocks)} blocks")
            return len(blocks)
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error loading blocks: {str(e)}")
            raise
    
    def stream_transactions(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Stream transactions to BigQuery
        
        Args:
            transactions: List of normalized transaction dictionaries
            
        Returns:
            Number of transactions successfully inserted
        """
        if not transactions:
            return 0
        
        try:
            errors = self.client.insert_rows_json(self.transactions_table, transactions)
            
            if errors:
                logger.error(f"Errors inserting transactions: {errors}")
                return len(transactions) - len(errors)
            
            logger.debug(f"Successfully inserted {len(transactions)} transactions")
            return len(transactions)
            
        except GoogleCloudError as e:
            logger.error(f"BigQuery error streaming transactions: {str(e)}")
            raise
    
    def check_tables_exist(self) -> bool:
        """Check if required tables exist"""
        try:
            self.client.get_table(self.blocks_table)
            # Transactions table is optional for now
            return True
        except Exception as e:
            logger.error(f"Tables not found: {str(e)}")
            return False
