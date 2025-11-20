"""
Insight Persistence Module for insight-generator service.

This module handles writing insights to BigQuery intel.insights table
and managing persistence failures with proper error handling.

Requirements: 4.1, 4.3, 4.4, 4.5
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from .insight_generation import Insight


logger = logging.getLogger(__name__)


@dataclass
class PersistenceResult:
    """Result of insight persistence operation"""
    success: bool
    insight_id: Optional[str] = None
    error: Optional[str] = None


class InsightPersistenceModule:
    """
    Handles persistence of insights to BigQuery intel.insights table.
    
    Responsibilities:
    - Write insights to BigQuery with all required fields
    - Set chart_url to null initially (populated later by chart-renderer)
    - Return insight_id on successful persistence
    - Handle persistence failures with proper error logging
    - Mark signals as unprocessed for retry on failure
    
    Requirements: 4.1, 4.3, 4.4, 4.5
    """
    
    def __init__(
        self,
        bigquery_client: bigquery.Client,
        project_id: str = "utxoiq-dev",
        dataset_id: str = "intel"
    ):
        """
        Initialize Insight Persistence Module.
        
        Args:
            bigquery_client: BigQuery client instance
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID for intel data
        """
        self.client = bigquery_client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.insights_table = f"{project_id}.{dataset_id}.insights"
        self.signals_table = f"{project_id}.{dataset_id}.signals"
        
        logger.info(
            f"InsightPersistenceModule initialized for table: {self.insights_table}"
        )
    
    async def persist_insight(
        self,
        insight: Insight,
        correlation_id: Optional[str] = None
    ) -> PersistenceResult:
        """
        Write insight to BigQuery intel.insights table.
        
        Creates a new row in the insights table with:
        - insight_id: UUID
        - signal_id: Reference to source signal
        - category: Signal type (mempool, exchange, miner, whale, treasury, predictive)
        - headline: AI-generated headline (max 80 chars)
        - summary: AI-generated summary (2-3 sentences)
        - confidence: Inherited from signal
        - evidence: Block heights and transaction IDs
        - chart_url: Set to null initially (populated later by chart-renderer)
        - created_at: Current timestamp
        
        Args:
            insight: Insight object to persist
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            PersistenceResult with success status and insight_id or error details
            
        Requirements: 4.1, 4.3, 4.5
        """
        try:
            log_extra = {
                "insight_id": insight.insight_id,
                "signal_id": insight.signal_id,
                "category": insight.category
            }
            
            if correlation_id:
                log_extra["correlation_id"] = correlation_id
            
            logger.info(
                f"Persisting insight {insight.insight_id} for signal {insight.signal_id}",
                extra=log_extra
            )
            
            # Convert insight to dictionary for BigQuery
            insight_dict = insight.to_dict()
            
            # Ensure chart_url is null
            insight_dict["chart_url"] = None
            
            # Ensure created_at is set
            if not insight_dict.get("created_at"):
                insight_dict["created_at"] = datetime.utcnow()
            
            # Insert row into BigQuery
            errors = self.client.insert_rows_json(
                self.insights_table,
                [insight_dict]
            )
            
            if errors:
                error_msg = f"BigQuery insert errors: {errors}"
                logger.error(
                    f"Failed to persist insight {insight.insight_id}: {error_msg}",
                    extra={**log_extra, "errors": errors}
                )
                
                # Mark signal as unprocessed for retry (Requirement 4.4)
                await self._mark_signal_unprocessed(
                    insight.signal_id,
                    correlation_id
                )
                
                return PersistenceResult(
                    success=False,
                    insight_id=None,
                    error=error_msg
                )
            
            logger.info(
                f"Successfully persisted insight {insight.insight_id}",
                extra=log_extra
            )
            
            return PersistenceResult(
                success=True,
                insight_id=insight.insight_id,
                error=None
            )
            
        except NotFound:
            error_msg = f"Table {self.insights_table} not found"
            logger.error(
                error_msg,
                extra={"signal_id": insight.signal_id}
            )
            
            # Mark signal as unprocessed for retry (Requirement 4.4)
            await self._mark_signal_unprocessed(
                insight.signal_id,
                correlation_id
            )
            
            return PersistenceResult(
                success=False,
                insight_id=None,
                error=error_msg
            )
            
        except Exception as e:
            error_msg = f"Unexpected error persisting insight: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "signal_id": insight.signal_id,
                    "insight_id": insight.insight_id,
                    "error": str(e)
                }
            )
            
            # Mark signal as unprocessed for retry (Requirement 4.4)
            await self._mark_signal_unprocessed(
                insight.signal_id,
                correlation_id
            )
            
            return PersistenceResult(
                success=False,
                insight_id=None,
                error=error_msg
            )
    
    async def _mark_signal_unprocessed(
        self,
        signal_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Mark a signal as unprocessed for retry after persistence failure.
        
        This ensures that failed insights can be retried in the next polling cycle.
        
        Args:
            signal_id: Signal ID to mark as unprocessed
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            True if update successful, False otherwise
            
        Requirements: 4.4
        """
        query = f"""
        UPDATE `{self.signals_table}`
        SET 
            processed = false,
            processed_at = NULL
        WHERE signal_id = '{signal_id}'
        """
        
        try:
            log_extra = {"signal_id": signal_id}
            if correlation_id:
                log_extra["correlation_id"] = correlation_id
            
            logger.warning(
                f"Marking signal {signal_id} as unprocessed for retry",
                extra=log_extra
            )
            
            query_job = self.client.query(query)
            query_job.result()  # Wait for query to complete
            
            if query_job.num_dml_affected_rows > 0:
                logger.info(
                    f"Successfully marked signal {signal_id} as unprocessed",
                    extra=log_extra
                )
                return True
            else:
                logger.warning(
                    f"Signal {signal_id} not found when marking unprocessed",
                    extra=log_extra
                )
                return False
                
        except Exception as e:
            logger.error(
                f"Error marking signal {signal_id} as unprocessed: {e}",
                extra={
                    "signal_id": signal_id,
                    "error": str(e)
                }
            )
            return False
    
    async def persist_insights_batch(
        self,
        insights: list[Insight],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Persist multiple insights in batch for better performance.
        
        Processes insights sequentially but provides a convenient batch interface.
        Returns summary of successes and failures.
        
        Args:
            insights: List of Insight objects to persist
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            Dictionary with success count, failure count, and insight IDs
        """
        results = {
            "success_count": 0,
            "failure_count": 0,
            "insight_ids": [],
            "errors": []
        }
        
        logger.info(
            f"Persisting batch of {len(insights)} insights",
            extra={"correlation_id": correlation_id} if correlation_id else {}
        )
        
        for insight in insights:
            result = await self.persist_insight(insight, correlation_id)
            
            if result.success:
                results["success_count"] += 1
                results["insight_ids"].append(result.insight_id)
            else:
                results["failure_count"] += 1
                results["errors"].append({
                    "signal_id": insight.signal_id,
                    "error": result.error
                })
        
        logger.info(
            f"Batch persistence complete: {results['success_count']} succeeded, "
            f"{results['failure_count']} failed",
            extra={"correlation_id": correlation_id} if correlation_id else {}
        )
        
        return results
    
    async def get_insight_by_id(
        self,
        insight_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an insight by its ID.
        
        Useful for verification and testing.
        
        Args:
            insight_id: Insight ID to retrieve
            
        Returns:
            Insight dictionary or None if not found
        """
        query = f"""
        SELECT *
        FROM `{self.insights_table}`
        WHERE insight_id = '{insight_id}'
        LIMIT 1
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            if results:
                return dict(results[0])
            
            logger.warning(f"Insight {insight_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving insight {insight_id}: {e}")
            return None
    
    async def get_insights_by_signal_id(
        self,
        signal_id: str
    ) -> list[Dict[str, Any]]:
        """
        Retrieve all insights generated from a specific signal.
        
        Useful for debugging and verification.
        
        Args:
            signal_id: Signal ID to find insights for
            
        Returns:
            List of insight dictionaries
        """
        query = f"""
        SELECT *
        FROM `{self.insights_table}`
        WHERE signal_id = '{signal_id}'
        ORDER BY created_at DESC
        """
        
        try:
            query_job = self.client.query(query)
            results = list(query_job.result())
            
            insights = [dict(row) for row in results]
            
            logger.debug(
                f"Found {len(insights)} insights for signal {signal_id}"
            )
            
            return insights
            
        except Exception as e:
            logger.error(
                f"Error retrieving insights for signal {signal_id}: {e}"
            )
            return []
