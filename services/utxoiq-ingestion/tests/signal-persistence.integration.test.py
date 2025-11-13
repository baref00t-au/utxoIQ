"""
Unit tests for SignalPersistenceModule.

Tests signal ID generation, batch persistence, error handling, and retry logic.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from signal_persistence import SignalPersistenceModule, PersistenceResult
from types.signal_models import Signal


class TestSignalPersistenceModule:
    """Test suite for SignalPersistenceModule."""
    
    @pytest.fixture
    def mock_bigquery_client(self):
        """Create a mock BigQuery client."""
        client = Mock(spec=bigquery.Client)
        return client
    
    @pytest.fixture
    def persistence_module(self, mock_bigquery_client):
        """Create a SignalPersistenceModule instance with mock client."""
        return SignalPersistenceModule(
            bigquery_client=mock_bigquery_client,
            project_id="test-project",
            dataset_id="intel",
            table_name="signals",
            max_retries=3,
            base_delay=0.1  # Short delay for testing
        )
    
    @pytest.fixture
    def sample_signal(self):
        """Create a sample signal for testing."""
        return Signal(
            signal_id="test-signal-123",
            signal_type="mempool",
            block_height=800000,
            confidence=0.85,
            metadata={
                "fee_rate_median": 50.5,
                "fee_rate_change_pct": 25.3,
                "tx_count": 15000,
                "mempool_size_mb": 120.5,
                "comparison_window": "1h"
            },
            created_at=datetime.utcnow(),
            processed=False,
            processed_at=None
        )
    
    def test_generate_signal_id(self, persistence_module):
        """Test signal ID generation returns valid UUID."""
        signal_id = persistence_module.generate_signal_id()
        
        # Check it's a string
        assert isinstance(signal_id, str)
        
        # Check it's a valid UUID format (36 characters with hyphens)
        assert len(signal_id) == 36
        assert signal_id.count('-') == 4
    
    def test_generate_signal_id_uniqueness(self, persistence_module):
        """Test that generated signal IDs are unique."""
        ids = [persistence_module.generate_signal_id() for _ in range(100)]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
    
    @pytest.mark.asyncio
    async def test_persist_signals_empty_list(self, persistence_module):
        """Test persisting empty signal list returns success."""
        result = await persistence_module.persist_signals(
            signals=[],
            correlation_id="test-correlation-123"
        )
        
        assert result.success is True
        assert result.signal_count == 0
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_persist_signals_success(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_signal
    ):
        """Test successful signal persistence."""
        # Mock successful insert (no errors)
        mock_bigquery_client.insert_rows_json.return_value = []
        
        signals = [sample_signal]
        result = await persistence_module.persist_signals(
            signals=signals,
            correlation_id="test-correlation-123"
        )
        
        # Verify result
        assert result.success is True
        assert result.signal_count == 1
        assert result.error is None
        
        # Verify BigQuery client was called
        mock_bigquery_client.insert_rows_json.assert_called_once()
        call_args = mock_bigquery_client.insert_rows_json.call_args
        
        # Check table ID
        assert call_args[0][0] == "test-project.intel.signals"
        
        # Check row data
        rows = call_args[0][1]
        assert len(rows) == 1
        assert rows[0]["signal_id"] == "test-signal-123"
        assert rows[0]["signal_type"] == "mempool"
        assert rows[0]["block_height"] == 800000
        assert rows[0]["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_persist_signals_multiple(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_signal
    ):
        """Test persisting multiple signals in batch."""
        # Mock successful insert
        mock_bigquery_client.insert_rows_json.return_value = []
        
        # Create multiple signals
        signals = [
            Signal(
                signal_id=f"signal-{i}",
                signal_type="mempool",
                block_height=800000 + i,
                confidence=0.8 + (i * 0.01),
                metadata={"test": i},
                created_at=datetime.utcnow()
            )
            for i in range(5)
        ]
        
        result = await persistence_module.persist_signals(
            signals=signals,
            correlation_id="test-correlation-123"
        )
        
        # Verify result
        assert result.success is True
        assert result.signal_count == 5
        
        # Verify single batch insert was called
        assert mock_bigquery_client.insert_rows_json.call_count == 1
        
        # Verify all signals were included
        rows = mock_bigquery_client.insert_rows_json.call_args[0][1]
        assert len(rows) == 5
    
    @pytest.mark.asyncio
    async def test_persist_signals_bigquery_errors(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_signal
    ):
        """Test handling of BigQuery insertion errors."""
        # Mock BigQuery returning errors
        mock_bigquery_client.insert_rows_json.return_value = [
            {"index": 0, "errors": [{"reason": "invalid", "message": "Invalid data"}]}
        ]
        
        result = await persistence_module.persist_signals(
            signals=[sample_signal],
            correlation_id="test-correlation-123"
        )
        
        # Verify failure result
        assert result.success is False
        assert result.signal_count == 0
        assert result.error is not None
        assert "BigQuery insertion errors" in result.error
    
    @pytest.mark.asyncio
    async def test_persist_signals_retry_on_exception(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_signal
    ):
        """Test retry logic on transient exceptions."""
        # Mock client to fail twice then succeed
        mock_bigquery_client.insert_rows_json.side_effect = [
            GoogleCloudError("Transient error 1"),
            GoogleCloudError("Transient error 2"),
            []  # Success on third attempt
        ]
        
        result = await persistence_module.persist_signals(
            signals=[sample_signal],
            correlation_id="test-correlation-123"
        )
        
        # Verify success after retries
        assert result.success is True
        assert result.signal_count == 1
        
        # Verify it was called 3 times (initial + 2 retries)
        assert mock_bigquery_client.insert_rows_json.call_count == 3
    
    @pytest.mark.asyncio
    async def test_persist_signals_max_retries_exceeded(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_signal
    ):
        """Test failure after max retries exceeded."""
        # Mock client to always fail
        mock_bigquery_client.insert_rows_json.side_effect = GoogleCloudError(
            "Persistent error"
        )
        
        result = await persistence_module.persist_signals(
            signals=[sample_signal],
            correlation_id="test-correlation-123"
        )
        
        # Verify failure result
        assert result.success is False
        assert result.signal_count == 0
        assert result.error is not None
        assert "failed after 3 attempts" in result.error
        
        # Verify it was called max_retries times
        assert mock_bigquery_client.insert_rows_json.call_count == 3
    
    @pytest.mark.asyncio
    async def test_persist_signals_exponential_backoff(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_signal
    ):
        """Test exponential backoff timing."""
        # Mock client to fail twice then succeed
        mock_bigquery_client.insert_rows_json.side_effect = [
            GoogleCloudError("Error 1"),
            GoogleCloudError("Error 2"),
            []
        ]
        
        import time
        start_time = time.time()
        
        result = await persistence_module.persist_signals(
            signals=[sample_signal],
            correlation_id="test-correlation-123"
        )
        
        elapsed = time.time() - start_time
        
        # Verify success
        assert result.success is True
        
        # Verify timing: 0.1s + 0.2s = 0.3s minimum
        # (base_delay=0.1, so delays are 0.1 * 2^0 = 0.1, 0.1 * 2^1 = 0.2)
        assert elapsed >= 0.3
    
    def test_signal_to_bigquery_row_conversion(
        self,
        persistence_module,
        sample_signal
    ):
        """Test conversion of Signal to BigQuery row format."""
        row = persistence_module._signal_to_bigquery_row(sample_signal)
        
        # Verify all required fields are present
        assert "signal_id" in row
        assert "signal_type" in row
        assert "block_height" in row
        assert "confidence" in row
        assert "metadata" in row
        assert "created_at" in row
        assert "processed" in row
        assert "processed_at" in row
        
        # Verify values
        assert row["signal_id"] == "test-signal-123"
        assert row["signal_type"] == "mempool"
        assert row["block_height"] == 800000
        assert row["confidence"] == 0.85
        assert row["processed"] is False
        assert row["processed_at"] is None
        
        # Verify metadata is preserved
        assert row["metadata"]["fee_rate_median"] == 50.5
        assert row["metadata"]["tx_count"] == 15000
    
    def test_signal_to_bigquery_row_datetime_serialization(
        self,
        persistence_module
    ):
        """Test datetime serialization in row conversion."""
        now = datetime.utcnow()
        signal = Signal(
            signal_id="test-123",
            signal_type="exchange",
            block_height=800000,
            confidence=0.9,
            metadata={},
            created_at=now,
            processed=True,
            processed_at=now
        )
        
        row = persistence_module._signal_to_bigquery_row(signal)
        
        # Verify datetime fields are converted to ISO format strings
        assert isinstance(row["created_at"], str)
        assert isinstance(row["processed_at"], str)
        assert "T" in row["created_at"]  # ISO format contains 'T'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
