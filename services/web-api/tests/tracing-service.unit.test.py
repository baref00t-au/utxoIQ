"""
Tests for distributed tracing service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4

from src.services.tracing_service import TracingService


@pytest.fixture
def mock_trace_client():
    """Mock Cloud Trace client"""
    with patch('src.services.tracing_service.trace_v2.TraceServiceClient') as mock:
        yield mock.return_value


@pytest.fixture
def mock_tracer():
    """Mock OpenTelemetry tracer"""
    with patch('src.services.tracing_service.trace') as mock:
        yield mock


@pytest.fixture
def tracing_service(mock_trace_client, mock_tracer):
    """Create tracing service instance"""
    return TracingService(project_id="test-project", service_name="test-service")


class TestTracingServiceInitialization:
    """Test tracing service initialization"""
    
    def test_init_sets_project_id(self, tracing_service):
        """Test that initialization sets project ID"""
        assert tracing_service.project_id == "test-project"
        assert tracing_service.service_name == "test-service"
        assert tracing_service.project_name == "projects/test-project"
    
    def test_init_configures_tracer_provider(self, mock_tracer):
        """Test that initialization configures OpenTelemetry tracer provider"""
        TracingService(project_id="test-project", service_name="test-service")
        
        # Verify tracer provider was set
        mock_tracer.set_tracer_provider.assert_called_once()
        
        # Verify tracer was obtained
        mock_tracer.get_tracer.assert_called_once_with("test-service")


class TestTraceRequestDecorator:
    """Test trace_request decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_traces_async_function(self, tracing_service, mock_tracer):
        """Test that decorator traces async function execution"""
        # Setup mock span
        mock_span = MagicMock()
        mock_span.__enter__ = Mock(return_value=mock_span)
        mock_span.__exit__ = Mock(return_value=False)
        tracing_service.tracer.start_as_current_span = Mock(return_value=mock_span)
        
        # Create decorated function
        @tracing_service.trace_request()
        async def test_function():
            return "success"
        
        # Execute function
        result = await test_function()
        
        # Verify result
        assert result == "success"
        
        # Verify span was created
        tracing_service.tracer.start_as_current_span.assert_called_once_with("test_function")
        
        # Verify attributes were set
        mock_span.set_attribute.assert_any_call("function", "test_function")
        mock_span.set_attribute.assert_any_call("service", "test-service")
        mock_span.set_attribute.assert_any_call("status", "success")
    
    @pytest.mark.asyncio
    async def test_decorator_handles_async_function_errors(self, tracing_service):
        """Test that decorator handles errors in async functions"""
        # Setup mock span
        mock_span = MagicMock()
        mock_span.__enter__ = Mock(return_value=mock_span)
        mock_span.__exit__ = Mock(return_value=False)
        tracing_service.tracer.start_as_current_span = Mock(return_value=mock_span)
        
        # Create decorated function that raises error
        @tracing_service.trace_request()
        async def test_function():
            raise ValueError("Test error")
        
        # Execute function and expect error
        with pytest.raises(ValueError, match="Test error"):
            await test_function()
        
        # Verify error attributes were set
        mock_span.set_attribute.assert_any_call("status", "error")
        mock_span.set_attribute.assert_any_call("error.type", "ValueError")
        mock_span.set_attribute.assert_any_call("error.message", "Test error")
    
    def test_decorator_traces_sync_function(self, tracing_service):
        """Test that decorator traces sync function execution"""
        # Setup mock span
        mock_span = MagicMock()
        mock_span.__enter__ = Mock(return_value=mock_span)
        mock_span.__exit__ = Mock(return_value=False)
        tracing_service.tracer.start_as_current_span = Mock(return_value=mock_span)
        
        # Create decorated function
        @tracing_service.trace_request()
        def test_function():
            return "success"
        
        # Execute function
        result = test_function()
        
        # Verify result
        assert result == "success"
        
        # Verify span was created
        tracing_service.tracer.start_as_current_span.assert_called_once_with("test_function")
    
    def test_decorator_with_custom_span_name(self, tracing_service):
        """Test decorator with custom span name"""
        # Setup mock span
        mock_span = MagicMock()
        mock_span.__enter__ = Mock(return_value=mock_span)
        mock_span.__exit__ = Mock(return_value=False)
        tracing_service.tracer.start_as_current_span = Mock(return_value=mock_span)
        
        # Create decorated function with custom name
        @tracing_service.trace_request(span_name="custom_span")
        def test_function():
            return "success"
        
        # Execute function
        test_function()
        
        # Verify custom span name was used
        tracing_service.tracer.start_as_current_span.assert_called_once_with("custom_span")


