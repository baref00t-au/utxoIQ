"""
Deployment Metrics Instrumentation
Provides Prometheus metrics for deployment monitoring
"""

from prometheus_client import Counter, Gauge, Histogram, Info
from datetime import datetime
from typing import Optional

# Deployment metrics
deployment_started = Counter(
    'deployment_started_total',
    'Total number of deployments started',
    ['service', 'environment', 'deployment_type']
)

deployment_success = Counter(
    'deployment_success_total',
    'Total number of successful deployments',
    ['service', 'environment', 'deployment_type']
)

deployment_rollback = Counter(
    'deployment_rollback_total',
    'Total number of deployment rollbacks',
    ['service', 'environment', 'reason']
)

deployment_duration = Histogram(
    'deployment_duration_seconds',
    'Deployment duration in seconds',
    ['service', 'environment', 'deployment_type'],
    buckets=[30, 60, 120, 300, 600, 1200, 1800, 3600]
)

canary_duration = Histogram(
    'deployment_canary_duration_seconds',
    'Canary monitoring duration in seconds',
    ['service', 'environment'],
    buckets=[60, 300, 600, 900, 1200, 1800]
)

deployment_started_timestamp = Gauge(
    'deployment_started_timestamp',
    'Timestamp when deployment started',
    ['service', 'environment', 'revision']
)

deployment_rollback_timestamp = Gauge(
    'deployment_rollback_timestamp',
    'Timestamp when rollback occurred',
    ['service', 'environment', 'reason']
)

current_revision = Info(
    'deployment_current_revision',
    'Current deployed revision',
    ['service', 'environment']
)

canary_traffic_percentage = Gauge(
    'deployment_canary_traffic_percentage',
    'Percentage of traffic routed to canary',
    ['service', 'environment', 'revision']
)

# OpenAPI schema compatibility metrics
openapi_schema_validation = Counter(
    'openapi_schema_validation_total',
    'Total OpenAPI schema validations',
    ['service', 'result']  # result: success, breaking_change, error
)

openapi_breaking_changes = Counter(
    'openapi_breaking_changes_total',
    'Total breaking changes detected in OpenAPI schema',
    ['service', 'change_type']
)


class DeploymentMetrics:
    """Helper class for recording deployment metrics"""
    
    @staticmethod
    def record_deployment_start(
        service: str,
        environment: str,
        deployment_type: str,
        revision: str
    ):
        """Record deployment start"""
        deployment_started.labels(
            service=service,
            environment=environment,
            deployment_type=deployment_type
        ).inc()
        
        deployment_started_timestamp.labels(
            service=service,
            environment=environment,
            revision=revision
        ).set(datetime.utcnow().timestamp())
    
    @staticmethod
    def record_deployment_success(
        service: str,
        environment: str,
        deployment_type: str,
        duration_seconds: float
    ):
        """Record successful deployment"""
        deployment_success.labels(
            service=service,
            environment=environment,
            deployment_type=deployment_type
        ).inc()
        
        deployment_duration.labels(
            service=service,
            environment=environment,
            deployment_type=deployment_type
        ).observe(duration_seconds)
    
    @staticmethod
    def record_deployment_rollback(
        service: str,
        environment: str,
        reason: str
    ):
        """Record deployment rollback"""
        deployment_rollback.labels(
            service=service,
            environment=environment,
            reason=reason
        ).inc()
        
        deployment_rollback_timestamp.labels(
            service=service,
            environment=environment,
            reason=reason
        ).set(datetime.utcnow().timestamp())
    
    @staticmethod
    def record_canary_duration(
        service: str,
        environment: str,
        duration_seconds: float
    ):
        """Record canary monitoring duration"""
        canary_duration.labels(
            service=service,
            environment=environment
        ).observe(duration_seconds)
    
    @staticmethod
    def set_current_revision(
        service: str,
        environment: str,
        revision: str,
        git_sha: str,
        deployed_at: str
    ):
        """Set current deployed revision info"""
        current_revision.labels(
            service=service,
            environment=environment
        ).info({
            'revision': revision,
            'git_sha': git_sha,
            'deployed_at': deployed_at
        })
    
    @staticmethod
    def set_canary_traffic(
        service: str,
        environment: str,
        revision: str,
        percentage: float
    ):
        """Set canary traffic percentage"""
        canary_traffic_percentage.labels(
            service=service,
            environment=environment,
            revision=revision
        ).set(percentage)
    
    @staticmethod
    def record_openapi_validation(
        service: str,
        result: str
    ):
        """Record OpenAPI schema validation result"""
        openapi_schema_validation.labels(
            service=service,
            result=result
        ).inc()
    
    @staticmethod
    def record_breaking_change(
        service: str,
        change_type: str
    ):
        """Record OpenAPI breaking change"""
        openapi_breaking_changes.labels(
            service=service,
            change_type=change_type
        ).inc()


# Example usage in deployment scripts
if __name__ == "__main__":
    import time
    from prometheus_client import start_http_server, generate_latest
    
    # Start metrics server
    start_http_server(8000)
    
    # Simulate deployment
    metrics = DeploymentMetrics()
    
    # Start deployment
    metrics.record_deployment_start(
        service="web-api",
        environment="production",
        deployment_type="canary",
        revision="web-api-canary-abc123"
    )
    
    # Set canary traffic
    metrics.set_canary_traffic(
        service="web-api",
        environment="production",
        revision="web-api-canary-abc123",
        percentage=10.0
    )
    
    # Simulate canary monitoring
    time.sleep(5)
    
    # Record success
    metrics.record_deployment_success(
        service="web-api",
        environment="production",
        deployment_type="canary",
        duration_seconds=900.0
    )
    
    metrics.record_canary_duration(
        service="web-api",
        environment="production",
        duration_seconds=900.0
    )
    
    # Set current revision
    metrics.set_current_revision(
        service="web-api",
        environment="production",
        revision="web-api-canary-abc123",
        git_sha="abc123def456",
        deployed_at=datetime.utcnow().isoformat()
    )
    
    print("Metrics available at http://localhost:8000/metrics")
    print(generate_latest().decode('utf-8'))
