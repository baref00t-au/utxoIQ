"""
Error Handler Module

Handles errors gracefully throughout the pipeline with proper logging,
retry logic, and alerting for critical failures.

Requirements: 6.1, 6.2, 6.4, 6.5
"""

import asyncio
import logging
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

from .monitoring import MonitoringModule

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Module for handling errors throughout the signal pipeline.
    
    Responsibilities:
    - Log errors with context (block_height, signal_type, correlation_id)
    - Implement exponential backoff retry (max 3 attempts)
    - Emit alerts for signals unprocessed >1 hour
    - Include correlation IDs in all log messages
    
    Requirements: 6.1, 6.2, 6.4, 6.5
    """
    
    def __init__(
        self,
        monitoring: Optional[MonitoringModule] = None,
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """
        Initialize Error Handler.
        
        Args:
            monitoring: Optional monitoring module for alerting
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        """
        self.monitoring = monitoring
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        logger.info(
            f"ErrorHandler initialized with max_retries={max_retries}, "
            f"base_delay={base_delay}s"
        )
    
    async def handle_processor_error(
        self,
        error: Exception,
        processor_name: str,
        block_height: int,
        correlation_id: str
    ) -> None:
        """
        Log processor error and continue processing.
        
        This method logs processor failures with full context but does not
        block other processors from executing. Each processor runs independently.
        
        Args:
            error: Exception that occurred
            processor_name: Name of the processor that failed
            block_height: Block height being processed
            correlation_id: Correlation ID for tracing
            
        Requirements: 6.1, 6.5
        """
        error_type = type(error).__name__
        
        logger.error(
            f"Signal processor failed: {processor_name}",
            extra={
                "correlation_id": correlation_id,
                "block_height": block_height,
                "processor": processor_name,
                "error": str(error),
                "error_type": error_type
            },
            exc_info=True
        )
        
        # Emit error metric if monitoring available
        if self.monitoring:
            try:
                await self.monitoring.emit_error_metric(
                    error_type="processor_failure",
                    service_name="utxoiq-ingestion",
                    processor=processor_name,
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.warning(
                    f"Failed to emit error metric: {e}",
                    extra={"correlation_id": correlation_id}
                )
    
    async def retry_with_backoff(
        self,
        operation: Callable,
        operation_name: str,
        correlation_id: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with exponential backoff retry.
        
        Implements exponential backoff with delays of 1s, 2s, 4s for up to
        3 retry attempts. If all attempts fail, the final exception is raised.
        
        Args:
            operation: Async function to execute
            operation_name: Name of operation for logging
            correlation_id: Correlation ID for tracing
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of successful operation
            
        Raises:
            Exception: If all retry attempts fail
            
        Requirements: 6.2, 6.5
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Execute operation
                result = await operation(*args, **kwargs)
                
                # Success - log if this was a retry
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded after {attempt + 1} attempts: {operation_name}",
                        extra={
                            "correlation_id": correlation_id,
                            "operation": operation_name,
                            "attempt": attempt + 1
                        }
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                
                # Check if this is the last attempt
                if attempt == self.max_retries - 1:
                    # Final attempt failed - log and raise
                    logger.error(
                        f"Operation failed after {self.max_retries} attempts: {operation_name}",
                        extra={
                            "correlation_id": correlation_id,
                            "operation": operation_name,
                            "error": str(e),
                            "error_type": error_type,
                            "total_attempts": self.max_retries
                        },
                        exc_info=True
                    )
                    raise
                
                # Calculate exponential backoff delay: 1s, 2s, 4s
                delay = self.base_delay * (2 ** attempt)
                
                # Log retry attempt with correlation ID
                logger.warning(
                    f"Operation failed, retrying in {delay}s: {operation_name}",
                    extra={
                        "correlation_id": correlation_id,
                        "operation": operation_name,
                        "error": str(e),
                        "error_type": error_type,
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "retry_delay_seconds": delay
                    }
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # Should never reach here, but handle it just in case
        if last_error:
            raise last_error
        else:
            raise RuntimeError(f"Operation failed unexpectedly: {operation_name}")
    
    async def check_stale_signals(
        self,
        signal_age_threshold: timedelta = timedelta(hours=1)
    ) -> None:
        """
        Check for stale unprocessed signals and emit alerts.
        
        This method should be called periodically to detect signals that have
        remained unprocessed for too long, indicating a problem with the
        insight generation pipeline.
        
        Args:
            signal_age_threshold: Maximum age for unprocessed signals (default: 1 hour)
            
        Requirements: 6.4, 6.5
        """
        # This is a placeholder for the actual implementation
        # In production, this would query BigQuery for stale signals
        # and emit alerts via Cloud Monitoring
        
        logger.debug(
            "Checking for stale signals",
            extra={
                "threshold_hours": signal_age_threshold.total_seconds() / 3600
            }
        )
        
        # TODO: Implement actual BigQuery query to find stale signals
        # For now, just log that the check was performed
        
        # Example of what the implementation would look like:
        # stale_signals = await self._query_stale_signals(signal_age_threshold)
        # if stale_signals:
        #     logger.warning(
        #         f"Found {len(stale_signals)} stale signals",
        #         extra={"stale_signal_count": len(stale_signals)}
        #     )
        #     
        #     if self.monitoring:
        #         await self.monitoring.emit_error_metric(
        #             error_type="stale_signals",
        #             service_name="insight-generator"
        #         )
    
    def log_with_context(
        self,
        level: str,
        message: str,
        correlation_id: str,
        **extra_context
    ) -> None:
        """
        Log message with correlation ID and additional context.
        
        This helper method ensures all log messages include correlation IDs
        for request tracing across services.
        
        Args:
            level: Log level (info, warning, error, debug)
            message: Log message
            correlation_id: Correlation ID for tracing
            **extra_context: Additional context fields
            
        Requirements: 6.5
        """
        context = {
            "correlation_id": correlation_id,
            **extra_context
        }
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message, extra=context)
    
    async def handle_bigquery_error(
        self,
        error: Exception,
        operation: str,
        correlation_id: str,
        **context
    ) -> None:
        """
        Handle BigQuery-specific errors with appropriate logging and metrics.
        
        Args:
            error: Exception that occurred
            operation: BigQuery operation that failed
            correlation_id: Correlation ID for tracing
            **context: Additional context for logging
            
        Requirements: 6.1, 6.5
        """
        error_type = type(error).__name__
        
        logger.error(
            f"BigQuery operation failed: {operation}",
            extra={
                "correlation_id": correlation_id,
                "operation": operation,
                "error": str(error),
                "error_type": error_type,
                **context
            },
            exc_info=True
        )
        
        # Emit error metric if monitoring available
        if self.monitoring:
            try:
                await self.monitoring.emit_error_metric(
                    error_type="bigquery_failure",
                    service_name="utxoiq-ingestion",
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.warning(
                    f"Failed to emit BigQuery error metric: {e}",
                    extra={"correlation_id": correlation_id}
                )
    
    async def handle_ai_provider_error(
        self,
        error: Exception,
        provider: str,
        signal_id: str,
        correlation_id: str
    ) -> None:
        """
        Handle AI provider errors with appropriate logging and metrics.
        
        Args:
            error: Exception that occurred
            provider: AI provider name
            signal_id: Signal ID being processed
            correlation_id: Correlation ID for tracing
            
        Requirements: 6.1, 6.5
        """
        error_type = type(error).__name__
        
        logger.error(
            f"AI provider failed: {provider}",
            extra={
                "correlation_id": correlation_id,
                "provider": provider,
                "signal_id": signal_id,
                "error": str(error),
                "error_type": error_type
            },
            exc_info=True
        )
        
        # Emit error metric if monitoring available
        if self.monitoring:
            try:
                await self.monitoring.emit_error_metric(
                    error_type="ai_provider_failure",
                    service_name="insight-generator",
                    correlation_id=correlation_id
                )
            except Exception as e:
                logger.warning(
                    f"Failed to emit AI provider error metric: {e}",
                    extra={"correlation_id": correlation_id}
                )
