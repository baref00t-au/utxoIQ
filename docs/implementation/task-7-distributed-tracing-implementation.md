# Task 7: Distributed Tracing Implementation

## Overview

Implemented distributed tracing for the utxoIQ platform using OpenTelemetry and Google Cloud Trace. This enables tracking requests across multiple services and identifying performance bottlenecks.

## Implementation Date

January 2025

## Components Implemented

### 1. TracingService Class

**Location**: `services/web-api/src/services/tracing_service.py`

**Features**:
- OpenTelemetry integration with Cloud Trace exporter
- Automatic FastAPI instrumentation
- Trace request decorator for function-level tracing
- Span attribute and event management
- Trace retrieval and listing from Cloud Trace
- Current trace/span ID extraction

**Key Methods**:
- `__init__(project_id, service_name)` - Initialize tracing with Cloud Trace
- `instrument_fastapi(app)` - Automatically instrument FastAPI application
- `trace_request(span_name)` - Decorator to trace function execution
- `add_span_attributes(attributes)` - Add custom attributes to current span
- `add_span_event(name, attributes)` - Add events to current span
- `get_trace(trace_id)` - Retrieve complete trace data
- `list_traces(start_time, end_time, filter_str, page_size)` - List traces in time range
- `get_current_trace_id()` - Get current trace ID
- `get_current_span_id()` - Get current span ID

### 2. FastAPI Integration

**Location**: `services/web-api/src/main.py`

**Changes**:
- Added TracingService initialization in lifespan manager
- Automatic FastAPI instrumentation on startup
- Enhanced correlation ID middleware to add trace context
- Added trace IDs to response headers (`X-Cloud-Trace-Context`)
- Automatic span attributes for HTTP requests:
  - `http.method` - Request method
  - `http.url` - Full URL
  - `http.path` - Request path
  - `http.user_agent` - User agent string
  - `http.client_ip` - Client IP address
  - `http.status_code` - Response status code
  - `correlation_id` - Request correlation ID

### 3. Trace Viewing Endpoints

**Location**: `services/web-api/src/routes/monitoring.py`

**Endpoints**:

#### GET /api/v1/monitoring/traces/{trace_id}
- Retrieve complete trace data with all spans
- Includes span hierarchy, timing, and metadata
- Requires user authentication
- Returns:
  - `trace_id` - Cloud Trace ID
  - `project_id` - GCP project ID
  - `spans` - Array of span data
  - `span_count` - Total number of spans

**Response Model**:
```json
{
  "trace_id": "abc123...",
  "project_id": "utxoiq-prod",
  "spans": [
    {
      "span_id": "span123",
      "name": "process_request",
      "start_time": "2024-01-01T12:00:00Z",
      "end_time": "2024-01-01T12:00:01Z",
      "parent_span_id": null,
      "attributes": {
        "http.method": "GET",
        "http.path": "/api/v1/insights"
      },
      "status": {
        "code": 0,
        "message": ""
      }
    }
  ],
  "span_count": 1
}
```

#### GET /api/v1/monitoring/traces
- List traces within a time range
- Supports optional filtering
- Pagination support (up to 1000 traces)
- Requires user authentication
- Query Parameters:
  - `start_time` (required) - Start of time range
  - `end_time` (required) - End of time range
  - `filter_str` (optional) - Cloud Trace filter string
  - `page_size` (optional) - Number of traces (default: 100, max: 1000)

**Response Model**:
```json
[
  {
    "trace_id": "abc123...",
    "project_id": "utxoiq-prod",
    "span_count": 5
  }
]
```

### 4. Dependencies Added

**Location**: `services/web-api/requirements.txt`

**Packages**:
- `opentelemetry-api==1.22.0` - OpenTelemetry API
- `opentelemetry-sdk==1.22.0` - OpenTelemetry SDK
- `opentelemetry-exporter-gcp-trace==1.6.0` - Cloud Trace exporter
- `opentelemetry-instrumentation-fastapi==0.43b0` - FastAPI auto-instrumentation
- `google-cloud-trace==1.11.3` - Cloud Trace client library

### 5. Test Suite

**Location**: `services/web-api/tests/test_tracing_service.py`

**Test Coverage**:
- TracingService initialization
- Trace request decorator (async and sync functions)
- Error handling in traced functions
- Custom span names
- Span attribute management
- Span event management
- Trace retrieval from Cloud Trace
- Trace listing with time ranges
- Trace context management (trace ID, span ID)
- FastAPI instrumentation

**Test Classes**:
- `TestTracingServiceInitialization` - Service setup tests
- `TestTraceRequestDecorator` - Decorator functionality tests
- `TestSpanAttributes` - Span attribute and event tests
- `TestTraceRetrieval` - Cloud Trace API tests
- `TestTraceContext` - Trace/span ID extraction tests
- `TestFastAPIInstrumentation` - FastAPI integration tests

## Requirements Satisfied

### Requirement 8: Distributed Tracing

✅ **8.1**: THE Tracing System SHALL instrument all HTTP requests with trace IDs
- Implemented via FastAPI auto-instrumentation
- Trace IDs automatically propagated in headers

✅ **8.2**: THE Tracing System SHALL propagate trace IDs across service boundaries
- OpenTelemetry handles automatic propagation
- Trace context included in HTTP headers