class TestSpanAttributes:
    """Test span attribute management"""
    
    def test_add_span_attributes(self, tracing_service, mock_tracer):
        """Test adding attributes to current span"""
        # Setup mock span
        mock_span = MagicMock()
        mock_tracer.get_current_span.return_value = mock_span
        
        # Add attributes
        attributes = {
            "http.method": "GET",
            "http.path": "/api/test",
            "user_id": "123"
        }
        tracing_service.add_span_attributes(attributes)
        
        # Verify attributes were set
        assert mock_span.set_attribute.call_count == 3
        mock_span.set_attribute.assert_any_call("http.method", "GET")
        mock_span.set_attribute.assert_any_call("http.path", "/api/test")
        mock_span.set_attribute.assert_any_call("user_id", "123")
    
    def test_add_span_attributes_no_current_span(self, tracing_service, mock_tracer):
        """Test adding attributes when no current span exists"""
        # Setup mock to return None
        mock_tracer.get_current_span.return_value = None
        
        # Should not raise error
        tracing_service.add_span_attributes({"key": "value"})
    
    def test_add_span_event(self, tracing_service, mock_tracer):
        """Test adding event to current span"""
        # Setup mock span
        mock_span = MagicMock()
        mock_tracer.get_current_span.return_value = mock_span
        
        # Add event
        tracing_service.add_span_event("test_event", {"detail": "test"})
        
        # Verify event was added
        mock_span.add_event.assert_called_once_with("test_event", {"detail": "test"})
    
    def test_add_span_event_no_attributes(self, tracing_service, mock_tracer):
        """Test adding event without attributes"""
        # Setup mock span
        mock_span = MagicMock()
        mock_tracer.get_current_span.return_value = mock_span
        
        # Add event without attributes
        tracing_service.add_span_event("test_event")
        
        # Verify event was added with empty dict
        mock_span.add_event.assert_called_once_with("test_event", {})


