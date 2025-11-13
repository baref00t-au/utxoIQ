"""
Tests for error tracking service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.error_tracking_service import ErrorTrackingService


@pytest.fixture
def mock_error_stats_client():
    """Mock Cloud Error Reporting stats client"""
    with patch('src.services.error_tracking_service.ErrorStatsServiceClient') as mock:
        yield mock.return_value


@pytest.fixture
def mock_error_group_client():
    """Mock Cloud Error Reporting group client"""
    with patch('src.services.error_tracking_service.ErrorGroupServiceClient') as mock:
        yield mock.return_value


@pytest.fixture
def error_tracking_service(mock_error_stats_client, mock_error_group_client):
    """Create error tracking service instance"""
    return ErrorTrackingService(project_id="test-project")


class TestErrorTrackingServiceInitialization:
    """Test error tracking service initialization"""
    
    def test_init_sets_project_id(self, error_tracking_service):
        """Test that initialization sets project ID"""
        assert error_tracking_service.project_id == "test-project"
        assert error_tracking_service.project_name == "projects/test-project"
    
    def test_init_creates_clients(self, mock_error_stats_client, mock_error_group_client):
        """Test that initialization creates Cloud Error Reporting clients"""
        service = ErrorTrackingService(project_id="test-project")
        
        # Verify clients were created
        assert service.error_stats_client is not None
        assert service.error_group_client is not None


class TestListErrorGroups:
    """Test listing error groups"""
    
    @pytest.mark.asyncio
    async def test_list_error_groups_default_time_range(self, error_tracking_service, mock_error_stats_client):
        """Test listing error groups with default time range"""
        # Setup mock error group data
        mock_group = MagicMock()
        mock_group.group.group_id = "group123"
        mock_group.group.name = "projects/test-project/groups/group123"
        mock_group.count = 42
        mock_group.affected_users_count = 5
        mock_group.first_seen_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_group.last_seen_time = datetime(2024, 1, 2, 12, 0, 0)
        mock_group.representative = None
        mock_group.num_affected_services = 1
        mock_group.affected_services = []
        
        mock_error_stats_client.list_group_stats.return_value = [mock_group]
        
        # List error groups
        result = await error_tracking_service.list_error_groups()
        
        # Verify result
        assert result["total_count"] == 1
        assert len(result["error_groups"]) == 1
        assert result["error_groups"][0]["group_id"] == "group123"
        assert result["error_groups"][0]["count"] == 42
        assert result["error_groups"][0]["affected_users_count"] == 5
    
    @pytest.mark.asyncio
    async def test_list_error_groups_with_service_filter(self, error_tracking_service, mock_error_stats_client):
        """Test listing error groups filtered by service"""
        # Setup mock error group data
        mock_group = MagicMock()
        mock_group.group.group_id = "group456"
        mock_group.group.name = "projects/test-project/groups/group456"
        mock_group.count = 10
        mock_group.affected_users_count = 2
        mock_group.first_seen_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_group.last_seen_time = datetime(2024, 1, 1, 13, 0, 0)
        mock_group.representative = None
        mock_group.num_affected_services = 1
        mock_group.affected_services = []
        
        mock_error_stats_client.list_group_stats.return_value = [mock_group]
        
        # List error groups with service filter
        result = await error_tracking_service.list_error_groups(service="web-api")
        
        # Verify result
        assert result["total_count"] == 1
        assert result["error_groups"][0]["group_id"] == "group456"
        
        # Verify service filter was applied
        call_args = mock_error_stats_client.list_group_stats.call_args
        assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_list_error_groups_with_time_range(self, error_tracking_service, mock_error_stats_client):
        """Test listing error groups with custom time range"""
        # Setup mock error group data
        mock_group = MagicMock()
        mock_group.group.group_id = "group789"
        mock_group.group.name = "projects/test-project/groups/group789"
        mock_group.count = 5
        mock_group.affected_users_count = 1
        mock_group.first_seen_time = datetime(2024, 1, 1, 0, 0, 0)
        mock_group.last_seen_time = datetime(2024, 1, 1, 1, 0, 0)
        mock_group.representative = None
        mock_group.num_affected_services = 1
        mock_group.affected_services = []
        
        mock_error_stats_client.list_group_stats.return_value = [mock_group]
        
        # List error groups with custom time range
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        result = await error_tracking_service.list_error_groups(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify result
        assert result["total_count"] == 1
        assert result["error_groups"][0]["group_id"] == "group789"
    
    @pytest.mark.asyncio
    async def test_list_error_groups_with_pagination(self, error_tracking_service, mock_error_stats_client):
        """Test listing error groups with pagination"""
        # Setup mock response with next page token
        mock_response = MagicMock()
        mock_response.next_page_token = "next_page_token_123"
        mock_response.__iter__ = Mock(return_value=iter([]))
        
        mock_error_stats_client.list_group_stats.return_value = mock_response
        
        # List error groups with pagination
        result = await error_tracking_service.list_error_groups(
            page_size=50,
            page_token="current_page_token"
        )
        
        # Verify pagination token is returned
        assert result["next_page_token"] == "next_page_token_123"
    
    @pytest.mark.asyncio
    async def test_list_error_groups_empty_result(self, error_tracking_service, mock_error_stats_client):
        """Test listing error groups with no results"""
        # Setup mock to return empty list
        mock_error_stats_client.list_group_stats.return_value = []
        
        # List error groups
        result = await error_tracking_service.list_error_groups()
        
        # Verify empty result
        assert result["total_count"] == 0
        assert len(result["error_groups"]) == 0


class TestGetErrorGroup:
    """Test getting error group details"""
    
    @pytest.mark.asyncio
    async def test_get_error_group(self, error_tracking_service, mock_error_group_client, mock_error_stats_client):
        """Test getting error group details"""
        # Setup mock error group
        mock_group = MagicMock()
        mock_group.group_id = "group123"
        mock_group.name = "projects/test-project/groups/group123"
        mock_group.tracking_issues = []
        
        mock_error_group_client.get_group.return_value = mock_group
        
        # Setup mock error events
        mock_error_stats_client.list_events.return_value = []
        
        # Get error group
        result = await error_tracking_service.get_error_group("group123")
        
        # Verify result
        assert result["group_id"] == "group123"
        assert result["name"] == "projects/test-project/groups/group123"
        assert "recent_events" in result
        
        # Verify client was called correctly
        mock_error_group_client.get_group.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_error_group_with_tracking_issues(self, error_tracking_service, mock_error_group_client, mock_error_stats_client):
        """Test getting error group with tracking issues"""
        # Setup mock error group with tracking issues
        mock_issue = MagicMock()
        mock_issue.url = "https://github.com/org/repo/issues/123"
        
        mock_group = MagicMock()
        mock_group.group_id = "group456"
        mock_group.name = "projects/test-project/groups/group456"
        mock_group.tracking_issues = [mock_issue]
        
        mock_error_group_client.get_group.return_value = mock_group
        mock_error_stats_client.list_events.return_value = []
        
        # Get error group
        result = await error_tracking_service.get_error_group("group456")
        
        # Verify tracking issues are included
        assert len(result["tracking_issues"]) == 1
        assert result["tracking_issues"][0]["url"] == "https://github.com/org/repo/issues/123"


class TestListErrorEvents:
    """Test listing error events"""
    
    @pytest.mark.asyncio
    async def test_list_error_events(self, error_tracking_service, mock_error_stats_client):
        """Test listing error events for a group"""
        # Setup mock error event
        mock_event = MagicMock()
        mock_event.event_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_event.message = "Test error message"
        
        mock_error_stats_client.list_events.return_value = [mock_event]
        
        # List error events
        result = await error_tracking_service.list_error_events("group123")
        
        # Verify result
        assert len(result["error_events"]) == 1
        assert result["error_events"][0]["message"] == "Test error message"
        
        # Verify client was called correctly
        mock_error_stats_client.list_events.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_error_events_with_pagination(self, error_tracking_service, mock_error_stats_client):
        """Test listing error events with pagination"""
        # Setup mock response with next page token
        mock_response = MagicMock()
        mock_response.next_page_token = "next_token"
        mock_response.__iter__ = Mock(return_value=iter([]))
        
        mock_error_stats_client.list_events.return_value = mock_response
        
        # List error events with pagination
        result = await error_tracking_service.list_error_events(
            "group123",
            page_size=50,
            page_token="current_token"
        )
        
        # Verify pagination token is returned
        assert result["next_page_token"] == "next_token"
    
    @pytest.mark.asyncio
    async def test_list_error_events_empty_result(self, error_tracking_service, mock_error_stats_client):
        """Test listing error events with no results"""
        # Setup mock to return empty list
        mock_error_stats_client.list_events.return_value = []
        
        # List error events
        result = await error_tracking_service.list_error_events("group123")
        
        # Verify empty result
        assert len(result["error_events"]) == 0


class TestGetErrorStatistics:
    """Test getting error statistics"""
    
    @pytest.mark.asyncio
    async def test_get_error_statistics(self, error_tracking_service, mock_error_stats_client):
        """Test getting error statistics"""
        # Setup mock error groups
        mock_group1 = MagicMock()
        mock_group1.group.group_id = "group1"
        mock_group1.group.name = "projects/test-project/groups/group1"
        mock_group1.count = 100
        mock_group1.affected_users_count = 10
        mock_group1.first_seen_time = datetime(2024, 1, 1, 0, 0, 0)
        mock_group1.last_seen_time = datetime(2024, 1, 7, 0, 0, 0)
        mock_group1.representative = None
        mock_group1.num_affected_services = 1
        mock_group1.affected_services = []
        
        mock_group2 = MagicMock()
        mock_group2.group.group_id = "group2"
        mock_group2.group.name = "projects/test-project/groups/group2"
        mock_group2.count = 50
        mock_group2.affected_users_count = 5
        mock_group2.first_seen_time = datetime(2024, 1, 2, 0, 0, 0)
        mock_group2.last_seen_time = datetime(2024, 1, 7, 0, 0, 0)
        mock_group2.representative = None
        mock_group2.num_affected_services = 1
        mock_group2.affected_services = []
        
        mock_error_stats_client.list_group_stats.return_value = [mock_group1, mock_group2]
        
        # Get error statistics
        result = await error_tracking_service.get_error_statistics()
        
        # Verify statistics
        assert result["total_errors"] == 150  # 100 + 50
        assert result["unique_error_groups"] == 2
        assert result["affected_users"] == 15  # 10 + 5
        assert len(result["top_errors"]) == 2
        assert result["top_errors"][0]["count"] == 100  # Sorted by count
        assert result["top_errors"][1]["count"] == 50
    
    @pytest.mark.asyncio
    async def test_get_error_statistics_with_service_filter(self, error_tracking_service, mock_error_stats_client):
        """Test getting error statistics filtered by service"""
        # Setup mock error group
        mock_group = MagicMock()
        mock_group.group.group_id = "group1"
        mock_group.group.name = "projects/test-project/groups/group1"
        mock_group.count = 25
        mock_group.affected_users_count = 3
        mock_group.first_seen_time = datetime(2024, 1, 1, 0, 0, 0)
        mock_group.last_seen_time = datetime(2024, 1, 7, 0, 0, 0)
        mock_group.representative = None
        mock_group.num_affected_services = 1
        mock_group.affected_services = []
        
        mock_error_stats_client.list_group_stats.return_value = [mock_group]
        
        # Get error statistics with service filter
        result = await error_tracking_service.get_error_statistics(service="web-api")
        
        # Verify statistics
        assert result["total_errors"] == 25
        assert result["unique_error_groups"] == 1
        assert result["affected_users"] == 3
        assert result["service_filter"] == "web-api"
    
    @pytest.mark.asyncio
    async def test_get_error_statistics_empty_result(self, error_tracking_service, mock_error_stats_client):
        """Test getting error statistics with no errors"""
        # Setup mock to return empty list
        mock_error_stats_client.list_group_stats.return_value = []
        
        # Get error statistics
        result = await error_tracking_service.get_error_statistics()
        
        # Verify empty statistics
        assert result["total_errors"] == 0
        assert result["unique_error_groups"] == 0
        assert result["affected_users"] == 0
        assert len(result["top_errors"]) == 0


class TestFormatErrorEvent:
    """Test error event formatting"""
    
    def test_format_error_event_basic(self, error_tracking_service):
        """Test formatting basic error event"""
        # Setup mock event
        mock_event = MagicMock()
        mock_event.event_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_event.message = "Test error"
        
        # Format event
        result = error_tracking_service._format_error_event(mock_event)
        
        # Verify formatting
        assert result["event_time"] == "2024-01-01T12:00:00"
        assert result["message"] == "Test error"
    
    def test_format_error_event_with_service_context(self, error_tracking_service):
        """Test formatting error event with service context"""
        # Setup mock event with service context
        mock_service_context = MagicMock()
        mock_service_context.service = "web-api"
        mock_service_context.version = "1.0.0"
        
        mock_event = MagicMock()
        mock_event.event_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_event.message = "Test error"
        mock_event.service_context = mock_service_context
        
        # Format event
        result = error_tracking_service._format_error_event(mock_event)
        
        # Verify service context is included
        assert "service_context" in result
        assert result["service_context"]["service"] == "web-api"
        assert result["service_context"]["version"] == "1.0.0"
    
    def test_format_error_event_with_http_request(self, error_tracking_service):
        """Test formatting error event with HTTP request context"""
        # Setup mock event with HTTP request
        mock_http_request = MagicMock()
        mock_http_request.method = "GET"
        mock_http_request.url = "https://api.example.com/test"
        mock_http_request.user_agent = "Mozilla/5.0"
        mock_http_request.referrer = "https://example.com"
        mock_http_request.response_status_code = 500
        
        mock_context = MagicMock()
        mock_context.http_request = mock_http_request
        
        mock_event = MagicMock()
        mock_event.event_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_event.message = "Test error"
        mock_event.context = mock_context
        
        # Format event
        result = error_tracking_service._format_error_event(mock_event)
        
        # Verify HTTP request context is included
        assert "context" in result
        assert "http_request" in result["context"]
        assert result["context"]["http_request"]["method"] == "GET"
        assert result["context"]["http_request"]["url"] == "https://api.example.com/test"
        assert result["context"]["http_request"]["response_status_code"] == 500
    
    def test_format_error_event_with_report_location(self, error_tracking_service):
        """Test formatting error event with report location"""
        # Setup mock event with report location
        mock_report_location = MagicMock()
        mock_report_location.file_path = "/app/src/main.py"
        mock_report_location.line_number = 42
        mock_report_location.function_name = "process_request"
        
        mock_context = MagicMock()
        mock_context.report_location = mock_report_location
        
        mock_event = MagicMock()
        mock_event.event_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_event.message = "Test error"
        mock_event.context = mock_context
        
        # Format event
        result = error_tracking_service._format_error_event(mock_event)
        
        # Verify report location is included
        assert "context" in result
        assert "report_location" in result["context"]
        assert result["context"]["report_location"]["file_path"] == "/app/src/main.py"
        assert result["context"]["report_location"]["line_number"] == 42
        assert result["context"]["report_location"]["function_name"] == "process_request"


class TestAsyncContextManager:
    """Test async context manager"""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, mock_error_stats_client, mock_error_group_client):
        """Test using service as async context manager"""
        async with ErrorTrackingService(project_id="test-project") as service:
            assert service.project_id == "test-project"
        
        # Service should be properly closed after context exit
        # (No explicit close needed for current Cloud clients)
