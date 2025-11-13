"""
Signal Persistence Module

Handles persistence of computed signals to BigQuery intel.signals table.
Implements batch insert logic with error handling and correlation ID logging.
Includes retry logic with exponential backoff for transient failures.
"""

import uuid
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

# Import Signal model from shared types
import sys
import os

# Add parent directory to path to access shared module
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import Signal from shared.types
from shared.types import Signal

logger = logging.getLogger(__name__)


class PersistenceResult:
    """Result of a signal persistence operation."""
    
    def __init__(
        self,
        success: bool,
        signal_count: int = 0,
        error: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        self.success = success
        self.signal_count = signal_count
        self.error = error
        self.correlation_id = correlation_id
    
    def __repr__(self):
        return (
            f"PersistenceResult(success={self.success}, "
            f"signal_count={self.signal_count}, error={self.error})"
        )


class SignalPersistenceModule:
    """
    Module for persisting blockchain signals to BigQuery.
    
    Responsibilities:
    - Generate unique signal IDs (UUID format)
    - Batch insert signals to BigQuery intel.signals table
    - Handle persistence failures gracefully
    - Log errors with correlation IDs for tracing
    
    Requirements: 1.2, 1.3, 1.4
    """
    
    def __init__(
        self,
        bigquery_client: bigquery.Client,
        project_id: str = "utxoiq-dev",
        dataset_id: str = "intel",
        table_name: str = "signals",
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """
        Initialize Signal Persistence Module.
        
        Args:
            bigquery_client: Initialized BigQuery client
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID (default: intel)
            table_name: Table name for signals (default: signals)
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        """
        self.client = bigquery_client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.table_id = f"{project_id}.{dataset_id}.{table_name}"
        self.max_retries = max_retries
        self.base_delay = base_delay
        
        logger.info(
            f"SignalPersistenceModule initialized with table: {self.table_id}, "
            f"max_retries: {max_retries}, base_delay: {base_delay}s"
        )
    
    def generate_signal_id(self) -> str:
        """
        Generate unique signal ID using UUID format.
        
        Returns:
            UUID string for signal identification
            
        Requirement: 1.2
        """
        return str(uuid.uuid4())
    
    async def persist_signals(
        self,
        signals: List[Signal],
        correlation_id: str
    ) -> PersistenceResult:
        """
        Batch insert signals to BigQuery intel.signals table with retry logic.
        
        This method performs a single batch insert operation for all signals,
        reducing API calls and improving performance. If persistence fails due
        to transient errors, it retries with exponential backoff (1s, 2s, 4s)
        up to max_retries attempts. If all retries fail, the error is logged
        with correlation ID but processing continues without blocking block ingestion.
        
        Args:
            signals: List of Signal objects to persist
            correlation_id: Correlation ID for request tracing
            
        Returns:
            PersistenceResult with success status and error details
            
        Requirements: 1.3, 1.4, 6.2
        """
        if not signals:
            logger.info(
                "No signals to persist",
                extra={"correlation_id": correlation_id}
            )
            return PersistenceResult(
                success=True,
                signal_count=0,
                correlation_id=correlation_id
            )
        
        # Convert Signal objects to BigQuery row format once
        rows_to_insert = []
        for signal in signals:
            row = self._signal_to_bigquery_row(signal)
            rows_to_insert.append(row)
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Perform batch insert
                errors = self.client.insert_rows_json(
                    self.table_id,
                    rows_to_insert
                )
                
                if errors:
                    # Log insertion errors with correlation ID
                    error_msg = f"BigQuery insertion errors: {errors}"
                    logger.error(
                        "Failed to insert signals to BigQuery",
                        extra={
                            "correlation_id": correlation_id,
                            "signal_count": len(signals),
                            "errors": errors,
                            "table_id": self.table_id,
                            "attempt": attempt + 1
                        }
                    )
                    
                    # Don't retry on schema/validation errors
                    return PersistenceResult(
                        success=False,
                        signal_count=0,
                        error=error_msg,
                        correlation_id=correlation_id
                    )
                
                # Success - log with correlation ID
                logger.info(
                    f"Successfully persisted {len(signals)} signals to BigQuery",
                    extra={
                        "correlation_id": correlation_id,
                        "signal_count": len(signals),
                        "table_id": self.table_id,
                        "signal_types": [s.signal_type for s in signals],
                        "attempt": attempt + 1
                    }
                )
                
                return PersistenceResult(
                    success=True,
                    signal_count=len(signals),
                    correlation_id=correlation_id
                )
                
            except (GoogleCloudError, Exception) as e:
                last_error = e
                error_type = type(e).__name__
                
                # Check if this is the last attempt
                if attempt == self.max_retries - 1:
                    # Final attempt failed - log and return error
                    error_msg = f"Signal persistence failed after {self.max_retries} attempts: {str(e)}"
                    logger.error(
                        error_msg,
                        extra={
                            "correlation_id": correlation_id,
                            "signal_count": len(signals),
                            "error_type": error_type,
                            "error": str(e),
                            "total_attempts": self.max_retries
                        },
                        exc_info=True
                    )
                    return PersistenceResult(
                        success=False,
                        signal_count=0,
                        error=error_msg,
                        correlation_id=correlation_id
                    )
                
                # Calculate exponential backoff delay: 1s, 2s, 4s
                delay = self.base_delay * (2 ** attempt)
                
                # Log retry attempt with correlation ID
                logger.warning(
                    f"BigQuery write failed, retrying in {delay}s",
                    extra={
                        "correlation_id": correlation_id,
                        "signal_count": len(signals),
                        "error_type": error_type,
                        "error": str(e),
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "retry_delay_seconds": delay
                    }
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # Should never reach here, but handle it just in case
        error_msg = f"Signal persistence failed unexpectedly after retry loop"
        logger.error(
            error_msg,
            extra={
                "correlation_id": correlation_id,
                "signal_count": len(signals)
            }
        )
        return PersistenceResult(
            success=False,
            signal_count=0,
            error=error_msg,
            correlation_id=correlation_id
        )
    
    def _signal_to_bigquery_row(self, signal: Signal) -> Dict[str, Any]:
        """
        Convert Signal object to BigQuery row format.
        
        Args:
            signal: Signal object to convert
            
        Returns:
            Dictionary matching BigQuery intel.signals schema
        """
        # Convert datetime to ISO format string for BigQuery
        created_at_str = signal.created_at.isoformat() if isinstance(
            signal.created_at, datetime
        ) else signal.created_at
        
        processed_at_str = None
        if signal.processed_at:
            processed_at_str = signal.processed_at.isoformat() if isinstance(
                signal.processed_at, datetime
            ) else signal.processed_at
        
        return {
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "block_height": signal.block_height,
            "confidence": signal.confidence,
            "metadata": signal.metadata,
            "created_at": created_at_str,
            "processed": signal.processed,
            "processed_at": processed_at_str
        }
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """
        Recursively serialize objects for JSON compatibility.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        return obj
