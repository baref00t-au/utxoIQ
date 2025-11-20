"""
Unit tests for Signal Polling Module

Tests signal polling, grouping, and marking logic.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.signal_polling import SignalPollingModule, SignalGroup


# Test Fixtures

@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client"""
    client = Mock()
    client.query = Mock()
    return client


@pytest.fixture
def signal_polling_module(mock_bigquery_client):
    """Signal polling module with mocked BigQuery client"""
    return SignalPollingModule(
        bigquery_client=mock_bigquery_client,
        project_id="test-project",
        dataset_id="intel",
        confidence_threshold=0.7
    )


@pytest.fixture
def sample_signals():
    """Sample signals for testing"""
    return [
        {
            'signal_id': 'signal-1',
            'signal_type': 'mempool',
            'block_height': 800000,
            'confidence': 0.85,
            'metadata': {'fee_rate_median': 50.5},
            'created_at': datetime(2024, 1, 1, 12, 0, 0)
        },
        {
            'signal_id': 'signal-2',
            'signal_type': 'mempool',
            'block_height': 800000,
            'confidence': 0.90,
            'metadata': {'fee_rate_median': 55.0},
            'created_at': datetime(2024, 1, 1, 12, 5, 0)
        },
        {
            'signal_id': 'signal-3',
            'signal_type': 'exchange',
            'block_height': 800001,
            'confidence': 0.75,
            'metadata': {'entity_name': 'Coinbase'},
            'created_at': datetime(2024, 1, 1, 12, 10, 0)
        }
    ]


# Tests

