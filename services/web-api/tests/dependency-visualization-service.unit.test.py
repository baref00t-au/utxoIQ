"""
Tests for Dependency Visualization Service

Tests the service dependency graph construction, health status updates,
and failed dependency detection.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import namedtuple

from src.services.dependency_visualization_service import DependencyVisualizationService


@pytest.fixture
def mock_project_id():
    """Mock GCP project ID"""
    return "test-project-id"


@pytest.fixture
def dependency_service(mock_project_id):
    """Create dependency visualization service with mocked clients"""
    with patch('src.services.dependency_visualization_service.trace_v2.TraceServiceClient'), \
         patch('src.services.dependency_visualization_service.monitoring_v3.MetricServiceClient'):
        service = DependencyVisualizationService(project_id=mock_project_id)
        return service


@pytest.fixture
def mock_trace_data():
    """Create mock trace data with service dependencies"""
    # Create mock span structure
    MockSpan = namedtuple('MockSpan', [
        'span_id', 'parent_span_id', 'display_name', 'attributes',
        'start_time', 'end_time', 'status'
    ])
    
    MockAttribute = namedtuple('MockAttribute', ['string_value'])
    MockStringValue = namedtuple('MockStringValue', ['value'])
    MockAttributeMap = namedtuple('MockAttributeMap', ['attribute_map'])
    MockTime = namedtuple('MockTime', ['ToDatetime'])
    MockStatus = namedtuple('MockStatus', ['code'])
    
    # Create mock traces with service dependencies
    # Trace 1: web-api -> feature-engine -> database
    trace1_spans = [
        MockSpan(
            span_id='span1',
            parent_span_id=None,
            display_name=Mock(value='web-api/request'),
            attributes=MockAttributeMap(attribute_map={
                'service': MockAttribute(string_value=MockStringValue(value='web-api'))
            }),
            start_time=MockTime(ToDatetime=lambda: datetime.utcnow()),
            end_time=MockTime(ToDatetime=lambda: datetime.utcnow() + timedelta(milliseconds=100)),
            status=MockStatus(code=0)
        ),
        MockSpan(
            span_id='span2',
            parent_span_id='span1',
            display_name=Mock(value='feature-engine/compute'),
            attributes=MockAttributeMap(attribute_map={
                'service': MockAttribute(string_value=MockStringValue(value='feature-engine'))
            }),
            start_time=MockTime(ToDatetime=lambda: datetime.utcnow()),
            end_time=MockTime(ToDatetime=lambda: datetime.utcnow() + timedelta(milliseconds=50)),
            status=MockStatus(code=0)
        ),
        MockSpan(
            span_id='span3',
            parent_span_id='span2',
            display_name=Mock(value='database/query'),
            attributes=MockAttributeMap(attribute_map={
                'service': MockAttribute(string_value=MockStringValue(value='database'))
            }),
            start_time=MockTime(ToDatetime=lambda: datetime.utcnow()),
            end_time=MockTime(ToDatetime=lambda: datetime.utcnow() + timedelta(milliseconds=20)),
            status=MockStatus(code=0)
        )
    ]
    
    # Trace 2: web-api -> insight-generator (with error)
    trace2_spans = [
        MockSpan(
            span_id='span4',
            parent_span_id=None,
            display_name=Mock(value='web-api/request'),
            attributes=MockAttributeMap(attribute_map={
                'service': MockAttribute(string_value=MockStringValue(value='web-api'))
            }),
            start_time=MockTime(ToDatetime=lambda: datetime.utcnow()),
            end_time=MockTime(ToDatetime=lambda: datetime.utcnow() + timedelta(milliseconds=200)),
            status=MockStatus(code=0)
        ),
        MockSpan(
            span_id='span5',
            parent_span_id='span4',
            display_name=Mock(value='insight-generator/generate'),
            attributes=MockAttributeMap(attribute_map={
                'service': MockAttribute(string_value=MockStringValue(value='insight-generator'))
            }),
            start_time=MockTime(ToDatetime=lambda: datetime.utcnow()),
            end_time=MockTime(ToDatetime=lambda: datetime.utcnow() + timedelta(milliseconds=150)),
            status=MockStatus(code=2)  # Error status
        )
    ]
    
    MockTrace = namedtuple('MockTrace', ['spans'])
    
    return [
        MockTrace(spans=trace1_spans),
        MockTrace(spans=trace2_spans)
    ]


class TestDependencyGraphConstruction:
    """Test dependency graph construction from traces"""
    
    @pytest.mark.asyncio
    async def test_build_dependency_graph_success(self, dependency_service, mock_trace_data):
        """Test successful dependency graph construction"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        
        # Mock health status
        dependency_service._get_service_health_status = AsyncMock(return_value={
            'web-api': 'healthy',
            'feature-engine': 'healthy',
            'database': 'healthy',
            'insight-generator': 'degraded'
        })
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time,
            max_traces=1000
        )
        
        # Verify graph structure
        assert 'nodes' in graph
        assert 'edges' in graph
        assert 'metadata' in graph
        
        # Verify nodes
        assert len(graph['nodes']) == 4  # web-api, feature-engine, database, insight-generator
        
        node_names = {node['service_name'] for node in graph['nodes']}
        assert 'web-api' in node_names
        assert 'feature-engine' in node_names
        assert 'database' in node_names
        assert 'insight-generator' in node_names
        
        # Verify edges
        assert len(graph['edges']) == 3  # web-api->feature-engine, feature-engine->database, web-api->insight-generator
        
        edge_pairs = {(edge['source'], edge['target']) for edge in graph['edges']}
        assert ('web-api', 'feature-engine') in edge_pairs
        assert ('feature-engine', 'database') in edge_pairs
        assert ('web-api', 'insight-generator') in edge_pairs
        
        # Verify metadata
        assert graph['metadata']['traces_analyzed'] == 2
        assert graph['metadata']['total_services'] == 4
        assert graph['metadata']['total_dependencies'] == 3
    
    @pytest.mark.asyncio
    async def test_build_dependency_graph_with_health_status(self, dependency_service, mock_trace_data):
        """Test dependency graph includes health status"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        
        # Mock health status with different statuses
        dependency_service._get_service_health_status = AsyncMock(return_value={
            'web-api': 'healthy',
            'feature-engine': 'degraded',
            'database': 'unhealthy',
            'insight-generator': 'unknown'
        })
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify health status is included
        health_by_service = {
            node['service_name']: node['health_status']
            for node in graph['nodes']
        }
        
        assert health_by_service['web-api'] == 'healthy'
        assert health_by_service['feature-engine'] == 'degraded'
        assert health_by_service['database'] == 'unhealthy'
        assert health_by_service['insight-generator'] == 'unknown'
    
    @pytest.mark.asyncio
    async def test_build_dependency_graph_empty_traces(self, dependency_service):
        """Test dependency graph with no traces"""
        # Mock empty trace query
        dependency_service._query_traces = AsyncMock(return_value=[])
        dependency_service._get_service_health_status = AsyncMock(return_value={})
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify empty graph
        assert len(graph['nodes']) == 0
        assert len(graph['edges']) == 0
        assert graph['metadata']['traces_analyzed'] == 0


class TestHealthStatusUpdates:
    """Test service health status updates"""
    
    @pytest.mark.asyncio
    async def test_get_service_health_status_healthy(self, dependency_service):
        """Test health status for healthy services"""
        # Mock error rate query (low error rate)
        dependency_service._get_service_error_rate = AsyncMock(return_value=0.02)  # 2% error rate
        
        # Get health status
        start_time = datetime.utcnow() - timedelta(minutes=5)
        end_time = datetime.utcnow()
        
        health_status = await dependency_service._get_service_health_status(
            ['web-api', 'feature-engine']
        )
        
        # Verify healthy status
        assert health_status['web-api'] == 'healthy'
        assert health_status['feature-engine'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_get_service_health_status_degraded(self, dependency_service):
        """Test health status for degraded services"""
        # Mock error rate query (medium error rate)
        dependency_service._get_service_error_rate = AsyncMock(return_value=0.07)  # 7% error rate
        
        # Get health status
        health_status = await dependency_service._get_service_health_status(
            ['insight-generator']
        )
        
        # Verify degraded status
        assert health_status['insight-generator'] == 'degraded'
    
    @pytest.mark.asyncio
    async def test_get_service_health_status_unhealthy(self, dependency_service):
        """Test health status for unhealthy services"""
        # Mock error rate query (high error rate)
        dependency_service._get_service_error_rate = AsyncMock(return_value=0.15)  # 15% error rate
        
        # Get health status
        health_status = await dependency_service._get_service_health_status(
            ['database']
        )
        
        # Verify unhealthy status
        assert health_status['database'] == 'unhealthy'
    
    @pytest.mark.asyncio
    async def test_get_service_health_status_unknown(self, dependency_service):
        """Test health status when no metrics available"""
        # Mock error rate query (no data)
        dependency_service._get_service_error_rate = AsyncMock(return_value=None)
        
        # Get health status
        health_status = await dependency_service._get_service_health_status(
            ['unknown-service']
        )
        
        # Verify unknown status
        assert health_status['unknown-service'] == 'unknown'
    
    @pytest.mark.asyncio
    async def test_get_service_health_status_error_handling(self, dependency_service):
        """Test health status with error during query"""
        # Mock error rate query that raises exception
        dependency_service._get_service_error_rate = AsyncMock(
            side_effect=Exception("Monitoring API error")
        )
        
        # Get health status
        health_status = await dependency_service._get_service_health_status(
            ['web-api']
        )
        
        # Verify unknown status on error
        assert health_status['web-api'] == 'unknown'


class TestFailedDependencyDetection:
    """Test failed dependency detection"""
    
    @pytest.mark.asyncio
    async def test_detect_failed_dependencies(self, dependency_service, mock_trace_data):
        """Test detection of failed dependencies"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        dependency_service._get_service_health_status = AsyncMock(return_value={
            'web-api': 'healthy',
            'feature-engine': 'healthy',
            'database': 'healthy',
            'insight-generator': 'degraded'
        })
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Find failed edges
        failed_edges = [edge for edge in graph['edges'] if edge['failed']]
        
        # Verify failed dependency is detected
        assert len(failed_edges) == 1
        assert failed_edges[0]['source'] == 'web-api'
        assert failed_edges[0]['target'] == 'insight-generator'
        assert failed_edges[0]['error_count'] > 0
    
    @pytest.mark.asyncio
    async def test_edge_error_count(self, dependency_service, mock_trace_data):
        """Test error count tracking on edges"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        dependency_service._get_service_health_status = AsyncMock(return_value={})
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify error counts
        for edge in graph['edges']:
            if edge['source'] == 'web-api' and edge['target'] == 'insight-generator':
                assert edge['error_count'] == 1
                assert edge['failed'] is True
            else:
                assert edge['error_count'] == 0
                assert edge['failed'] is False
    
    @pytest.mark.asyncio
    async def test_node_error_count(self, dependency_service, mock_trace_data):
        """Test error count tracking on nodes"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        dependency_service._get_service_health_status = AsyncMock(return_value={})
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify error counts on nodes
        error_by_service = {
            node['service_name']: node['error_count']
            for node in graph['nodes']
        }
        
        assert error_by_service['insight-generator'] == 1
        assert error_by_service['web-api'] == 0
        assert error_by_service['feature-engine'] == 0
        assert error_by_service['database'] == 0


