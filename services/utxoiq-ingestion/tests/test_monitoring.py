"""
Unit tests for MonitoringModule.

Tests the emission of metrics to Cloud Monitoring for observability.
Covers pipeline metrics, signal metrics, insight metrics, entity metrics,
error metrics, AI provider metrics, and backfill metrics.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime

from src.monitoring import MonitoringModule


@pytest.fixture
def mock_monitoring_client():
    """Create a mock Cloud Monitoring client."""
    with patch('src.monitoring.monitoring_v3.MetricServiceClient') as mock_client:
        mock_instance = Mock()
        mock_instance.create_time_series = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def monitoring_module(mock_monitoring_client):
    """Create a MonitoringModule instance with mocked client."""
    with patch('src.monitoring.MONITORING_AVAILABLE', True):
        module = MonitoringModule(project_id="test-project", enabled=True)
        return module


@pytest.fixture
def monitoring_module_disabled():
    """Create a MonitoringModule instance with monitoring disabled."""
    module = MonitoringModule(project_id="test-project", enabled=False)
    return module


class TestMonitoringModuleInitialization:
    """Test MonitoringModule initialization."""
    
    def test_init_with_project_id(self, mock_monitoring_client):
        """Test initialization with explicit project ID."""
        with patch('src.monitoring.MONITORING_AVAILABLE', True):
            module = MonitoringModule(project_id="custom-project", enabled=True)
            assert module.project_id == "custom-project"
            assert module.enabled is True
            assert module.client is not None
    
    def test_init_with_env_project_id(self, mock_monitoring_client):
        """Test initialization with PROJECT_ID from environment."""
        with patch('src.monitoring.MONITORING_AVAILABLE', True):
            with patch.dict(os.environ, {'PROJECT_ID': 'env-project'}):
                module = MonitoringModule(enabled=True)
                assert module.project_id == "env-project"
    
    def test_init_disabled(self):
        """Test initialization with monitoring disabled."""
        module = MonitoringModule(enabled=False)
        assert module.enabled is False
        assert module.client is None
    
    def test_init_monitoring_unavailable(self):
        """Test initialization when Cloud Monitoring is unavailable."""
        with patch('src.monitoring.MONITORING_AVAILABLE', False):
            module = MonitoringModule(enabled=True)
            assert module.enabled is False


class TestPipelineMetrics:
    """Test emit_pipeline_metrics method."""
    
    @pytest.mark.asyncio
    async def test_emit_pipeline_metrics(self, monitoring_module, mock_monitoring_client):
        """Test emitting pipeline timing metrics."""
        await monitoring_module.emit_pipeline_metrics(
            correlation_id="test-correlation-123",
            block_height=800000,
            signal_count=5,
            signal_generation_ms=1500.0,
            signal_persistence_ms=500.0,
            total_duration_ms=2000.0
        )
        
        # Verify create_time_series was called for each metric
        assert mock_monitoring_client.create_time_series.call_count == 4


class TestSignalMetrics:
    """Test emit_signal_metrics method."""
    
    @pytest.mark.asyncio
    async def test_emit_signal_metrics_high_confidence(self, monitoring_module, mock_monitoring_client):
        """Test emitting signal metrics with high confidence."""
        await monitoring_module.emit_signal_metrics(
            signal_type="mempool",
            confidence=0.9
        )
        
        # Verify metric was written
        assert mock_monitoring_client.create_time_series.call_count == 1


class TestInsightMetrics:
    """Test emit_insight_metrics method."""
    
    @pytest.mark.asyncio
    async def test_emit_insight_metrics(self, monitoring_module, mock_monitoring_client):
        """Test emitting insight generation metrics."""
        await monitoring_module.emit_insight_metrics(
            category="mempool",
            confidence=0.85,
            generation_ms=3000.0
        )
        
        # Should emit 2 metrics: duration and count
        assert mock_monitoring_client.create_time_series.call_count == 2


class TestEntityMetrics:
    """Test emit_entity_metrics method."""
    
    @pytest.mark.asyncio
    async def test_emit_entity_metrics_exchange(self, monitoring_module, mock_monitoring_client):
        """Test emitting entity identification metrics for exchange."""
        await monitoring_module.emit_entity_metrics(
            entity_name="Coinbase",
            entity_type="exchange"
        )
        
        assert mock_monitoring_client.create_time_series.call_count == 1


class TestErrorMetrics:
    """Test emit_error_metric method."""
    
    @pytest.mark.asyncio
    async def test_emit_error_metric_basic(self, monitoring_module, mock_monitoring_client):
        """Test emitting basic error metric."""
        await monitoring_module.emit_error_metric(
            error_type="processor_failure",
            service_name="utxoiq-ingestion"
        )
        
        assert mock_monitoring_client.create_time_series.call_count == 1


class TestAIProviderMetrics:
    """Test emit_ai_provider_metrics method."""
    
    @pytest.mark.asyncio
    async def test_emit_ai_provider_metrics_success(self, monitoring_module, mock_monitoring_client):
        """Test emitting AI provider metrics for successful call."""
        await monitoring_module.emit_ai_provider_metrics(
            provider="vertex_ai",
            latency_ms=2500.0,
            success=True
        )
        
        assert mock_monitoring_client.create_time_series.call_count == 1


class TestBackfillMetrics:
    """Test emit_backfill_metrics method."""
    
    @pytest.mark.asyncio
    async def test_emit_backfill_metrics(self, monitoring_module, mock_monitoring_client):
        """Test emitting backfill progress metrics."""
        await monitoring_module.emit_backfill_metrics(
            blocks_processed=1000,
            signals_generated=5000
        )
        
        # Should emit 2 metrics: blocks_processed and signals_generated
        assert mock_monitoring_client.create_time_series.call_count == 2


class TestCounterMetrics:
    """Test increment_counter method."""
    
    @pytest.mark.asyncio
    async def test_increment_counter_default(self, monitoring_module, mock_monitoring_client):
        """Test incrementing counter with default value."""
        await monitoring_module.increment_counter("total_blocks_processed")
        
        assert mock_monitoring_client.create_time_series.call_count == 1


class TestConfidenceBucket:
    """Test _get_confidence_bucket helper method."""
    
    def test_confidence_bucket_high(self, monitoring_module):
        """Test high confidence bucket (>= 0.85)."""
        assert monitoring_module._get_confidence_bucket(0.85) == "high"
        assert monitoring_module._get_confidence_bucket(0.9) == "high"
        assert monitoring_module._get_confidence_bucket(1.0) == "high"
    
    def test_confidence_bucket_medium(self, monitoring_module):
        """Test medium confidence bucket (0.7 - 0.84)."""
        assert monitoring_module._get_confidence_bucket(0.7) == "medium"
        assert monitoring_module._get_confidence_bucket(0.75) == "medium"
        assert monitoring_module._get_confidence_bucket(0.84) == "medium"
    
    def test_confidence_bucket_low(self, monitoring_module):
        """Test low confidence bucket (< 0.7)."""
        assert monitoring_module._get_confidence_bucket(0.0) == "low"
        assert monitoring_module._get_confidence_bucket(0.5) == "low"
        assert monitoring_module._get_confidence_bucket(0.69) == "low"


class TestWriteMetric:
    """Test _write_metric internal method."""
    
    @pytest.mark.asyncio
    async def test_write_metric_with_labels(self, monitoring_module, mock_monitoring_client):
        """Test writing metric with labels."""
        await monitoring_module._write_metric(
            "test_metric",
            100.0,
            labels={"label1": "value1", "label2": "value2"}
        )
        
        assert mock_monitoring_client.create_time_series.call_count == 1
    
    @pytest.mark.asyncio
    async def test_write_metric_disabled(self, monitoring_module_disabled):
        """Test writing metric when monitoring is disabled."""
        # Should not raise an error
        await monitoring_module_disabled._write_metric(
            "test_metric",
            75.0
        )
