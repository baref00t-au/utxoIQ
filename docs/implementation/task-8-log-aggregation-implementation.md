# Task 8: Log Aggregation Service Implementation

## Overview

Implemented a comprehensive log aggregation service for centralized log collection and search across all services using Google Cloud Logging. This implementation satisfies Requirement 9 from the advanced monitoring specification.

## Implementation Summary

### 1. Core Service Implementation

**File**: `services/web-api/src/services/log_aggregation_service.py`

Created `LogAggregationService` class with the following capabilities:

#### Key Features:
- **Full-text search** across all logs with query support
- **Multi-dimensional filtering** by service, severity, and time range
- **Pagination support** for large result sets
- **Log context retrieval** with surrounding log entries
- **Statistics calculation** for log analysis

#### Main Methods:

1. **`search_logs()`**
   - Searches logs with flexible filtering options
   - Supports full-text queries, time ranges, severity levels, and service names
   - Returns paginated results with next page tokens
   - Validates and corrects limit parameters (1-1000)

2. **`get_log_context()`**
   - Retrieves surrounding log entries for context
   - Returns configurable number of lines before and after target log
   - Highlights target log in results
   - Supports service filtering for focused context

3. **`get_log_statistics()`**
   - Calculates aggregate statistics for time ranges
   - Provides severity breakdowns
   - Supports service-specific statistics

4. **`_format_log_entry()`**
   - Formats Cloud Logging entries for API responses
   - Extracts message from various payload types
   - Includes resource information, labels, and trace data
   - Handles HTTP request metadata when available

### 2. API Endpoints

**File**: `services/web-api/src/routes/monitoring.py`

Added three new endpoints to the monitoring router:

#### Endpoints:

1. **`POST /api/v1/monitoring/logs/search`**
   - Full-text log search with filtering
   - Query parameters:
     - `query`: Full-text search string (optional)
     - `start_time`: Start of time range (optional)
     - `end_time`: End of time range (optional)
     - `severity`: Log severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (optional)
     - `service`: Service name filter (optional)
     - `limit`: Max results (1-1000, default: 100)
     - `page_token`: Pagination token (optional)
   - Returns: `LogSearchResponse` with logs, pagination token, and filter info
   - Requires: User authentication

2. **`GET /api/v1/monitoring/logs/{log_id}/context`**
   - Retrieves log context with surrounding entries
   - Query parameters:
     - `timestamp`: Timestamp of target log (required)
     - `context_lines`: Number of lines before/after (1-50, default: 10)
     - `service`: Service name filter (optional)
   - Returns: `LogContextResponse` with before, target, and after logs
   - Requires: User authentication

3. **`GET /api/v1/monitoring/logs/statistics`**
   - Provides log statistics for time ranges
   - Query parameters:
     - `start_time`: Start of time range (required)
     - `end_time`: End of time range (required)
     - `service`: Service name filter (optional)
   - Returns: `LogStatisticsResponse` with counts and severity breakdown
   - Requires: User authentication

#### Response Models:

- **`LogEntryResponse`**: Individual log entry with metadata
- **`LogSearchResponse`**: Search results with pagination
- **`LogContextResponse`**: Context with before/target/after logs
- **`LogStatisticsResponse`**: Aggregate statistics

### 3. Dependencies

**File**: `services/web-api/requirements.txt`

Added:
```
google-cloud-logging==3.9.0
```

### 4. Comprehensive Test Suite

**File**: `services/web-api/tests/test_log_aggregation_service.py`

Created 20 comprehensive tests covering:

#### Test Coverage:

1. **Initialization Tests**
   - Service initialization with project ID
   - Client creation

2. **Search Functionality Tests**
   - Basic log search without filters
   - Time range filtering
   - Severity level filtering
   - Service name filtering
   - Full-text query search
   - Pagination with page tokens
   - Limit validation and correction
   - Error handling

3. **Context Retrieval Tests**
   - Basic context retrieval
   - Service-filtered context
   - Error handling

4. **Statistics Tests**
   - Basic statistics calculation
   - Service-filtered statistics
   - Severity breakdown
   - Error handling

5. **Formatting Tests**
   - String payload formatting
   - Dictionary payload formatting
   - HTTP request metadata extraction

