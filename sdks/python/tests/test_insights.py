"""Tests for insights resource."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from utxoiq import UtxoIQClient
from utxoiq.models import Insight


class TestInsightsResource:
    """Test cases for InsightsResource."""
    
    @patch('requests.Session.request')
    def test_get_latest_insights(self, mock_request):
        """Test getting latest insights."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "insights": [
                {
                    "id": "insight-1",
                    "signal_type": "mempool",
                    "headline": "Test Insight",
                    "summary": "Test summary",
                    "confidence": 0.85,
                    "timestamp": "2025-11-07T10:00:00Z",
                    "block_height": 800000,
                    "evidence": [],
                    "tags": ["test"],
                    "is_predictive": False
                }
            ]
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        insights = client.insights.get_latest(limit=10)
        
        assert len(insights) == 1
        assert isinstance(insights[0], Insight)
        assert insights[0].id == "insight-1"
        assert insights[0].confidence == 0.85
    
    @patch('requests.Session.request')
    def test_get_latest_with_filters(self, mock_request):
        """Test getting latest insights with filters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"insights": []}
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        client.insights.get_latest(
            limit=20,
            category="mempool",
            min_confidence=0.7
        )
        
        # Verify request was made with correct parameters
        call_args = mock_request.call_args
        assert call_args[1]["params"]["limit"] == 20
        assert call_args[1]["params"]["category"] == "mempool"
        assert call_args[1]["params"]["min_confidence"] == 0.7
    
    @patch('requests.Session.request')
    def test_get_public_insights(self, mock_request):
        """Test getting public insights (Guest Mode)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"insights": []}
        mock_request.return_value = mock_response
        
        client = UtxoIQClient()  # No auth
        insights = client.insights.get_public(limit=20)
        
        assert isinstance(insights, list)
    
    @patch('requests.Session.request')
    def test_get_insight_by_id(self, mock_request):
        """Test getting specific insight by ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "insight-123",
            "signal_type": "exchange",
            "headline": "Exchange Inflow Spike",
            "summary": "Large inflow detected",
            "confidence": 0.92,
            "timestamp": "2025-11-07T10:00:00Z",
            "block_height": 800001,
            "evidence": [],
            "tags": [],
            "is_predictive": False
        }
        mock_request.return_value = mock_response
        
        client = UtxoIQClient(api_key="test-key")
        insight = client.insights.get_by_id("insight-123")
        
        assert isinstance(insight, Insight)
        assert insight.id == "insight-123"
        assert insight.signal_type == "exchange"
