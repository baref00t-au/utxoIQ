"""Insights service for data retrieval."""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from google.cloud import bigquery
from ..models import Insight, User, SignalType, Citation, CitationType, ExplainabilitySummary
from ..config import settings

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for managing insights data."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(project=settings.gcp_project_id)
        self.dataset_intel = settings.bigquery_dataset_intel
    
    def _row_to_insight(self, row: dict) -> Insight:
        """Convert BigQuery row to Insight model."""
        # Parse evidence/citations
        evidence = []
        if row.get('evidence_blocks'):
            for block_id in row['evidence_blocks']:
                evidence.append(Citation(
                    type=CitationType.BLOCK,
                    id=str(block_id),
                    description=f"Block {block_id}",
                    url=f"https://blockstream.info/block/{block_id}"
                ))
        
        if row.get('evidence_txids'):
            for txid in row['evidence_txids'][:3]:  # Limit to 3 transactions
                evidence.append(Citation(
                    type=CitationType.TRANSACTION,
                    id=txid,
                    description=f"Transaction {txid[:8]}...",
                    url=f"https://blockstream.info/tx/{txid}"
                ))
        
        # Parse explainability
        explainability = None
        if row.get('confidence_factors'):
            explainability = ExplainabilitySummary(
                confidence_factors=row['confidence_factors'],
                explanation=row.get('confidence_explanation', ''),
                supporting_evidence=row.get('supporting_evidence', [])
            )
        
        return Insight(
            id=row['insight_id'],
            signal_type=SignalType(row['signal_type']),
            headline=row['headline'],
            summary=row['summary'],
            confidence=float(row['confidence']),
            timestamp=row['created_at'],
            block_height=int(row['block_height']),
            evidence=evidence,
            chart_url=row.get('chart_url'),
            tags=row.get('tags', []),
            explainability=explainability,
            accuracy_rating=row.get('accuracy_rating'),
            is_predictive=row.get('is_predictive', False)
        )
    
    async def get_latest_insights(
        self,
        limit: int = 20,
        page: int = 1,
        signal_type: Optional[SignalType] = None,
        min_confidence: Optional[float] = None,
        user: Optional[User] = None
    ) -> Tuple[List[Insight], int]:
        """
        Get latest insights with filtering and pagination.
        
        Args:
            limit: Number of insights to return
            page: Page number
            signal_type: Optional signal type filter
            min_confidence: Optional minimum confidence filter
            user: Optional authenticated user
            
        Returns:
            Tuple of (insights list, total count)
        """
        logger.info(f"Fetching insights: limit={limit}, page={page}, type={signal_type}")
        
        # Build query with filters
        where_clauses = []
        params = []
        
        if signal_type:
            where_clauses.append("signal_type = ?")
            params.append(signal_type.value)
        
        if min_confidence:
            where_clauses.append("confidence >= ?")
            params.append(min_confidence)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Count query
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{self.dataset_intel}.insights`
            {where_sql}
        """
        
        # Data query with pagination
        offset = (page - 1) * limit
        data_query = f"""
            SELECT 
                insight_id,
                signal_type,
                headline,
                summary,
                confidence,
                created_at,
                block_height,
                evidence_blocks,
                evidence_txids,
                chart_url,
                tags,
                confidence_factors,
                confidence_explanation,
                supporting_evidence,
                accuracy_rating,
                is_predictive
            FROM `{self.dataset_intel}.insights`
            {where_sql}
            ORDER BY created_at DESC
            LIMIT {limit}
            OFFSET {offset}
        """
        
        try:
            # Get total count
            count_job = self.client.query(count_query, job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(None, "STRING" if isinstance(p, str) else "FLOAT64", p)
                    for p in params
                ]
            ))
            count_result = list(count_job.result())
            total = count_result[0]['total'] if count_result else 0
            
            # Get insights
            data_job = self.client.query(data_query, job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(None, "STRING" if isinstance(p, str) else "FLOAT64", p)
                    for p in params
                ]
            ))
            rows = list(data_job.result())
            
            insights = [self._row_to_insight(dict(row)) for row in rows]
            
            return insights, total
            
        except Exception as e:
            logger.error(f"Error querying BigQuery: {e}")
            # Return empty results on error
            return [], 0
    
    async def get_public_insights(self) -> Tuple[List[Insight], int]:
        """
        Get public insights for Guest Mode (20 most recent).
        
        Returns:
            Tuple of (insights list, total count)
        """
        logger.info("Fetching public insights")
        
        query = f"""
            SELECT 
                insight_id,
                signal_type,
                headline,
                summary,
                confidence,
                created_at,
                block_height,
                evidence_blocks,
                evidence_txids,
                chart_url,
                tags,
                confidence_factors,
                confidence_explanation,
                supporting_evidence,
                accuracy_rating,
                is_predictive
            FROM `{self.dataset_intel}.insights`
            WHERE confidence >= 0.7
            ORDER BY created_at DESC
            LIMIT 20
        """
        
        try:
            job = self.client.query(query)
            rows = list(job.result())
            
            insights = [self._row_to_insight(dict(row)) for row in rows]
            
            return insights, len(insights)
            
        except Exception as e:
            logger.error(f"Error querying BigQuery for public insights: {e}")
            return [], 0
    
    async def get_insight_by_id(
        self,
        insight_id: str,
        user: Optional[User] = None
    ) -> Optional[Insight]:
        """
        Get a specific insight by ID.
        
        Args:
            insight_id: The insight ID
            user: Optional authenticated user
            
        Returns:
            Insight object or None if not found
        """
        logger.info(f"Fetching insight: {insight_id}")
        
        query = f"""
            SELECT 
                insight_id,
                signal_type,
                headline,
                summary,
                confidence,
                created_at,
                block_height,
                evidence_blocks,
                evidence_txids,
                chart_url,
                tags,
                confidence_factors,
                confidence_explanation,
                supporting_evidence,
                accuracy_rating,
                is_predictive
            FROM `{self.dataset_intel}.insights`
            WHERE insight_id = @insight_id
            LIMIT 1
        """
        
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("insight_id", "STRING", insight_id)
                ]
            )
            
            job = self.client.query(query, job_config=job_config)
            rows = list(job.result())
            
            if rows:
                return self._row_to_insight(dict(rows[0]))
            
            return None
            
        except Exception as e:
            logger.error(f"Error querying BigQuery for insight {insight_id}: {e}")
            return None
    
    async def get_accuracy_leaderboard(self) -> List[dict]:
        """
        Get accuracy leaderboard by model version.
        
        Returns:
            List of leaderboard entries
        """
        logger.info("Fetching accuracy leaderboard")
        
        query = f"""
            SELECT 
                model_version,
                AVG(accuracy_rating) as avg_accuracy,
                COUNT(*) as total_insights,
                COUNT(CASE WHEN accuracy_rating >= 0.8 THEN 1 END) as high_accuracy_count
            FROM `{self.dataset_intel}.insights`
            WHERE accuracy_rating IS NOT NULL
            GROUP BY model_version
            ORDER BY avg_accuracy DESC
            LIMIT 10
        """
        
        try:
            job = self.client.query(query)
            rows = list(job.result())
            
            leaderboard = [
                {
                    "model_version": row['model_version'],
                    "avg_accuracy": float(row['avg_accuracy']),
                    "total_insights": int(row['total_insights']),
                    "high_accuracy_count": int(row['high_accuracy_count'])
                }
                for row in rows
            ]
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error querying BigQuery for leaderboard: {e}")
            return []
