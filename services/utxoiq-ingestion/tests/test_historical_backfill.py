"""
Unit tests for Historical Backfill Module.

Tests the historical backfill functionality including date range queries,
chronological processing, rate limiting, and selective backfill.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from google.cloud import bigquery

from src.historical_backfill import (
    HistoricalBackfillModule,
    BackfillResult
)
from src.models import BlockData
from src.signal_persistence import SignalPersistenceModule, PersistenceResult

# Import Signal from shared types
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from shared.types import Signal


@pytest.fixture
def mock_bigquery_client():
    """Create mock BigQuery client."""
    client = Mock(spec=bigquery.Client)
    return client


@pytest.fixture
def mock_signal_processor():
    """Create mock signal processor."""
    processor = AsyncMock()
    processor.enabled = True
    processor.signal_type = "mempool"
    processor.__class__.__name__ = "MempoolProcessor"
    return processor


@pytest.fixture
def mock_signal_persistence():
    """Create mock signal persistence module."""
    persistence = AsyncMock(spec=SignalPersistenceModule)
    persistence.persist_signals = AsyncMock(return_value=PersistenceResult(
        success=True,
        signal_count=1,
        correlation_id="test-correlation-id"
    ))
    return persistence


@pytest.fixture
def backfill_module(mock_bigquery_client, mock_signal_processor, mock_signal_persistence):
    """Create HistoricalBackfillModule instance."""
    return HistoricalBackfillModule(
        bigquery_client=mock_bigquery_client,
        signal_processors=[mock_signal_processor],
        signal_persistence=mock_signal_persistence,
        rate_limit_blocks_per_minute=100
    )


@pytest.fixture
def sample_block():
    """Create sample block data."""
    return BlockData(
        block_hash="00000000000000000001",
        height=800000,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        size=1000000,
        tx_count=2000,
        fees_total=0.5
    )


@pytest.fixture
def sample_signal():
    """Create sample signal."""
    return Signal(
        signal_id="test-signal-id",
        signal_type="mempool",
        block_height=800000,
        confidence=0.85,
        metadata={"fee_rate_median": 50.0},
        created_at=datetime.utcnow(),
        processed=False,
        processed_at=None
    )


class TestHistoricalBackfillModuleInit:
    """Test HistoricalBackfillModule initialization."""
    
    def test_init_with_defaults(self, mock_bigquery_client, mock_signal_processor, mock_signal_persistence):
        """Test initialization with default rate limit."""
        module = HistoricalBackfillModule(
            bigquery_client=mock_bigquery_client,
            signal_processors=[mock_signal_processor],
            signal_persistence=mock_signal_persistence
        )
        
        assert module.rate_limit == 100
        assert module.block_delay_seconds == 0.6  # 60 / 100
    
    def test_init_with_custom_rate_limit(self, mock_bigquery_client, mock_signal_processor, mock_signal_persistence):
        """Test initialization with custom rate limit."""
        module = HistoricalBackfillModule(
            bigquery_client=mock_bigquery_client,
            signal_processors=[mock_signal_processor],
            signal_persistence=mock_signal_persistence,
            rate_limit_blocks_per_minute=50
        )
        
        assert module.rate_limit == 50
        assert module.block_delay_seconds == 1.2  # 60 / 50


class TestQueryHistoricalBlocks:
    """Test _query_historical_blocks method."""
    
    @pytest.mark.asyncio
    async def test_query_historical_blocks_success(self, backfill_module, sample_block):
        """Test successful query of historical blocks."""
        # Mock BigQuery query result
        mock_row = {
            'block_hash': sample_block.block_hash,
            'height': sample_block.height,
            'timestamp': sample_block.timestamp,
            'size': sample_block.size,
            'tx_count': sample_block.tx_count,
            'fees_total': sample_block.fees_total
        }
        
        mock_query_job = Mock()
        mock_query_job.result.return_value = [mock_row]
        backfill_module.client.query.return_value = mock_query_job
        
        # Query blocks
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        blocks = await backfill_module._query_historical_blocks(start_date, end_date)
        
        # Verify results
        assert len(blocks) == 1
        assert blocks[0].height == sample_block.height
        assert blocks[0].block_hash == sample_block.block_hash
        
        # Verify query was called
        backfill_module.client.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_historical_blocks_empty_result(self, backfill_module):
        """Test query with no blocks found."""
        # Mock empty query result
        mock_query_job = Mock()
        mock_query_job.result.return_value = []
        backfill_module.client.query.return_value = mock_query_job
        
        # Query blocks
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        blocks = await backfill_module._query_historical_blocks(start_date, end_date)
        
        # Verify empty result
        assert len(blocks) == 0
    
    @pytest.mark.asyncio
    async def test_query_historical_blocks_error(self, backfill_module):
        """Test query error handling."""
        # Mock query error
        backfill_module.client.query.side_effect = Exception("BigQuery error")
        
        # Query should raise exception
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        
        with pytest.raises(Exception, match="BigQuery error"):
            await backfill_module._query_historical_blocks(start_date, end_date)


class TestGetHistoricalContext:
    """Test _get_historical_context method."""
    
    @pytest.mark.asyncio
    async def test_get_historical_context_success(self, backfill_module, sample_block):
        """Test successful retrieval of historical context."""
        # Mock surrounding blocks
        mock_rows = [
            {
                'block_hash': f"hash_{i}",
                'height': sample_block.height - 5 + i,
                'timestamp': sample_block.timestamp + timedelta(minutes=i * 10),
                'size': 1000000,
                'tx_count': 2000,
                'fees_total': 0.5
            }
            for i in range(11)  # 5 before, target, 5 after
        ]
        
        mock_query_job = Mock()
        mock_query_job.result.return_value = mock_rows
        backfill_module.client.query.return_value = mock_query_job
        
        # Get context
        context = await backfill_module._get_historical_context(sample_block)
        
        # Verify context structure
        assert "surrounding_blocks" in context
        assert "context_window" in context
        assert "blocks_before" in context
        assert "blocks_after" in context
        
        assert len(context["surrounding_blocks"]) == 11
        assert context["context_window"] == 10
    
    @pytest.mark.asyncio
    async def test_get_historical_context_error(self, backfill_module, sample_block):
        """Test error handling in context retrieval."""
        # Mock query error
        backfill_module.client.query.side_effect = Exception("BigQuery error")
        
        # Should return empty context without raising
        context = await backfill_module._get_historical_context(sample_block)
        
        # Verify empty context
        assert context["surrounding_blocks"] == []
        assert context["context_window"] == 0
        assert context["blocks_before"] == []
        assert context["blocks_after"] == []


class TestProcessHistoricalBlock:
    """Test _process_historical_block method."""
    
    @pytest.mark.asyncio
    async def test_process_historical_block_success(
        self,
        backfill_module,
        sample_block,
        sample_signal,
        mock_signal_processor
    ):
        """Test successful processing of historical block."""
        # Mock processor to return signal
        mock_signal_processor.process_block = AsyncMock(return_value=[sample_signal])
        
        # Mock historical context
        backfill_module._get_historical_context = AsyncMock(return_value={
            "surrounding_blocks": [],
            "context_window": 10,
            "blocks_before": [],
            "blocks_after": []
        })
        
        # Process block
        signals = await backfill_module._process_historical_block(sample_block, None)
        
        # Verify signals
        assert len(signals) == 1
        assert signals[0].created_at == sample_block.timestamp
        assert signals[0].processed is False
        assert signals[0].processed_at is None
        
        # Verify persistence was called
        backfill_module.persistence.persist_signals.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_historical_block_with_signal_type_filter(
        self,
        backfill_module,
        sample_block,
        sample_signal,
        mock_signal_processor
    ):
        """Test processing with signal type filter."""
        # Mock processor
        mock_signal_processor.process_block = AsyncMock(return_value=[sample_signal])
        
        # Mock historical context
        backfill_module._get_historical_context = AsyncMock(return_value={
            "surrounding_blocks": [],
            "context_window": 10,
            "blocks_before": [],
            "blocks_after": []
        })
        
        # Process with matching signal type
        signals = await backfill_module._process_historical_block(
            sample_block,
            signal_types=["mempool"]
        )
        assert len(signals) == 1
        
        # Process with non-matching signal type
        signals = await backfill_module._process_historical_block(
            sample_block,
            signal_types=["exchange"]
        )
        assert len(signals) == 0
    
    @pytest.mark.asyncio
    async def test_process_historical_block_processor_error(
        self,
        backfill_module,
        sample_block,
        mock_signal_processor
    ):
        """Test handling of processor errors."""
        # Mock processor to raise error
        mock_signal_processor.process_block = AsyncMock(
            side_effect=Exception("Processor error")
        )
        
        # Mock historical context
        backfill_module._get_historical_context = AsyncMock(return_value={
            "surrounding_blocks": [],
            "context_window": 10,
            "blocks_before": [],
            "blocks_after": []
        })
        
        # Process should continue despite processor error
        signals = await backfill_module._process_historical_block(sample_block, None)
        
        # Should return empty list (processor failed)
        assert len(signals) == 0


class TestBackfillDateRange:
    """Test backfill_date_range method."""
    
    @pytest.mark.asyncio
    async def test_backfill_date_range_success(
        self,
        backfill_module,
        sample_block,
        sample_signal
    ):
        """Test successful backfill of date range."""
        # Mock query to return blocks
        backfill_module._query_historical_blocks = AsyncMock(return_value=[sample_block])
        
        # Mock process to return signals
        backfill_module._process_historical_block = AsyncMock(return_value=[sample_signal])
        
        # Run backfill
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        result = await backfill_module.backfill_date_range(start_date, end_date)
        
        # Verify result
        assert isinstance(result, BackfillResult)
        assert result.blocks_processed == 1
        assert result.signals_generated == 1
        assert result.start_date == start_date
        assert result.end_date == end_date
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_backfill_date_range_no_blocks(self, backfill_module):
        """Test backfill with no blocks found."""
        # Mock query to return empty list
        backfill_module._query_historical_blocks = AsyncMock(return_value=[])
        
        # Run backfill
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        result = await backfill_module.backfill_date_range(start_date, end_date)
        
        # Verify result
        assert result.blocks_processed == 0
        assert result.signals_generated == 0
    
    @pytest.mark.asyncio
    async def test_backfill_date_range_with_errors(
        self,
        backfill_module,
        sample_block
    ):
        """Test backfill with processing errors."""
        # Mock query to return blocks
        backfill_module._query_historical_blocks = AsyncMock(return_value=[sample_block])
        
        # Mock process to raise error
        backfill_module._process_historical_block = AsyncMock(
            side_effect=Exception("Processing error")
        )
        
        # Run backfill
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        result = await backfill_module.backfill_date_range(start_date, end_date)
        
        # Verify result includes error
        assert result.blocks_processed == 1
        assert result.signals_generated == 0
        assert len(result.errors) == 1
        assert "Processing error" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_backfill_date_range_rate_limiting(
        self,
        backfill_module,
        sample_block,
        sample_signal
    ):
        """Test rate limiting during backfill."""
        # Create multiple blocks
        blocks = [sample_block for _ in range(3)]
        
        # Mock query to return blocks
        backfill_module._query_historical_blocks = AsyncMock(return_value=blocks)
        
        # Mock process to return signals
        backfill_module._process_historical_block = AsyncMock(return_value=[sample_signal])
        
        # Track sleep calls
        sleep_calls = []
        original_sleep = asyncio.sleep
        
        async def mock_sleep(delay):
            sleep_calls.append(delay)
            # Don't actually sleep in tests
            await original_sleep(0)
        
        # Run backfill with mocked sleep
        with patch('asyncio.sleep', side_effect=mock_sleep):
            start_date = date(2024, 1, 1)
            end_date = date(2024, 1, 2)
            result = await backfill_module.backfill_date_range(start_date, end_date)
        
        # Verify rate limiting was applied
        assert len(sleep_calls) == 3  # One sleep per block
        assert all(delay == backfill_module.block_delay_seconds for delay in sleep_calls)
    
    @pytest.mark.asyncio
    async def test_backfill_date_range_with_signal_types(
        self,
        backfill_module,
        sample_block,
        sample_signal
    ):
        """Test selective backfill by signal types."""
        # Mock query to return blocks
        backfill_module._query_historical_blocks = AsyncMock(return_value=[sample_block])
        
        # Mock process to return signals
        backfill_module._process_historical_block = AsyncMock(return_value=[sample_signal])
        
        # Run backfill with signal type filter
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 2)
        signal_types = ["mempool", "exchange"]
        result = await backfill_module.backfill_date_range(
            start_date,
            end_date,
            signal_types=signal_types
        )
        
        # Verify process was called with signal_types
        backfill_module._process_historical_block.assert_called()
        call_args = backfill_module._process_historical_block.call_args
        assert call_args[0][1] == signal_types  # Second argument is signal_types


class TestBackfillResult:
    """Test BackfillResult dataclass."""
    
    def test_backfill_result_creation(self):
        """Test BackfillResult creation."""
        result = BackfillResult(
            blocks_processed=100,
            signals_generated=500,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            duration_seconds=600.0,
            errors=[]
        )
        
        assert result.blocks_processed == 100
        assert result.signals_generated == 500
        assert result.start_date == date(2024, 1, 1)
        assert result.end_date == date(2024, 1, 31)
        assert result.duration_seconds == 600.0
        assert len(result.errors) == 0
    
    def test_backfill_result_repr(self):
        """Test BackfillResult string representation."""
        result = BackfillResult(
            blocks_processed=100,
            signals_generated=500,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            duration_seconds=600.0,
            errors=["error1", "error2"]
        )
        
        repr_str = repr(result)
        assert "blocks=100" in repr_str
        assert "signals=500" in repr_str
        assert "errors=2" in repr_str