#### Test Approach:
- Uses mocks for Google Cloud Logging client
- Tests both success and error scenarios
- Validates filter construction
- Verifies pagination behavior
- Ensures proper error propagation

## Requirements Satisfied

### Requirement 9: Centralized Log Aggregation

✅ **Acceptance Criteria Met:**

1. **Real-time log collection**: Service connects to Cloud Logging for real-time access
2. **Full-text search**: Implemented with query parameter and regex matching
3. **Multi-dimensional filtering**: Service, severity, and time range filters supported
4. **Log context display**: `get_log_context()` returns surrounding log entries
5. **30-day retention**: Relies on Cloud Logging's default retention (configurable)

## Architecture Integration

### Data Flow:
```
Services → Cloud Logging → LogAggregationService → API Endpoints → Frontend
```

### Key Design Decisions:

1. **Cloud Logging Integration**: Uses Google Cloud Logging client for native GCP integration
2. **Pagination**: Implements token-based pagination for efficient large result handling
3. **Filter Construction**: Builds Cloud Logging filter strings dynamically based on parameters
4. **Error Handling**: Custom exceptions (`LogSearchError`, `LogAggregationError`) for clear error reporting
5. **Format Flexibility**: Handles both string and JSON payloads, extracts HTTP metadata

## Usage Examples

### Search Logs
```python
# Search for errors in the last hour
GET /api/v1/monitoring/logs/search?severity=ERROR&start_time=2024-01-15T10:00:00Z&end_time=2024-01-15T11:00:00Z

# Full-text search
POST /api/v1/monitoring/logs/search
{
  "query": "database connection failed",
  "service": "web-api",
  "limit": 50
}
```

### Get Log Context
```python
# Get 10 lines before and after a specific log
GET /api/v1/monitoring/logs/abc123/context?timestamp=2024-01-15T10:30:00Z&context_lines=10
```

### Get Statistics
```python
# Get log statistics for the last 24 hours
GET /api/v1/monitoring/logs/statistics?start_time=2024-01-14T10:00:00Z&end_time=2024-01-15T10:00:00Z&service=web-api
```

## Security Considerations

1. **Authentication Required**: All endpoints require user authentication via `require_role(Role.USER)`
2. **Rate Limiting**: All endpoints use rate limiting via `rate_limit_dependency`
3. **Input Validation**: Severity patterns validated, limits bounded (1-1000)
4. **Query Escaping**: Special characters in queries are escaped to prevent injection

## Performance Optimizations

1. **Limit Validation**: Automatically corrects invalid limits to prevent excessive queries
2. **Pagination**: Token-based pagination for efficient large dataset handling
3. **Filter Optimization**: Constructs efficient Cloud Logging filter strings
4. **Descending Order**: Returns most recent logs first for faster access to relevant data

## Future Enhancements

1. **Caching**: Add Redis caching for frequently accessed logs
2. **Export**: Add CSV/JSON export functionality
3. **Saved Searches**: Allow users to save and reuse search queries
4. **Real-time Streaming**: WebSocket support for live log tailing
5. **Advanced Filtering**: Support for complex boolean queries
6. **Log Correlation**: Link logs to traces and metrics

## Testing

### Running Tests:
```bash
cd services/web-api
python -m pytest tests/test_log_aggregation_service.py -v
```

### Test Results:
- 20 tests implemented
- Covers all major functionality
- Tests both success and error paths
- Validates filter construction and pagination

## Documentation

- API endpoints documented with OpenAPI/Swagger
- Docstrings for all public methods
- Type hints for all parameters and return values
- Error handling documented

## Deployment Notes

1. **Prerequisites**:
   - Google Cloud Logging API enabled
   - Service account with `logging.viewer` role
   - `google-cloud-logging` package installed

2. **Configuration**:
   - Set `GCP_PROJECT_ID` environment variable
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to service account key

3. **Monitoring**:
   - Log search operations are logged for audit
   - Errors are logged with context for debugging

## Conclusion

Successfully implemented a comprehensive log aggregation service that provides centralized log search, filtering, and context retrieval across all services. The implementation satisfies all acceptance criteria for Requirement 9 and integrates seamlessly with the existing monitoring infrastructure.
