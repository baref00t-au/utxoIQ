"""
Cloud Monitoring metrics service for querying time series data and calculating baselines.
"""
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
from google.cloud import monitoring_v3
from google.api_core import retry
import redis.asyncio as redis

from src.config import settings

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for querying Cloud Monitoring metrics and calculating baselines."""
    
    def __init__(self, project_id: str, redis_client: Optional[redis.Redis] = None):
        """
        Initialize metrics service.
        
        Args:
            project_id: GCP project ID
            redis_client: Optional Redis client for caching
        """
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.query_client = monitoring_v3.QueryServiceClient()
        self.project_name = f"projects/{project_id}"
        self.redis_client = redis_client
        
        logger.info(f"MetricsService initialized for project {project_id}")
    
    def _parse_time_range(self, time_range: str) -> timedelta:
        """
        Parse time range string to timedelta.
        
        Args:
            time_range: Time range string (e.g., '1h', '24h', '7d', '30d')
            
        Returns:
            timedelta object
            
        Raises:
            ValueError: If time range format is invalid
        """
        time_range = time_range.lower().strip()
        
        # Extract number and unit
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return timedelta(days=days)
        else:
            raise ValueError(
                f"Invalid time range format: {time_range}. "
                "Expected format: <number>h or <number>d (e.g., '1h', '24h', '7d', '30d')"
            )
    
    def _format_time_series(self, time_series: monitoring_v3.TimeSeries) -> Dict[str, Any]:
        """
        Format time series data for API response.
        
        Args:
            time_series: Cloud Monitoring TimeSeries object
            
        Returns:
            Formatted time series data
        """
        points = []
        for point in time_series.points:
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
        
        return {
            'metric_type': time_series.metric.type,
            'resource_type': time_series.resource.type,
            'labels': dict(time_series.metric.labels),
            'points': points
        }
    
    @retry.Retry(predicate=retry.if_exception_type(Exception))
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
            metric_type: Metric type to query (e.g., 'custom.googleapis.com/api/response_time')
            start_time: Start of time range
            end_time: End of time range
            aggregation: Aggregation method (ALIGN_MEAN, ALIGN_MAX, ALIGN_MIN, etc.)
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
            formatted_results = [self._format_time_series(ts) for ts in results]
            
            logger.debug(
                f"Retrieved {len(formatted_results)} time series for {metric_type} "
                f"from {start_time} to {end_time}"
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying time series for {metric_type}: {e}")
            raise
    
    async def get_service_metrics(
        self,
        service_name: str,
        metrics: List[str],
        time_range: str = "1h",
        aggregation: str = "ALIGN_MEAN",
        interval_seconds: int = 300
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get multiple metrics for a service.
        
        Args:
            service_name: Service name (e.g., 'web-api', 'feature-engine')
            metrics: List of metric names (e.g., ['cpu_usage', 'memory_usage'])
            time_range: Time range string (e.g., '1h', '24h', '7d', '30d')
            aggregation: Aggregation method
            interval_seconds: Aggregation interval in seconds
            
        Returns:
            Dictionary mapping metric names to time series data
        """
        # Check cache first
        if self.redis_client:
            cache_key = f"metrics:{service_name}:{time_range}:{','.join(metrics)}"
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    import json
                    logger.debug(f"Cache hit for service metrics: {cache_key}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Error reading from cache: {e}")
        
        # Parse time range
        end_time = datetime.utcnow()
        start_time = end_time - self._parse_time_range(time_range)
        
        # Query each metric
        results = {}
        for metric in metrics:
            metric_type = f"custom.googleapis.com/{service_name}/{metric}"
            try:
                results[metric] = await self.get_time_series(
                    metric_type=metric_type,
                    start_time=start_time,
                    end_time=end_time,
                    aggregation=aggregation,
                    interval_seconds=interval_seconds,
                    resource_labels={"service_name": service_name}
                )
            except Exception as e:
                logger.error(f"Error querying metric {metric} for {service_name}: {e}")
                results[metric] = []
        
        # Cache the results
        if self.redis_client:
            try:
                import json
                cache_ttl = 60  # 1 minute cache
                await self.redis_client.setex(
                    cache_key,
                    cache_ttl,
                    json.dumps(results)
                )
                logger.debug(f"Cached service metrics: {cache_key}")
            except Exception as e:
                logger.warning(f"Error writing to cache: {e}")
        
        return results
    
    async def calculate_baseline(
        self,
        metric_type: str,
        days: int = 7,
        resource_labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """
        Calculate baseline statistics for a metric.
        
        Args:
            metric_type: Metric type to analyze
            days: Number of days to include in baseline calculation
            resource_labels: Optional resource label filters
            
        Returns:
            Dictionary containing baseline statistics:
            - mean: Average value
            - median: Median value
            - std_dev: Standard deviation
            - p95: 95th percentile
            - p99: 99th percentile
        """
        # Check cache first
        if self.redis_client:
            cache_key = f"baseline:{metric_type}:{days}"
            if resource_labels:
                cache_key += f":{','.join(f'{k}={v}' for k, v in resource_labels.items())}"
            
            try:
                cached_baseline = await self.redis_client.get(cache_key)
                if cached_baseline:
                    import json
                    logger.debug(f"Cache hit for baseline: {cache_key}")
                    return json.loads(cached_baseline)
            except Exception as e:
                logger.warning(f"Error reading baseline from cache: {e}")
        
        # Query historical data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        try:
            data = await self.get_time_series(
                metric_type=metric_type,
                start_time=start_time,
                end_time=end_time,
                aggregation="ALIGN_MEAN",
                interval_seconds=3600,  # Hourly data for baseline
                resource_labels=resource_labels
            )
            
            # Extract all values
            values = []
            for series in data:
                for point in series['points']:
                    values.append(point['value'])
            
            if not values:
                logger.warning(f"No data found for baseline calculation: {metric_type}")
                return {
                    "mean": 0.0,
                    "median": 0.0,
                    "std_dev": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                    "sample_count": 0
                }
            
            # Calculate statistics
            baseline = {
                "mean": float(statistics.mean(values)),
                "median": float(statistics.median(values)),
                "std_dev": float(statistics.stdev(values)) if len(values) > 1 else 0.0,
                "p95": float(np.percentile(values, 95)),
                "p99": float(np.percentile(values, 99)),
                "sample_count": len(values)
            }
            
            # Cache the baseline with 1-hour TTL
            if self.redis_client:
                try:
                    import json
                    cache_ttl = 3600  # 1 hour
                    await self.redis_client.setex(
                        cache_key,
                        cache_ttl,
                        json.dumps(baseline)
                    )
                    logger.debug(f"Cached baseline: {cache_key}")
                except Exception as e:
                    logger.warning(f"Error caching baseline: {e}")
            
            logger.info(
                f"Calculated baseline for {metric_type} over {days} days: "
                f"mean={baseline['mean']:.2f}, p95={baseline['p95']:.2f}, "
                f"samples={baseline['sample_count']}"
            )
            
            return baseline
            
        except Exception as e:
            logger.error(f"Error calculating baseline for {metric_type}: {e}")
            raise


# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service(redis_client: Optional[redis.Redis] = None) -> MetricsService:
    """
    Get or create the global metrics service instance.
    
    Args:
        redis_client: Optional Redis client for caching
        
    Returns:
        MetricsService instance
    """
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService(
            project_id=settings.gcp_project_id,
            redis_client=redis_client
        )
    return _metrics_service
