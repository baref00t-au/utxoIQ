"""Tests for Cloud Monitoring metrics service."""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from google.cloud import monitoring_v3

from src.services.metrics_service import MetricsService, get_metrics_service


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def metrics_service(mock_redis_client):
    """Create metrics service instance for testing."""
    with patch('src.services.metrics_service.monitoring_v3.MetricServiceClient'):
        with patch('src.services.metrics_service.monitoring_v3.QueryServiceClient'):
            service = MetricsService(
                project_id="test-project",
                redis_client=mock_redis_client
            )
            return service


class TestTimeRangeParsing:
    """Test time range parsing utility."""
    
    def test_parse_hours(self, metrics_service):
        """Test parsing hour-based time ranges."""
        result = metrics_service._parse_time_range("1h")
        assert result == timedelta(hours=1)
        
        result = metrics_service._parse_time_range("24h")
        assert result == timedelta(hours=24)
        
        result = metrics_service._parse_time_range("168h")
        assert result == timedelta(hours=168)
    
    def test_parse_days(self, metrics_service):
        """Test parsing day-based time ranges."""
        result = metrics_service._parse_time_range("1d")
        assert result == timedelta(days=1)
        
        result = metrics_service._parse_time_range("7d")
        assert result == timedelta(days=7)
        
        result = metrics_service._parse_time_range("30d")
        assert result == timedelta(days=30)
    
    def test_parse_case_insensitive(self, metrics_service):
        """Test case-insensitive parsing."""
        result = metrics_service._parse_time_range("1H")
        assert result == timedelta(hours=1)
        
        result = metrics_service._parse_time_range("7D")
        assert result == timedelta(days=7)
    
    def test_parse_with_whitespace(self, metrics_service):
        """Test parsing with whitespace."""
        result = metrics_service._parse_time_range(" 1h ")
        assert result == timedelta(hours=1)
    
    def test_parse_invalid_format(self, metrics_service):
        """Test parsing invalid formats."""
        with pytest.raises(ValueError, match="Invalid time range format"):
            metrics_service._parse_time_range("1w")
        
        with pytest.raises(ValueError):
            metrics_service._parse_time_range("invalid")
        
        with pytest.raises(ValueError):
            metrics_service._parse_time_range("1")


class TestTimeSeriesFormatting:
    """Test time series data formatting."""
    
    def test_format_double_value(self, metrics_service):
        """Test formatting time series with double values."""
        # Create mock time series
        mock_ts = Mock()
        mock_ts.metric = Mock()
        mock_ts.metric.type = "custom.googleapis.com/test/metric"
        mock_ts.metric.labels = {"service": "test"}
        mock_ts.resource = Mock()
        mock_ts.resource.type = "cloud_run_revision"
        
        # Create mock point with double value
        mock_point = Mock()
        mock_point.value = Mock()
        mock_point.value.HasField = lambda field: field == 'double_value'
        mock_point.value.double_value = 42.5
        mock_point.interval = Mock()
        mock_point.interval.end_time = Mock()
        mock_point.interval.end_time.isoformat = lambda: "2024-01-01T00:00:00Z"
        mock_ts.points = [mock_point]
        
        result = metrics_service._format_time_series(mock_ts)
        
        assert result['metric_type'] == "custom.googleapis.com/test/metric"
        assert result['resource_type'] == "cloud_run_revision"
        assert result['labels'] == {"service": "test"}
        assert len(result['points']) == 1
        assert result['points'][0]['value'] == 42.5
        assert result['points'][0]['timestamp'] == "2024-01-01T00:00:00Z"
    
    def test_format_int64_value(self, metrics_service):
        """Test formatting time series with int64 values."""
        mock_ts = Mock()
        mock_ts.metric = Mock()
        mock_ts.metric.type = "custom.googleapis.com/test/metric"
        mock_ts.metric.labels = {}
        mock_ts.resource = Mock()
        mock_ts.resource.type = "cloud_run_revision"
        
        mock_point = Mock()
        mock_point.value = Mock()
        mock_point.value.HasField = lambda field: field == 'int64_value'
        mock_point.value.int64_value = 100
        mock_point.interval = Mock()
        mock_point.interval.end_time = Mock()
        mock_point.interval.end_time.isoformat = lambda: "2024-01-01T00:00:00Z"
        mock_ts.points = [mock_point]
        
        result = metrics_service._format_time_series(mock_ts)
        
        assert result['points'][0]['value'] == 100.0
    
    def test_format_bool_value(self, metrics_service):
        """Test formatting time series with boolean values."""
        mock_ts = Mock()
        mock_ts.metric = Mock()
        mock_ts.metric.type = "custom.googleapis.com/test/metric"
        mock_ts.metric.labels = {}
        mock_ts.resource = Mock()
        mock_ts.resource.type = "cloud_run_revision"
        
        # Test True
        mock_point = Mock()
        mock_point.value = Mock()
        mock_point.value.HasField = lambda field: field == 'bool_value'
        mock_point.value.bool_value = True
        mock_point.interval = Mock()
        mock_point.interval.end_time = Mock()
        mock_point.interval.end_time.isoformat = lambda: "2024-01-01T00:00:00Z"
        mock_ts.points = [mock_point]
        
        result = metrics_service._format_time_series(mock_ts)
        assert result['points'][0]['value'] == 1.0
        
        # Test False
        mock_point.value.bool_value = False
        result = metrics_service._format_time_series(mock_ts)
        assert result['points'][0]['value'] == 0.0


