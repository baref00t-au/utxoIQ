"""
Historical Backfill Module

Handles backfilling of historical signals for past blocks. Queries BigQuery for
historical blocks, processes them chronologically with proper context, and writes
signals with original timestamps. Implements rate limiting to avoid overwhelming
external services.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from google.cloud import bigquery

from .models import BlockData
from .processors.base_processor import SignalProcessor, ProcessingContext
from .signal_persistence import SignalPersistenceModule
from .config import settings

# Import Signal from shared types
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from shared.types import Signal

logger = logging.getLogger(__name__)


@dataclass
class BackfillResult:
    """Result of a historical backfill operation."""
    blocks_processed: int
    signals_generated: int
    start_date: date
    end_date: date
    duration_seconds: float
    errors: List[str]
    
    def __repr__(self):
        return (
            f"BackfillResult(blocks={self.blocks_processed}, "
            f"signals={self.signals_generated}, "
            f"date_range={self.start_date} to {self.end_date}, "
            f"duration={self.duration_seconds:.2f}s, "
            f"errors={len(self.errors)})"
        )


class HistoricalBackfillModule:
    """
    Module for backfilling historical signals from past blocks.
    
    Responsibilities:
    - Query btc.blocks for historical blocks in date range
    - Process blocks in chronological order
    - Write signals with original block timestamps
    - Mark signals as unprocessed for insight generation
    - Implement rate limiting (max 100 blocks/minute)
    - Support selective backfill by signal type or date range
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
    """
    
    def __init__(
        self,
        bigquery_client: bigquery.Client,
        signal_processors: List[SignalProcessor],
        signal_persistence: SignalPersistenceModule,
        rate_limit_blocks_per_minute: int = 100
    ):
        """
        Initialize Historical Backfill Module.
        
        Args:
            bigquery_client: BigQuery client for querying historical blocks
            signal_processors: List of signal processor instances
            signal_persistence: Signal persistence module for BigQuery writes
            rate_limit_blocks_per_minute: Maximum blocks to process per minute (default: 100)
        """
        self.client = bigquery_client
        self.processors = signal_processors
        self.persistence = signal_persistence
        self.rate_limit = rate_limit_blocks_per_minute
        
        # Calculate delay between blocks to achieve rate limit
        self.block_delay_seconds = 60.0 / rate_limit_blocks_per_minute
        
        logger.info(
            f"HistoricalBackfillModule initialized with rate limit: "
            f"{rate_limit_blocks_per_minute} blocks/min "
            f"(delay: {self.block_delay_seconds:.2f}s per block)"
        )
    
    async def backfill_date_range(
        self,
        start_date: date,
        end_date: date,
        signal_types: Optional[List[str]] = None
    ) -> BackfillResult:
        """
        Backfill signals for historical blocks in date range.
        
        This method queries BigQuery for all blocks within the specified date range,
        processes them in chronological order, and generates signals using the
        configured signal processors. Signals are written with their original block
        timestamps and marked as unprocessed for insight generation.
        
        Rate limiting is applied to avoid overwhelming Bitcoin Core RPC, BigQuery,
        and AI provider APIs. The default rate limit is 100 blocks per minute.
        
        Args:
            start_date: Start date for backfill (inclusive)
            end_date: End date for backfill (inclusive)
            signal_types: Optional list of signal types to generate (e.g., ["mempool", "exchange"])
                         If None, all enabled processors will run
            
        Returns:
            BackfillResult with statistics about the backfill operation
            
        Requirements: 11.1, 11.4, 11.6, 11.7
        """
        import time
        start_time = time.time()
        
        logger.info(
            f"Starting historical backfill from {start_date} to {end_date}",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "signal_types": signal_types,
                "rate_limit": self.rate_limit
            }
        )
        
        # Query historical blocks
        blocks = await self._query_historical_blocks(start_date, end_date)
        
        if not blocks:
            logger.warning(
                f"No blocks found in date range {start_date} to {end_date}"
            )
            return BackfillResult(
                blocks_processed=0,
                signals_generated=0,
                start_date=start_date,
                end_date=end_date,
                duration_seconds=time.time() - start_time,
                errors=[]
            )
        
        logger.info(
            f"Found {len(blocks)} blocks to backfill",
            extra={
                "block_count": len(blocks),
                "first_block": blocks[0].height,
                "last_block": blocks[-1].height
            }
        )
        
        # Process blocks with rate limiting
        total_signals = 0
        errors = []
        
        for i, block in enumerate(blocks):
            try:
                # Process historical block
                signals = await self._process_historical_block(
                    block,
                    signal_types
                )
                total_signals += len(signals)
                
                # Log progress every 100 blocks
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    blocks_per_sec = (i + 1) / elapsed
                    remaining_blocks = len(blocks) - (i + 1)
                    eta_seconds = remaining_blocks / blocks_per_sec if blocks_per_sec > 0 else 0
                    
                    logger.info(
                        f"Backfill progress: {i + 1}/{len(blocks)} blocks "
                        f"({total_signals} signals), "
                        f"ETA: {eta_seconds / 60:.1f} minutes",
                        extra={
                            "blocks_processed": i + 1,
                            "total_blocks": len(blocks),
                            "signals_generated": total_signals,
                            "blocks_per_second": blocks_per_sec,
                            "eta_seconds": eta_seconds
                        }
                    )
                
                # Rate limiting: sleep between blocks
                await asyncio.sleep(self.block_delay_seconds)
                
            except Exception as e:
                error_msg = f"Failed to process block {block.height}: {str(e)}"
                logger.error(
                    error_msg,
                    extra={
                        "block_height": block.height,
                        "block_hash": block.block_hash,
                        "error": str(e)
                    },
                    exc_info=True
                )
                errors.append(error_msg)
                # Continue processing other blocks
        
        duration = time.time() - start_time
        
        result = BackfillResult(
            blocks_processed=len(blocks),
            signals_generated=total_signals,
            start_date=start_date,
            end_date=end_date,
            duration_seconds=duration,
            errors=errors
        )
        
        logger.info(
            f"Historical backfill completed: {result}",
            extra={
                "blocks_processed": result.blocks_processed,
                "signals_generated": result.signals_generated,
                "duration_seconds": result.duration_seconds,
                "error_count": len(result.errors),
                "blocks_per_minute": (result.blocks_processed / duration * 60) if duration > 0 else 0
            }
        )
        
        return result
    
    async def _query_historical_blocks(
        self,
        start_date: date,
        end_date: date
    ) -> List[BlockData]:
        """
        Query BigQuery for historical blocks within date range.
        
        Blocks are returned in chronological order (ascending by block height)
        to maintain temporal consistency for time-series analysis.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of BlockData objects in chronological order
            
        Requirements: 11.1, 11.4
        """
        try:
            # Convert dates to datetime for BigQuery timestamp comparison
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            query = f"""
            SELECT 
                hash as block_hash,
                height,
                timestamp,
                size,
                tx_count,
                fees_total
            FROM `{settings.gcp_project_id}.{settings.bigquery_dataset_btc}.blocks`
            WHERE timestamp >= @start_datetime
              AND timestamp <= @end_datetime
            ORDER BY height ASC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_datetime", "TIMESTAMP", start_datetime),
                    bigquery.ScalarQueryParameter("end_datetime", "TIMESTAMP", end_datetime),
                ]
            )
            
            logger.debug(
                f"Querying historical blocks from {start_date} to {end_date}",
                extra={
                    "start_datetime": start_datetime.isoformat(),
                    "end_datetime": end_datetime.isoformat()
                }
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            blocks = []
            for row in results:
                block = BlockData(
                    block_hash=row['block_hash'],
                    height=row['height'],
                    timestamp=row['timestamp'],
                    size=row['size'],
                    tx_count=row['tx_count'],
                    fees_total=row['fees_total']
                )
                blocks.append(block)
            
            logger.info(
                f"Retrieved {len(blocks)} historical blocks",
                extra={
                    "block_count": len(blocks),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "first_block": blocks[0].height if blocks else None,
                    "last_block": blocks[-1].height if blocks else None
                }
            )
            
            return blocks
            
        except Exception as e:
            logger.error(
                f"Failed to query historical blocks: {e}",
                extra={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def _process_historical_block(
        self,
        block: BlockData,
        signal_types: Optional[List[str]]
    ) -> List[Signal]:
        """
        Process historical block with temporal context.
        
        This method processes a historical block by:
        1. Getting surrounding blocks for historical context
        2. Running enabled signal processors (filtered by signal_types if provided)
        3. Writing signals with original block timestamp
        4. Marking signals as unprocessed for insight generation
        
        Args:
            block: Historical block to process
            signal_types: Optional list of signal types to generate
            
        Returns:
            List of signals generated from this block
            
        Requirements: 11.2, 11.3, 11.5
        """
        correlation_id = f"backfill-{block.height}"
        
        logger.debug(
            f"Processing historical block {block.height}",
            extra={
                "correlation_id": correlation_id,
                "block_height": block.height,
                "block_timestamp": block.timestamp.isoformat(),
                "signal_types": signal_types
            }
        )
        
        try:
            # Get surrounding blocks for context
            historical_context = await self._get_historical_context(block)
            
            # Create processing context
            context = ProcessingContext(
                block=block,
                historical_data=historical_context,
                correlation_id=correlation_id
            )
            
            # Run processors (filtered by signal_types if provided)
            signals = []
            for processor in self.processors:
                # Skip if processor is disabled
                if not processor.enabled:
                    continue
                
                # Skip if signal_types filter is provided and processor type not in list
                if signal_types and processor.signal_type not in signal_types:
                    continue
                
                try:
                    processor_signals = await processor.process_block(block, context)
                    
                    if processor_signals:
                        # Override created_at with original block timestamp
                        # Mark as unprocessed for insight generation
                        for signal in processor_signals:
                            signal.created_at = block.timestamp
                            signal.processed = False
                            signal.processed_at = None
                        
                        signals.extend(processor_signals)
                        
                        logger.debug(
                            f"Processor {processor.__class__.__name__} generated "
                            f"{len(processor_signals)} signals for block {block.height}",
                            extra={
                                "correlation_id": correlation_id,
                                "block_height": block.height,
                                "processor": processor.__class__.__name__,
                                "signal_count": len(processor_signals)
                            }
                        )
                
                except Exception as e:
                    logger.error(
                        f"Processor {processor.__class__.__name__} failed for block {block.height}",
                        extra={
                            "correlation_id": correlation_id,
                            "block_height": block.height,
                            "processor": processor.__class__.__name__,
                            "error": str(e)
                        },
                        exc_info=True
                    )
                    # Continue with other processors
            
            # Persist signals with original timestamp
            if signals:
                persistence_result = await self.persistence.persist_signals(
                    signals,
                    correlation_id
                )
                
                if not persistence_result.success:
                    logger.error(
                        f"Failed to persist signals for block {block.height}",
                        extra={
                            "correlation_id": correlation_id,
                            "block_height": block.height,
                            "signal_count": len(signals),
                            "error": persistence_result.error
                        }
                    )
                    # Raise exception to trigger retry or error handling
                    raise Exception(f"Signal persistence failed: {persistence_result.error}")
            
            return signals
            
        except Exception as e:
            logger.error(
                f"Failed to process historical block {block.height}: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "block_height": block.height,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def _get_historical_context(
        self,
        block: BlockData
    ) -> Dict[str, Any]:
        """
        Query surrounding blocks for historical context.
        
        This method retrieves blocks before and after the target block to provide
        temporal context for signal processors. This is important for processors
        that compare current values to historical trends.
        
        Args:
            block: Target block
            
        Returns:
            Dictionary with historical context data including surrounding blocks
            
        Requirements: 11.2
        """
        try:
            # Query blocks within +/- 10 blocks for context
            context_window = 10
            
            query = f"""
            SELECT 
                hash as block_hash,
                height,
                timestamp,
                size,
                tx_count,
                fees_total
            FROM `{settings.gcp_project_id}.{settings.bigquery_dataset_btc}.blocks`
            WHERE height >= @min_height
              AND height <= @max_height
            ORDER BY height ASC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("min_height", "INT64", block.height - context_window),
                    bigquery.ScalarQueryParameter("max_height", "INT64", block.height + context_window),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            surrounding_blocks = []
            for row in results:
                surrounding_block = BlockData(
                    block_hash=row['block_hash'],
                    height=row['height'],
                    timestamp=row['timestamp'],
                    size=row['size'],
                    tx_count=row['tx_count'],
                    fees_total=row['fees_total']
                )
                surrounding_blocks.append(surrounding_block)
            
            context = {
                "surrounding_blocks": surrounding_blocks,
                "context_window": context_window,
                "blocks_before": [b for b in surrounding_blocks if b.height < block.height],
                "blocks_after": [b for b in surrounding_blocks if b.height > block.height]
            }
            
            logger.debug(
                f"Retrieved historical context for block {block.height}",
                extra={
                    "block_height": block.height,
                    "surrounding_blocks": len(surrounding_blocks),
                    "blocks_before": len(context["blocks_before"]),
                    "blocks_after": len(context["blocks_after"])
                }
            )
            
            return context
            
        except Exception as e:
            logger.warning(
                f"Failed to get historical context for block {block.height}: {e}",
                extra={
                    "block_height": block.height,
                    "error": str(e)
                }
            )
            # Return empty context - allow processing to continue
            return {
                "surrounding_blocks": [],
                "context_window": 0,
                "blocks_before": [],
                "blocks_after": []
            }
