"""
Pipeline Orchestrator Module

Orchestrates the complete signal generation pipeline from block detection
to signal persistence. Coordinates all signal processors, handles timing
metrics, and ensures graceful error handling.

Requirements: 5.1, 5.3, 5.4, 6.1
"""

import uuid
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import BlockData, Signal
from .processors.base_processor import SignalProcessor, ProcessingContext
from .signal_persistence import SignalPersistenceModule, PersistenceResult

logger = logging.getLogger(__name__)


class PipelineResult:
    """Result of a complete pipeline execution."""
    
    def __init__(
        self,
        success: bool,
        correlation_id: str,
        block_height: int,
        signals: Optional[List[Signal]] = None,
        error: Optional[str] = None,
        timing_metrics: Optional[Dict[str, float]] = None
    ):
        self.success = success
        self.correlation_id = correlation_id
        self.block_height = block_height
        self.signals = signals or []
        self.error = error
        self.timing_metrics = timing_metrics or {}
    
    def __repr__(self):
        return (
            f"PipelineResult(success={self.success}, "
            f"block_height={self.block_height}, "
            f"signal_count={len(self.signals)}, "
            f"correlation_id={self.correlation_id})"
        )


class PipelineOrchestrator:
    """
    Orchestrates the complete signal generation pipeline.
    
    Responsibilities:
    - Trigger signal generation within 5 seconds of block detection
    - Run all enabled processors in parallel
    - Persist signals to BigQuery
    - Log timing metrics for each stage with correlation IDs
    - Handle failures without blocking subsequent blocks
    - Emit success metrics to Cloud Monitoring
    
    Requirements: 5.1, 5.3, 5.4, 6.1
    """
    
    def __init__(
        self,
        signal_processors: List[SignalProcessor],
        signal_persistence: SignalPersistenceModule,
        monitoring_module: Optional[Any] = None
    ):
        """
        Initialize Pipeline Orchestrator.
        
        Args:
            signal_processors: List of signal processor instances
            signal_persistence: Signal persistence module for BigQuery writes
            monitoring_module: Optional monitoring module for metrics emission
        """
        self.processors = signal_processors
        self.persistence = signal_persistence
        self.monitoring = monitoring_module
        
        # Count enabled processors
        enabled_count = sum(1 for p in self.processors if p.enabled)
        
        logger.info(
            f"PipelineOrchestrator initialized with {len(self.processors)} processors "
            f"({enabled_count} enabled)"
        )
    
    async def process_new_block(
        self,
        block: BlockData,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Execute complete pipeline for new block.
        
        This method orchestrates the entire signal generation workflow:
        1. Generate unique correlation ID for tracing
        2. Run all enabled signal processors in parallel
        3. Persist generated signals to BigQuery
        4. Log timing metrics for each stage
        5. Emit success metrics to Cloud Monitoring
        
        If any stage fails, the error is logged with context but processing
        continues for subsequent blocks without blocking.
        
        Args:
            block: Block data to process
            historical_data: Optional historical context for processors
            
        Returns:
            PipelineResult with timing metrics and success/failure status
            
        Requirements: 5.1, 5.3
        """
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(
            f"Starting pipeline for block {block.height}",
            extra={
                "correlation_id": correlation_id,
                "block_height": block.height,
                "block_hash": block.block_hash,
                "timestamp": block.timestamp.isoformat()
            }
        )
        
        try:
            # Stage 1: Signal Generation (run processors in parallel)
            signal_gen_start = time.time()
            signals = await self._generate_signals(block, historical_data, correlation_id)
            signal_gen_duration = (time.time() - signal_gen_start) * 1000  # Convert to ms
            
            logger.info(
                f"Signal generation completed for block {block.height}",
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height,
                    "signal_count": len(signals),
                    "duration_ms": signal_gen_duration
                }
            )
            
            # Stage 2: Signal Persistence
            persist_start = time.time()
            persistence_result = await self.persistence.persist_signals(
                signals,
                correlation_id
            )
            persist_duration = (time.time() - persist_start) * 1000  # Convert to ms
            
            if not persistence_result.success:
                logger.error(
                    f"Signal persistence failed for block {block.height}",
                    extra={
                        "correlation_id": correlation_id,
                        "block_height": block.height,
                        "error": persistence_result.error
                    }
                )
                # Continue processing - don't block on persistence failures
            
            # Calculate total duration
            total_duration = (time.time() - start_time) * 1000  # Convert to ms
            
            # Collect timing metrics
            timing_metrics = {
                "signal_generation_ms": signal_gen_duration,
                "signal_persistence_ms": persist_duration,
                "total_duration_ms": total_duration
            }
            
            # Emit metrics to Cloud Monitoring if available
            if self.monitoring:
                try:
                    await self.monitoring.emit_pipeline_metrics(
                        correlation_id=correlation_id,
                        block_height=block.height,
                        signal_count=len(signals),
                        signal_generation_ms=signal_gen_duration,
                        signal_persistence_ms=persist_duration,
                        total_duration_ms=total_duration
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to emit pipeline metrics: {e}",
                        extra={"correlation_id": correlation_id}
                    )
            
            # Log pipeline completion
            logger.info(
                f"Pipeline completed for block {block.height}",
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height,
                    "signal_count": len(signals),
                    "total_duration_ms": total_duration,
                    "signal_generation_ms": signal_gen_duration,
                    "signal_persistence_ms": persist_duration
                }
            )
            
            return PipelineResult(
                success=True,
                correlation_id=correlation_id,
                block_height=block.height,
                signals=signals,
                timing_metrics=timing_metrics
            )
            
        except Exception as e:
            # Log pipeline failure with full context
            total_duration = (time.time() - start_time) * 1000
            error_msg = f"Pipeline failed for block {block.height}: {str(e)}"
            
            logger.error(
                error_msg,
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": total_duration
                },
                exc_info=True
            )
            
            # Emit error metric if monitoring available
            if self.monitoring:
                try:
                    await self.monitoring.emit_error_metric(
                        error_type="pipeline_failure",
                        service_name="utxoiq-ingestion",
                        correlation_id=correlation_id
                    )
                except Exception as metric_error:
                    logger.warning(
                        f"Failed to emit error metric: {metric_error}",
                        extra={"correlation_id": correlation_id}
                    )
            
            return PipelineResult(
                success=False,
                correlation_id=correlation_id,
                block_height=block.height,
                error=error_msg,
                timing_metrics={"total_duration_ms": total_duration}
            )
    
    async def _generate_signals(
        self,
        block: BlockData,
        historical_data: Optional[Dict[str, Any]],
        correlation_id: str
    ) -> List[Signal]:
        """
        Run all enabled signal processors in parallel.
        
        This method executes all enabled processors concurrently using asyncio,
        allowing for faster signal generation. If a processor fails, the error
        is logged but other processors continue executing.
        
        Args:
            block: Block data to process
            historical_data: Optional historical context
            correlation_id: Correlation ID for tracing
            
        Returns:
            List of all signals generated by enabled processors
            
        Requirements: 5.1, 6.1
        """
        signals = []
        
        # Create processing context
        context = ProcessingContext(
            block=block,
            historical_data=historical_data,
            correlation_id=correlation_id
        )
        
        # Create tasks for all enabled processors
        tasks = []
        processor_names = []
        
        for processor in self.processors:
            if not processor.enabled:
                logger.debug(
                    f"Skipping disabled processor: {processor.__class__.__name__}",
                    extra={"correlation_id": correlation_id}
                )
                continue
            
            tasks.append(self._run_processor_safe(processor, block, context))
            processor_names.append(processor.__class__.__name__)
        
        if not tasks:
            logger.warning(
                "No enabled processors found",
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height
                }
            )
            return signals
        
        logger.debug(
            f"Running {len(tasks)} processors in parallel: {', '.join(processor_names)}",
            extra={
                "correlation_id": correlation_id,
                "block_height": block.height
            }
        )
        
        # Run all processors in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect signals from successful processors
        for i, result in enumerate(results):
            processor_name = processor_names[i]
            
            if isinstance(result, Exception):
                # Processor raised an exception (already logged in _run_processor_safe)
                logger.error(
                    f"Processor {processor_name} failed with exception",
                    extra={
                        "correlation_id": correlation_id,
                        "block_height": block.height,
                        "processor": processor_name,
                        "error": str(result)
                    }
                )
                continue
            
            if isinstance(result, list):
                # Processor returned signals
                processor_signals = result
                signals.extend(processor_signals)
                
                logger.debug(
                    f"Processor {processor_name} generated {len(processor_signals)} signals",
                    extra={
                        "correlation_id": correlation_id,
                        "block_height": block.height,
                        "processor": processor_name,
                        "signal_count": len(processor_signals)
                    }
                )
        
        logger.info(
            f"Generated {len(signals)} total signals from {len(tasks)} processors",
            extra={
                "correlation_id": correlation_id,
                "block_height": block.height,
                "signal_count": len(signals),
                "processor_count": len(tasks)
            }
        )
        
        return signals
    
    async def _run_processor_safe(
        self,
        processor: SignalProcessor,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Run a single processor with error handling.
        
        This wrapper method ensures that processor failures are caught and logged
        without blocking other processors. Each processor runs independently.
        
        Args:
            processor: Signal processor to run
            block: Block data to process
            context: Processing context
            
        Returns:
            List of signals from processor, or empty list if processor fails
            
        Requirements: 6.1
        """
        processor_name = processor.__class__.__name__
        correlation_id = context.correlation_id
        
        try:
            start_time = time.time()
            
            # Run processor
            signals = await processor.process_block(block, context)
            
            duration = (time.time() - start_time) * 1000  # Convert to ms
            
            logger.debug(
                f"Processor {processor_name} completed",
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height,
                    "processor": processor_name,
                    "signal_count": len(signals) if signals else 0,
                    "duration_ms": duration
                }
            )
            
            return signals if signals else []
            
        except Exception as e:
            # Log processor failure with context
            error_type = type(e).__name__
            
            logger.error(
                f"Signal processor failed: {processor_name}",
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height,
                    "processor": processor_name,
                    "error": str(e),
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
                except Exception as metric_error:
                    logger.warning(
                        f"Failed to emit processor error metric: {metric_error}",
                        extra={"correlation_id": correlation_id}
                    )
            
            # Return empty list - don't block other processors
            return []
