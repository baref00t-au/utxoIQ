"""
Monitoring Module

Handles emission of metrics to Cloud Monitoring for observability.
Tracks pipeline performance, signal generation, errors, and entity identification.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from google.cloud import monitoring_v3
    from google.api import metric_pb2 as ga_metric
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logging.warning("Google Cloud Monitoring not available - metrics will be logged only")

logger = logging.getLogger(__name__)


class MonitoringModule:
    """
    Module for emitting metrics to Cloud Monitoring.
    
    Responsibilities:
    - Emit timing metrics to Cloud Monitoring
    - Track signal counts by type and confidence bucket
    - Track insight counts by category
    - Track entity identification counts
    - Track error counts by type and service
    - Track AI provider latency by provider
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize Monitoring Module.
        
        Args:
            project_id: GCP project ID (defaults to PROJECT_ID env var)
            enabled: Whether monitoring is enabled (default: True)
        """
        self.project_id = project_id or os.getenv("PROJECT_ID", "utxoiq-dev")
        self.enabled = enabled and MONITORING_AVAILABLE
        self.client = None
        
        if self.enabled:
            try:
                self.client = monitoring_v3.MetricServiceClient()
                self.project_name = f"projects/{self.project_id}"
                logger.info(
                    f"MonitoringModule initialized for project: {self.project_id}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Cloud Monitoring client: {e}. "
                    "Metrics will be logged only."
                )
                self.enabled = False
        else:
            logger.info(
                "MonitoringModule initialized in logging-only mode "
                "(Cloud Monitoring not available)"
            )
    
    async def emit_pipeline_metrics(
        self,
        correlation_id: str,
        block_height: int,
        signal_count: int,
        signal_generation_ms: float,
        signal_persistence_ms: float,
        total_duration_ms: float
    ) -> None:
        """
        Emit pipeline timing metrics.
        
        Tracks the duration of each pipeline stage and total execution time.
        
        Args:
            correlation_id: Correlation ID for tracing
            block_height: Block height processed
            signal_count: Number of signals generated
            signal_generation_ms: Signal generation duration in milliseconds
            signal_persistence_ms: Signal persistence duration in milliseconds
            total_duration_ms: Total pipeline duration in milliseconds
            
        Requirements: 12.1
        """
        metrics = {
            "signal_generation_duration_ms": signal_generation_ms,
            "signal_persistence_duration_ms": signal_persistence_ms,
            "total_pipeline_duration_ms": total_duration_ms,
            "signals_generated": signal_count
        }
        
        labels = {
            "correlation_id": correlation_id,
            "block_height": str(block_height)
        }
        
        for metric_name, value in metrics.items():
            await self._write_metric(
                metric_name,
                value,
                labels=labels
            )
        
        logger.info(
            "Pipeline metrics emitted",
            extra={
                "correlation_id": correlation_id,
                "block_height": block_height,
                "signal_count": signal_count,
                "signal_generation_ms": signal_generation_ms,
                "signal_persistence_ms": signal_persistence_ms,
                "total_duration_ms": total_duration_ms
            }
        )
    
    async def emit_signal_metrics(
        self,
        signal_type: str,
        confidence: float
    ) -> None:
        """
        Emit signal count metrics by type and confidence bucket.
        
        Args:
            signal_type: Type of signal (mempool, exchange, miner, whale, treasury, predictive)
            confidence: Confidence score (0.0 to 1.0)
            
        Requirements: 12.2
        """
        confidence_bucket = self._get_confidence_bucket(confidence)
        
        await self._write_metric(
            "signals_by_type",
            1,
            labels={
                "signal_type": signal_type,
                "confidence_bucket": confidence_bucket
            }
        )
        
        logger.debug(
            "Signal metric emitted",
            extra={
                "signal_type": signal_type,
                "confidence": confidence,
                "confidence_bucket": confidence_bucket
            }
        )
    
    async def emit_insight_metrics(
        self,
        category: str,
        confidence: float,
        generation_ms: float
    ) -> None:
        """
        Emit insight generation metrics.
        
        Args:
            category: Insight category (mempool, exchange, miner, whale, treasury, predictive)
            confidence: Confidence score (0.0 to 1.0)
            generation_ms: Insight generation duration in milliseconds
            
        Requirements: 12.3
        """
        confidence_bucket = self._get_confidence_bucket(confidence)
        
        # Emit duration metric
        await self._write_metric(
            "insight_generation_duration_ms",
            generation_ms,
            labels={"category": category}
        )
        
        # Emit count metric
        await self._write_metric(
            "insights_by_category",
            1,
            labels={
                "category": category,
                "confidence_bucket": confidence_bucket
            }
        )
        
        logger.debug(
            "Insight metrics emitted",
            extra={
                "category": category,
                "confidence": confidence,
                "confidence_bucket": confidence_bucket,
                "generation_ms": generation_ms
            }
        )
    
    async def emit_entity_metrics(
        self,
        entity_name: str,
        entity_type: str
    ) -> None:
        """
        Emit entity identification count metrics.
        
        Args:
            entity_name: Name of identified entity
            entity_type: Type of entity (exchange, mining_pool, treasury)
            
        Requirements: 12.4
        """
        await self._write_metric(
            "entity_identifications",
            1,
            labels={
                "entity_name": entity_name,
                "entity_type": entity_type
            }
        )
        
        logger.debug(
            "Entity metric emitted",
            extra={
                "entity_name": entity_name,
                "entity_type": entity_type
            }
        )
    
    async def emit_error_metric(
        self,
        error_type: str,
        service_name: str,
        processor: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Emit error count metrics.
        
        Args:
            error_type: Type of error (processor_failure, pipeline_failure, etc.)
            service_name: Name of service where error occurred
            processor: Optional processor name if processor-specific error
            correlation_id: Optional correlation ID for tracing
            
        Requirements: 12.5
        """
        labels = {
            "error_type": error_type,
            "service_name": service_name
        }
        
        if processor:
            labels["processor"] = processor
        
        await self._write_metric(
            "error_count",
            1,
            labels=labels
        )
        
        logger.debug(
            "Error metric emitted",
            extra={
                "error_type": error_type,
                "service_name": service_name,
                "processor": processor,
                "correlation_id": correlation_id
            }
        )
    
    async def emit_ai_provider_metrics(
        self,
        provider: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """
        Emit AI provider performance metrics.
        
        Args:
            provider: AI provider name (vertex_ai, openai, anthropic, grok)
            latency_ms: API call latency in milliseconds
            success: Whether the API call succeeded
            
        Requirements: 12.6
        """
        await self._write_metric(
            "ai_provider_latency_ms",
            latency_ms,
            labels={
                "provider": provider,
                "success": str(success)
            }
        )
        
        logger.debug(
            "AI provider metric emitted",
            extra={
                "provider": provider,
                "latency_ms": latency_ms,
                "success": success
            }
        )
    
    async def emit_backfill_metrics(
        self,
        blocks_processed: int,
        signals_generated: int,
        estimated_completion_time: Optional[str] = None
    ) -> None:
        """
        Emit historical backfill progress metrics.
        
        Args:
            blocks_processed: Number of blocks processed in backfill
            signals_generated: Number of signals generated in backfill
            estimated_completion_time: Optional estimated completion time
            
        Requirements: 12.8
        """
        await self._write_metric(
            "backfill_blocks_processed",
            blocks_processed
        )
        
        await self._write_metric(
            "backfill_signals_generated",
            signals_generated
        )
        
        logger.info(
            "Backfill metrics emitted",
            extra={
                "blocks_processed": blocks_processed,
                "signals_generated": signals_generated,
                "estimated_completion_time": estimated_completion_time
            }
        )
    
    async def increment_counter(
        self,
        counter_name: str,
        value: int = 1,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            counter_name: Name of counter (total_blocks_processed, total_insights_generated)
            value: Value to increment by (default: 1)
            labels: Optional labels for the metric
            
        Requirements: 12.7
        """
        await self._write_metric(
            counter_name,
            value,
            labels=labels or {}
        )
        
        logger.debug(
            f"Counter {counter_name} incremented by {value}",
            extra={"counter": counter_name, "value": value, "labels": labels}
        )
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """
        Categorize confidence into buckets.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Confidence bucket: "high", "medium", or "low"
        """
        if confidence >= 0.85:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        else:
            return "low"
    
    async def _write_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Write a metric to Cloud Monitoring.
        
        If Cloud Monitoring is not available or disabled, metrics are logged only.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            labels: Optional labels for the metric
        """
        labels = labels or {}
        
        # Always log metrics
        logger.debug(
            f"Metric: {metric_name} = {value}",
            extra={"metric": metric_name, "value": value, "labels": labels}
        )
        
        # Write to Cloud Monitoring if enabled
        if not self.enabled or not self.client:
            return
        
        try:
            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/utxoiq/{metric_name}"
            
            # Add labels
            for key, val in labels.items():
                series.metric.labels[key] = str(val)
            
            # Set resource
            series.resource.type = "global"
            series.resource.labels["project_id"] = self.project_id
            
            # Create data point
            now = datetime.utcnow()
            seconds = int(now.timestamp())
            nanos = int((now.timestamp() - seconds) * 10**9)
            
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            
            point = monitoring_v3.Point(
                {
                    "interval": interval,
                    "value": {"double_value": float(value)}
                }
            )
            
            series.points = [point]
            
            # Write time series
            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
        except Exception as e:
            logger.warning(
                f"Failed to write metric {metric_name} to Cloud Monitoring: {e}",
                extra={"metric": metric_name, "value": value, "error": str(e)}
            )
