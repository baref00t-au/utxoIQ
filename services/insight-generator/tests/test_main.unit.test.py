"""
Unit tests for main FastAPI application.

Tests the FastAPI application structure, health check endpoint,
and service initialization.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("DATASET_INTEL", "intel")
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "10")
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.7")
    monkeypatch.setenv("AI_PROVIDER", "vertex_ai")
    monkeypatch.setenv("VERTEX_AI_PROJECT", "test-project")
    monkeypatch.setenv("VERTEX_AI_LOCATION", "us-central1")


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client."""
    with patch("services.insight-generator.src.main.bigquery.Client") as mock:
        yield mock.return_value


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider."""
    with patch("services.insight-generator.src.main.get_configured_provider") as mock:
        provider = Mock()
        provider.__class__.__name__ = "VertexAIProvider"
        mock.return_value = provider
        yield provider


def test_root_endpoint(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test root endpoint returns service information."""
    from src.main import app
    
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "utxoIQ Insight Generator"
    assert data["version"] == "1.0.0"
    assert "status" in data


def test_health_check_endpoint(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test health check endpoint returns service status."""
    from src.main import app, get_service
    
    # Mock the service methods
    with patch.object(get_service(), "signal_polling") as mock_polling:
        mock_polling.get_unprocessed_signal_count = AsyncMock(return_value=5)
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ai_provider" in data
        assert "unprocessed_signals" in data


def test_service_initialization(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test InsightGeneratorService initializes all modules correctly."""
    from src.main import InsightGeneratorService
    
    service = InsightGeneratorService()
    
    # Verify all modules are initialized
    assert service.bq_client is not None
    assert service.ai_provider is not None
    assert service.signal_polling is not None
    assert service.insight_generation is not None
    assert service.insight_persistence is not None


@pytest.mark.asyncio
async def test_process_signal_group(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test processing a signal group generates insights."""
    from src.main import InsightGeneratorService
    from src.signal_polling import SignalGroup
    from src.insight_generation import Insight, Evidence
    
    service = InsightGeneratorService()
    
    # Mock signal group
    signal_group = SignalGroup(
        signal_type="mempool",
        block_height=870000,
        signals=[
            {
                "signal_id": "test-signal-1",
                "signal_type": "mempool",
                "block_height": 870000,
                "confidence": 0.85,
                "metadata": {
                    "fee_rate_median": 50.5,
                    "fee_rate_change_pct": 25.3,
                    "tx_count": 15000,
                    "mempool_size_mb": 120.5
                }
            }
        ]
    )
    
    # Mock insight generation
    mock_insight = Insight(
        insight_id="test-insight-1",
        signal_id="test-signal-1",
        category="mempool",
        headline="Test Headline",
        summary="Test Summary",
        confidence=0.85,
        evidence=Evidence(block_heights=[870000], transaction_ids=[])
    )
    
    with patch.object(service.insight_generation, "generate_insight", return_value=mock_insight):
        with patch.object(service.insight_persistence, "persist_insight") as mock_persist:
            mock_persist.return_value = Mock(success=True, insight_id="test-insight-1")
            
            with patch.object(service.signal_polling, "mark_signal_processed"):
                insights_count = await service.process_signal_group(
                    signal_group,
                    "test-correlation-id"
                )
                
                assert insights_count == 1


@pytest.mark.asyncio
async def test_run_polling_cycle(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test running a complete polling cycle."""
    from src.main import InsightGeneratorService
    from src.signal_polling import SignalGroup
    
    service = InsightGeneratorService()
    
    # Mock signal groups
    signal_groups = [
        SignalGroup(
            signal_type="mempool",
            block_height=870000,
            signals=[
                {
                    "signal_id": "test-signal-1",
                    "signal_type": "mempool",
                    "block_height": 870000,
                    "confidence": 0.85,
                    "metadata": {}
                }
            ]
        )
    ]
    
    with patch.object(service.signal_polling, "poll_unprocessed_signals", return_value=signal_groups):
        with patch.object(service, "process_signal_group", return_value=1):
            result = await service.run_polling_cycle()
            
            assert result["signal_groups"] == 1
            assert result["signals_processed"] == 1
            assert result["insights_generated"] == 1


def test_trigger_cycle_endpoint(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test manual trigger cycle endpoint."""
    from src.main import app, get_service
    
    with patch.object(get_service(), "run_polling_cycle") as mock_cycle:
        mock_cycle.return_value = {
            "correlation_id": "test-id",
            "signal_groups": 1,
            "signals_processed": 2,
            "insights_generated": 2
        }
        
        client = TestClient(app)
        response = client.post("/trigger-cycle")
        
        assert response.status_code == 200
        data = response.json()
        assert data["signal_groups"] == 1
        assert data["insights_generated"] == 2


def test_stats_endpoint(mock_env_vars, mock_bigquery_client, mock_ai_provider):
    """Test stats endpoint returns service statistics."""
    from src.main import app, get_service
    
    with patch.object(get_service().signal_polling, "get_unprocessed_signal_count", return_value=10):
        with patch.object(get_service().signal_polling, "get_stale_signals", return_value=[]):
            client = TestClient(app)
            response = client.get("/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["unprocessed_signals"] == 10
            assert data["stale_signals"] == 0
