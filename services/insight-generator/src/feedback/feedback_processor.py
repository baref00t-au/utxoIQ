"""
User feedback collection and processing
Stores feedback in BigQuery and calculates aggregate accuracy ratings
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class FeedbackRating(Enum):
    """User feedback rating options"""
    USEFUL = "useful"
    NOT_USEFUL = "not_useful"


@dataclass
class UserFeedback:
    """User feedback model"""
    insight_id: str
    user_id: str
    rating: FeedbackRating
    timestamp: datetime
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for BigQuery"""
        return {
            'insight_id': self.insight_id,
            'user_id': self.user_id,
            'rating': self.rating.value,
            'timestamp': self.timestamp.isoformat(),
            'comment': self.comment
        }


@dataclass
class AccuracyRating:
    """Aggregate accuracy rating for an insight"""
    insight_id: str
    total_feedback: int
    useful_count: int
    not_useful_count: int
    accuracy_score: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'insight_id': self.insight_id,
            'total_feedback': self.total_feedback,
            'useful_count': self.useful_count,
            'not_useful_count': self.not_useful_count,
            'accuracy_score': self.accuracy_score
        }


@dataclass
class ModelAccuracy:
    """Accuracy metrics for a model version"""
    model_version: str
    signal_type: str
    total_insights: int
    total_feedback: int
    accuracy_score: float
    period_start: datetime
    period_end: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'model_version': self.model_version,
            'signal_type': self.signal_type,
            'total_insights': self.total_insights,
            'total_feedback': self.total_feedback,
            'accuracy_score': self.accuracy_score,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat()
        }


