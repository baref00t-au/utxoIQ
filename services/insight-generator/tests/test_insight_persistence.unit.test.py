"""
Unit tests for InsightPersistenceModule.

Tests the core functionality of insight persistence including:
- Successful persistence operations
- Error handling and retry mechanisms
- Batch operations
- Query utilities

Requirements: 4.1, 4.3, 4.4, 4.5
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.insight_persistence import (
    InsightPersistenceModule,
    PersistenceResult
)
from src.insight_generation import Insight, Evidence


@pytest.fixture
def mock_bigquery_client():
    """Create a mock BigQuery client"""
    client = Mock()
    client.insert_rows_json = Mock()
    client.query = Mock()
    return client


@pytest.fixture
def persistence_module(mock_bigquery_client):
    """Create InsightPersistenceModule with mock client"""
    return InsightPersistenceModule(
        bigquery_client=mock_bigquery_client,
        project_id="test-project",
        dataset_id="test_intel"
    )


@pytest.fixture
def sample_insight():
    """Create a sample insight for testing"""
    return Insight(
        insight_id="test-insight-001",
        signal_id="test-signal-001",
        category="mempool",
        headline="Test Headline",
        summary="Test summary for unit testing.",
        confidence=0.85,
        evidence=Evidence(
            block_heights=[820000],
            transaction_ids=["tx-001", "tx-002"]
        ),
        chart_url=None,
        created_at=datetime.utcnow()
    )


class TestInsightPersistence:
    """Test suite for InsightPersistenceModule"""
    
    @pytest.mark.asyncio
    async def test_persist_insight_success(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_insight
    ):
        """Test successful insight persistence"""
        # Mock successful insert (no errors)
        mock_bigquery_client.insert_rows_json.return_value = []
        
        # Persist insight
        result = await persistence_module.persist_insight(
            insight=sample_insight,
            correlation_id="test-corr-001"
        )
        
        # Verify result
        assert result.success is True
        assert result.insight_id == sample_insight.insight_id
        assert result.error is None
        
        # Verify BigQuery was called
        mock_bigquery_client.insert_rows_json.assert_called_once()
        
        # Verify chart_url was set to None
        call_args = mock_bigquery_client.insert_rows_json.call_args
        inserted_data = call_args[0][1][0]  # First row of data
        assert inserted_data["chart_url"] is None
    
    @pytest.mark.asyncio
    async def test_persist_insight_bigquery_error(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_insight
    ):
        """Test persistence failure with BigQuery error"""
        # Mock BigQuery insert error
        mock_bigquery_client.insert_rows_json.return_value = [
            {"error": "Schema mismatch"}
        ]
        
        # Mock query for marking signal unprocessed
        mock_query_job = Mock()
        mock_query_job.result = Mock()
        mock_query_job.num_dml_affected_rows = 1
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Persist insight
        result = await persistence_module.persist_insight(
            insight=sample_insight,
            correlation_id="test-corr-002"
        )
        
        # Verify result
        assert result.success is False
        assert result.insight_id is None
        assert "BigQuery insert errors" in result.error
        
        # Verify signal was marked as unprocessed
        mock_bigquery_client.query.assert_called_once()
        query_call = mock_bigquery_client.query.call_args[0][0]
        assert "processed = false" in query_call
        assert sample_insight.signal_id in query_call
    
    @pytest.mark.asyncio
    async def test_persist_insight_table_not_found(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_insight
    ):
        """Test persistence failure when table doesn't exist"""
        from google.cloud.exceptions import NotFound
        
        # Mock NotFound exception
        mock_bigquery_client.insert_rows_json.side_effect = NotFound("Table not found")
        
        # Mock query for marking signal unprocessed
        mock_query_job = Mock()
        mock_query_job.result = Mock()
        mock_query_job.num_dml_affected_rows = 1
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Persist insight
        result = await persistence_module.persist_insight(
            insight=sample_insight,
            correlation_id="test-corr-003"
        )
        
        # Verify result
        assert result.success is False
        assert "not found" in result.error.lower()
        
        # Verify signal was marked as unprocessed
        mock_bigquery_client.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_persist_insight_unexpected_error(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_insight
    ):
        """Test persistence failure with unexpected exception"""
        # Mock unexpected exception
        mock_bigquery_client.insert_rows_json.side_effect = Exception("Unexpected error")
        
        # Mock query for marking signal unprocessed
        mock_query_job = Mock()
        mock_query_job.result = Mock()
        mock_query_job.num_dml_affected_rows = 1
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Persist insight
        result = await persistence_module.persist_insight(
            insight=sample_insight,
            correlation_id="test-corr-004"
        )
        
        # Verify result
        assert result.success is False
        assert "Unexpected error" in result.error
        
        # Verify signal was marked as unprocessed
        mock_bigquery_client.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_signal_unprocessed_success(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test marking signal as unprocessed"""
        # Mock successful update
        mock_query_job = Mock()
        mock_query_job.result = Mock()
        mock_query_job.num_dml_affected_rows = 1
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Mark signal unprocessed
        result = await persistence_module._mark_signal_unprocessed(
            signal_id="test-signal-001",
            correlation_id="test-corr-005"
        )
        
        # Verify result
        assert result is True
        
        # Verify query was executed
        mock_bigquery_client.query.assert_called_once()
        query = mock_bigquery_client.query.call_args[0][0]
        assert "processed = false" in query
        assert "processed_at = NULL" in query
        assert "test-signal-001" in query
    
    @pytest.mark.asyncio
    async def test_mark_signal_unprocessed_not_found(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test marking signal unprocessed when signal doesn't exist"""
        # Mock no rows affected
        mock_query_job = Mock()
        mock_query_job.result = Mock()
        mock_query_job.num_dml_affected_rows = 0
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Mark signal unprocessed
        result = await persistence_module._mark_signal_unprocessed(
            signal_id="nonexistent-signal",
            correlation_id="test-corr-006"
        )
        
        # Verify result
        assert result is False
    
    @pytest.mark.asyncio
    async def test_persist_insights_batch(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test batch persistence of multiple insights"""
        # Create multiple insights
        insights = [
            Insight(
                insight_id=f"insight-{i}",
                signal_id=f"signal-{i}",
                category="exchange",
                headline=f"Headline {i}",
                summary=f"Summary {i}",
                confidence=0.75,
                evidence=Evidence(
                    block_heights=[820000 + i],
                    transaction_ids=[]
                )
            )
            for i in range(3)
        ]
        
        # Mock successful inserts
        mock_bigquery_client.insert_rows_json.return_value = []
        
        # Persist batch
        results = await persistence_module.persist_insights_batch(
            insights=insights,
            correlation_id="test-corr-007"
        )
        
        # Verify results
        assert results["success_count"] == 3
        assert results["failure_count"] == 0
        assert len(results["insight_ids"]) == 3
        assert len(results["errors"]) == 0
        
        # Verify BigQuery was called for each insight
        assert mock_bigquery_client.insert_rows_json.call_count == 3
    
    @pytest.mark.asyncio
    async def test_persist_insights_batch_partial_failure(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test batch persistence with some failures"""
        # Create multiple insights
        insights = [
            Insight(
                insight_id=f"insight-{i}",
                signal_id=f"signal-{i}",
                category="miner",
                headline=f"Headline {i}",
                summary=f"Summary {i}",
                confidence=0.80,
                evidence=Evidence(
                    block_heights=[820000 + i],
                    transaction_ids=[]
                )
            )
            for i in range(3)
        ]
        
        # Mock mixed results (first succeeds, second fails, third succeeds)
        mock_bigquery_client.insert_rows_json.side_effect = [
            [],  # Success
            [{"error": "Error"}],  # Failure
            []   # Success
        ]
        
        # Mock query for marking signal unprocessed
        mock_query_job = Mock()
        mock_query_job.result = Mock()
        mock_query_job.num_dml_affected_rows = 1
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Persist batch
        results = await persistence_module.persist_insights_batch(
            insights=insights,
            correlation_id="test-corr-008"
        )
        
        # Verify results
        assert results["success_count"] == 2
        assert results["failure_count"] == 1
        assert len(results["insight_ids"]) == 2
        assert len(results["errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_insight_by_id(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test retrieving insight by ID"""
        # Mock query result
        mock_row = {
            "insight_id": "test-insight-001",
            "signal_id": "test-signal-001",
            "category": "whale",
            "headline": "Test Headline",
            "summary": "Test Summary",
            "confidence": 0.90
        }
        mock_query_job = Mock()
        mock_query_job.result.return_value = [mock_row]
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Get insight
        result = await persistence_module.get_insight_by_id("test-insight-001")
        
        # Verify result
        assert result is not None
        assert result["insight_id"] == "test-insight-001"
        assert result["headline"] == "Test Headline"
    
    @pytest.mark.asyncio
    async def test_get_insight_by_id_not_found(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test retrieving non-existent insight"""
        # Mock empty result
        mock_query_job = Mock()
        mock_query_job.result.return_value = []
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Get insight
        result = await persistence_module.get_insight_by_id("nonexistent")
        
        # Verify result
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_insights_by_signal_id(
        self,
        persistence_module,
        mock_bigquery_client
    ):
        """Test retrieving insights by signal ID"""
        # Mock query results
        mock_rows = [
            {"insight_id": f"insight-{i}", "signal_id": "test-signal-001"}
            for i in range(2)
        ]
        mock_query_job = Mock()
        mock_query_job.result.return_value = mock_rows
        mock_bigquery_client.query.return_value = mock_query_job
        
        # Get insights
        results = await persistence_module.get_insights_by_signal_id("test-signal-001")
        
        # Verify results
        assert len(results) == 2
        assert all(r["signal_id"] == "test-signal-001" for r in results)
    
    def test_module_initialization(self, mock_bigquery_client):
        """Test module initialization with custom parameters"""
        module = InsightPersistenceModule(
            bigquery_client=mock_bigquery_client,
            project_id="custom-project",
            dataset_id="custom_dataset"
        )
        
        assert module.project_id == "custom-project"
        assert module.dataset_id == "custom_dataset"
        assert module.insights_table == "custom-project.custom_dataset.insights"
        assert module.signals_table == "custom-project.custom_dataset.signals"
    
    @pytest.mark.asyncio
    async def test_chart_url_always_null(
        self,
        persistence_module,
        mock_bigquery_client,
        sample_insight
    ):
        """Test that chart_url is always set to null on persistence"""
        # Set chart_url to non-null value
        sample_insight.chart_url = "https://example.com/chart.png"
        
        # Mock successful insert
        mock_bigquery_client.insert_rows_json.return_value = []
        
        # Persist insight
        await persistence_module.persist_insight(sample_insight)
        
        # Verify chart_url was set to None
        call_args = mock_bigquery_client.insert_rows_json.call_args
        inserted_data = call_args[0][1][0]
        assert inserted_data["chart_url"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