class TestSignalPollingModule:
    """Test SignalPollingModule class"""
    
    def test_initialization(self, signal_polling_module):
        """Test module initialization"""
        assert signal_polling_module.project_id == "test-project"
        assert signal_polling_module.dataset_id == "intel"
        assert signal_polling_module.confidence_threshold == 0.7
        assert signal_polling_module.signals_table == "test-project.intel.signals"
        assert signal_polling_module.poll_interval == 10
    
    @pytest.mark.asyncio
    async def test_poll_unprocessed_signals_success(
        self,
        signal_polling_module,
        mock_bigquery_client,
        sample_signals
    ):
        """Test successful polling of unprocessed signals"""
        # Mock query result
        mock_result = [Mock(**signal) for signal in sample_signals]
        mock_job = Mock()
        mock_job.result.return_value = mock_result
        mock_bigquery_client.query.return_value = mock_job
        
        # Poll signals
        groups = await signal_polling_module.poll_unprocessed_signals()
        
        # Verify query was called
        assert mock_bigquery_client.query.called
        
        # Verify grouping
        assert len(groups) == 2  # 2 mempool signals in one group, 1 exchange in another
        assert all(isinstance(g, SignalGroup) for g in groups)
        
        # Verify first group (mempool, block 800000)
        mempool_group = next(g for g in groups if g.signal_type == 'mempool')
        assert mempool_group.block_height == 800000
        assert len(mempool_group.signals) == 2
        
        # Verify second group (exchange, block 800001)
        exchange_group = next(g for g in groups if g.signal_type == 'exchange')
        assert exchange_group.block_height == 800001
        assert len(exchange_group.signals) == 1
    
    @pytest.mark.asyncio
    async def test_poll_unprocessed_signals_empty(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test polling when no signals are available"""
        # Mock empty result
        mock_job = Mock()
        mock_job.result.return_value = []
        mock_bigquery_client.query.return_value = mock_job
        
        # Poll signals
        groups = await signal_polling_module.poll_unprocessed_signals()
        
        # Verify empty result
        assert groups == []
    
    @pytest.mark.asyncio
    async def test_poll_unprocessed_signals_error(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test polling with BigQuery error"""
        # Mock query error
        mock_bigquery_client.query.side_effect = Exception("BigQuery error")
        
        # Poll signals
        groups = await signal_polling_module.poll_unprocessed_signals()
        
        # Verify error handling
        assert groups == []
    
    def test_group_signals(self, signal_polling_module, sample_signals):
        """Test signal grouping logic"""
        groups = signal_polling_module._group_signals(sample_signals)
        
        # Verify grouping
        assert len(groups) == 2
        
        # Verify groups are sorted by block_height
        assert groups[0].block_height <= groups[1].block_height
        
        # Verify mempool group
        mempool_group = next(g for g in groups if g.signal_type == 'mempool')
        assert len(mempool_group.signals) == 2
        assert all(s['signal_type'] == 'mempool' for s in mempool_group.signals)
        
        # Verify exchange group
        exchange_group = next(g for g in groups if g.signal_type == 'exchange')
        assert len(exchange_group.signals) == 1
        assert exchange_group.signals[0]['signal_type'] == 'exchange'
    
    @pytest.mark.asyncio
    async def test_mark_signal_processed_success(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test marking a signal as processed"""
        # Mock successful update
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_job.num_dml_affected_rows = 1
        mock_bigquery_client.query.return_value = mock_job
        
        # Mark signal as processed
        result = await signal_polling_module.mark_signal_processed('signal-1')
        
        # Verify success
        assert result is True
        assert mock_bigquery_client.query.called
    
    @pytest.mark.asyncio
    async def test_mark_signal_processed_not_found(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test marking a non-existent signal"""
        # Mock no rows affected
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_job.num_dml_affected_rows = 0
        mock_bigquery_client.query.return_value = mock_job
        
        # Mark signal as processed
        result = await signal_polling_module.mark_signal_processed('nonexistent')
        
        # Verify failure
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mark_signal_processed_error(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test marking signal with BigQuery error"""
        # Mock query error
        mock_bigquery_client.query.side_effect = Exception("BigQuery error")
        
        # Mark signal as processed
        result = await signal_polling_module.mark_signal_processed('signal-1')
        
        # Verify error handling
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mark_signals_processed_batch(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test batch marking of signals"""
        # Mock successful batch update
        mock_job = Mock()
        mock_job.result.return_value = None
        mock_job.num_dml_affected_rows = 3
        mock_bigquery_client.query.return_value = mock_job
        
        # Mark signals as processed
        signal_ids = ['signal-1', 'signal-2', 'signal-3']
        count = await signal_polling_module.mark_signals_processed_batch(signal_ids)
        
        # Verify success
        assert count == 3
        assert mock_bigquery_client.query.called
    
    @pytest.mark.asyncio
    async def test_mark_signals_processed_batch_empty(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test batch marking with empty list"""
        # Mark empty list
        count = await signal_polling_module.mark_signals_processed_batch([])
        
        # Verify no query was made
        assert count == 0
        assert not mock_bigquery_client.query.called
    
    @pytest.mark.asyncio
    async def test_get_unprocessed_signal_count(
        self,
        signal_polling_module,
        mock_bigquery_client
    ):
        """Test getting unprocessed signal count"""
        # Mock count result
        mock_result = [{'count': 42}]
        mock_job = Mock()
        mock_job.result.return_value = mock_result
        mock_bigquery_client.query.return_value = mock_job
        
        # Get count
        count = await signal_polling_module.get_unprocessed_signal_count()
        
        # Verify count
        assert count == 42
    
    @pytest.mark.asyncio
    async def test_get_stale_signals(
        self,
        signal_polling_module,
        mock_bigquery_client,
        sample_signals
    ):
        """Test getting stale signals"""
        # Mock stale signals result
        stale_signals = [
            {**sample_signals[0], 'age_hours': 2},
            {**sample_signals[1], 'age_hours': 3}
        ]
        mock_result = [Mock(**signal) for signal in stale_signals]
        mock_job = Mock()
        mock_job.result.return_value = mock_result
        mock_bigquery_client.query.return_value = mock_job
        
        # Get stale signals
        result = await signal_polling_module.get_stale_signals(max_age_hours=1)
        
        # Verify stale signals
        assert len(result) == 2
        assert all('age_hours' in s for s in result)


class TestSignalGroup:
    """Test SignalGroup dataclass"""
    
    def test_signal_group_creation(self):
        """Test creating a SignalGroup"""
        signals = [
            {'signal_id': 'sig-1', 'confidence': 0.8},
            {'signal_id': 'sig-2', 'confidence': 0.9}
        ]
        
        group = SignalGroup(
            signal_type='mempool',
            block_height=800000,
            signals=signals
        )
        
        assert group.signal_type == 'mempool'
        assert group.block_height == 800000
        assert len(group.signals) == 2
        assert group.signals[0]['signal_id'] == 'sig-1'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