class FeedbackProcessor:
    """Processes user feedback and calculates accuracy metrics"""
    
    def __init__(self, bigquery_client=None):
        """
        Initialize feedback processor
        
        Args:
            bigquery_client: BigQuery client instance (optional for testing)
        """
        self.bigquery_client = bigquery_client
        self.dataset_id = "intel"
        self.feedback_table = "user_feedback"
        self.insights_table = "insights"
    
    def store_feedback(self, feedback: UserFeedback) -> bool:
        """
        Store user feedback in BigQuery
        
        Args:
            feedback: UserFeedback instance
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bigquery_client:
            # Mock storage for testing
            return True
        
        try:
            table_id = f"{self.dataset_id}.{self.feedback_table}"
            rows_to_insert = [feedback.to_dict()]
            
            errors = self.bigquery_client.insert_rows_json(table_id, rows_to_insert)
            
            if errors:
                print(f"Errors inserting feedback: {errors}")
                return False
            
            return True
        except Exception as e:
            print(f"Error storing feedback: {e}")
            return False
    
    def calculate_accuracy_rating(self, insight_id: str) -> Optional[AccuracyRating]:
        """
        Calculate aggregate accuracy rating for an insight
        
        Args:
            insight_id: Insight ID
            
        Returns:
            AccuracyRating or None if no feedback exists
        """
        if not self.bigquery_client:
            # Mock calculation for testing
            return AccuracyRating(
                insight_id=insight_id,
                total_feedback=10,
                useful_count=8,
                not_useful_count=2,
                accuracy_score=0.8
            )
        
        try:
            query = f"""
            SELECT
                insight_id,
                COUNT(*) as total_feedback,
                COUNTIF(rating = 'useful') as useful_count,
                COUNTIF(rating = 'not_useful') as not_useful_count,
                SAFE_DIVIDE(COUNTIF(rating = 'useful'), COUNT(*)) as accuracy_score
            FROM `{self.dataset_id}.{self.feedback_table}`
            WHERE insight_id = @insight_id
            GROUP BY insight_id
            """
            
            job_config = {
                'query_parameters': [
                    {'name': 'insight_id', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': insight_id}}
                ]
            }
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if not results:
                return None
            
            row = results[0]
            return AccuracyRating(
                insight_id=row['insight_id'],
                total_feedback=row['total_feedback'],
                useful_count=row['useful_count'],
                not_useful_count=row['not_useful_count'],
                accuracy_score=row['accuracy_score'] or 0.0
            )
        except Exception as e:
            print(f"Error calculating accuracy rating: {e}")
            return None
    
    def get_model_accuracy(
        self,
        model_version: str,
        signal_type: Optional[str] = None,
        days: int = 30
    ) -> Optional[ModelAccuracy]:
        """
        Calculate accuracy metrics for a model version
        
        Args:
            model_version: Model version string
            signal_type: Optional signal type filter
            days: Number of days to look back
            
        Returns:
            ModelAccuracy or None if insufficient data
        """
        if not self.bigquery_client:
            # Mock calculation for testing
            return ModelAccuracy(
                model_version=model_version,
                signal_type=signal_type or "all",
                total_insights=100,
                total_feedback=75,
                accuracy_score=0.82,
                period_start=datetime.now() - timedelta(days=days),
                period_end=datetime.now()
            )
        
        try:
            period_start = datetime.now() - timedelta(days=days)
            
            signal_filter = ""
            if signal_type:
                signal_filter = "AND i.signal_type = @signal_type"
            
            query = f"""
            WITH insight_feedback AS (
                SELECT
                    i.insight_id,
                    i.signal_type,
                    i.model_version,
                    i.created_at,
                    f.rating
                FROM `{self.dataset_id}.{self.insights_table}` i
                LEFT JOIN `{self.dataset_id}.{self.feedback_table}` f
                    ON i.insight_id = f.insight_id
                WHERE i.model_version = @model_version
                    AND i.created_at >= @period_start
                    {signal_filter}
            )
            SELECT
                @model_version as model_version,
                COALESCE(@signal_type, 'all') as signal_type,
                COUNT(DISTINCT insight_id) as total_insights,
                COUNT(rating) as total_feedback,
                SAFE_DIVIDE(COUNTIF(rating = 'useful'), COUNT(rating)) as accuracy_score
            FROM insight_feedback
            """
            
            job_config = {
                'query_parameters': [
                    {'name': 'model_version', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': model_version}},
                    {'name': 'period_start', 'parameterType': {'type': 'TIMESTAMP'}, 'parameterValue': {'value': period_start.isoformat()}},
                ]
            }
            
            if signal_type:
                job_config['query_parameters'].append(
                    {'name': 'signal_type', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': signal_type}}
                )
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if not results:
                return None
            
            row = results[0]
            return ModelAccuracy(
                model_version=row['model_version'],
                signal_type=row['signal_type'],
                total_insights=row['total_insights'],
                total_feedback=row['total_feedback'],
                accuracy_score=row['accuracy_score'] or 0.0,
                period_start=period_start,
                period_end=datetime.now()
            )
        except Exception as e:
            print(f"Error calculating model accuracy: {e}")
            return None
    
    def get_accuracy_leaderboard(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[ModelAccuracy]:
        """
        Get public accuracy leaderboard by model version
        
        Args:
            limit: Maximum number of results
            days: Number of days to look back
            
        Returns:
            List of ModelAccuracy sorted by accuracy score
        """
        if not self.bigquery_client:
            # Mock leaderboard for testing
            return [
                ModelAccuracy(
                    model_version="1.0.0",
                    signal_type="all",
                    total_insights=100,
                    total_feedback=80,
                    accuracy_score=0.85,
                    period_start=datetime.now() - timedelta(days=days),
                    period_end=datetime.now()
                ),
                ModelAccuracy(
                    model_version="0.9.0",
                    signal_type="all",
                    total_insights=150,
                    total_feedback=120,
                    accuracy_score=0.78,
                    period_start=datetime.now() - timedelta(days=days),
                    period_end=datetime.now()
                )
            ]
        
        try:
            period_start = datetime.now() - timedelta(days=days)
            
            query = f"""
            WITH insight_feedback AS (
                SELECT
                    i.insight_id,
                    i.model_version,
                    i.created_at,
                    f.rating
                FROM `{self.dataset_id}.{self.insights_table}` i
                LEFT JOIN `{self.dataset_id}.{self.feedback_table}` f
                    ON i.insight_id = f.insight_id
                WHERE i.created_at >= @period_start
            )
            SELECT
                model_version,
                'all' as signal_type,
                COUNT(DISTINCT insight_id) as total_insights,
                COUNT(rating) as total_feedback,
                SAFE_DIVIDE(COUNTIF(rating = 'useful'), COUNT(rating)) as accuracy_score
            FROM insight_feedback
            GROUP BY model_version
            HAVING total_feedback >= 10  -- Minimum feedback threshold
            ORDER BY accuracy_score DESC
            LIMIT @limit
            """
            
            job_config = {
                'query_parameters': [
                    {'name': 'period_start', 'parameterType': {'type': 'TIMESTAMP'}, 'parameterValue': {'value': period_start.isoformat()}},
                    {'name': 'limit', 'parameterType': {'type': 'INT64'}, 'parameterValue': {'value': str(limit)}}
                ]
            }
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            leaderboard = []
            for row in results:
                leaderboard.append(ModelAccuracy(
                    model_version=row['model_version'],
                    signal_type=row['signal_type'],
                    total_insights=row['total_insights'],
                    total_feedback=row['total_feedback'],
                    accuracy_score=row['accuracy_score'] or 0.0,
                    period_start=period_start,
                    period_end=datetime.now()
                ))
            
            return leaderboard
        except Exception as e:
            print(f"Error getting accuracy leaderboard: {e}")
            return []
    
    def collect_retraining_data(
        self,
        signal_type: Optional[str] = None,
        min_feedback: int = 5,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Collect feedback data for model retraining
        
        Args:
            signal_type: Optional signal type filter
            min_feedback: Minimum feedback count per insight
            days: Number of days to look back
            
        Returns:
            List of insights with feedback for retraining
        """
        if not self.bigquery_client:
            # Mock retraining data for testing
            return [
                {
                    'insight_id': 'insight-1',
                    'signal_type': 'mempool',
                    'confidence': 0.85,
                    'accuracy_score': 0.9,
                    'feedback_count': 10
                }
            ]
        
        try:
            period_start = datetime.now() - timedelta(days=days)
            
            signal_filter = ""
            if signal_type:
                signal_filter = "AND i.signal_type = @signal_type"
            
            query = f"""
            WITH insight_feedback AS (
                SELECT
                    i.insight_id,
                    i.signal_type,
                    i.confidence,
                    i.signal_strength,
                    i.data_quality,
                    i.historical_accuracy,
                    f.rating
                FROM `{self.dataset_id}.{self.insights_table}` i
                LEFT JOIN `{self.dataset_id}.{self.feedback_table}` f
                    ON i.insight_id = f.insight_id
                WHERE i.created_at >= @period_start
                    {signal_filter}
            )
            SELECT
                insight_id,
                signal_type,
                confidence,
                signal_strength,
                data_quality,
                historical_accuracy,
                COUNT(rating) as feedback_count,
                SAFE_DIVIDE(COUNTIF(rating = 'useful'), COUNT(rating)) as accuracy_score
            FROM insight_feedback
            GROUP BY insight_id, signal_type, confidence, signal_strength, data_quality, historical_accuracy
            HAVING feedback_count >= @min_feedback
            ORDER BY feedback_count DESC
            """
            
            job_config = {
                'query_parameters': [
                    {'name': 'period_start', 'parameterType': {'type': 'TIMESTAMP'}, 'parameterValue': {'value': period_start.isoformat()}},
                    {'name': 'min_feedback', 'parameterType': {'type': 'INT64'}, 'parameterValue': {'value': str(min_feedback)}}
                ]
            }
            
            if signal_type:
                job_config['query_parameters'].append(
                    {'name': 'signal_type', 'parameterType': {'type': 'STRING'}, 'parameterValue': {'value': signal_type}}
                )
            
            query_job = self.bigquery_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            retraining_data = []
            for row in results:
                retraining_data.append({
                    'insight_id': row['insight_id'],
                    'signal_type': row['signal_type'],
                    'confidence': row['confidence'],
                    'signal_strength': row['signal_strength'],
                    'data_quality': row['data_quality'],
                    'historical_accuracy': row['historical_accuracy'],
                    'feedback_count': row['feedback_count'],
                    'accuracy_score': row['accuracy_score'] or 0.0
                })
            
            return retraining_data
        except Exception as e:
            print(f"Error collecting retraining data: {e}")
            return []
