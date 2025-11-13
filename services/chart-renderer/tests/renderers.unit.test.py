"""
Unit tests for chart renderers
"""

import pytest
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from src.models import (
    MempoolChartRequest,
    ExchangeChartRequest,
    MinerChartRequest,
    WhaleChartRequest,
    PredictiveChartRequest,
    ChartSize
)
from src.renderers import (
    MempoolRenderer,
    ExchangeRenderer,
    MinerRenderer,
    WhaleRenderer,
    PredictiveRenderer
)


class TestMempoolRenderer:
    """Tests for mempool chart renderer"""
    
    def test_render_mempool_chart_desktop(self):
        """Test mempool chart rendering for desktop"""
        renderer = MempoolRenderer()
        
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
        
        chart_bytes = renderer.render(request)
        
        # Verify it's valid PNG
        assert chart_bytes is not None
        assert len(chart_bytes) > 0
        
        # Verify image can be opened
        img = Image.open(BytesIO(chart_bytes))
        assert img.format == 'PNG'
        assert img.width > 0
        assert img.height > 0
    
    def test_render_mempool_chart_mobile(self):
        """Test mempool chart rendering for mobile"""
        renderer = MempoolRenderer()
        
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
            size=ChartSize.MOBILE
        )
        
        chart_bytes = renderer.render(request)
        
        # Verify mobile size is smaller than desktop
        img = Image.open(BytesIO(chart_bytes))
        assert img.width == 800  # Mobile width


class TestExchangeRenderer:
    """Tests for exchange chart renderer"""
    
    def test_render_exchange_chart(self):
        """Test exchange flow chart rendering"""
        renderer = ExchangeRenderer()
        
        # Generate sample data
        now = datetime.now()
        timestamps = [now - timedelta(hours=i) for i in range(24, 0, -1)]
        
        request = ExchangeChartRequest(
            entity_name="Binance",
            timestamps=timestamps,
            inflows=[100.0 + i * 10 for i in range(24)],
            outflows=[80.0 + i * 8 for i in range(24)],
            net_flows=[20.0 + i * 2 for i in range(24)],
            spike_threshold=300.0,
            size=ChartSize.DESKTOP
        )
        
        chart_bytes = renderer.render(request)
        
        # Verify it's valid PNG
        assert chart_bytes is not None
        img = Image.open(BytesIO(chart_bytes))
        assert img.format == 'PNG'


class TestMinerRenderer:
    """Tests for miner chart renderer"""
    
    def test_render_miner_chart(self):
        """Test miner treasury chart rendering"""
        renderer = MinerRenderer()
        
        # Generate sample data
        now = datetime.now()
        timestamps = [now - timedelta(days=i) for i in range(30, 0, -1)]
        
        request = MinerChartRequest(
            entity_name="Foundry USA",
            timestamps=timestamps,
            balances=[10000.0 + i * 50 for i in range(30)],
            daily_changes=[50.0 if i % 3 == 0 else -20.0 for i in range(30)],
            size=ChartSize.DESKTOP
        )
        
        chart_bytes = renderer.render(request)
        
        # Verify it's valid PNG
        assert chart_bytes is not None
        img = Image.open(BytesIO(chart_bytes))
        assert img.format == 'PNG'
        # Dual-panel chart should be taller
        assert img.height > img.width * 0.375


class TestWhaleRenderer:
    """Tests for whale chart renderer"""
    
    def test_render_whale_chart(self):
        """Test whale accumulation chart rendering"""
        renderer = WhaleRenderer()
        
        # Generate sample data
        now = datetime.now()
        timestamps = [now - timedelta(days=i) for i in range(30, 0, -1)]
        
        request = WhaleChartRequest(
            address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            timestamps=timestamps,
            balances=[5000.0 + i * 100 for i in range(30)],
            seven_day_changes=[100.0 if i % 2 == 0 else -50.0 for i in range(30)],
            accumulation_streak_days=7,
            size=ChartSize.DESKTOP
        )
        
        chart_bytes = renderer.render(request)
        
        # Verify it's valid PNG
        assert chart_bytes is not None
        img = Image.open(BytesIO(chart_bytes))
        assert img.format == 'PNG'


class TestPredictiveRenderer:
    """Tests for predictive chart renderer"""
    
    def test_render_predictive_chart(self):
        """Test predictive signal chart rendering"""
        renderer = PredictiveRenderer()
        
        # Generate sample data
        now = datetime.now()
        historical_times = [now - timedelta(hours=i) for i in range(24, 0, -1)]
        predicted_times = [now + timedelta(hours=i) for i in range(1, 7)]
        all_times = historical_times + predicted_times
        
        request = PredictiveChartRequest(
            signal_type="fee_forecast",
            timestamps=all_times,
            historical_values=[20.0 + i * 2 for i in range(24)],
            predicted_values=[70.0 + i * 5 for i in range(6)],
            confidence_intervals=[(60.0 + i * 4, 80.0 + i * 6) for i in range(6)],
            forecast_horizon="6h",
            size=ChartSize.DESKTOP
        )
        
        chart_bytes = renderer.render(request)
        
        # Verify it's valid PNG
        assert chart_bytes is not None
        img = Image.open(BytesIO(chart_bytes))
        assert img.format == 'PNG'


class TestChartStyling:
    """Tests for chart styling consistency"""
    
    def test_mobile_vs_desktop_sizing(self):
        """Test that mobile charts are smaller than desktop"""
        renderer = MempoolRenderer()
        
        base_request = MempoolChartRequest(
            block_height=800000,
            timestamp=datetime.now(),
            fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 35.0, "p90": 50.0},
            avg_fee_rate=25.0,
            transaction_count=2500,
            size=ChartSize.DESKTOP
        )
        
        # Desktop chart
        desktop_bytes = renderer.render(base_request)
        desktop_img = Image.open(BytesIO(desktop_bytes))
        
        # Mobile chart
        base_request.size = ChartSize.MOBILE
        mobile_bytes = renderer.render(base_request)
        mobile_img = Image.open(BytesIO(mobile_bytes))
        
        # Mobile should be smaller
        assert mobile_img.width < desktop_img.width
        assert mobile_img.height < desktop_img.height
    
    def test_aspect_ratio_consistency(self):
        """Test that charts maintain 16:6 aspect ratio"""
        renderer = MempoolRenderer()
        
        request = MempoolChartRequest(
            block_height=800000,
            timestamp=datetime.now(),
            fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 35.0, "p90": 50.0},
            avg_fee_rate=25.0,
            transaction_count=2500,
            size=ChartSize.DESKTOP
        )
        
        chart_bytes = renderer.render(request)
        img = Image.open(BytesIO(chart_bytes))
        
        # Check aspect ratio (allowing for some margin due to tight_layout)
        aspect_ratio = img.width / img.height
        expected_ratio = 16 / 6
        assert abs(aspect_ratio - expected_ratio) < 0.5  # Allow some variance
