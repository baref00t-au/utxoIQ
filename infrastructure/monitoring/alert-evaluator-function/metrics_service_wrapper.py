"""
Metrics service wrapper for Cloud Function.

This module provides a simplified wrapper around the MetricsService
that can be used in the Cloud Function context.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.cloud import monitoring_v3
from google.api_core import retry
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class MetricsServiceWrapper:
    """Wrapper for MetricsService compatible with Cloud Function."""
    
    def __init__(self, project_id: str, redis_client: Optional[redis.Redis] = None):
        """
        Initialize metrics service wrapper.
        
        Args:
            project_id: GCP project ID
            redis_client: Optional Redis client for caching
        """
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        self.redis_client = redis_client
        
        logger.info(f"MetricsServiceWrapper initialized for project {project_id}")
    
    async def get_time_series(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: str = "ALIGN_MEAN",
        interval_seconds: int = 300,
        resource_labels: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query time series data from Cloud Monitoring.
        
        Args:
            metric_type: Metric type to query
            start_time: Start of time range
            end_time: End of time range
            aggregation: Aggregation method
            interval_seconds: Aggregation interval in seconds
            resource_labels: Optional resource label filters
            
        Returns:
            List of formatted time series data
        """
        try:
            # Build time interval
            interval = monitoring_v3.TimeInterval({
                "start_time": start_time,
                "end_time": end_time
            })
            
            # Build aggregation
            aggregation_obj = monitoring_v3.Aggregation({
                "alignment_period": {"seconds": interval_seconds},
                "per_series_aligner": getattr(
                    monitoring_v3.Aggregation.Aligner,
                    aggregation
                ),
            })
            
            # Build filter
            filter_str = f'metric.type = "{metric_type}"'
            if resource_labels:
                for key, value in resource_labels.items():
                    filter_str += f' AND resource.labels.{key} = "{value}"'
            
            # Query time series
            results = self.client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": filter_str,
                    "interval": interval,
                    "aggregation": aggregation_obj,
                }
            )
            
            # Format results
            formatted_results = []
            for ts in results:
                points = []
                for point in ts.points:
                    # Extract value based on type
                    if point.value.HasField('double_value'):
                        value = point.value.double_value
                    elif point.value.HasField('int64_value'):
                        value = float(point.value.int64_value)
                    elif point.value.HasField('bool_value'):
                        value = 1.0 if point.value.bool_value else 0.0
                    else:
                        value = 0.0
                    
                    points.append({
                        'timestamp': point.interval.end_time.isoformat(),
                        'value': value
                    })
                
                formatted_results.append({
                    'metric_type': ts.metric.type,
                    'resource_type': ts.resource.type,
                    'labels': dict(ts.metric.labels),
                    'points': points
                })
            
            logger.debug(
                f"Retrieved {len(formatted_results)} time series for {metric_type}"
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying time series for {metric_type}: {e}")
            raise
