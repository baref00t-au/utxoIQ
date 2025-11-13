"""
Entity Identification Module for blockchain address identification.

This module provides methods to identify known entities (exchanges, mining pools,
treasury companies) from Bitcoin addresses.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from google.cloud import bigquery

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EntityInfo:
    """Information about a known entity (exchange, mining pool, treasury)."""
    entity_id: str
    entity_name: str
    entity_type: str  # exchange|mining_pool|treasury
    addresses: List[str]
    metadata: Dict[str, Any]  # For treasury: {"ticker": "MSTR", "known_holdings_btc": 152800}


class EntityIdentificationModule:
    """
    Module for identifying known blockchain entities.
    
    Responsibilities:
    - Load known entities database on startup
    - Match transaction addresses against entity database
    - Identify exchanges (Coinbase, Kraken, Binance, etc.)
    - Identify mining pools (Foundry USA, AntPool, F2Pool, etc.)
    - Identify treasury companies (MicroStrategy, Tesla, etc.)
    - Reload entity list periodically (every 5 minutes)
    """
    
    def __init__(self, bigquery_client: bigquery.Client):
        """
        Initialize Entity Identification Module.
        
        Args:
            bigquery_client: BigQuery client for querying known_entities table
        """
        self.client = bigquery_client
        self.entities_cache: Dict[str, EntityInfo] = {}  # address -> EntityInfo
        self.entities_by_id: Dict[str, EntityInfo] = {}  # entity_id -> EntityInfo
        self.last_reload: Optional[datetime] = None
        self.reload_interval = timedelta(minutes=5)
        self._background_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
        logger.info("EntityIdentificationModule initialized")
    
    async def load_known_entities(self) -> None:
        """
        Load entities from btc.known_entities table.
        
        Populates internal cache with address -> EntityInfo mappings.
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
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            # Clear existing caches
            self.entities_cache.clear()
            self.entities_by_id.clear()
            
            # Build mappings
            entity_count = 0
            address_count = 0
            
            for row in results:
                entity = EntityInfo(
                    entity_id=row['entity_id'],
                    entity_name=row['entity_name'],
                    entity_type=row['entity_type'],
                    addresses=list(row['addresses']) if row['addresses'] else [],
                    metadata=dict(row['metadata']) if row['metadata'] else {}
                )
                
                # Store by entity_id
                self.entities_by_id[entity.entity_id] = entity
                entity_count += 1
                
                # Map each address to this entity
                for address in entity.addresses:
                    self.entities_cache[address] = entity
                    address_count += 1
            
            self.last_reload = datetime.utcnow()
            
            logger.info(
                f"Loaded {entity_count} entities with {address_count} addresses "
                f"(exchanges: {self._count_by_type('exchange')}, "
                f"mining_pools: {self._count_by_type('mining_pool')}, "
                f"treasury: {self._count_by_type('treasury')})"
            )
            
        except Exception as e:
            logger.error(f"Failed to load known entities: {e}")
            # Don't raise - allow processing to continue with empty cache
    
    async def identify_entity(self, address: str) -> Optional[EntityInfo]:
        """
        Match address against known entities.
        
        Args:
            address: Bitcoin address to identify
            
        Returns:
            EntityInfo if address is known, None otherwise
        """
        # Check if reload is needed
        if self._should_reload():
            await self.load_known_entities()
        
        return self.entities_cache.get(address)
    
    async def identify_mining_pool(self, coinbase_tx: Dict[str, Any]) -> Optional[EntityInfo]:
        """
        Extract mining pool from coinbase transaction.
        
        Args:
            coinbase_tx: Coinbase transaction data with 'inputs' field
            
        Returns:
            EntityInfo for mining pool if identified, None otherwise
        """
        try:
            # Ensure entities are loaded
            if self._should_reload():
                await self.load_known_entities()
            
            # Coinbase transactions have a single input with coinbase script
            if not coinbase_tx.get('inputs') or len(coinbase_tx['inputs']) == 0:
                return None
            
            coinbase_input = coinbase_tx['inputs'][0]
            
            # Check if this is actually a coinbase transaction
            if not coinbase_input.get('is_coinbase', False):
                return None
            
            # Extract coinbase script signature
            script_sig = coinbase_input.get('script_sig', '')
            
            # Try to identify pool from script signature
            # Common pool identifiers in coinbase scripts
            pool_identifiers = {
                'Foundry USA': ['foundry', 'foundryusa'],
                'AntPool': ['antpool'],
                'F2Pool': ['f2pool', '鱼池'],
                'ViaBTC': ['viabtc'],
                'Binance Pool': ['binance', 'binancepool'],
                'Poolin': ['poolin'],
                'BTC.com': ['btc.com'],
                'Slush Pool': ['slushpool', 'braiins']
            }
            
            script_lower = script_sig.lower()
            
            for pool_name, identifiers in pool_identifiers.items():
                for identifier in identifiers:
                    if identifier in script_lower:
                        # Find entity by name
                        for entity in self.entities_by_id.values():
                            if (entity.entity_type == 'mining_pool' and 
                                pool_name.lower() in entity.entity_name.lower()):
                                logger.debug(f"Identified mining pool: {entity.entity_name}")
                                return entity
            
            # Check output addresses if script signature didn't match
            if coinbase_tx.get('outputs'):
                for output in coinbase_tx['outputs']:
                    if output.get('addresses'):
                        for address in output['addresses']:
                            entity = await self.identify_entity(address)
                            if entity and entity.entity_type == 'mining_pool':
                                logger.debug(
                                    f"Identified mining pool from output address: "
                                    f"{entity.entity_name}"
                                )
                                return entity
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to identify mining pool: {e}")
            return None
    
    async def identify_treasury_company(self, address: str) -> Optional[EntityInfo]:
        """
        Identify if address belongs to a public company treasury.
        
        Args:
            address: Bitcoin address to check
            
        Returns:
            EntityInfo with company ticker and known holdings if identified, None otherwise
        """
        entity = await self.identify_entity(address)
        
        if entity and entity.entity_type == 'treasury':
            return entity
        
        return None
    
    def _should_reload(self) -> bool:
        """Check if entity cache should be reloaded."""
        if self.last_reload is None:
            return True
        
        return datetime.utcnow() - self.last_reload > self.reload_interval
    
    def _count_by_type(self, entity_type: str) -> int:
        """Count entities of a specific type."""
        return sum(
            1 for entity in self.entities_by_id.values()
            if entity.entity_type == entity_type
        )
    
    async def _background_reload_task(self) -> None:
        """
        Background task for automatic cache refresh.
        
        Runs continuously and reloads entity cache every 5 minutes.
        """
        logger.info("Starting background entity cache reload task")
        
        # Initial load
        await self.load_known_entities()
        
        while not self._shutdown:
            try:
                # Wait for reload interval
                await asyncio.sleep(self.reload_interval.total_seconds())
                
                if not self._shutdown:
                    logger.debug("Background task triggering entity cache reload")
                    await self.load_known_entities()
                    
            except asyncio.CancelledError:
                logger.info("Background reload task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in background reload task: {e}")
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait 1 minute before retry
        
        logger.info("Background entity cache reload task stopped")
    
    def start_background_reload(self) -> None:
        """
        Start the background task for automatic cache refresh.
        
        This should be called once during application startup.
        """
        if self._background_task is None or self._background_task.done():
            self._shutdown = False
            self._background_task = asyncio.create_task(self._background_reload_task())
            logger.info("Background entity cache reload task started")
        else:
            logger.warning("Background reload task already running")
    
    async def stop_background_reload(self) -> None:
        """
        Stop the background task for automatic cache refresh.
        
        This should be called during application shutdown.
        """
        if self._background_task and not self._background_task.done():
            logger.info("Stopping background entity cache reload task")
            self._shutdown = True
            self._background_task.cancel()
            
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            
            logger.info("Background entity cache reload task stopped")
        else:
            logger.debug("No background reload task to stop")
