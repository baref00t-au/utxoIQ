"""
BigQuery adapter for hybrid dataset approach with nested inputs/outputs.
Uses public dataset for historical data and custom dataset for real-time data.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)


class BigQueryAdapter:
    """Adapter for BigQuery hybrid dataset operations with 1-hour buffer."""
    
    def __init__(
        self,
        project_id: str = "utxoiq-dev",
        dataset_id: str = "btc",
        realtime_hours: int = 1
    ):
        """
        Initialize BigQuery adapter.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            realtime_hours: Hours of data to keep in custom dataset (default: 1 hour)
        """
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.realtime_hours = realtime_hours
        
        # Table references
        self.blocks_table = f"{project_id}.{dataset_id}.blocks"
        self.transactions_table = f"{project_id}.{dataset_id}.transactions"
        
        # Unified view references (always use these in queries)
        self.blocks_view = f"{project_id}.{dataset_id}.blocks_unified"
        self.transactions_view = f"{project_id}.{dataset_id}.transactions_unified"
    
    def should_ingest_block(self, block_timestamp: datetime) -> bool:
        """
        Determine if block should be ingested into custom dataset.
        
        Args:
            block_timestamp: Block timestamp
            
        Returns:
            True if block is recent enough to ingest
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.realtime_hours)
        return block_timestamp >= cutoff
    
    def _serialize_datetime(self, obj):
        """Convert datetime objects to ISO format strings for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        return obj
    
    def insert_block(self, block_data: Dict) -> None:
        """
        Insert block into custom dataset.
        
        Args:
            block_data: Block data matching blockchain-etl schema
        """
        if not self.should_ingest_block(block_data['timestamp']):
            logger.info(
                f"Skipping historical block {block_data['number']} "
                f"(timestamp: {block_data['timestamp']})"
            )
            return
        
        # Serialize datetime objects for JSON
        serialized_data = self._serialize_datetime(block_data)
        
        errors = self.client.insert_rows_json(self.blocks_table, [serialized_data])
        if errors:
            raise Exception(f"Failed to insert block: {errors}")
        
        logger.info(f"Inserted block {block_data['number']} into custom dataset")
    
    def insert_transactions(self, transactions: List[Dict]) -> None:
        """
        Insert transactions with nested inputs/outputs into custom dataset.
        
        Args:
            transactions: List of transaction data with nested inputs/outputs arrays
                         Each transaction must have 'inputs' and 'outputs' as nested arrays
        """
        if not transactions:
            return
        
        # Filter to only recent transactions
        recent_txs = [
            tx for tx in transactions
            if self.should_ingest_block(tx['block_timestamp'])
        ]
        
        if not recent_txs:
            logger.info(f"Skipping {len(transactions)} historical transactions")
            return
        
        # Serialize datetime objects for JSON
        serialized_txs = [self._serialize_datetime(tx) for tx in recent_txs]
        
        errors = self.client.insert_rows_json(
            self.transactions_table,
            serialized_txs
        )
        if errors:
            raise Exception(f"Failed to insert transactions: {errors}")
        
        logger.info(
            f"Inserted {len(recent_txs)} transactions into custom dataset"
        )
    
    def query_recent_blocks(
        self,
        hours: int = 1,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query recent blocks using unified view.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of blocks to return
            
        Returns:
            List of block data
        """
        query = f"""
        SELECT *
        FROM `{self.blocks_view}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
        ORDER BY number DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def query_block_by_height(self, block_height: int) -> Optional[Dict]:
        """
        Query block by height using unified view.
        
        Args:
            block_height: Block height
            
        Returns:
            Block data or None if not found
        """
        query = f"""
        SELECT *
        FROM `{self.blocks_view}`
        WHERE number = {block_height}
        LIMIT 1
        """
        
        query_job = self.client.query(query)
        results = list(query_job.result())
        
        return dict(results[0]) if results else None
    
    def query_transactions_by_block(
        self,
        block_height: int
    ) -> List[Dict]:
        """
        Query transactions for a specific block using unified view.
        
        Args:
            block_height: Block height
            
        Returns:
            List of transaction data with nested inputs/outputs
        """
        query = f"""
        SELECT *
        FROM `{self.transactions_view}`
        WHERE block_number = {block_height}
        ORDER BY `hash`
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def query_large_transactions(
        self,
        min_btc: float = 1000.0,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query large transactions using unified view.
        
        Args:
            min_btc: Minimum BTC amount
            hours: Hours to look back
            limit: Maximum results
            
        Returns:
            List of large transactions
        """
        min_satoshis = int(min_btc * 100_000_000)
        
        query = f"""
        SELECT 
            `hash`,
            block_number,
            block_timestamp,
            output_value / 100000000 as btc_amount,
            fee / 100000000 as fee_btc,
            input_count,
            output_count
        FROM `{self.transactions_view}`
        WHERE output_value > {min_satoshis}
          AND block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
        ORDER BY output_value DESC
        LIMIT {limit}
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def query_address_activity(
        self,
        address: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query activity for a specific address using unified view.
        
        Args:
            address: Bitcoin address
            hours: Hours to look back
            limit: Maximum results
            
        Returns:
            List of transactions involving the address
        """
        query = f"""
        SELECT 
            t.`hash` as tx_hash,
            t.block_number,
            t.block_timestamp,
            output.`index` as output_index,
            output.value,
            output.`type`
        FROM `{self.transactions_view}` t,
        UNNEST(t.outputs) as output,
        UNNEST(output.addresses) as addr
        WHERE addr = '{address}'
          AND t.block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
        ORDER BY t.block_number DESC
        LIMIT {limit}
        """
        
        query_job = self.client.query(query)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def cleanup_old_data(self, hours: int = 2) -> Dict[str, int]:
        """
        Delete data older than specified hours from custom dataset.
        
        Args:
            hours: Delete data older than this many hours (default: 2 hours)
            
        Returns:
            Dictionary with deletion counts per table
        """
        results = {}
        
        # Delete old blocks
        query = f"""
        DELETE FROM `{self.blocks_table}`
        WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
        """
        job = self.client.query(query)
        job.result()
        results['blocks'] = job.num_dml_affected_rows
        
        # Delete old transactions
        query = f"""
        DELETE FROM `{self.transactions_table}`
        WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
        """
        job = self.client.query(query)
        job.result()
        results['transactions'] = job.num_dml_affected_rows
        
        # Alert if too much data was deleted (indicates ingestion failure)
        if results['blocks'] > 200:  # More than ~3 hours of blocks
            logger.warning(
                f"Cleanup deleted {results['blocks']} blocks - "
                f"ingestion may have been down for extended period"
            )
        
        logger.info(f"Cleanup completed: {results}")
        return results
    
    def get_latest_block_height(self) -> Optional[int]:
        """
        Get the latest block height from custom dataset.
        
        Returns:
            Latest block height or None if no blocks
        """
        query = f"""
        SELECT MAX(number) as max_height
        FROM `{self.blocks_table}`
        """
        
        query_job = self.client.query(query)
        results = list(query_job.result())
        
        if results and results[0]['max_height'] is not None:
            return results[0]['max_height']
        
        return None
    
    def get_dataset_stats(self) -> Dict:
        """
        Get statistics about the custom dataset.
        
        Returns:
            Dictionary with dataset statistics
        """
        query = f"""
        SELECT 
            COUNT(*) as block_count,
            MIN(timestamp) as oldest_block,
            MAX(timestamp) as newest_block,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MIN(timestamp), HOUR) as oldest_age_hours,
            TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), HOUR) as span_hours
        FROM `{self.blocks_table}`
        """
        
        query_job = self.client.query(query)
        results = list(query_job.result())
        
        if results and results[0]['block_count'] > 0:
            return dict(results[0])
        
        return {
            'block_count': 0,
            'oldest_block': None,
            'newest_block': None,
            'oldest_age_hours': None,
            'span_hours': None
        }
