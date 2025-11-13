"""
Data Extraction Module for signal processing.

This module provides methods to extract blockchain data from Bitcoin Core RPC
and BigQuery for signal generation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from google.cloud import bigquery

from src.utils.tor_rpc import TorAuthServiceProxy
from src.adapters.bigquery_adapter import BigQueryAdapter
from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MempoolStats:
    """Mempool statistics from Bitcoin Core RPC."""
    size: int  # Number of transactions
    bytes: int  # Total size in bytes
    usage: int  # Memory usage
    total_fee: float  # Total fees in BTC
    maxmempool: int  # Maximum memory pool size
    mempoolminfee: float  # Minimum fee rate for tx acceptance
    minrelaytxfee: float  # Minimum relay fee rate
    unbroadcastcount: int  # Number of unbroadcast transactions
    fee_rate_median: float  # Median fee rate (sat/vB)
    fee_rate_p25: float  # 25th percentile fee rate
    fee_rate_p75: float  # 75th percentile fee rate


@dataclass
class EntityInfo:
    """Information about a known entity (exchange, mining pool, treasury)."""
    entity_id: str
    entity_name: str
    entity_type: str  # exchange|mining_pool|treasury
    addresses: List[str]
    metadata: Dict[str, Any]  # For treasury: {"ticker": "MSTR", "known_holdings_btc": 152800}


@dataclass
class WhaleAddress:
    """Information about a whale address detected in a transaction."""
    address: str
    balance_btc: float
    output_value_btc: float


@dataclass
class HistoricalSignal:
    """Historical signal data from BigQuery."""
    signal_id: str
    signal_type: str
    block_height: int
    confidence: float
    metadata: Dict[str, Any]
    created_at: datetime


class DataExtractionModule:
    """
    Module for extracting blockchain data from Bitcoin Core RPC and BigQuery.
    
    Responsibilities:
    - Query Bitcoin Core RPC for mempool statistics
    - Identify exchange addresses from known entities database
    - Detect whale addresses (>1000 BTC)
    - Query historical signal data from BigQuery
    """
    
    def __init__(
        self,
        bitcoin_rpc: TorAuthServiceProxy,
        bigquery_adapter: BigQueryAdapter,
        bigquery_client: Optional[bigquery.Client] = None
    ):
        """
        Initialize Data Extraction Module.
        
        Args:
            bitcoin_rpc: Bitcoin Core RPC client
            bigquery_adapter: BigQuery adapter for blockchain data
            bigquery_client: BigQuery client for intel dataset queries
        """
        self.rpc = bitcoin_rpc
        self.bq_adapter = bigquery_adapter
        self.bq_client = bigquery_client or bigquery.Client(project=settings.gcp_project_id)
        self.known_entities: Dict[str, EntityInfo] = {}
        self.last_entity_load: Optional[datetime] = None
        self.entity_reload_interval = timedelta(minutes=5)
        
        logger.info("DataExtractionModule initialized")
    
    async def get_mempool_stats(self) -> MempoolStats:
        """
        Query Bitcoin Core RPC for current mempool state.
        
        Returns:
            MempoolStats object with current mempool data
            
        Raises:
            Exception: If RPC call fails
        """
        try:
            # Get mempool info
            mempool_info = self.rpc.getmempoolinfo()
            
            # Get raw mempool for fee analysis
            raw_mempool = self.rpc.getrawmempool(True)
            
            # Calculate fee statistics
            fee_rates = []
            total_fee_btc = 0.0
            
            for txid, tx_info in raw_mempool.items():
                if 'fees' in tx_info and 'base' in tx_info['fees']:
                    fee_btc = tx_info['fees']['base']
                    total_fee_btc += fee_btc
                    
                    # Calculate fee rate (sat/vB)
                    if 'vsize' in tx_info and tx_info['vsize'] > 0:
                        fee_rate = (fee_btc * 100_000_000) / tx_info['vsize']
                        fee_rates.append(fee_rate)
            
            # Calculate percentiles
            fee_rates.sort()
            n = len(fee_rates)
            
            if n > 0:
                fee_rate_median = fee_rates[n // 2]
                fee_rate_p25 = fee_rates[n // 4]
                fee_rate_p75 = fee_rates[(3 * n) // 4]
            else:
                fee_rate_median = 0.0
                fee_rate_p25 = 0.0
                fee_rate_p75 = 0.0
            
            stats = MempoolStats(
                size=mempool_info.get('size', 0),
                bytes=mempool_info.get('bytes', 0),
                usage=mempool_info.get('usage', 0),
                total_fee=total_fee_btc,
                maxmempool=mempool_info.get('maxmempool', 0),
                mempoolminfee=mempool_info.get('mempoolminfee', 0.0),
                minrelaytxfee=mempool_info.get('minrelaytxfee', 0.0),
                unbroadcastcount=mempool_info.get('unbroadcastcount', 0),
                fee_rate_median=fee_rate_median,
                fee_rate_p25=fee_rate_p25,
                fee_rate_p75=fee_rate_p75
            )
            
            logger.debug(
                f"Mempool stats: {stats.size} txs, "
                f"median fee rate: {stats.fee_rate_median:.2f} sat/vB"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get mempool stats: {e}")
            raise
    
    async def get_historical_signals(
        self,
        signal_type: str,
        time_window: timedelta
    ) -> List[HistoricalSignal]:
        """
        Query BigQuery for previous signal values within specified time window.
        
        Args:
            signal_type: Type of signal to query (mempool, exchange, miner, whale, predictive)
            time_window: Time window to look back (e.g., timedelta(hours=1))
            
        Returns:
            List of historical signals
            
        Raises:
            Exception: If BigQuery query fails
        """
        try:
            # Calculate cutoff timestamp
            cutoff = datetime.utcnow() - time_window
            
            query = f"""
            SELECT 
                signal_id,
                signal_type,
                block_height,
                confidence,
                metadata,
                created_at
            FROM `{settings.gcp_project_id}.{settings.bigquery_dataset_intel}.signals`
            WHERE signal_type = @signal_type
              AND created_at >= @cutoff
            ORDER BY created_at DESC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("signal_type", "STRING", signal_type),
                    bigquery.ScalarQueryParameter("cutoff", "TIMESTAMP", cutoff),
                ]
            )
            
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            signals = []
            for row in results:
                signal = HistoricalSignal(
                    signal_id=row['signal_id'],
                    signal_type=row['signal_type'],
                    block_height=row['block_height'],
                    confidence=row['confidence'],
                    metadata=dict(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at']
                )
                signals.append(signal)
            
            logger.debug(
                f"Retrieved {len(signals)} historical {signal_type} signals "
                f"from last {time_window}"
            )
            
            return signals
            
        except Exception as e:
            logger.error(
                f"Failed to query historical signals: {e}",
                extra={"signal_type": signal_type, "time_window": str(time_window)}
            )
            raise
    
    async def identify_exchange_addresses(
        self,
        addresses: List[str]
    ) -> Dict[str, EntityInfo]:
        """
        Match addresses against known entities database.
        
        Args:
            addresses: List of Bitcoin addresses to identify
            
        Returns:
            Dictionary mapping address to EntityInfo for identified exchanges
        """
        # Ensure entities are loaded
        await self._ensure_entities_loaded()
        
        identified = {}
        for address in addresses:
            if address in self.known_entities:
                entity = self.known_entities[address]
                if entity.entity_type == "exchange":
                    identified[address] = entity
        
        if identified:
            logger.debug(f"Identified {len(identified)} exchange addresses")
        
        return identified
    
    async def detect_whale_addresses(
        self,
        outputs: List[Dict[str, Any]]
    ) -> List[WhaleAddress]:
        """
        Identify outputs to addresses with >1000 BTC balance.
        
        Args:
            outputs: List of transaction outputs with 'addresses' and 'value' fields
            
        Returns:
            List of WhaleAddress objects for outputs exceeding threshold
        """
        whale_addresses = []
        whale_threshold_satoshis = settings.whale_threshold_btc * 100_000_000
        
        for output in outputs:
            # Skip if no addresses or value
            if not output.get('addresses') or not output.get('value'):
                continue
            
            output_value = output['value']
            
            # Check if output value exceeds whale threshold
            if output_value >= whale_threshold_satoshis:
                for address in output['addresses']:
                    # Query address balance from BigQuery
                    balance_btc = await self._get_address_balance(address)
                    
                    if balance_btc >= settings.whale_threshold_btc:
                        whale = WhaleAddress(
                            address=address,
                            balance_btc=balance_btc,
                            output_value_btc=output_value / 100_000_000
                        )
                        whale_addresses.append(whale)
                        
                        logger.debug(
                            f"Detected whale address: {address[:10]}... "
                            f"(balance: {balance_btc:.2f} BTC)"
                        )
        
        return whale_addresses
    
    async def _ensure_entities_loaded(self) -> None:
        """Ensure known entities are loaded and up-to-date."""
        now = datetime.utcnow()
        
        # Load if never loaded or reload interval exceeded
        if (self.last_entity_load is None or 
            now - self.last_entity_load > self.entity_reload_interval):
            await self._load_known_entities()
    
    async def _load_known_entities(self) -> None:
        """
        Load known entities from btc.known_entities BigQuery table.
        
        Populates self.known_entities dictionary mapping address -> EntityInfo.
        """
        try:
            query = f"""
            SELECT 
                entity_id,
                entity_name,
                entity_type,
                addresses,
                metadata
            FROM `{settings.gcp_project_id}.{settings.bigquery_dataset_btc}.known_entities`
            """
            
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            # Clear existing entities
            self.known_entities.clear()
            
            # Build address -> entity mapping
            for row in results:
                entity = EntityInfo(
                    entity_id=row['entity_id'],
                    entity_name=row['entity_name'],
                    entity_type=row['entity_type'],
                    addresses=list(row['addresses']) if row['addresses'] else [],
                    metadata=dict(row['metadata']) if row['metadata'] else {}
                )
                
                # Map each address to this entity
                for address in entity.addresses:
                    self.known_entities[address] = entity
            
            self.last_entity_load = datetime.utcnow()
            
            logger.info(
                f"Loaded {len(self.known_entities)} known entity addresses "
                f"({len(set(e.entity_id for e in self.known_entities.values()))} unique entities)"
            )
            
        except Exception as e:
            logger.error(f"Failed to load known entities: {e}")
            # Don't raise - allow processing to continue with empty entity list
    
    async def _get_address_balance(self, address: str) -> float:
        """
        Query address balance from BigQuery.
        
        Args:
            address: Bitcoin address
            
        Returns:
            Balance in BTC
        """
        try:
            # Query recent outputs to this address
            query = f"""
            WITH address_outputs AS (
                SELECT 
                    output.value as value_satoshis
                FROM `{settings.gcp_project_id}.{settings.bigquery_dataset_btc}.transactions_unified` t,
                UNNEST(t.outputs) as output,
                UNNEST(output.addresses) as addr
                WHERE addr = @address
                  AND t.block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            )
            SELECT SUM(value_satoshis) / 100000000 as balance_btc
            FROM address_outputs
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("address", "STRING", address),
                ]
            )
            
            query_job = self.bq_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results and results[0]['balance_btc'] is not None:
                return float(results[0]['balance_btc'])
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Failed to get balance for address {address}: {e}")
            return 0.0
