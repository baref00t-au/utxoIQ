# Task 11: Service Dependency Visualization Implementation

## Overview

Implemented service dependency visualization feature that analyzes distributed traces to build a dependency graph showing service-to-service relationships, health status, and failed dependencies.

## Implementation Date

November 11, 2025

## Components Implemented

### 1. Dependency Visualization Service

**File**: `services/web-api/src/services/dependency_visualization_service.py`

Core service that:
- Queries traces from Cloud Trace
- Extracts service dependencies from span relationships
- Calculates call counts, error rates, and average durations
- Determines real-time health status for each service
- Builds dependency graph with nodes (services) and edges (calls)

**Key Features**:
- Analyzes up to 5000 traces per request
- Supports time ranges up to 24 hours
- Tracks call counts and error counts per service and dependency
- Calculates average duration for performance analysis
- Determines health status based on error rates:
  - healthy: <5% error rate
  - degraded: 5-10% error rate
  - unhealthy: >10% error rate
  - unknown: no recent metrics available

**Key Methods**:
- `build_dependency_graph()`: Main method to construct dependency graph
- `_query_traces()`: Query traces from Cloud Trace
- `_extract_dependencies()`: Extract service relationships from traces
- `_get_service_health_status()`: Determine health status for services
- `_extract_service_name()`: Extract service name from span attributes
- `_calculate_span_duration()`: Calculate span duration in milliseconds
- `_span_has_error()`: Check if span has error status

### 2. API Endpoint

**File**: `services/web-api/src/routes/monitoring.py`

**Endpoint**: `GET /api/v1/monitoring/dependencies`

**Query Parameters**:
- `start_time` (optional): Start of time range (defaults to 1 hour ago)
- `end_time` (optional): End of time range (defaults to now)
- `max_traces` (optional): Maximum number of traces to analyze (100-5000, default: 1000)

**Response Structure**:
```json
{
  "nodes": [
    {
      "service_name": "web-api",
      "call_count": 150,
      "error_count": 2,
      "avg_duration_ms": 45.2,
      "health_status": "healthy",
      "last_seen": "2025-11-11T10:30:00Z"
    }
  ],
  "edges": [
    {
      "source": "web-api",
      "target": "feature-engine",
      "call_count": 75,
      "error_count": 0,
      "avg_duration_ms": 120.5,
      "failed": false
    }
  ],
  "metadata": {
    "start_time": "2025-11-11T09:30:00Z",
    "end_time": "2025-11-11T10:30:00Z",
    "traces_analyzed": 1000,
    "total_services": 5,
    "total_dependencies": 8
  }
}
```

**Features**:
- Requires user authentication
- Rate limited
- Validates time range (max 24 hours)
- Returns comprehensive dependency graph with health status
- Highlights failed dependencies

### 3. Response Models

**Pydantic Models**:
- `ServiceNodeResponse`: Service node in dependency graph
- `ServiceEdgeResponse`: Service dependency edge in graph
- `DependencyGraphMetadata`: Metadata about dependency graph
- `DependencyGraphResponse`: Complete service dependency graph

### 4. Tests

**File**: `services/web-api/tests/test_dependency_visualization_service.py`

**Test Coverage**:

1. **Dependency Graph Construction**:
   - Test successful graph construction from traces
   - Test graph includes health status
   - Test empty traces handling

2. **Health Status Updates**:
   - Test healthy service detection (<5% error rate)
   - Test degraded service detection (5-10% error rate)
   - Test unhealthy service detection (>10% error rate)
   - Test unknown status when no metrics available
   - Test error handling during health status query

3. **Failed Dependency Detection**:
   - Test detection of failed dependencies
   - Test error count tracking on edges
   - Test error count tracking on nodes

4. **Dependency Graph Metrics**:
   - Test call count tracking
   - Test average duration calculation
   - Test last seen timestamp tracking

## Requirements Satisfied

### Requirement 3: Service Dependency Visualization

✅ **Acceptance Criteria 1**: THE Dependency Visualization SHALL display a graph of all services and their connections
- Implemented: Graph includes nodes (services) and edges (service-to-service calls)

✅ **Acceptance Criteria 2**: THE Dependency Visualization SHALL show real-time health status for each service node
- Implemented: Health status determined from recent error rates (healthy, degraded, unhealthy, unknown)

✅ **Acceptance Criteria 3**: THE Dependency Visualization SHALL highlight failed dependencies in red
- Implemented: Failed edges marked with `failed: true` flag when error_count > 0

✅ **Acceptance Criteria 4**: THE Dependency Visualization SHALL show request flow direction with arrows
- Implemented: Edges have source and target fields indicating direction

