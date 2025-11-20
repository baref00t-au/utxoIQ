"""
Signal Polling Module for insight-generator service.
Polls BigQuery for unprocessed signals and groups them for batch processing.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)


@dataclass
class SignalGroup:
    """Group of signals by type and block height."""
    signal_type: str
    block_height: int
    signals: List[Dict]


class SignalPollingModule:
    """
    Polls BigQuery for unprocessed signals and manages signal processing state.
    
    Responsibilities:
    - Query intel.signals for unprocessed signals with confidence >= 0.7
    - Group signals by signal_type and block_height for batch processing
    - Mark signals as processed after insight generation
    """
    
    def __init__(
        self,
        bigquery_client: bigquery.Client,
        project_id: str = "utxoiq-dev",
        dataset_id: str = "intel",
        confidence_threshold: float = 0.7
    ):
        """
        Initialize Signal Polling Module.
        
        Args:
            bigquery_client: BigQuery client instance
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID for intel data
            confidence_threshold: Minimum confidence score for processing (default: 0.7)
        """
        self.client = bigquery_client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.confidence_threshold = confidence_threshold
        self.signals_table = f"{project_id}.{dataset_id}.signals"
        self.poll_interval = 10  # seconds
        
        logger.info(
            f"SignalPollingModule initialized with confidence threshold: {confidence_threshold}"
        )
    
    async def poll_unprocessed_signals(
        self,
        limit: int = 100
    ) -> List[SignalGroup]:
        """
        Query BigQuery for unprocessed signals and group them for batch processing.
        
        Filters signals by:
        - processed = false
        - confidence >= confidence_threshold
        - signal_type in (mempool, exchange, miner, whale, treasury, predictive)
        
        Groups signals by signal_type and block_height for efficient processing.
        
        Args:
            limit: Maximum number of signals to retrieve (default: 100)
            
        Returns:
            List of SignalGroup objects containing grouped signals
        """
        query = f"""
        SELECT 
            signal_id,
            signal_type,
            block_height,
            confidence,
            metadata,
            created_at
        FROM `{self.signals_table}`
        WHERE processed = false
          AND confidence >= {self.confidence_threshold}
          AND signal_type IN ('mempool', 'exchange', 'miner', 'whale', 'treasury', 'predictive')
        ORDER BY created_at ASC
        LIMIT {limit}
        """
        
        try:
            logger.info(
                f"Polling for unprocessed signals (confidence >= {self.confidence_threshold})"
            )
            
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if not results:
                logger.debug("No unprocessed signals found")
                return []
            
            logger.info(f"Found {len(results)} unprocessed signals")
            
            # Convert results to dictionaries
            signals = [dict(row) for row in results]
            
            # Group signals by signal_type and block_height
            groups = self._group_signals(signals)
            
            logger.info(
                f"Grouped {len(signals)} signals into {len(groups)} groups"
            )
            
            return groups
            
        except NotFound:
            logger.error(f"Table {self.signals_table} not found")
            return []
        except Exception as e:
            logger.error(f"Error polling unprocessed signals: {e}")
            return []
    
    def _group_signals(self, signals: List[Dict]) -> List[SignalGroup]:
        """
        Group signals by signal_type and block_height.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of SignalGroup objects
        """
        # Create a dictionary to group signals
        groups_dict: Dict[tuple, List[Dict]] = {}
        
        for signal in signals:
            key = (signal['signal_type'], signal['block_height'])
            if key not in groups_dict:
                groups_dict[key] = []
            groups_dict[key].append(signal)
        
        # Convert to SignalGroup objects
        groups = [
            SignalGroup(
                signal_type=signal_type,
                block_height=block_height,
                signals=signal_list
            )
            for (signal_type, block_height), signal_list in groups_dict.items()
        ]
        
        # Sort by block_height (oldest first)
        groups.sort(key=lambda g: g.block_height)
        
        return groups
    
    async def mark_signal_processed(
        self,
        signal_id: str,
        processed_at: Optional[datetime] = None
    ) -> bool:
        """
        Mark a signal as processed in BigQuery.
        
        Updates the signal record to set:
        - processed = true
        - processed_at = current timestamp
        
        Args:
            signal_id: Signal ID to mark as processed
            processed_at: Timestamp when processed (default: current time)
            
        Returns:
            True if update successful, False otherwise
        """
        if processed_at is None:
            processed_at = datetime.utcnow()
        
        query = f"""
        UPDATE `{self.signals_table}`
        SET 
            processed = true,
            processed_at = TIMESTAMP('{processed_at.isoformat()}')
        WHERE signal_id = '{signal_id}'
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for query to complete
            
            if query_job.num_dml_affected_rows > 0:
                logger.debug(f"Marked signal {signal_id} as processed")
                return True
            else:
                logger.warning(f"Signal {signal_id} not found or already processed")
                return False
                
        except Exception as e:
            logger.error(f"Error marking signal {signal_id} as processed: {e}")
            return False
    
    async def mark_signals_processed_batch(
        self,
        signal_ids: List[str],
        processed_at: Optional[datetime] = None
    ) -> int:
        """
        Mark multiple signals as processed in a single query.
        
        More efficient than calling mark_signal_processed() multiple times.
        
        Args:
            signal_ids: List of signal IDs to mark as processed
            processed_at: Timestamp when processed (default: current time)
            
        Returns:
            Number of signals successfully marked as processed
        """
        if not signal_ids:
            return 0
        
        if processed_at is None:
            processed_at = datetime.utcnow()
        
        # Create comma-separated list of signal IDs for SQL IN clause
        signal_ids_str = "', '".join(signal_ids)
        
        query = f"""
        UPDATE `{self.signals_table}`
        SET 
            processed = true,
            processed_at = TIMESTAMP('{processed_at.isoformat()}')
        WHERE signal_id IN ('{signal_ids_str}')
        """
        
        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for query to complete
            
            affected_rows = query_job.num_dml_affected_rows
            logger.info(f"Marked {affected_rows} signals as processed")
            return affected_rows
            
        except Exception as e:
            logger.error(f"Error marking signals as processed: {e}")
            return 0
    
    async def get_unprocessed_signal_count(self) -> int:
        """
        Get count of unprocessed signals above confidence threshold.
        
        Useful for monitoring and alerting.
        
        Returns:
            Number of unprocessed signals
        """
        query = f"""
        SELECT COUNT(*) as count
        FROM `{self.signals_table}`
        WHERE processed = false
          AND confidence >= {self.confidence_threshold}
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if results:
                return results[0]['count']
            return 0
            
        except Exception as e:
            logger.error(f"Error getting unprocessed signal count: {e}")
            return 0
    
    async def get_stale_signals(
        self,
        max_age_hours: int = 1
    ) -> List[Dict]:
        """
        Get signals that have been unprocessed for too long.
        
        Used for alerting when signals are stuck in the queue.
        
        Args:
            max_age_hours: Maximum age in hours before signal is considered stale
            
        Returns:
            List of stale signal dictionaries
        """
        query = f"""
        SELECT 
            signal_id,
            signal_type,
            block_height,
            confidence,
            created_at,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), created_at, HOUR) as age_hours
        FROM `{self.signals_table}`
        WHERE processed = false
          AND confidence >= {self.confidence_threshold}
          AND created_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {max_age_hours} HOUR)
        ORDER BY created_at ASC
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if results:
                stale_signals = [dict(row) for row in results]
                logger.warning(
                    f"Found {len(stale_signals)} stale signals "
                    f"(older than {max_age_hours} hours)"
                )
                return stale_signals
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting stale signals: {e}")
            return []
