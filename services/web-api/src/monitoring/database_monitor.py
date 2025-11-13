"""Database monitoring service for tracking connection pool and query metrics."""
import logging
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool
from google.cloud import monitoring_v3
from google.api import metric_pb2 as ga_metric
from google.api import label_pb2 as ga_label

from src.config import settings

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Monitor database connection pool and query performance."""
    
    def __init__(self, project_id: str):
        """
        Initialize database monitor.
        
        Args:
            project_id: GCP project ID for Cloud Monitoring
        """
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        
        # Metrics tracking
        self.query_count = 0
        self.slow_query_count = 0
        self.total_query_time = 0.0
        self.slow_query_threshold = 0.2  # 200ms
        
        logger.info("Database monitor initialized")
    
    def setup_pool_listeners(self, engine: Engine):
        """
        Set up SQLAlchemy pool event listeners.
        
        Args:
            engine: SQLAlchemy engine instance
        """
        @event.listens_for(engine.sync_engine.pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Track new connections."""
            logger.debug("New database connection established")
        
        @event.listens_for(engine.sync_engine.pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkouts from pool."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(engine.sync_engine.pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection returns to pool."""
            logger.debug("Connection returned to pool")
        
        logger.info("Pool event listeners configured")
    
    @asynccontextmanager
    async def track_query(self, query_name: str = "unknown"):
        """
        Context manager to track query execution time.
        
        Args:
            query_name: Name/identifier for the query
            
        Yields:
            Dict with query metadata
        """
        start_time = time.time()
        query_metadata = {
            "name": query_name,
            "start_time": start_time,
            "duration": 0.0,
            "is_slow": False
        }
        
        try:
            yield query_metadata
        finally:
            duration = time.time() - start_time
            query_metadata["duration"] = duration
            
            # Update metrics
            self.query_count += 1
            self.total_query_time += duration
            
            # Check if slow query
            if duration > self.slow_query_threshold:
                self.slow_query_count += 1
                query_metadata["is_slow"] = True
                logger.warning(
                    f"Slow query detected: {query_name} took {duration:.3f}s "
                    f"(threshold: {self.slow_query_threshold}s)"
                )
            
            # Log query metrics
            logger.debug(
                f"Query '{query_name}' completed in {duration:.3f}s"
            )
    
    async def get_pool_metrics(self, pool: Pool) -> Dict[str, Any]:
        """
        Get current connection pool metrics.
        
        Args:
            pool: SQLAlchemy connection pool
            
        Returns:
            Dict containing pool metrics
        """
        try:
            metrics = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total_connections": pool.size() + pool.overflow(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Pool metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error getting pool metrics: {e}")
            return {}
    
    async def get_query_metrics(self) -> Dict[str, Any]:
        """
        Get query performance metrics.
        
        Returns:
            Dict containing query metrics
        """
        avg_query_time = (
            self.total_query_time / self.query_count 
            if self.query_count > 0 
            else 0.0
        )
        
        metrics = {
            "total_queries": self.query_count,
            "slow_queries": self.slow_query_count,
            "slow_query_percentage": (
                (self.slow_query_count / self.query_count * 100)
                if self.query_count > 0
                else 0.0
            ),
            "average_query_time": avg_query_time,
            "total_query_time": self.total_query_time,
            "slow_query_threshold": self.slow_query_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
    
    def write_metric(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Write a custom metric to Cloud Monitoring.
        
        Args:
            metric_type: Metric type (e.g., 'connection_pool_size')
            value: Metric value
            labels: Optional metric labels
        """
        try:
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/database/{metric_type}"
            
            # Add labels
            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = val
            
            # Set resource
            series.resource.type = "cloud_run_revision"
            series.resource.labels["project_id"] = self.project_id
            series.resource.labels["service_name"] = "utxoiq-api"
            series.resource.labels["revision_name"] = "latest"
            series.resource.labels["location"] = "us-central1"
            
            # Create data point
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10 ** 9)
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point(
                {"interval": interval, "value": {"double_value": value}}
            )
            series.points = [point]
            
            # Write to Cloud Monitoring
            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
            logger.debug(f"Wrote metric {metric_type}={value}")
        except Exception as e:
            logger.error(f"Error writing metric to Cloud Monitoring: {e}")
    
    async def publish_pool_metrics(self, pool: Pool):
        """
        Publish connection pool metrics to Cloud Monitoring.
        
        Args:
            pool: SQLAlchemy connection pool
        """
        metrics = await self.get_pool_metrics(pool)
        
        if metrics:
            self.write_metric("connection_pool_size", metrics["size"])
            self.write_metric("connection_pool_checked_in", metrics["checked_in"])
            self.write_metric("connection_pool_checked_out", metrics["checked_out"])
            self.write_metric("connection_pool_overflow", metrics["overflow"])
            self.write_metric("connection_pool_total", metrics["total_connections"])
    
    async def publish_query_metrics(self):
        """Publish query performance metrics to Cloud Monitoring."""
        metrics = await self.get_query_metrics()
        
        self.write_metric("query_count", metrics["total_queries"])
        self.write_metric("slow_query_count", metrics["slow_queries"])
        self.write_metric("slow_query_percentage", metrics["slow_query_percentage"])
        self.write_metric("average_query_time_ms", metrics["average_query_time"] * 1000)
    
    async def check_slow_queries(self) -> bool:
        """
        Check if slow query threshold is exceeded.
        
        Returns:
            True if slow queries exceed threshold
        """
        metrics = await self.get_query_metrics()
        
        # Alert if more than 5% of queries are slow
        if metrics["slow_query_percentage"] > 5.0:
            logger.warning(
                f"High slow query rate: {metrics['slow_query_percentage']:.2f}% "
                f"({metrics['slow_queries']}/{metrics['total_queries']})"
            )
            return True
        
        return False


# Global monitor instance
_monitor: Optional[DatabaseMonitor] = None


def get_database_monitor() -> DatabaseMonitor:
    """
    Get or create the global database monitor instance.
    
    Returns:
        DatabaseMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = DatabaseMonitor(settings.gcp_project_id)
    return _monitor
