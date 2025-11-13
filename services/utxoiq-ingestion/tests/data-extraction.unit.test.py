"""
Tests for Data Extraction Module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.data_extraction import (
    DataExtractionModule,
    MempoolStats,
    EntityInfo,
    WhaleAddress,
    HistoricalSignal
)


class TestDataExtractionModule:
    """Test suite for DataExtractionModule."""
    
    @pytest.fixture
    def mock_rpc(self):
        """Create mock Bitcoin RPC client."""
        rpc = Mock()
        return rpc
    
    @pytest.fixture
    def mock_bq_adapter(self):
        """Create mock BigQuery adapter."""
        adapter = Mock()
        return adapter
    
    @pytest.fixture
    def mock_bq_client(self):
        """Create mock BigQuery client."""
        client = Mock()
        return client
    
    @pytest.fixture
    def data_extraction(self, mock_rpc, mock_bq_adapter, mock_bq_client):
        """Create DataExtractionModule instance."""
        return DataExtractionModule(
            bitcoin_rpc=mock_rpc,
            bigquery_adapter=mock_bq_adapter,
            bigquery_client=mock_bq_client
        )
    
    @pytest.mark.asyncio
    async def test_get_mempool_stats_success(self, data_extraction, mock_rpc):
        """Test successful mempool stats retrieval."""
        # Mock RPC responses
        mock_rpc.getmempoolinfo.return_value = {
            'size': 1000,
            'bytes': 500000,
            'usage': 600000,
            'maxmempool': 300000000,
            'mempoolminfee': 0.00001,
            'minrelaytxfee': 0.00001,
            'unbroadcastcount': 5
        }
        
        mock_rpc.getrawmempool.return_value = {
            'tx1': {
                'fees': {'base': 0.0001},
                'vsize': 250
            },
            'tx2': {
                'fees': {'base': 0.0002},
                'vsize': 300
            }
        }
        
        # Call method
        stats = await data_extraction.get_mempool_stats()
        
        # Verify
        assert isinstance(stats, MempoolStats)
        assert stats.size == 1000
        assert stats.bytes == 500000
        assert stats.total_fee == 0.0003
        assert stats.fee_rate_median > 0
    
    @pytest.mark.asyncio
    async def test_get_mempool_stats_empty_mempool(self, data_extraction, mock_rpc):
        """Test mempool stats with empty mempool."""
        mock_rpc.getmempoolinfo.return_value = {
            'size': 0,
            'bytes': 0,
            'usage': 0,
            'maxmempool': 300000000,
            'mempoolminfee': 0.00001,
            'minrelaytxfee': 0.00001,
            'unbroadcastcount': 0
        }
        
        mock_rpc.getrawmempool.return_value = {}
        
        stats = await data_extraction.get_mempool_stats()
        
        assert stats.size == 0
        assert stats.total_fee == 0.0
        assert stats.fee_rate_median == 0.0
    
    @pytest.mark.asyncio
    async def test_identify_exchange_addresses_found(self, data_extraction):
        """Test identifying known exchange addresses."""
        # Setup mock entities
        exchange_entity = EntityInfo(
            entity_id='coinbase_001',
            entity_name='Coinbase',
            entity_type='exchange',
            addresses=['bc1qtest123'],
            metadata={}
        )
        
        data_extraction.known_entities = {
            'bc1qtest123': exchange_entity
        }
        data_extraction.last_entity_load = datetime.utcnow()
        
        # Test
        addresses = ['bc1qtest123', 'bc1qunknown']
        result = await data_extraction.identify_exchange_addresses(addresses)
        
        assert len(result) == 1
        assert 'bc1qtest123' in result
        assert result['bc1qtest123'].entity_name == 'Coinbase'
    
    @pytest.mark.asyncio
    async def test_identify_exchange_addresses_not_found(self, data_extraction):
        """Test identifying addresses with no matches."""
        data_extraction.known_entities = {}
        data_extraction.last_entity_load = datetime.utcnow()
        
        addresses = ['bc1qunknown1', 'bc1qunknown2']
        result = await data_extraction.identify_exchange_addresses(addresses)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_detect_whale_addresses(self, data_extraction):
        """Test whale address detection."""
        # Mock address balance query
        async def mock_get_balance(address):
            if address == 'bc1qwhale':
                return 1500.0  # Above threshold
            return 50.0  # Below threshold
        
        data_extraction._get_address_balance = mock_get_balance
        
        # Test outputs
        outputs = [
            {
                'addresses': ['bc1qwhale'],
                'value': 150_000_000_000  # 1500 BTC in satoshis
            },
            {
                'addresses': ['bc1qsmall'],
                'value': 5_000_000_000  # 50 BTC in satoshis
            }
        ]
        
        whales = await data_extraction.detect_whale_addresses(outputs)
        
        assert len(whales) == 1
        assert whales[0].address == 'bc1qwhale'
        assert whales[0].balance_btc == 1500.0
    
    @pytest.mark.asyncio
    async def test_get_historical_signals(self, data_extraction, mock_bq_client):
        """Test querying historical signals."""
        # Mock BigQuery response
        mock_row = {
            'signal_id': 'sig_123',
            'signal_type': 'mempool',
            'block_height': 800000,
            'confidence': 0.85,
            'metadata': {'fee_rate_median': 50.0},
            'created_at': datetime.utcnow()
        }
        
        mock_result = MagicMock()
        mock_result.__iter__ = Mock(return_value=iter([mock_row]))
        
        mock_job = Mock()
        mock_job.result.return_value = mock_result
        
        mock_bq_client.query.return_value = mock_job
        
        # Test
        signals = await data_extraction.get_historical_signals(
            signal_type='mempool',
            time_window=timedelta(hours=1)
        )
        
        assert len(signals) == 1
        assert signals[0].signal_id == 'sig_123'
        assert signals[0].signal_type == 'mempool'
        assert signals[0].confidence == 0.85
