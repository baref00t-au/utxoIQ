"""
Tests for Log Aggregation Service

Tests log search, filtering, and context retrieval functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.services.log_aggregation_service import (
    LogAggregationService,
    LogSearchError,
    LogAggregationError
)


@pytest.fixture
def mock_logging_client():
    """Mock Google Cloud Logging client"""
    with patch('src.services.log_aggregation_service.logging.Client') as mock_client:
        yield mock_client


@pytest.fixture
def log_service(mock_logging_client):
    """Create LogAggregationService instance with mocked client"""
    service = LogAggregationService(project_id="test-project")
    return service


@pytest.fixture
def sample_log_entry():
    """Create a sample log entry mock"""
    entry = Mock()
    entry.insert_id = "test-log-id-123"
    entry.timestamp = datetime(2024, 1, 15, 10, 30, 0)
    entry.severity = "INFO"
    entry.payload = "Test log message"
    entry.trace = "projects/test-project/traces/abc123"
    entry.span_id = "span123"
    
    # Mock resource
    entry.resource = Mock()
    entry.resource.type = "cloud_run_revision"
    entry.resource.labels = {"service_name": "web-api", "location": "us-central1"}
    
    # Mock labels
    entry.labels = {"environment": "test", "version": "1.0.0"}
    
    return entry


class TestLogAggregationService:
    """Test suite for LogAggregationService"""
    
    def test_initialization(self, log_service):
        """Test service initialization"""
        assert log_service.project_id == "test-project"
        assert log_service.client is not None
    
    @pytest.mark.asyncio
    async def test_search_logs_basic(self, log_service, sample_log_entry):
        """Test basic log search without filters"""
        # Mock list_entries to return sample logs
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = None
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute search
        result = await log_service.search_logs(limit=100)
        
        # Verify results
        assert "logs" in result
        assert "next_page_token" in result
        assert "total_count" in result
        assert len(result["logs"]) == 1
        assert result["logs"][0]["log_id"] == "test-log-id-123"
        assert result["logs"][0]["severity"] == "INFO"
        assert result["logs"][0]["message"] == "Test log message"
    
    @pytest.mark.asyncio
    async def test_search_logs_with_time_range(self, log_service, sample_log_entry):
        """Test log search with time range filters"""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 11, 0, 0)
        
        # Mock list_entries
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = None
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute search
        result = await log_service.search_logs(
            start_time=start_time,
            end_time=end_time,
            limit=100
        )
        
        # Verify filter was constructed correctly
        call_args = log_service.client.list_entries.call_args
        filter_str = call_args.kwargs.get('filter_')
        
        assert 'timestamp >=' in filter_str
        assert 'timestamp <=' in filter_str
        assert len(result["logs"]) == 1
    
    @pytest.mark.asyncio
    async def test_search_logs_with_severity_filter(self, log_service, sample_log_entry):
        """Test log search with severity filter"""
        # Mock list_entries
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = None
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute search with severity filter
        result = await log_service.search_logs(severity="ERROR", limit=100)
        
        # Verify filter includes severity
        call_args = log_service.client.list_entries.call_args
        filter_str = call_args.kwargs.get('filter_')
        
        assert 'severity = "ERROR"' in filter_str
    
    @pytest.mark.asyncio
    async def test_search_logs_with_service_filter(self, log_service, sample_log_entry):
        """Test log search with service name filter"""
        # Mock list_entries
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = None
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute search with service filter
        result = await log_service.search_logs(service="web-api", limit=100)
        
        # Verify filter includes service
        call_args = log_service.client.list_entries.call_args
        filter_str = call_args.kwargs.get('filter_')
        
        assert 'resource.labels.service_name = "web-api"' in filter_str
    
    @pytest.mark.asyncio
    async def test_search_logs_with_full_text_query(self, log_service, sample_log_entry):
        """Test log search with full-text query"""
        # Mock list_entries
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = None
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute search with query
        result = await log_service.search_logs(query="error occurred", limit=100)
        
        # Verify filter includes text search
        call_args = log_service.client.list_entries.call_args
        filter_str = call_args.kwargs.get('filter_')
        
        assert 'textPayload =~' in filter_str
        assert 'error occurred' in filter_str
    
    @pytest.mark.asyncio
    async def test_search_logs_with_pagination(self, log_service, sample_log_entry):
        """Test log search with pagination"""
        # Mock list_entries with next page token
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = "next-page-token-123"
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute search
        result = await log_service.search_logs(
            limit=100,
            page_token="current-page-token"
        )
        
        # Verify pagination token is returned
        assert result["next_page_token"] == "next-page-token-123"
        
        # Verify page token was passed to list_entries
        call_args = log_service.client.list_entries.call_args
        assert call_args.kwargs.get('page_token') == "current-page-token"
    
    @pytest.mark.asyncio
    async def test_search_logs_limit_validation(self, log_service, sample_log_entry):
        """Test that invalid limits are corrected"""
        # Mock list_entries
        mock_page = [sample_log_entry]
        mock_entries = Mock()
        mock_entries.pages = Mock()
        mock_entries.pages.__next__ = Mock(return_value=iter(mock_page))
        mock_entries.next_page_token = None
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Test with limit too high
        result = await log_service.search_logs(limit=5000)
        call_args = log_service.client.list_entries.call_args
        assert call_args.kwargs.get('max_results') == 100  # Should be corrected to 100
        
        # Test with limit too low
        result = await log_service.search_logs(limit=0)
        call_args = log_service.client.list_entries.call_args
        assert call_args.kwargs.get('max_results') == 100  # Should be corrected to 100
    
    @pytest.mark.asyncio
    async def test_search_logs_error_handling(self, log_service):
        """Test error handling in log search"""
        # Mock list_entries to raise an exception
        log_service.client.list_entries = Mock(side_effect=Exception("API error"))
        
        # Execute search and expect error
        with pytest.raises(LogSearchError) as exc_info:
            await log_service.search_logs(limit=100)
        
        assert "Failed to search logs" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_log_context(self, log_service, sample_log_entry):
        """Test retrieving log context"""
        target_timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        # Create mock entries for before, target, and after
        before_entry = Mock()
        before_entry.insert_id = "before-log-id"
        before_entry.timestamp = datetime(2024, 1, 15, 10, 29, 50)
        before_entry.severity = "INFO"
        before_entry.payload = "Before log"
        before_entry.resource = Mock()
        before_entry.resource.type = "cloud_run_revision"
        before_entry.resource.labels = {}
        before_entry.labels = {}
        before_entry.trace = None
        before_entry.span_id = None
        
        after_entry = Mock()
        after_entry.insert_id = "after-log-id"
        after_entry.timestamp = datetime(2024, 1, 15, 10, 30, 10)
        after_entry.severity = "INFO"
        after_entry.payload = "After log"
        after_entry.resource = Mock()
        after_entry.resource.type = "cloud_run_revision"
        after_entry.resource.labels = {}
        after_entry.labels = {}
        after_entry.trace = None
        after_entry.span_id = None
        
        # Mock list_entries for before, target, and after queries
        def mock_list_entries(filter_=None, order_by=None, max_results=None):
            mock_entries = Mock()
            if "timestamp <" in filter_:
                # Before logs
                mock_entries.__iter__ = Mock(return_value=iter([before_entry]))
            elif "timestamp >" in filter_:
                # After logs
                mock_entries.__iter__ = Mock(return_value=iter([after_entry]))
            elif "insertId" in filter_:
                # Target log
                mock_entries.__iter__ = Mock(return_value=iter([sample_log_entry]))
            else:
                mock_entries.__iter__ = Mock(return_value=iter([]))
            return mock_entries
        
        log_service.client.list_entries = Mock(side_effect=mock_list_entries)
        
        # Execute get_log_context
        result = await log_service.get_log_context(
            target_log_id="test-log-id-123",
            target_timestamp=target_timestamp,
            context_lines=10
        )
        
        # Verify results
        assert "before" in result
        assert "target" in result
        assert "after" in result
        assert len(result["before"]) == 1
        assert len(result["after"]) == 1
        assert result["target"]["log_id"] == "test-log-id-123"
        assert result["target"]["is_target"] is True
        assert result["context_lines"] == 10
    
    @pytest.mark.asyncio
    async def test_get_log_context_with_service_filter(self, log_service, sample_log_entry):
        """Test log context retrieval with service filter"""
        target_timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        # Mock list_entries
        def mock_list_entries(filter_=None, order_by=None, max_results=None):
            mock_entries = Mock()
            mock_entries.__iter__ = Mock(return_value=iter([]))
            return mock_entries
        
        log_service.client.list_entries = Mock(side_effect=mock_list_entries)
        
        # Execute with service filter
        result = await log_service.get_log_context(
            target_log_id="test-log-id-123",
            target_timestamp=target_timestamp,
            context_lines=10,
            service="web-api"
        )
        
        # Verify service filter was applied
        calls = log_service.client.list_entries.call_args_list
        
        # Check that service filter appears in the calls
        service_filter_found = False
        for call in calls:
            filter_str = call.kwargs.get('filter_', '')
            if 'resource.labels.service_name = "web-api"' in filter_str:
                service_filter_found = True
                break
        
        assert service_filter_found
    
    @pytest.mark.asyncio
    async def test_get_log_context_error_handling(self, log_service):
        """Test error handling in log context retrieval"""
        # Mock list_entries to raise an exception
        log_service.client.list_entries = Mock(side_effect=Exception("API error"))
        
        # Execute and expect error
        with pytest.raises(LogSearchError) as exc_info:
            await log_service.get_log_context(
                target_log_id="test-log-id",
                target_timestamp=datetime.utcnow(),
                context_lines=10
            )
        
        assert "Failed to retrieve log context" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_log_statistics(self, log_service, sample_log_entry):
        """Test log statistics calculation"""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 11, 0, 0)
        
        # Create mock entries with different severities
        info_entry = Mock()
        info_entry.severity = "INFO"
        
        error_entry = Mock()
        error_entry.severity = "ERROR"
        
        warning_entry = Mock()
        warning_entry.severity = "WARNING"
        
        # Mock list_entries to return sample logs
        mock_entries = Mock()
        mock_entries.__iter__ = Mock(return_value=iter([info_entry, error_entry, warning_entry]))
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute statistics query
        result = await log_service.get_log_statistics(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify results
        assert "total_count" in result
        assert "severity_counts" in result
        assert "time_range" in result
        assert result["total_count"] == 3
        assert result["severity_counts"]["INFO"] == 1
        assert result["severity_counts"]["ERROR"] == 1
        assert result["severity_counts"]["WARNING"] == 1
    
    @pytest.mark.asyncio
    async def test_get_log_statistics_with_service_filter(self, log_service, sample_log_entry):
        """Test log statistics with service filter"""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 11, 0, 0)
        
        # Mock list_entries
        mock_entries = Mock()
        mock_entries.__iter__ = Mock(return_value=iter([sample_log_entry]))
        
        log_service.client.list_entries = Mock(return_value=mock_entries)
        
        # Execute with service filter
        result = await log_service.get_log_statistics(
            start_time=start_time,
            end_time=end_time,
            service="web-api"
        )
        
        # Verify service filter was applied
        call_args = log_service.client.list_entries.call_args
        filter_str = call_args.kwargs.get('filter_')
        
        assert 'resource.labels.service_name = "web-api"' in filter_str
        assert result["service"] == "web-api"
    
    @pytest.mark.asyncio
    async def test_get_log_statistics_error_handling(self, log_service):
        """Test error handling in statistics calculation"""
        # Mock list_entries to raise an exception
        log_service.client.list_entries = Mock(side_effect=Exception("API error"))
        
        # Execute and expect error
        with pytest.raises(LogSearchError) as exc_info:
            await log_service.get_log_statistics(
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow()
            )
        
        assert "Failed to get log statistics" in str(exc_info.value)
    
    def test_format_log_entry_with_string_payload(self, log_service):
        """Test formatting log entry with string payload"""
        entry = Mock()
        entry.insert_id = "test-id"
        entry.timestamp = datetime(2024, 1, 15, 10, 30, 0)
        entry.severity = "INFO"
        entry.payload = "Simple log message"
        entry.trace = None
        entry.span_id = None
        entry.resource = Mock()
        entry.resource.type = "cloud_run_revision"
        entry.resource.labels = {"service_name": "web-api"}
        entry.labels = {"env": "prod"}
        
        formatted = log_service._format_log_entry(entry)
        
        assert formatted["log_id"] == "test-id"
        assert formatted["severity"] == "INFO"
        assert formatted["message"] == "Simple log message"
        assert "json_payload" not in formatted
    
    def test_format_log_entry_with_dict_payload(self, log_service):
        """Test formatting log entry with dictionary payload"""
        entry = Mock()
        entry.insert_id = "test-id"
        entry.timestamp = datetime(2024, 1, 15, 10, 30, 0)
        entry.severity = "ERROR"
        entry.payload = {"message": "Error occurred", "error_code": 500}
        entry.trace = None
        entry.span_id = None
        entry.resource = Mock()
        entry.resource.type = "cloud_run_revision"
        entry.resource.labels = {}
        entry.labels = {}
        
        formatted = log_service._format_log_entry(entry)
        
        assert formatted["log_id"] == "test-id"
        assert formatted["severity"] == "ERROR"
        assert formatted["message"] == "Error occurred"
        assert formatted["json_payload"] == {"message": "Error occurred", "error_code": 500}
    
    def test_format_log_entry_with_http_request(self, log_service):
        """Test formatting log entry with HTTP request info"""
        entry = Mock()
        entry.insert_id = "test-id"
        entry.timestamp = datetime(2024, 1, 15, 10, 30, 0)
        entry.severity = "INFO"
        entry.payload = "HTTP request"
        entry.trace = None
        entry.span_id = None
        entry.resource = Mock()
        entry.resource.type = "cloud_run_revision"
        entry.resource.labels = {}
        entry.labels = {}
        
        # Mock HTTP request
        entry.http_request = Mock()
        entry.http_request.request_method = "GET"
        entry.http_request.request_url = "/api/v1/test"
        entry.http_request.status = 200
        entry.http_request.user_agent = "Mozilla/5.0"
        
        formatted = log_service._format_log_entry(entry)
        
        assert "http_request" in formatted
        assert formatted["http_request"]["method"] == "GET"
        assert formatted["http_request"]["url"] == "/api/v1/test"
        assert formatted["http_request"]["status"] == 200