class TestTimeSeriesQueries:
    """Test time series data queries."""
    
    @pytest.mark.asyncio
    async def test_get_time_series_basic(self, metrics_service):
        """Test basic time series query."""
        # Mock the client response
        mock_ts = Mock()
        mock_ts.metric = Mock()
        mock_ts.metric.type = "custom.googleapis.com/api/response_time"
        mock_ts.metric.labels = {}
        mock_ts.resource = Mock()
        mock_ts.resource.type = "cloud_run_revision"
        
        mock_point = Mock()
        mock_point.value = Mock()
        mock_point.value.HasField = lambda field: field == 'double_value'
        mock_point.value.double_value = 150.5
        mock_point.interval = Mock()
        mock_point.interval.end_time = Mock()
        mock_point.interval.end_time.isoformat = lambda: "2024-01-01T00:00:00Z"
        mock_ts.points = [mock_point]
        
        metrics_service.client.list_time_series = Mock(return_value=[mock_ts])
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 1, 0, 0)
        
        result = await metrics_service.get_time_series(
            metric_type="custom.googleapis.com/api/response_time",
            start_time=start_time,
            end_time=end_time
        )
        
        assert len(result) == 1
        assert result[0]['metric_type'] == "custom.googleapis.com/api/response_time"
        assert result[0]['points'][0]['value'] == 150.5
    
    @pytest.mark.asyncio
    async def test_get_time_series_with_resource_labels(self, metrics_service):
        """Test time series query with resource label filters."""
        metrics_service.client.list_time_series = Mock(return_value=[])
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 1, 0, 0)
        
        await metrics_service.get_time_series(
            metric_type="custom.googleapis.com/api/response_time",
            start_time=start_time,
            end_time=end_time,
            resource_labels={"service_name": "web-api", "region": "us-central1"}
        )
        
        # Verify the filter includes resource labels
        call_args = metrics_service.client.list_time_series.call_args
        filter_str = call_args[1]['request']['filter']
        assert 'resource.labels.service_name = "web-api"' in filter_str
        assert 'resource.labels.region = "us-central1"' in filter_str
    
    @pytest.mark.asyncio
    async def test_get_time_series_with_aggregation(self, metrics_service):
        """Test time series query with custom aggregation."""
        metrics_service.client.list_time_series = Mock(return_value=[])
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 1, 0, 0)
        
        await metrics_service.get_time_series(
            metric_type="custom.googleapis.com/api/response_time",
            start_time=start_time,
            end_time=end_time,
            aggregation="ALIGN_MAX",
            interval_seconds=60
        )
        
        # Verify aggregation parameters
        call_args = metrics_service.client.list_time_series.call_args
        aggregation = call_args[1]['request']['aggregation']
        assert aggregation.alignment_period.seconds == 60