class TestTraceRetrieval:
    """Test trace retrieval from Cloud Trace"""
    
    @pytest.mark.asyncio
    async def test_get_trace(self, tracing_service, mock_trace_client):
        """Test retrieving a trace by ID"""
        # Setup mock trace data
        mock_span = MagicMock()
        mock_span.span_id = "span123"
        mock_span.display_name = MagicMock(value="test_span")
        mock_span.start_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_span.end_time = datetime(2024, 1, 1, 12, 0, 1)
        mock_span.parent_span_id = None
        
        mock_trace = MagicMock()
        mock_trace.name = "projects/test-project/traces/trace123"
        mock_trace.project_id = "test-project"
        mock_trace.spans = [mock_span]
        
        mock_trace_client.get_trace.return_value = mock_trace
        
        # Get trace
        result = await tracing_service.get_trace("trace123")
        
        # Verify result
        assert result["trace_id"] == "trace123"
        assert result["project_id"] == "test-project"
        assert result["span_count"] == 1
        assert len(result["spans"]) == 1
        assert result["spans"][0]["span_id"] == "span123"
        
        # Verify client was called correctly
        mock_trace_client.get_trace.assert_called_once_with(
            name="projects/test-project/traces/trace123"
        )
    
    @pytest.mark.asyncio
    async def test_get_trace_error(self, tracing_service, mock_trace_client):
        """Test error handling when retrieving trace"""
        # Setup mock to raise error
        mock_trace_client.get_trace.side_effect = Exception("Trace not found")
        
        # Attempt to get trace
        with pytest.raises(Exception, match="Trace not found"):
            await tracing_service.get_trace("invalid_trace")
    
    @pytest.mark.asyncio
    async def test_list_traces(self, tracing_service, mock_trace_client):
        """Test listing traces within time range"""
        # Setup mock trace data
        mock_trace1 = MagicMock()
        mock_trace1.name = "projects/test-project/traces/trace1"
        mock_trace1.project_id = "test-project"
        mock_trace1.spans = [MagicMock(), MagicMock()]
        
        mock_trace2 = MagicMock()
        mock_trace2.name = "projects/test-project/traces/trace2"
        mock_trace2.project_id = "test-project"
        mock_trace2.spans = [MagicMock()]
        
        mock_trace_client.list_traces.return_value = [mock_trace1, mock_trace2]
        
        # List traces
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 2, 0, 0, 0)
        
        result = await tracing_service.list_traces(
            start_time=start_time,
            end_time=end_time,
            page_size=100
        )
        
        # Verify result
        assert len(result) == 2
        assert result[0]["trace_id"] == "trace1"
        assert result[0]["span_count"] == 2
        assert result[1]["trace_id"] == "trace2"
        assert result[1]["span_count"] == 1


class TestTraceContext:
    """Test trace context management"""
    
    def test_get_current_trace_id(self, tracing_service, mock_tracer):
        """Test getting current trace ID"""
        # Setup mock span with valid context
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = True
        mock_context.trace_id = 12345678901234567890123456789012
        mock_span.get_span_context.return_value = mock_context
        mock_tracer.get_current_span.return_value = mock_span
        
        # Get trace ID
        trace_id = tracing_service.get_current_trace_id()
        
        # Verify trace ID is formatted correctly (32 hex chars)
        assert trace_id is not None
        assert len(trace_id) == 32
    
    def test_get_current_trace_id_no_span(self, tracing_service, mock_tracer):
        """Test getting trace ID when no current span"""
        # Setup mock to return None
        mock_tracer.get_current_span.return_value = None
        
        # Get trace ID
        trace_id = tracing_service.get_current_trace_id()
        
        # Should return None
        assert trace_id is None
    
    def test_get_current_span_id(self, tracing_service, mock_tracer):
        """Test getting current span ID"""
        # Setup mock span with valid context
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = True
        mock_context.span_id = 1234567890123456
        mock_span.get_span_context.return_value = mock_context
        mock_tracer.get_current_span.return_value = mock_span
        
        # Get span ID
        span_id = tracing_service.get_current_span_id()
        
        # Verify span ID is formatted correctly (16 hex chars)
        assert span_id is not None
        assert len(span_id) == 16
    
    def test_get_current_span_id_no_span(self, tracing_service, mock_tracer):
        """Test getting span ID when no current span"""
        # Setup mock to return None
        mock_tracer.get_current_span.return_value = None
        
        # Get span ID
        span_id = tracing_service.get_current_span_id()
        
        # Should return None
        assert span_id is None


class TestFastAPIInstrumentation:
    """Test FastAPI instrumentation"""
    
    def test_instrument_fastapi(self, tracing_service):
        """Test instrumenting FastAPI application"""
        # Create mock FastAPI app
        mock_app = MagicMock()
        
        # Instrument app
        with patch('src.services.tracing_service.FastAPIInstrumentor') as mock_instrumentor:
            tracing_service.instrument_fastapi(mock_app)
            
            # Verify instrumentation was called
            mock_instrumentor.instrument_app.assert_called_once_with(mock_app)