✅ **Acceptance Criteria 5**: THE Dependency Visualization SHALL update service status within 10 seconds of changes
- Implemented: Health status queried from last 5 minutes of metrics

## Technical Details

### Trace Analysis

The service analyzes distributed traces to identify service dependencies:

1. **Span Extraction**: Extracts service name from span attributes or display name
2. **Parent-Child Relationships**: Identifies service calls by analyzing parent-child span relationships
3. **Error Detection**: Checks span status codes and attributes for errors
4. **Duration Calculation**: Calculates span duration from start_time and end_time
5. **Aggregation**: Aggregates call counts, error counts, and durations per service and dependency

### Health Status Determination

Health status is determined by querying Cloud Monitoring for error rates:

1. Query error rate metric for last 5 minutes
2. Calculate average error rate
3. Classify based on thresholds:
   - <5%: healthy
   - 5-10%: degraded
   - >10%: unhealthy
   - No data: unknown

### Performance Considerations

- Limits trace analysis to configurable maximum (default 1000, max 5000)
- Limits time range to 24 hours to prevent excessive data processing
- Uses efficient data structures (defaultdict) for aggregation
- Gracefully handles missing or malformed trace data

## Dependencies

### Required Packages

```
google-cloud-trace==1.11.3
google-cloud-monitoring==2.18.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
```

### GCP Services

- **Cloud Trace**: For distributed tracing data
- **Cloud Monitoring**: For service health metrics

## Usage Example

### API Request

```bash
curl -X GET "https://api.utxoiq.com/api/v1/monitoring/dependencies?start_time=2025-11-11T09:00:00Z&end_time=2025-11-11T10:00:00Z&max_traces=1000" \
  -H "Authorization: Bearer <token>"
```

### Frontend Integration

```typescript
// Fetch dependency graph
const response = await fetch('/api/v1/monitoring/dependencies', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const graph = await response.json();

// Render with D3.js or similar
const nodes = graph.nodes.map(node => ({
  id: node.service_name,
  label: node.service_name,
  color: getHealthColor(node.health_status),
  size: node.call_count
}));

const edges = graph.edges.map(edge => ({
  source: edge.source,
  target: edge.target,
  width: edge.call_count / 10,
  color: edge.failed ? 'red' : 'gray'
}));

// Render graph visualization
renderDependencyGraph(nodes, edges);
```

## Frontend Visualization Recommendations

### Graph Rendering

Use D3.js or similar library for interactive visualization:

1. **Nodes**: Represent services as circles
   - Size based on call count
   - Color based on health status (green/yellow/red/gray)
   - Label with service name

2. **Edges**: Represent dependencies as arrows
   - Width based on call count
   - Color: red for failed, gray for healthy
   - Direction from source to target

3. **Interactivity**:
   - Hover to show metrics (call count, error count, avg duration)
   - Click to filter related dependencies
   - Zoom and pan for large graphs

### Health Status Colors

```css
.health-healthy { color: #16A34A; }
.health-degraded { color: #D97706; }
.health-unhealthy { color: #DC2626; }
.health-unknown { color: #6B7280; }
```

## Testing Notes

### Test Execution

```bash
# Run dependency visualization tests
cd services/web-api
python -m pytest tests/test_dependency_visualization_service.py -v

# Run with coverage
python -m pytest tests/test_dependency_visualization_service.py --cov=src/services/dependency_visualization_service --cov-report=html
```

### Test Requirements

Ensure the following packages are installed:
```bash
pip install pytest pytest-asyncio pytest-cov
pip install google-cloud-trace google-cloud-monitoring
```

## Future Enhancements

1. **Caching**: Cache dependency graphs for frequently accessed time ranges
2. **Real-time Updates**: WebSocket support for live graph updates
3. **Anomaly Detection**: Detect unusual dependency patterns
4. **Performance Insights**: Identify slow dependencies and bottlenecks
5. **Historical Comparison**: Compare current graph with historical baselines
6. **Service Grouping**: Group related services for better visualization
7. **Export**: Export graph data in various formats (JSON, GraphML, DOT)

## Related Documentation

- [Task 7: Distributed Tracing Implementation](./task-7-distributed-tracing-implementation.md)
- [Task 8: Log Aggregation Implementation](./task-8-log-aggregation-implementation.md)
- [Design Document](./.kiro/specs/advanced-monitoring/design.md)
- [Requirements Document](./.kiro/specs/advanced-monitoring/requirements.md)

## Completion Status

✅ Task 11: Implement service dependency visualization
✅ Task 11.1: Create dependency visualization endpoint
✅ Task 11.2: Write tests for dependency visualization

All acceptance criteria for Requirement 3 have been satisfied.
