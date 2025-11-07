"""
Metrics Instrumentation Helper for utxoIQ Services

This module provides pre-configured Prometheus metrics for all utxoIQ services.
Import and use these metrics in your FastAPI services to ensure consistent monitoring.

Usage:
    from infrastructure.grafana.metrics_instrumentation import (
        block_to_insight_latency,
        ai_inference_cost,
        user_feedback_useful
    )
    
    # Track latency
    with block_to_insight_latency.time():
        process_block()
    
    # Track cost
    ai_inference_cost.labels(signal_type='mempool', model_version='v1').inc(0.05)
    
    # Track feedback
    user_feedback_useful.labels(signal_type='exchange', model_version='v1').inc()
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Optional

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

block_to_insight_latency = Histogram(
    'block_to_insight_latency_seconds',
    'Time from block detection to insight publication',
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'code', 'job']
)

websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total WebSocket connections'
)

websocket_disconnections_total = Counter(
    'websocket_disconnections_total',
    'Total WebSocket disconnections'
)

signals_generated_total = Counter(
    'signals_generated_total',
    'Total signals generated',
    ['signal_type']
)

duplicate_signals_total = Counter(
    'duplicate_signals_total',
    'Total duplicate signals',
    ['signal_type']
)

# ============================================================================
# COST METRICS
# ============================================================================

ai_inference_cost_usd = Counter(
    'ai_inference_cost_usd',
    'AI inference cost in USD',
    ['signal_type', 'model_version']
)

bigquery_cost_usd = Counter(
    'bigquery_cost_usd',
    'BigQuery cost in USD',
    ['query_type']
)

bigquery_query_cost_usd = Gauge(
    'bigquery_query_cost_usd',
    'Individual query cost in USD',
    ['query_id']
)

bigquery_query_duration_seconds = Histogram(
    'bigquery_query_duration_seconds',
    'BigQuery query duration in seconds',
    ['query_type'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60]
)

insights_generated_total = Counter(
    'insights_generated_total',
    'Total insights generated',
    ['signal_type']
)

# ============================================================================
# ACCURACY METRICS
# ============================================================================

user_feedback_total = Counter(
    'user_feedback_total',
    'Total user feedback received',
    ['signal_type', 'model_version']
)

user_feedback_useful_total = Counter(
    'user_feedback_useful_total',
    'Total useful feedback received',
    ['signal_type', 'model_version']
)

predictions_evaluated_total = Counter(
    'predictions_evaluated_total',
    'Total predictions evaluated',
    ['prediction_type']
)

prediction_accurate_total = Counter(
    'prediction_accurate_total',
    'Total accurate predictions',
    ['prediction_type']
)

api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['correlation_id', 'error_type', 'error_message']
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_http_request(method: str, endpoint: str, status_code: int, job: str):
    """Track an HTTP request"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        code=str(status_code),
        job=job
    ).inc()


def track_signal_generation(signal_type: str, is_duplicate: bool = False):
    """Track signal generation"""
    signals_generated_total.labels(signal_type=signal_type).inc()
    if is_duplicate:
        duplicate_signals_total.labels(signal_type=signal_type).inc()


def track_ai_cost(signal_type: str, model_version: str, cost_usd: float):
    """Track AI inference cost"""
    ai_inference_cost_usd.labels(
        signal_type=signal_type,
        model_version=model_version
    ).inc(cost_usd)


def track_bigquery_cost(query_type: str, cost_usd: float, duration_seconds: float, query_id: Optional[str] = None):
    """Track BigQuery query cost and performance"""
    bigquery_cost_usd.labels(query_type=query_type).inc(cost_usd)
    bigquery_query_duration_seconds.labels(query_type=query_type).observe(duration_seconds)
    if query_id:
        bigquery_query_cost_usd.labels(query_id=query_id).set(cost_usd)


def track_insight_generation(signal_type: str):
    """Track insight generation"""
    insights_generated_total.labels(signal_type=signal_type).inc()


def track_user_feedback(signal_type: str, model_version: str, is_useful: bool):
    """Track user feedback"""
    user_feedback_total.labels(
        signal_type=signal_type,
        model_version=model_version
    ).inc()
    if is_useful:
        user_feedback_useful_total.labels(
            signal_type=signal_type,
            model_version=model_version
        ).inc()


def track_prediction_accuracy(prediction_type: str, is_accurate: bool):
    """Track prediction accuracy"""
    predictions_evaluated_total.labels(prediction_type=prediction_type).inc()
    if is_accurate:
        prediction_accurate_total.labels(prediction_type=prediction_type).inc()


def track_api_error(correlation_id: str, error_type: str, error_message: str):
    """Track API error with correlation ID"""
    api_errors_total.labels(
        correlation_id=correlation_id,
        error_type=error_type,
        error_message=error_message[:100]  # Truncate long messages
    ).inc()


def track_websocket_connection(is_disconnect: bool = False):
    """Track WebSocket connection or disconnection"""
    if is_disconnect:
        websocket_disconnections_total.inc()
    else:
        websocket_connections_total.inc()


# ============================================================================
# FASTAPI INTEGRATION
# ============================================================================

def setup_metrics_endpoint(app):
    """
    Add /metrics endpoint to FastAPI app
    
    Usage:
        from fastapi import FastAPI
        from infrastructure.grafana.metrics_instrumentation import setup_metrics_endpoint
        
        app = FastAPI()
        setup_metrics_endpoint(app)
    """
    from fastapi import Response
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(content=generate_latest(), media_type="text/plain")
    
    return app


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class BlockProcessingTimer:
    """Context manager for tracking block-to-insight latency"""
    
    def __enter__(self):
        self.timer = block_to_insight_latency.time()
        self.timer.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timer.__exit__(exc_type, exc_val, exc_tb)


class BigQueryQueryTimer:
    """Context manager for tracking BigQuery query performance"""
    
    def __init__(self, query_type: str, query_id: Optional[str] = None):
        self.query_type = query_type
        self.query_id = query_id
        self.timer = bigquery_query_duration_seconds.labels(query_type=query_type).time()
    
    def __enter__(self):
        self.timer.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timer.__exit__(exc_type, exc_val, exc_tb)
    
    def set_cost(self, cost_usd: float):
        """Set the cost of the query"""
        bigquery_cost_usd.labels(query_type=self.query_type).inc(cost_usd)
        if self.query_id:
            bigquery_query_cost_usd.labels(query_id=self.query_id).set(cost_usd)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Track block processing
    with BlockProcessingTimer():
        # Process block
        pass
    
    # Example: Track signal generation
    track_signal_generation('mempool', is_duplicate=False)
    
    # Example: Track AI cost
    track_ai_cost('exchange', 'gemini-pro-v1', 0.05)
    
    # Example: Track BigQuery query
    with BigQueryQueryTimer('signal_computation', 'query-123') as timer:
        # Execute query
        pass
        timer.set_cost(0.02)
    
    # Example: Track user feedback
    track_user_feedback('whale', 'gemini-pro-v1', is_useful=True)
    
    # Example: Track prediction accuracy
    track_prediction_accuracy('fee_forecast', is_accurate=True)
    
    print("Metrics instrumentation examples completed")