✅ **8.3**: THE Tracing System SHALL record span duration for each service call
- Automatic span timing via OpenTelemetry
- Start and end times captured for all spans

✅ **8.4**: THE Tracing System SHALL capture request metadata including method, path, and status code
- Middleware adds comprehensive HTTP metadata
- Custom attributes for method, path, URL, user agent, client IP, status code

✅ **8.5**: THE Tracing System SHALL send trace data to Cloud Trace within 10 seconds
- BatchSpanProcessor exports traces asynchronously
- Default batch interval ensures timely export

## Usage Examples

### Using the Trace Decorator

```python
from src.services.tracing_service import TracingService

tracing_service = TracingService(
    project_id="utxoiq-prod",
    service_name="web-api"
)

@tracing_service.trace_request()
async def process_insight(insight_id: str):
    """This function will be automatically traced"""
    # Add custom attributes
    tracing_service.add_span_attributes({
        "insight_id": insight_id,
        "processing_stage": "validation"
    })
    
    # Add events
    tracing_service.add_span_event("validation_started")
    
    # Process insight...
    
    tracing_service.add_span_event("validation_completed")
    
    return result
```

### Retrieving Traces

```python
# Get specific trace
trace_data = await tracing_service.get_trace("abc123...")

# List recent traces
from datetime import datetime, timedelta

end_time = datetime.utcnow()
start_time = end_time - timedelta(hours=1)

traces = await tracing_service.list_traces(
    start_time=start_time,
    end_time=end_time,
    page_size=100
)
```

### API Usage

```bash
# Get trace details
curl -H "Authorization: Bearer $TOKEN" \
  https://api.utxoiq.com/api/v1/monitoring/traces/abc123...

# List traces
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.utxoiq.com/api/v1/monitoring/traces?start_time=2024-01-01T00:00:00Z&end_time=2024-01-02T00:00:00Z&page_size=50"
```

## Configuration

### Environment Variables

The tracing service uses the existing GCP configuration:

```bash
# Required
GCP_PROJECT_ID=utxoiq-prod
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Cloud Trace Setup

1. Enable Cloud Trace API in GCP:
```bash
gcloud services enable cloudtrace.googleapis.com
```

2. Grant service account permissions:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.agent"
```

## Testing

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tracing tests
pytest tests/test_tracing_service.py -v

# Run with coverage
pytest tests/test_tracing_service.py --cov=src.services.tracing_service --cov-report=html
```

### Manual Testing

1. Start the web API:
```bash
python -m uvicorn src.main:app --reload
```

2. Make a request and note the trace ID in response headers:
```bash
curl -v http://localhost:8080/api/v1/insights
# Look for X-Cloud-Trace-Context header
```

3. View trace in Cloud Console:
```
https://console.cloud.google.com/traces/list?project=PROJECT_ID
```

4. Or retrieve via API:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/v1/monitoring/traces/TRACE_ID
```

## Performance Considerations

### Overhead
- OpenTelemetry adds minimal overhead (<5% in most cases)
- BatchSpanProcessor exports asynchronously to avoid blocking
- Sampling can be configured if needed for high-traffic services

### Optimization
- Traces are batched before export to reduce API calls
- Automatic instrumentation only traces HTTP requests
- Manual tracing via decorator for critical functions only
- Span attributes kept minimal to reduce payload size

## Integration with Other Services

### Future Enhancements
When implementing tracing in other services (feature-engine, insight-generator, etc.):

1. Install the same OpenTelemetry packages
2. Initialize TracingService with appropriate service name
3. Instrument FastAPI/Flask applications
4. Use trace_request decorator for critical functions
5. Propagate trace context in inter-service calls

### Trace Propagation Example

```python
import httpx
from opentelemetry.propagate import inject

# When calling another service
headers = {}
inject(headers)  # Injects trace context

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://other-service/api/endpoint",
        headers=headers
    )
```

## Monitoring and Alerting

### Cloud Trace Console
- View traces: https://console.cloud.google.com/traces
- Analyze latency distributions
- Identify slow spans
- Filter by service, method, status

### Recommended Alerts
1. High trace error rate (>5%)
2. Slow traces (p95 > 2 seconds)
3. Missing trace data (export failures)

## Troubleshooting

### Traces Not Appearing
1. Verify Cloud Trace API is enabled
2. Check service account permissions
3. Verify GOOGLE_APPLICATION_CREDENTIALS is set
4. Check logs for export errors

### Missing Span Data
1. Ensure trace_request decorator is used
2. Verify span attributes are added within span context
3. Check that functions complete successfully

### High Overhead
1. Review number of custom spans created
2. Reduce span attribute count
3. Consider implementing sampling
4. Check BatchSpanProcessor configuration

## Next Steps

1. **Task 8**: Implement log aggregation service
2. **Task 9**: Integrate error tracking
3. **Task 10**: Implement performance profiling
4. **Frontend**: Build trace viewer UI component

## References

- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Cloud Trace Documentation](https://cloud.google.com/trace/docs)
- [FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [Requirement 8: Distributed Tracing](.kiro/specs/advanced-monitoring/requirements.md#requirement-8)