class TestServiceMetrics:
    """Test service metrics queries."""
    
    @pytest.mark.asyncio
    async def test_get_service_metrics_no_cache(self, metrics_service, mock_redis_client):
        """Test getting service metrics without cache."""
        # Mock get_time_series to return data
        async def mock_get_time_series(*args, **kwargs):
            return [{
                'metric_type': kwargs['metric_type'],
                'points': [{'timestamp': '2024-01-01T00:00:00Z', 'value': 50.0}]
            }]
        
        metrics_service.get_time_series = mock_get_time_series
        mock_redis_client.get.return_value = None
        
        result = await metrics_service.get_service_metrics(
            service_name="web-api",
            metrics=["cpu_usage", "memory_usage"],
            time_range="1h"
        )
        
        assert "cpu_usage" in result
        assert "memory_usage" in result
        assert len(result["cpu_usage"]) == 1
        assert len(result["memory_usage"]) == 1
        
        # Verify cache was written
        assert mock_redis_client.setex.called
    
    @pytest.mark.asyncio
    async def test_get_service_metrics_with_cache(self, metrics_service, mock_redis_client):
        """Test getting service metrics from cache."""
        import json
        
        cached_data = {
            "cpu_usage": [{'metric_type': 'test', 'points': []}],
            "memory_usage": [{'metric_type': 'test', 'points': []}]
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = await metrics_service.get_service_metrics(
            service_name="web-api",
            metrics=["cpu_usage", "memory_usage"],
            time_range="1h"
        )
        
        assert result == cached_data


class TestBaselineCalculation:
    """Test baseline calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_baseline_basic(self, metrics_service, mock_redis_client):
        """Test basic baseline calculation."""
        # Mock get_time_series to return sample data
        async def mock_get_time_series(*args, **kwargs):
            return [{
                'metric_type': 'test',
                'points': [
                    {'timestamp': '2024-01-01T00:00:00Z', 'value': 10.0},
                    {'timestamp': '2024-01-01T01:00:00Z', 'value': 20.0},
                    {'timestamp': '2024-01-01T02:00:00Z', 'value': 30.0},
                    {'timestamp': '2024-01-01T03:00:00Z', 'value': 40.0},
                    {'timestamp': '2024-01-01T04:00:00Z', 'value': 50.0},
                ]
            }]
        
        metrics_service.get_time_series = mock_get_time_series
        mock_redis_client.get.return_value = None
        
        result = await metrics_service.calculate_baseline(
            metric_type="custom.googleapis.com/api/response_time",
            days=7
        )
        
        assert result['mean'] == 30.0
        assert result['median'] == 30.0
        assert result['sample_count'] == 5
        assert 'std_dev' in result
        assert 'p95' in result
        assert 'p99' in result
        
        # Verify cache was written with 1-hour TTL
        assert mock_redis_client.setex.called
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == 3600  # 1 hour TTL
    
    @pytest.mark.asyncio
    async def test_calculate_baseline_from_cache(self, metrics_service, mock_redis_client):
        """Test baseline calculation from cache."""
        import json
        
        cached_baseline = {
            "mean": 25.0,
            "median": 24.0,
            "std_dev": 5.0,
            "p95": 35.0,
            "p99": 38.0,
            "sample_count": 100
        }
        mock_redis_client.get.return_value = json.dumps(cached_baseline)
        
        result = await metrics_service.calculate_baseline(
            metric_type="custom.googleapis.com/api/response_time",
            days=7
        )
        
        assert result == cached_baseline
    
    @pytest.mark.asyncio
    async def test_calculate_baseline_no_data(self, metrics_service, mock_redis_client):
        """Test baseline calculation with no data."""
        async def mock_get_time_series(*args, **kwargs):
            return []
        
        metrics_service.get_time_series = mock_get_time_series
        mock_redis_client.get.return_value = None
        
        result = await metrics_service.calculate_baseline(
            metric_type="custom.googleapis.com/api/response_time",
            days=7
        )
        
        assert result['mean'] == 0.0
        assert result['median'] == 0.0
        assert result['std_dev'] == 0.0
        assert result['p95'] == 0.0
        assert result['p99'] == 0.0
        assert result['sample_count'] == 0
    
    @pytest.mark.asyncio
    async def test_calculate_baseline_single_value(self, metrics_service, mock_redis_client):
        """Test baseline calculation with single value (no std dev)."""
        async def mock_get_time_series(*args, **kwargs):
            return [{
                'metric_type': 'test',
                'points': [{'timestamp': '2024-01-01T00:00:00Z', 'value': 42.0}]
            }]
        
        metrics_service.get_time_series = mock_get_time_series
        mock_redis_client.get.return_value = None
        
        result = await metrics_service.calculate_baseline(
            metric_type="custom.googleapis.com/api/response_time",
            days=7
        )
        
        assert result['mean'] == 42.0
        assert result['median'] == 42.0
        assert result['std_dev'] == 0.0  # Can't calculate std dev with 1 value
        assert result['sample_count'] == 1


class TestCachingBehavior:
    """Test caching behavior."""
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, metrics_service, mock_redis_client):
        """Test cache key generation for different queries."""
        async def mock_get_time_series(*args, **kwargs):
            return []
        
        metrics_service.get_time_series = mock_get_time_series
        mock_redis_client.get.return_value = None
        
        # Query service metrics
        await metrics_service.get_service_metrics(
            service_name="web-api",
            metrics=["cpu", "memory"],
            time_range="1h"
        )
        
        # Verify cache key format
        call_args = mock_redis_client.setex.call_args
        cache_key = call_args[0][0]
        assert cache_key.startswith("metrics:web-api:1h:")
        assert "cpu" in cache_key
        assert "memory" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, metrics_service, mock_redis_client):
        """Test graceful handling of cache errors."""
        async def mock_get_time_series(*args, **kwargs):
            return [{'metric_type': 'test', 'points': []}]
        
        metrics_service.get_time_series = mock_get_time_series
        
        # Simulate cache read error
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        # Should still work without cache
        result = await metrics_service.get_service_metrics(
            service_name="web-api",
            metrics=["cpu"],
            time_range="1h"
        )
        
        assert "cpu" in result
        
        # Simulate cache write error
        mock_redis_client.get.side_effect = None
        mock_redis_client.get.return_value = None
        mock_redis_client.setex.side_effect = Exception("Redis write error")
        
        # Should still work without caching
        result = await metrics_service.get_service_metrics(
            service_name="web-api",
            metrics=["cpu"],
            time_range="1h"
        )
        
        assert "cpu" in result


class TestGlobalInstance:
    """Test global metrics service instance."""
    
    def test_get_metrics_service_singleton(self):
        """Test that get_metrics_service returns singleton."""
        with patch('src.services.metrics_service.monitoring_v3.MetricServiceClient'):
            with patch('src.services.metrics_service.monitoring_v3.QueryServiceClient'):
                with patch('src.services.metrics_service.settings') as mock_settings:
                    mock_settings.gcp_project_id = "test-project"
                    
                    service1 = get_metrics_service()
                    service2 = get_metrics_service()
                    
                    assert service1 is service2
