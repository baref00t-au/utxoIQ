"""
Distributed Tracing Service for utxoIQ Platform

This service provides distributed tracing capabilities using OpenTelemetry
and Google Cloud Trace for tracking requests across multiple services.
"""

import logging
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from google.cloud import trace_v2
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)


class TracingService:
    """Service for managing distributed tracing with Cloud Trace"""
    
    def __init__(self, project_id: str, service_name: str = "web-api"):
        """
        Initialize the tracing service
        
        Args:
            project_id: GCP project ID
            service_name: Name of the service for trace identification
        """
        self.project_id = project_id
        self.service_name = service_name
        self.project_name = f"projects/{project_id}"
        
        # Set up OpenTelemetry with Cloud Trace exporter
        trace.set_tracer_provider(TracerProvider())
        cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(cloud_trace_exporter)
        )
        
        # Get tracer instance
        self.tracer = trace.get_tracer(service_name)
        
        # Initialize Cloud Trace client for reading traces
        self.trace_client = trace_v2.TraceServiceClient()
        
        logger.info(f"TracingService initialized for project {project_id}")
    
    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application with automatic tracing
        
        Args:
            app: FastAPI application instance
        """
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI application instrumented with tracing")
    
    def trace_request(self, span_name: Optional[str] = None):
        """
        Decorator to trace function execution
        
        Args:
            span_name: Optional custom span name (defaults to function name)
        
        Returns:
            Decorated function with tracing
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                name = span_name or func.__name__
                with self.tracer.start_as_current_span(name) as span:
                    # Add function metadata
                    span.set_attribute("function", func.__name__)
                    span.set_attribute("service", self.service_name)
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("status", "success")
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_attribute("status", "error")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.set_status(
                            Status(StatusCode.ERROR, description=str(e))
                        )
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                name = span_name or func.__name__
                with self.tracer.start_as_current_span(name) as span:
                    # Add function metadata
                    span.set_attribute("function", func.__name__)
                    span.set_attribute("service", self.service_name)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("status", "success")
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_attribute("status", "error")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.set_status(
                            Status(StatusCode.ERROR, description=str(e))
                        )
                        raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def add_span_attributes(self, attributes: Dict[str, Any]):
        """
        Add custom attributes to the current span
        
        Args:
            attributes: Dictionary of attribute key-value pairs
        """
        current_span = trace.get_current_span()
        if current_span:
            for key, value in attributes.items():
                current_span.set_attribute(key, str(value))
    
    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to the current span
        
        Args:
            name: Event name
            attributes: Optional event attributes
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes or {})
    
    async def get_trace(self, trace_id: str) -> Dict:
        """
        Retrieve trace details from Cloud Trace
        
        Args:
            trace_id: The trace ID to retrieve
            
        Returns:
            Formatted trace data with spans
        """
        try:
            trace_name = f"{self.project_name}/traces/{trace_id}"
            trace_data = self.trace_client.get_trace(name=trace_name)
            return self._format_trace(trace_data)
        except Exception as e:
            logger.error(f"Error retrieving trace {trace_id}: {e}")
            raise
    
    async def list_traces(
        self,
        start_time: datetime,
        end_time: datetime,
        filter_str: Optional[str] = None,
        page_size: int = 100
    ) -> List[Dict]:
        """
        List traces within a time range
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            filter_str: Optional filter string
            page_size: Number of traces per page
            
        Returns:
            List of trace summaries
        """
        try:
            request = trace_v2.ListTracesRequest(
                parent=self.project_name,
                start_time=start_time,
                end_time=end_time,
                filter=filter_str,
                page_size=page_size
            )
            
            traces = []
            for trace_data in self.trace_client.list_traces(request=request):
                traces.append(self._format_trace_summary(trace_data))
            
            return traces
        except Exception as e:
            logger.error(f"Error listing traces: {e}")
            raise
    
    def _format_trace(self, trace_data) -> Dict:
        """
        Format trace data for API response
        
        Args:
            trace_data: Raw trace data from Cloud Trace
            
        Returns:
            Formatted trace dictionary
        """
        spans = []
        for span in trace_data.spans:
            spans.append({
                "span_id": span.span_id,
                "name": span.display_name.value if hasattr(span.display_name, 'value') else str(span.display_name),
                "start_time": span.start_time.isoformat() if span.start_time else None,
                "end_time": span.end_time.isoformat() if span.end_time else None,
                "parent_span_id": span.parent_span_id if span.parent_span_id else None,
                "attributes": self._format_attributes(span.attributes) if hasattr(span, 'attributes') else {},
                "status": self._format_status(span.status) if hasattr(span, 'status') else None,
            })
        
        return {
            "trace_id": trace_data.name.split('/')[-1],
            "project_id": trace_data.project_id,
            "spans": spans,
            "span_count": len(spans)
        }
    
    def _format_trace_summary(self, trace_data) -> Dict:
        """
        Format trace summary for list view
        
        Args:
            trace_data: Raw trace data from Cloud Trace
            
        Returns:
            Formatted trace summary
        """
        return {
            "trace_id": trace_data.name.split('/')[-1],
            "project_id": trace_data.project_id,
            "span_count": len(trace_data.spans) if hasattr(trace_data, 'spans') else 0
        }
    
    def _format_attributes(self, attributes) -> Dict[str, str]:
        """
        Format span attributes
        
        Args:
            attributes: Raw attributes from span
            
        Returns:
            Formatted attributes dictionary
        """
        formatted = {}
        if hasattr(attributes, 'attribute_map'):
            for key, value in attributes.attribute_map.items():
                if hasattr(value, 'string_value'):
                    formatted[key] = value.string_value.value
                elif hasattr(value, 'int_value'):
                    formatted[key] = str(value.int_value)
                elif hasattr(value, 'bool_value'):
                    formatted[key] = str(value.bool_value)
                else:
                    formatted[key] = str(value)
        return formatted
    
    def _format_status(self, status) -> Optional[Dict]:
        """
        Format span status
        
        Args:
            status: Raw status from span
            
        Returns:
            Formatted status dictionary
        """
        if not status:
            return None
        
        return {
            "code": status.code if hasattr(status, 'code') else 0,
            "message": status.message if hasattr(status, 'message') else ""
        }
    
    def get_current_trace_id(self) -> Optional[str]:
        """
        Get the current trace ID from the active span
        
        Returns:
            Current trace ID or None
        """
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            trace_id = format(current_span.get_span_context().trace_id, '032x')
            return trace_id
        return None
    
    def get_current_span_id(self) -> Optional[str]:
        """
        Get the current span ID from the active span
        
        Returns:
            Current span ID or None
        """
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            span_id = format(current_span.get_span_context().span_id, '016x')
            return span_id
        return None
