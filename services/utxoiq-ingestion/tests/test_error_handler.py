"""
Unit tests for ErrorHandler module.

Tests error handling, retry logic, and correlation ID logging.

Requirements: 6.1, 6.2, 6.4, 6.5
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from datetime import timedelta

from src.error_handler import ErrorHandler
from src.monitoring import MonitoringModule


@pytest.fixture
def mock_monitoring():
    """Create a mock monitoring module."""
    monitoring = Mock(spec=MonitoringModule)
    monitoring.emit_error_metric = AsyncMock()
    return monitoring


@pytest.fixture
def error_handler(mock_monitoring):
    """Create an ErrorHandler instance with mock monitoring."""
    return ErrorHandler(
        monitoring=mock_monitoring,
        max_retries=3,
        base_delay=0.1  # Shorter delay for tests
    )


@pytest.fixture
def error_handler_no_monitoring():
    """Create an ErrorHandler instance without monitoring."""
    return ErrorHandler(
        monitoring=None,
        max_retries=3,
        base_delay=0.1
    )


class TestErrorHandlerInitialization:
    """Test ErrorHandler initialization."""
    
    def test_init_with_monitoring(self, mock_monitoring):
        """Test initialization with monitoring module."""
        handler = ErrorHandler(
            monitoring=mock_monitoring,
            max_retries=5,
            base_delay=2.0
        )
        
        assert handler.monitoring == mock_monitoring
        assert handler.max_retries == 5
        assert handler.base_delay == 2.0
    
    def test_init_without_monitoring(self):
        """Test initialization without monitoring module."""
        handler = ErrorHandler(
            monitoring=None,
            max_retries=3,
            base_delay=1.0
        )
        
        assert handler.monitoring is None
        assert handler.max_retries == 3
        assert handler.base_delay == 1.0
    
    def test_init_defaults(self):
        """Test initialization with default values."""
        handler = ErrorHandler()
        
        assert handler.monitoring is None
        assert handler.max_retries == 3
        assert handler.base_delay == 1.0


class TestHandleProcessorError:
    """Test handle_processor_error method."""
    
    @pytest.mark.asyncio
    async def test_handle_processor_error_with_monitoring(
        self,
        error_handler,
        mock_monitoring,
        caplog
    ):
        """Test handling processor error with monitoring enabled."""
        error = ValueError("Test error")
        processor_name = "MempoolProcessor"
        block_height = 800000
        correlation_id = "test-correlation-id"
        
        with caplog.at_level(logging.ERROR):
            await error_handler.handle_processor_error(
                error=error,
                processor_name=processor_name,
                block_height=block_height,
                correlation_id=correlation_id
            )
        
        # Verify error was logged
        assert "Signal processor failed: MempoolProcessor" in caplog.text
        assert correlation_id in caplog.text
        assert str(block_height) in caplog.text
        
        # Verify monitoring metric was emitted
        mock_monitoring.emit_error_metric.assert_called_once_with(
            error_type="processor_failure",
            service_name="utxoiq-ingestion",
            processor=processor_name,
            correlation_id=correlation_id
        )
    
    @pytest.mark.asyncio
    async def test_handle_processor_error_without_monitoring(
        self,
        error_handler_no_monitoring,
        caplog
    ):
        """Test handling processor error without monitoring."""
        error = RuntimeError("Test error")
        processor_name = "ExchangeProcessor"
        block_height = 800001
        correlation_id = "test-correlation-id-2"
        
        with caplog.at_level(logging.ERROR):
            await error_handler_no_monitoring.handle_processor_error(
                error=error,
                processor_name=processor_name,
                block_height=block_height,
                correlation_id=correlation_id
            )
        
        # Verify error was logged
        assert "Signal processor failed: ExchangeProcessor" in caplog.text
        assert correlation_id in caplog.text
    
    @pytest.mark.asyncio
    async def test_handle_processor_error_monitoring_failure(
        self,
        error_handler,
        mock_monitoring,
        caplog
    ):
        """Test handling processor error when monitoring fails."""
        # Make monitoring emit fail
        mock_monitoring.emit_error_metric.side_effect = Exception("Monitoring error")
        
        error = ValueError("Test error")
        processor_name = "WhaleProcessor"
        block_height = 800002
        correlation_id = "test-correlation-id-3"
        
        with caplog.at_level(logging.WARNING):
            await error_handler.handle_processor_error(
                error=error,
                processor_name=processor_name,
                block_height=block_height,
                correlation_id=correlation_id
            )
        
        # Verify warning was logged about monitoring failure
        assert "Failed to emit error metric" in caplog.text


class TestRetryWithBackoff:
    """Test retry_with_backoff method."""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self, error_handler):
        """Test successful operation on first attempt."""
        async def successful_operation():
            return "success"
        
        result = await error_handler.retry_with_backoff(
            operation=successful_operation,
            operation_name="test_operation",
            correlation_id="test-id"
        )
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self, error_handler, caplog):
        """Test successful operation after some failures."""
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"
        
        with caplog.at_level(logging.WARNING):
            result = await error_handler.retry_with_backoff(
                operation=flaky_operation,
                operation_name="flaky_operation",
                correlation_id="test-id"
            )
        
        assert result == "success"
        assert call_count == 3
        
        # Verify retry warnings were logged
        assert "Operation failed, retrying" in caplog.text
        assert "Operation succeeded after 3 attempts" in caplog.text
    
    @pytest.mark.asyncio
    async def test_retry_all_attempts_fail(self, error_handler, caplog):
        """Test operation that fails all retry attempts."""
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match="Attempt 3 failed"):
                await error_handler.retry_with_backoff(
                    operation=failing_operation,
                    operation_name="failing_operation",
                    correlation_id="test-id"
                )
        
        assert call_count == 3
        
        # Verify final error was logged
        assert "Operation failed after 3 attempts" in caplog.text
    
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self, error_handler):
        """Test exponential backoff timing."""
        call_times = []
        
        async def failing_operation():
            call_times.append(asyncio.get_event_loop().time())
            raise ValueError("Test error")
        
        try:
            await error_handler.retry_with_backoff(
                operation=failing_operation,
                operation_name="test_operation",
                correlation_id="test-id"
            )
        except ValueError:
            pass
        
        # Verify we made 3 attempts
        assert len(call_times) == 3
        
        # Verify exponential backoff delays (0.1s, 0.2s)
        # Allow some tolerance for timing
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        assert 0.08 < delay1 < 0.15  # ~0.1s
        assert 0.18 < delay2 < 0.25  # ~0.2s
    
    @pytest.mark.asyncio
    async def test_retry_with_args_and_kwargs(self, error_handler):
        """Test retry with operation arguments."""
        async def operation_with_args(x, y, z=0):
            return x + y + z
        
        result = await error_handler.retry_with_backoff(
            operation_with_args,  # operation
            "test_operation",     # operation_name
            "test-id",            # correlation_id
            10,                   # x
            20,                   # y
            z=5                   # z
        )
        
        assert result == 35


class TestCheckStaleSignals:
    """Test check_stale_signals method."""
    
    @pytest.mark.asyncio
    async def test_check_stale_signals_default_threshold(
        self,
        error_handler,
        caplog
    ):
        """Test checking for stale signals with default threshold."""
        with caplog.at_level(logging.DEBUG):
            await error_handler.check_stale_signals()
        
        # Verify check was logged
        assert "Checking for stale signals" in caplog.text
        assert "threshold_hours" in caplog.text
    
    @pytest.mark.asyncio
    async def test_check_stale_signals_custom_threshold(
        self,
        error_handler,
        caplog
    ):
        """Test checking for stale signals with custom threshold."""
        custom_threshold = timedelta(hours=2)
        
        with caplog.at_level(logging.DEBUG):
            await error_handler.check_stale_signals(
                signal_age_threshold=custom_threshold
            )
        
        # Verify custom threshold was used
        assert "Checking for stale signals" in caplog.text


class TestLogWithContext:
    """Test log_with_context method."""
    
    def test_log_info_with_context(self, error_handler, caplog):
        """Test logging info message with context."""
        with caplog.at_level(logging.INFO):
            error_handler.log_with_context(
                level="info",
                message="Test message",
                correlation_id="test-id",
                block_height=800000,
                signal_count=5
            )
        
        # Verify message and context were logged
        assert "Test message" in caplog.text
        assert "test-id" in caplog.text
    
    def test_log_warning_with_context(self, error_handler, caplog):
        """Test logging warning message with context."""
        with caplog.at_level(logging.WARNING):
            error_handler.log_with_context(
                level="warning",
                message="Warning message",
                correlation_id="test-id",
                error_type="test_error"
            )
        
        assert "Warning message" in caplog.text
    
    def test_log_error_with_context(self, error_handler, caplog):
        """Test logging error message with context."""
        with caplog.at_level(logging.ERROR):
            error_handler.log_with_context(
                level="error",
                message="Error message",
                correlation_id="test-id",
                processor="TestProcessor"
            )
        
        assert "Error message" in caplog.text


class TestHandleBigQueryError:
    """Test handle_bigquery_error method."""
    
    @pytest.mark.asyncio
    async def test_handle_bigquery_error_with_monitoring(
        self,
        error_handler,
        mock_monitoring,
        caplog
    ):
        """Test handling BigQuery error with monitoring."""
        error = Exception("BigQuery write failed")
        operation = "insert_signals"
        correlation_id = "test-id"
        
        with caplog.at_level(logging.ERROR):
            await error_handler.handle_bigquery_error(
                error=error,
                operation=operation,
                correlation_id=correlation_id,
                table_id="intel.signals"
            )
        
        # Verify error was logged
        assert "BigQuery operation failed: insert_signals" in caplog.text
        assert correlation_id in caplog.text
        
        # Verify monitoring metric was emitted
        mock_monitoring.emit_error_metric.assert_called_once_with(
            error_type="bigquery_failure",
            service_name="utxoiq-ingestion",
            correlation_id=correlation_id
        )
    
    @pytest.mark.asyncio
    async def test_handle_bigquery_error_without_monitoring(
        self,
        error_handler_no_monitoring,
        caplog
    ):
        """Test handling BigQuery error without monitoring."""
        error = Exception("BigQuery query failed")
        operation = "query_signals"
        correlation_id = "test-id"
        
        with caplog.at_level(logging.ERROR):
            await error_handler_no_monitoring.handle_bigquery_error(
                error=error,
                operation=operation,
                correlation_id=correlation_id
            )
        
        # Verify error was logged
        assert "BigQuery operation failed: query_signals" in caplog.text


class TestHandleAIProviderError:
    """Test handle_ai_provider_error method."""
    
    @pytest.mark.asyncio
    async def test_handle_ai_provider_error_with_monitoring(
        self,
        error_handler,
        mock_monitoring,
        caplog
    ):
        """Test handling AI provider error with monitoring."""
        error = Exception("API rate limit exceeded")
        provider = "vertex_ai"
        signal_id = "signal-123"
        correlation_id = "test-id"
        
        with caplog.at_level(logging.ERROR):
            await error_handler.handle_ai_provider_error(
                error=error,
                provider=provider,
                signal_id=signal_id,
                correlation_id=correlation_id
            )
        
        # Verify error was logged
        assert "AI provider failed: vertex_ai" in caplog.text
        assert signal_id in caplog.text
        assert correlation_id in caplog.text
        
        # Verify monitoring metric was emitted
        mock_monitoring.emit_error_metric.assert_called_once_with(
            error_type="ai_provider_failure",
            service_name="insight-generator",
            correlation_id=correlation_id
        )
    
    @pytest.mark.asyncio
    async def test_handle_ai_provider_error_without_monitoring(
        self,
        error_handler_no_monitoring,
        caplog
    ):
        """Test handling AI provider error without monitoring."""
        error = Exception("Model timeout")
        provider = "openai"
        signal_id = "signal-456"
        correlation_id = "test-id"
        
        with caplog.at_level(logging.ERROR):
            await error_handler_no_monitoring.handle_ai_provider_error(
                error=error,
                provider=provider,
                signal_id=signal_id,
                correlation_id=correlation_id
            )
        
        # Verify error was logged
        assert "AI provider failed: openai" in caplog.text


class TestCorrelationIDLogging:
    """Test that correlation IDs are included in all log messages."""
    
    @pytest.mark.asyncio
    async def test_correlation_id_in_processor_error(
        self,
        error_handler,
        caplog
    ):
        """Test correlation ID is logged in processor errors."""
        correlation_id = "unique-correlation-id-123"
        
        with caplog.at_level(logging.ERROR):
            await error_handler.handle_processor_error(
                error=ValueError("Test"),
                processor_name="TestProcessor",
                block_height=800000,
                correlation_id=correlation_id
            )
        
        # Verify correlation ID appears in logs
        assert correlation_id in caplog.text
    
    @pytest.mark.asyncio
    async def test_correlation_id_in_retry_logs(
        self,
        error_handler,
        caplog
    ):
        """Test correlation ID is logged in retry attempts."""
        correlation_id = "unique-correlation-id-456"
        
        async def failing_operation():
            raise ValueError("Test error")
        
        with caplog.at_level(logging.WARNING):
            try:
                await error_handler.retry_with_backoff(
                    operation=failing_operation,
                    operation_name="test_op",
                    correlation_id=correlation_id
                )
            except ValueError:
                pass
        
        # Verify correlation ID appears in retry logs
        assert correlation_id in caplog.text
    
    def test_correlation_id_in_context_logging(
        self,
        error_handler,
        caplog
    ):
        """Test correlation ID is logged in context logging."""
        correlation_id = "unique-correlation-id-789"
        
        with caplog.at_level(logging.INFO):
            error_handler.log_with_context(
                level="info",
                message="Test message",
                correlation_id=correlation_id
            )
        
        # Verify correlation ID appears in logs
        assert correlation_id in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
