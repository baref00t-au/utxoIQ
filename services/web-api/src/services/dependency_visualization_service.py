"""
Service Dependency Visualization Service for utxoIQ Platform

This service provides service dependency graph visualization by analyzing
distributed traces to understand service-to-service call patterns and health status.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from google.cloud import trace_v2
from google.cloud import monitoring_v3

logger = logging.getLogger(__name__)


class DependencyVisualizationService:
    """Service for visualizing service dependencies from traces"""
    
    def __init__(self, project_id: str):
        """
        Initialize the dependency visualization service
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.project_name = f"projects/{project_id}"
        
        # Initialize Cloud Trace client for reading traces
        self.trace_client = trace_v2.TraceServiceClient()
        
        # Initialize Cloud Monitoring client for health status
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        
        logger.info(f"DependencyVisualizationService initialized for project {project_id}")
    
    async def build_dependency_graph(
        self,
        start_time: datetime,
        end_time: datetime,
        max_traces: int = 1000
    ) -> Dict:
        """
        Build service dependency graph from trace data
        
        Analyzes traces within the time range to identify service-to-service
        call patterns and construct a dependency graph.
        
        Args:
            start_time: Start of time range to analyze
            end_time: End of time range to analyze
            max_traces: Maximum number of traces to analyze
            
        Returns:
            Dictionary containing nodes (services) and edges (calls)
        """
        try:
            # Query traces from Cloud Trace
            traces = await self._query_traces(start_time, end_time, max_traces)
            
            # Extract service dependencies from traces
            nodes, edges = self._extract_dependencies(traces)
            
            # Get health status for each service
            health_status = await self._get_service_health_status(list(nodes.keys()))
            
            # Combine into graph structure
            graph = {
                "nodes": [
                    {
                        "service_name": service_name,
                        "call_count": node_data["call_count"],
                        "error_count": node_data["error_count"],
                        "avg_duration_ms": node_data["avg_duration_ms"],
                        "health_status": health_status.get(service_name, "unknown"),
                        "last_seen": node_data["last_seen"].isoformat() if node_data["last_seen"] else None
                    }
                    for service_name, node_data in nodes.items()
                ],
                "edges": [
                    {
                        "source": source,
                        "target": target,
                        "call_count": edge_data["call_count"],
                        "error_count": edge_data["error_count"],
                        "avg_duration_ms": edge_data["avg_duration_ms"],
                        "failed": edge_data["error_count"] > 0
                    }
                    for (source, target), edge_data in edges.items()
                ],
                "metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "traces_analyzed": len(traces),
                    "total_services": len(nodes),
                    "total_dependencies": len(edges)
                }
            }
            
            logger.info(
                f"Built dependency graph: {len(nodes)} services, "
                f"{len(edges)} dependencies from {len(traces)} traces"
            )
            
            return graph
            
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
            raise
    
    async def _query_traces(
        self,
        start_time: datetime,
        end_time: datetime,
        max_traces: int
    ) -> List:
        """
        Query traces from Cloud Trace
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            max_traces: Maximum number of traces to retrieve
            
        Returns:
            List of trace data
        """
        try:
            request = trace_v2.ListTracesRequest(
                parent=self.project_name,
                start_time=start_time,
                end_time=end_time,
                page_size=min(max_traces, 1000)
            )
            
            traces = []
            for trace_data in self.trace_client.list_traces(request=request):
                traces.append(trace_data)
                if len(traces) >= max_traces:
                    break
            
            logger.debug(f"Retrieved {len(traces)} traces from Cloud Trace")
            return traces
            
        except Exception as e:
            logger.error(f"Error querying traces: {e}")
            # Return empty list on error to allow graceful degradation
            return []
    
    def _extract_dependencies(
        self,
        traces: List
    ) -> Tuple[Dict, Dict]:
        """
        Extract service dependencies from traces
        
        Analyzes span relationships to identify which services call which other services.
        
        Args:
            traces: List of trace data
            
        Returns:
            Tuple of (nodes dict, edges dict)
        """
        nodes = defaultdict(lambda: {
            "call_count": 0,
            "error_count": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0,
            "last_seen": None
        })
        
        edges = defaultdict(lambda: {
            "call_count": 0,
            "error_count": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0
        })
        
        for trace in traces:
            if not hasattr(trace, 'spans'):
                continue
            
            # Build span lookup and parent-child relationships
            spans_by_id = {}
            for span in trace.spans:
                span_id = span.span_id
                spans_by_id[span_id] = span
            
            # Process each span
            for span in trace.spans:
                # Extract service name from span
                service_name = self._extract_service_name(span)
                if not service_name:
                    continue
                
                # Calculate span duration
                duration_ms = self._calculate_span_duration(span)
                
                # Check if span has error
                has_error = self._span_has_error(span)
                
                # Update node data
                nodes[service_name]["call_count"] += 1
                nodes[service_name]["total_duration_ms"] += duration_ms
                if has_error:
                    nodes[service_name]["error_count"] += 1
                
                # Update last seen time
                if hasattr(span, 'start_time') and span.start_time:
                    span_time = span.start_time.ToDatetime() if hasattr(span.start_time, 'ToDatetime') else None
                    if span_time:
                        if not nodes[service_name]["last_seen"] or span_time > nodes[service_name]["last_seen"]:
                            nodes[service_name]["last_seen"] = span_time
                
                # Process parent-child relationship for edges
                if span.parent_span_id and span.parent_span_id in spans_by_id:
                    parent_span = spans_by_id[span.parent_span_id]
                    parent_service = self._extract_service_name(parent_span)
                    
                    if parent_service and parent_service != service_name:
                        # Create edge from parent to child
                        edge_key = (parent_service, service_name)
                        edges[edge_key]["call_count"] += 1
                        edges[edge_key]["total_duration_ms"] += duration_ms
                        if has_error:
                            edges[edge_key]["error_count"] += 1
        
        # Calculate averages
        for service_name, node_data in nodes.items():
            if node_data["call_count"] > 0:
                node_data["avg_duration_ms"] = round(
                    node_data["total_duration_ms"] / node_data["call_count"],
                    2
                )
        
        for edge_key, edge_data in edges.items():
            if edge_data["call_count"] > 0:
                edge_data["avg_duration_ms"] = round(
                    edge_data["total_duration_ms"] / edge_data["call_count"],
                    2
                )
        
        logger.debug(
            f"Extracted {len(nodes)} services and {len(edges)} dependencies from traces"
        )
        
        return dict(nodes), dict(edges)
    
    def _extract_service_name(self, span) -> Optional[str]:
        """
        Extract service name from span attributes
        
        Args:
            span: Trace span
            
        Returns:
            Service name or None
        """
        # Try to get service name from attributes
        if hasattr(span, 'attributes') and hasattr(span.attributes, 'attribute_map'):
            attr_map = span.attributes.attribute_map
            
            # Check common attribute keys for service name
            for key in ['service', 'service.name', 'service_name', 'component']:
                if key in attr_map:
                    value = attr_map[key]
                    if hasattr(value, 'string_value') and hasattr(value.string_value, 'value'):
                        return value.string_value.value
                    elif hasattr(value, 'string_value'):
                        return str(value.string_value)
        
        # Fallback: try to extract from span name
        if hasattr(span, 'display_name'):
            display_name = span.display_name.value if hasattr(span.display_name, 'value') else str(span.display_name)
            # Common patterns: "service-name/endpoint" or "service-name.method"
            if '/' in display_name:
                return display_name.split('/')[0]
            elif '.' in display_name:
                parts = display_name.split('.')
                if len(parts) > 1:
                    return parts[0]
        
        return None
    
    def _calculate_span_duration(self, span) -> float:
        """
        Calculate span duration in milliseconds
        
        Args:
            span: Trace span
            
        Returns:
            Duration in milliseconds
        """
        if not hasattr(span, 'start_time') or not hasattr(span, 'end_time'):
            return 0.0
        
        if not span.start_time or not span.end_time:
            return 0.0
        
        try:
            start = span.start_time.ToDatetime() if hasattr(span.start_time, 'ToDatetime') else span.start_time
            end = span.end_time.ToDatetime() if hasattr(span.end_time, 'ToDatetime') else span.end_time
            
            if start and end:
                duration = (end - start).total_seconds() * 1000
                return max(0.0, duration)
        except Exception as e:
            logger.debug(f"Error calculating span duration: {e}")
        
        return 0.0
    
    def _span_has_error(self, span) -> bool:
        """
        Check if span has an error status
        
        Args:
            span: Trace span
            
        Returns:
            True if span has error, False otherwise
        """
        if hasattr(span, 'status') and span.status:
            # Check status code (non-zero indicates error)
            if hasattr(span.status, 'code') and span.status.code != 0:
                return True
            
            # Check for error in attributes
            if hasattr(span, 'attributes') and hasattr(span.attributes, 'attribute_map'):
                attr_map = span.attributes.attribute_map
                if 'error' in attr_map or 'status' in attr_map:
                    status_attr = attr_map.get('status')
                    if status_attr and hasattr(status_attr, 'string_value'):
                        status_value = status_attr.string_value.value if hasattr(status_attr.string_value, 'value') else str(status_attr.string_value)
                        if status_value == 'error':
                            return True
        
        return False
    
    async def _get_service_health_status(
        self,
        service_names: List[str]
    ) -> Dict[str, str]:
        """
        Get real-time health status for services
        
        Queries Cloud Monitoring for recent error rates and response times
        to determine service health status.
        
        Args:
            service_names: List of service names
            
        Returns:
            Dictionary mapping service names to health status
        """
        health_status = {}
        
        # Get metrics for last 5 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        for service_name in service_names:
            try:
                # Query error rate metric
                error_rate = await self._get_service_error_rate(
                    service_name,
                    start_time,
                    end_time
                )
                
                # Determine health status based on error rate
                if error_rate is None:
                    health_status[service_name] = "unknown"
                elif error_rate > 0.1:  # >10% error rate
                    health_status[service_name] = "unhealthy"
                elif error_rate > 0.05:  # >5% error rate
                    health_status[service_name] = "degraded"
                else:
                    health_status[service_name] = "healthy"
                    
            except Exception as e:
                logger.debug(f"Error getting health status for {service_name}: {e}")
                health_status[service_name] = "unknown"
        
        return health_status
    
    async def _get_service_error_rate(
        self,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[float]:
        """
        Get error rate for a service
        
        Args:
            service_name: Service name
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Error rate (0.0 to 1.0) or None if no data
        """
        try:
            # Build metric filter for error rate
            metric_type = f"custom.googleapis.com/{service_name}/error_rate"
            
            interval = monitoring_v3.TimeInterval({
                "start_time": start_time,
                "end_time": end_time
            })
            
            aggregation = monitoring_v3.Aggregation({
                "alignment_period": {"seconds": 60},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
            })
            
            results = self.monitoring_client.list_time_series(
                request={
                    "name": self.project_name,
                    "filter": f'metric.type = "{metric_type}"',
                    "interval": interval,
                    "aggregation": aggregation,
                }
            )
            
            # Calculate average error rate from results
            error_rates = []
            for result in results:
                for point in result.points:
                    if hasattr(point.value, 'double_value'):
                        error_rates.append(point.value.double_value)
                    elif hasattr(point.value, 'int64_value'):
                        error_rates.append(float(point.value.int64_value))
            
            if error_rates:
                return sum(error_rates) / len(error_rates)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error querying error rate for {service_name}: {e}")
            return None
