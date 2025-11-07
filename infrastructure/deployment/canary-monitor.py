"""
Canary Deployment Monitoring Script
Monitors canary deployments and triggers automated rollback if thresholds are exceeded
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from google.cloud import monitoring_v3
from google.cloud import run_v2
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CanaryMetrics:
    """Canary deployment metrics"""
    error_rate: float
    p95_latency_ms: float
    p99_latency_ms: float
    request_count: int
    error_count: int
    timestamp: datetime


@dataclass
class CanaryThresholds:
    """Canary deployment thresholds"""
    max_error_rate: float = 1.0  # 1%
    max_p95_latency_ms: float = 60000  # 60 seconds
    max_p99_latency_ms: float = 120000  # 120 seconds
    min_request_count: int = 100  # Minimum requests before evaluation


class CanaryMonitor:
    """Monitor canary deployments and trigger rollback if needed"""
    
    def __init__(
        self,
        project_id: str,
        region: str,
        service_name: str,
        canary_revision: str,
        thresholds: Optional[CanaryThresholds] = None
    ):
        self.project_id = project_id
        self.region = region
        self.service_name = service_name
        self.canary_revision = canary_revision
        self.thresholds = thresholds or CanaryThresholds()
        
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.run_client = run_v2.ServicesClient()
        
        self.project_name = f"projects/{project_id}"
    
    def get_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> CanaryMetrics:
        """
        Fetch canary metrics from Cloud Monitoring
        
        Args:
            start_time: Start time for metrics query
            end_time: End time for metrics query
            
        Returns:
            CanaryMetrics object with current metrics
        """
        # Query error count
        error_count = self._query_metric(
            metric_type="run.googleapis.com/request_count",
            start_time=start_time,
            end_time=end_time,
            filters={
                "resource.labels.service_name": self.service_name,
                "resource.labels.revision_name": self.canary_revision,
                "metric.labels.response_code_class": "5xx"
            }
        )
        
        # Query total request count
        request_count = self._query_metric(
            metric_type="run.googleapis.com/request_count",
            start_time=start_time,
            end_time=end_time,
            filters={
                "resource.labels.service_name": self.service_name,
                "resource.labels.revision_name": self.canary_revision
            }
        )
        
        # Calculate error rate
        error_rate = (error_count / request_count * 100) if request_count > 0 else 0.0
        
        # Query latency distribution
        latency_distribution = self._query_distribution_metric(
            metric_type="run.googleapis.com/request_latencies",
            start_time=start_time,
            end_time=end_time,
            filters={
                "resource.labels.service_name": self.service_name,
                "resource.labels.revision_name": self.canary_revision
            }
        )
        
        p95_latency = latency_distribution.get("p95", 0.0)
        p99_latency = latency_distribution.get("p99", 0.0)
        
        return CanaryMetrics(
            error_rate=error_rate,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            request_count=request_count,
            error_count=error_count,
            timestamp=datetime.utcnow()
        )
    
    def _query_metric(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, str]
    ) -> int:
        """Query a counter metric from Cloud Monitoring"""
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(end_time.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())},
            }
        )
        
        filter_parts = [f'metric.type="{metric_type}"']
        for key, value in filters.items():
            filter_parts.append(f'{key}="{value}"')
        
        filter_str = " AND ".join(filter_parts)
        
        results = self.monitoring_client.list_time_series(
            request={
                "name": self.project_name,
                "filter": filter_str,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )
        
        total = 0
        for result in results:
            for point in result.points:
                total += point.value.int64_value or 0
        
        return total
    
    def _query_distribution_metric(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        filters: Dict[str, str]
    ) -> Dict[str, float]:
        """Query a distribution metric and calculate percentiles"""
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(end_time.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())},
            }
        )
        
        filter_parts = [f'metric.type="{metric_type}"']
        for key, value in filters.items():
            filter_parts.append(f'{key}="{value}"')
        
        filter_str = " AND ".join(filter_parts)
        
        results = self.monitoring_client.list_time_series(
            request={
                "name": self.project_name,
                "filter": filter_str,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )
        
        # Calculate percentiles from distribution
        all_values = []
        for result in results:
            for point in result.points:
                if point.value.distribution_value:
                    dist = point.value.distribution_value
                    # Approximate values from bucket counts
                    for i, count in enumerate(dist.bucket_counts):
                        if i < len(dist.bucket_options.explicit_buckets.bounds):
                            value = dist.bucket_options.explicit_buckets.bounds[i]
                            all_values.extend([value] * int(count))
        
        if not all_values:
            return {"p95": 0.0, "p99": 0.0}
        
        all_values.sort()
        p95_idx = int(len(all_values) * 0.95)
        p99_idx = int(len(all_values) * 0.99)
        
        return {
            "p95": all_values[p95_idx] if p95_idx < len(all_values) else 0.0,
            "p99": all_values[p99_idx] if p99_idx < len(all_values) else 0.0
        }
    
    def check_thresholds(self, metrics: CanaryMetrics) -> Tuple[bool, List[str]]:
        """
        Check if metrics exceed thresholds
        
        Args:
            metrics: Current canary metrics
            
        Returns:
            Tuple of (should_rollback, reasons)
        """
        should_rollback = False
        reasons = []
        
        # Check minimum request count
        if metrics.request_count < self.thresholds.min_request_count:
            logger.info(
                f"Insufficient requests ({metrics.request_count} < {self.thresholds.min_request_count}), "
                "skipping threshold checks"
            )
            return False, []
        
        # Check error rate
        if metrics.error_rate > self.thresholds.max_error_rate:
            should_rollback = True
            reasons.append(
                f"Error rate {metrics.error_rate:.2f}% exceeds threshold "
                f"{self.thresholds.max_error_rate}%"
            )
        
        # Check P95 latency
        if metrics.p95_latency_ms > self.thresholds.max_p95_latency_ms:
            should_rollback = True
            reasons.append(
                f"P95 latency {metrics.p95_latency_ms:.0f}ms exceeds threshold "
                f"{self.thresholds.max_p95_latency_ms}ms"
            )
        
        # Check P99 latency
        if metrics.p99_latency_ms > self.thresholds.max_p99_latency_ms:
            should_rollback = True
            reasons.append(
                f"P99 latency {metrics.p99_latency_ms:.0f}ms exceeds threshold "
                f"{self.thresholds.max_p99_latency_ms}ms"
            )
        
        return should_rollback, reasons
    
    def rollback_canary(self) -> bool:
        """
        Rollback canary deployment by routing all traffic to stable revision
        
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            logger.info(f"Rolling back canary deployment for {self.service_name}")
            
            # Get service
            service_path = self.run_client.service_path(
                self.project_id,
                self.region,
                self.service_name
            )
            
            service = self.run_client.get_service(name=service_path)
            
            # Find stable revision (not canary)
            stable_revision = None
            for traffic in service.traffic:
                if traffic.revision != self.canary_revision:
                    stable_revision = traffic.revision
                    break
            
            if not stable_revision:
                logger.error("No stable revision found for rollback")
                return False
            
            # Update traffic to route 100% to stable
            service.traffic = [
                run_v2.TrafficTarget(
                    type_=run_v2.TrafficTargetAllocationType.TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION,
                    revision=stable_revision,
                    percent=100
                )
            ]
            
            # Update service
            update_request = run_v2.UpdateServiceRequest(
                service=service
            )
            
            operation = self.run_client.update_service(request=update_request)
            operation.result()  # Wait for completion
            
            logger.info(f"Successfully rolled back to {stable_revision}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back canary: {e}")
            return False
    
    def monitor(
        self,
        duration_minutes: int = 15,
        check_interval_seconds: int = 60
    ) -> bool:
        """
        Monitor canary deployment for specified duration
        
        Args:
            duration_minutes: How long to monitor the canary
            check_interval_seconds: How often to check metrics
            
        Returns:
            True if canary is healthy, False if rolled back
        """
        logger.info(
            f"Starting canary monitoring for {self.service_name} "
            f"(revision: {self.canary_revision})"
        )
        logger.info(f"Monitoring for {duration_minutes} minutes")
        logger.info(f"Thresholds: error_rate={self.thresholds.max_error_rate}%, "
                   f"p95_latency={self.thresholds.max_p95_latency_ms}ms")
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.utcnow() < end_time:
            check_start = datetime.utcnow() - timedelta(minutes=5)
            check_end = datetime.utcnow()
            
            # Get current metrics
            metrics = self.get_metrics(check_start, check_end)
            
            logger.info(
                f"Metrics: error_rate={metrics.error_rate:.2f}%, "
                f"p95_latency={metrics.p95_latency_ms:.0f}ms, "
                f"requests={metrics.request_count}"
            )
            
            # Check thresholds
            should_rollback, reasons = self.check_thresholds(metrics)
            
            if should_rollback:
                logger.error(f"Canary failed threshold checks: {', '.join(reasons)}")
                if self.rollback_canary():
                    logger.info("Canary rolled back successfully")
                    return False
                else:
                    logger.error("Failed to rollback canary")
                    return False
            
            # Wait before next check
            time.sleep(check_interval_seconds)
        
        logger.info("Canary monitoring completed successfully")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Monitor canary deployment")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--region", required=True, help="GCP region")
    parser.add_argument("--service", required=True, help="Service name")
    parser.add_argument("--revision", required=True, help="Canary revision name")
    parser.add_argument("--duration", type=int, default=15, help="Monitoring duration in minutes")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--error-rate-threshold", type=float, default=1.0, help="Max error rate %")
    parser.add_argument("--latency-threshold", type=float, default=60000, help="Max P95 latency ms")
    
    args = parser.parse_args()
    
    thresholds = CanaryThresholds(
        max_error_rate=args.error_rate_threshold,
        max_p95_latency_ms=args.latency_threshold
    )
    
    monitor = CanaryMonitor(
        project_id=args.project_id,
        region=args.region,
        service_name=args.service,
        canary_revision=args.revision,
        thresholds=thresholds
    )
    
    success = monitor.monitor(
        duration_minutes=args.duration,
        check_interval_seconds=args.interval
    )
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
