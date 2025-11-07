"""
Tests for data models
"""

import pytest
from datetime import datetime
from src.models import (
    MempoolChartRequest,
    ExchangeChartRequest,
    MinerChartRequest,
    WhaleChartRequest,
    PredictiveChartRequest,
    ChartSize,
    ChartResponse
)


class TestMempoolChartRequest:
    """Tests for mempool chart request model"""
    
    def test_valid_mempool_request(self):
        """Test valid mempool chart request"""
        request = MempoolChartRequest(
            block_height=800000,
            timestamp=datetime.now(),
            fee_quantiles={
                "p10": 5.0,
                "p25": 10.0,
                "p50": 20.0,
                "p75": 35.0,
                "p90": 50.0
            },
            avg_fee_rate=25.0,
            transaction_count=2500,
            size=ChartSize.DESKTOP
        )
        
        assert request.block_height == 800000
        assert request.avg_fee_rate == 25.0
        assert request.size == ChartSize.DESKTOP
    
    def test_invalid_block_height(self):
        """Test validation for invalid block height"""
        with pytest.raises(Exception):  # Pydantic validation error
            MempoolChartRequest(
                block_height=-1,  # Invalid
                timestamp=datetime.now(),
                fee_quantiles={},
                avg_fee_rate=25.0,
                transaction_count=2500
            )


class TestExchangeChartRequest:
    """Tests for exchange chart request model"""
    
    def test_valid_exchange_request(self):
        """Test valid exchange chart request"""
        now = datetime.now()
        request = ExchangeChartRequest(
            entity_name="Binance",
            timestamps=[now],
            inflows=[100.0],
            outflows=[80.0],
            net_flows=[20.0],
            size=ChartSize.MOBILE
        )
        
        assert request.entity_name == "Binance"
        assert len(request.timestamps) == 1
        assert request.size == ChartSize.MOBILE


class TestChartResponse:
    """Tests for chart response model"""
    
    def test_valid_chart_response(self):
        """Test valid chart response"""
        response = ChartResponse(
            chart_url="https://storage.googleapis.com/bucket/chart.png",
            chart_path="charts/mempool/abc123.png",
            width=1200,
            height=450,
            size_bytes=50000
        )
        
        assert response.width == 1200
        assert response.height == 450
        assert "chart.png" in response.chart_url