class TestDependencyGraphMetrics:
    """Test dependency graph metrics calculation"""
    
    @pytest.mark.asyncio
    async def test_call_count_tracking(self, dependency_service, mock_trace_data):
        """Test call count tracking for nodes and edges"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        dependency_service._get_service_health_status = AsyncMock(return_value={})
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify call counts
        for node in graph['nodes']:
            assert node['call_count'] > 0
        
        for edge in graph['edges']:
            assert edge['call_count'] > 0
    
    @pytest.mark.asyncio
    async def test_average_duration_calculation(self, dependency_service, mock_trace_data):
        """Test average duration calculation"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        dependency_service._get_service_health_status = AsyncMock(return_value={})
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify average durations are calculated
        for node in graph['nodes']:
            assert node['avg_duration_ms'] >= 0
        
        for edge in graph['edges']:
            assert edge['avg_duration_ms'] >= 0
    
    @pytest.mark.asyncio
    async def test_last_seen_timestamp(self, dependency_service, mock_trace_data):
        """Test last seen timestamp tracking"""
        # Mock trace query
        dependency_service._query_traces = AsyncMock(return_value=mock_trace_data)
        dependency_service._get_service_health_status = AsyncMock(return_value={})
        
        # Build graph
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        graph = await dependency_service.build_dependency_graph(
            start_time=start_time,
            end_time=end_time
        )
        
        # Verify last seen timestamps
        for node in graph['nodes']:
            assert node['last_seen'] is not None
