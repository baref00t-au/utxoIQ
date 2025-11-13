"""
Tests for Entity Identification Module.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock

from src.entity_identification import EntityIdentificationModule, EntityInfo


class TestEntityIdentificationModule:
    """Test suite for EntityIdentificationModule."""
    
    @pytest.fixture
    def mock_bq_client(self):
        """Create mock BigQuery client."""
        client = Mock()
        return client
    
    @pytest.fixture
    def entity_module(self, mock_bq_client):
        """Create EntityIdentificationModule instance."""
        return EntityIdentificationModule(bigquery_client=mock_bq_client)
    
    @pytest.mark.asyncio
    async def test_load_known_entities(self, entity_module, mock_bq_client):
        """Test loading entities from BigQuery."""
        # Mock BigQuery response
        mock_rows = [
            {
                'entity_id': 'coinbase_001',
                'entity_name': 'Coinbase',
                'entity_type': 'exchange',
                'addresses': ['bc1qtest1', 'bc1qtest2'],
                'metadata': {}
            },
            {
                'entity_id': 'foundry_001',
                'entity_name': 'Foundry USA',
                'entity_type': 'mining_pool',
                'addresses': ['bc1qpool1'],
                'metadata': {}
            }
        ]
        
        mock_result = MagicMock()
        mock_result.__iter__ = Mock(return_value=iter(mock_rows))
        
        mock_job = Mock()
        mock_job.result.return_value = mock_result
        
        mock_bq_client.query.return_value = mock_job
        
        # Load entities
        await entity_module.load_known_entities()
        
        # Verify
        assert len(entity_module.entities_cache) == 3  # 3 addresses total
        assert len(entity_module.entities_by_id) == 2  # 2 entities
        assert 'bc1qtest1' in entity_module.entities_cache
        assert 'bc1qpool1' in entity_module.entities_cache
        assert entity_module.last_reload is not None
    
    @pytest.mark.asyncio
    async def test_identify_entity_found(self, entity_module):
        """Test identifying a known entity."""
        # Setup cache
        entity = EntityInfo(
            entity_id='coinbase_001',
            entity_name='Coinbase',
            entity_type='exchange',
            addresses=['bc1qtest'],
            metadata={}
        )
        
        entity_module.entities_cache = {'bc1qtest': entity}
        entity_module.last_reload = datetime.utcnow()
        
        # Test
        result = await entity_module.identify_entity('bc1qtest')
        
        assert result is not None
        assert result.entity_name == 'Coinbase'
        assert result.entity_type == 'exchange'
    
    @pytest.mark.asyncio
    async def test_identify_entity_not_found(self, entity_module):
        """Test identifying an unknown address."""
        entity_module.entities_cache = {}
        entity_module.last_reload = datetime.utcnow()
        
        result = await entity_module.identify_entity('bc1qunknown')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_identify_mining_pool_from_script(self, entity_module):
        """Test identifying mining pool from coinbase script."""
        # Setup cache with mining pool
        pool_entity = EntityInfo(
            entity_id='foundry_001',
            entity_name='Foundry USA',
            entity_type='mining_pool',
            addresses=[],
            metadata={}
        )
        
        entity_module.entities_by_id = {'foundry_001': pool_entity}
        entity_module.last_reload = datetime.utcnow()
        
        # Coinbase transaction with Foundry identifier
        coinbase_tx = {
            'inputs': [
                {
                    'is_coinbase': True,
                    'script_sig': 'foundryusa pool mining'
                }
            ],
            'outputs': []
        }
        
        result = await entity_module.identify_mining_pool(coinbase_tx)
        
        assert result is not None
        assert result.entity_name == 'Foundry USA'
        assert result.entity_type == 'mining_pool'
    
    @pytest.mark.asyncio
    async def test_identify_mining_pool_not_coinbase(self, entity_module):
        """Test that non-coinbase transactions return None."""
        entity_module.last_reload = datetime.utcnow()
        
        regular_tx = {
            'inputs': [
                {
                    'is_coinbase': False,
                    'script_sig': 'regular transaction'
                }
            ]
        }
        
        result = await entity_module.identify_mining_pool(regular_tx)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_identify_treasury_company(self, entity_module):
        """Test identifying treasury company address."""
        # Setup cache with treasury entity
        treasury_entity = EntityInfo(
            entity_id='microstrategy_001',
            entity_name='MicroStrategy',
            entity_type='treasury',
            addresses=['bc1qtreasury'],
            metadata={'ticker': 'MSTR', 'known_holdings_btc': 152800}
        )
        
        entity_module.entities_cache = {'bc1qtreasury': treasury_entity}
        entity_module.last_reload = datetime.utcnow()
        
        result = await entity_module.identify_treasury_company('bc1qtreasury')
        
        assert result is not None
        assert result.entity_name == 'MicroStrategy'
        assert result.entity_type == 'treasury'
        assert result.metadata['ticker'] == 'MSTR'
    
    @pytest.mark.asyncio
    async def test_identify_treasury_company_not_treasury(self, entity_module):
        """Test that non-treasury entities return None."""
        # Setup cache with exchange entity
        exchange_entity = EntityInfo(
            entity_id='coinbase_001',
            entity_name='Coinbase',
            entity_type='exchange',
            addresses=['bc1qexchange'],
            metadata={}
        )
        
        entity_module.entities_cache = {'bc1qexchange': exchange_entity}
        entity_module.last_reload = datetime.utcnow()
        
        result = await entity_module.identify_treasury_company('bc1qexchange')
        
        assert result is None
    
    def test_should_reload_never_loaded(self, entity_module):
        """Test reload check when never loaded."""
        assert entity_module._should_reload() is True
    
    def test_should_reload_recently_loaded(self, entity_module):
        """Test reload check when recently loaded."""
        entity_module.last_reload = datetime.utcnow()
        assert entity_module._should_reload() is False
    
    def test_should_reload_expired(self, entity_module):
        """Test reload check when cache expired."""
        entity_module.last_reload = datetime.utcnow() - timedelta(minutes=10)
        assert entity_module._should_reload() is True
    
    def test_count_by_type(self, entity_module):
        """Test counting entities by type."""
        entity_module.entities_by_id = {
            'ex1': EntityInfo('ex1', 'Exchange 1', 'exchange', [], {}),
            'ex2': EntityInfo('ex2', 'Exchange 2', 'exchange', [], {}),
            'pool1': EntityInfo('pool1', 'Pool 1', 'mining_pool', [], {}),
            'treasury1': EntityInfo('treasury1', 'Treasury 1', 'treasury', [], {})
        }
        
        assert entity_module._count_by_type('exchange') == 2
        assert entity_module._count_by_type('mining_pool') == 1
        assert entity_module._count_by_type('treasury') == 1
        assert entity_module._count_by_type('unknown') == 0
    
    @pytest.mark.asyncio
    async def test_background_reload_task_initial_load(self, entity_module, mock_bq_client):
        """Test that background task performs initial load."""
        # Mock BigQuery response
        mock_rows = [
            {
                'entity_id': 'test_001',
                'entity_name': 'Test Entity',
                'entity_type': 'exchange',
                'addresses': ['bc1qtest'],
                'metadata': {}
            }
        ]
        
        mock_result = MagicMock()
        mock_result.__iter__ = Mock(return_value=iter(mock_rows))
        
        mock_job = Mock()
        mock_job.result.return_value = mock_result
        
        mock_bq_client.query.return_value = mock_job
        
        # Start background task
        entity_module.start_background_reload()
        
        # Wait a bit for initial load
        await asyncio.sleep(0.1)
        
        # Verify initial load happened
        assert len(entity_module.entities_cache) > 0
        assert entity_module.last_reload is not None
        
        # Stop background task
        await entity_module.stop_background_reload()
    
    @pytest.mark.asyncio
    async def test_start_background_reload(self, entity_module):
        """Test starting background reload task."""
        assert entity_module._background_task is None
        
        entity_module.start_background_reload()
        
        assert entity_module._background_task is not None
        assert not entity_module._background_task.done()
        assert entity_module._shutdown is False
        
        # Clean up
        await entity_module.stop_background_reload()
    
    @pytest.mark.asyncio
    async def test_stop_background_reload(self, entity_module):
        """Test stopping background reload task."""
        # Start task first
        entity_module.start_background_reload()
        await asyncio.sleep(0.1)
        
        # Stop task
        await entity_module.stop_background_reload()
        
        assert entity_module._shutdown is True
        assert entity_module._background_task.done()
    
    @pytest.mark.asyncio
    async def test_background_reload_already_running(self, entity_module, caplog):
        """Test that starting background reload when already running logs warning."""
        import logging
        
        # Start task
        entity_module.start_background_reload()
        await asyncio.sleep(0.1)
        
        # Try to start again
        with caplog.at_level(logging.WARNING):
            entity_module.start_background_reload()
        
        assert "already running" in caplog.text
        
        # Clean up
        await entity_module.stop_background_reload()
    
    @pytest.mark.asyncio
    async def test_stop_background_reload_not_running(self, entity_module, caplog):
        """Test stopping background reload when not running."""
        import logging
        
        with caplog.at_level(logging.DEBUG):
            await entity_module.stop_background_reload()
        
        assert "No background reload task to stop" in caplog.text
