"""
Integration tests for Chart Renderer API
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from src.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self):
        """Test health check returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chart-renderer"


class TestMempoolEndpoint:
    """Tests for mempool chart endpoint"""
    
    def test_render_mempool_chart(self):
        """Test mempool chart generation endpoint"""
        request_data = {
            "block_height": 800000,
            "timestamp": datetime.now().isoformat(),
            "fee_quantiles": {
                "p10": 5.0,
                "p25": 10.0,
                "p50": 20.0,
                "p75": 35.0,
                "p90": 50.0
            },
            "avg_fee_rate": 25.0,
            "transaction_count": 2500,
            "size": "desktop"
        }
        
        response = client.post("/render/mempool", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "chart_url" in data
        assert "chart_path" in data
        assert data["width"] > 0
        assert data["height"] > 0
        assert data["size_bytes"] > 0
    
    def test_render_mempool_chart_mobile(self):
        """Test mobile mempool chart generation"""
        request_data = {
            "block_height": 800000,
            "timestamp": datetime.now().isoformat(),
            "fee_quantiles": {
                "p10": 5.0,
                "p25": 10.0,
                "p50": 20.0,
                "p75": 35.0,
                "p90": 50.0
            },
            "avg_fee_rate": 25.0,
            "transaction_count": 2500,
            "size": "mobile"
        }
        
        response = client.post("/render/mempool", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["width"] == 800  # Mobile width


class TestExchangeEndpoint:
    """Tests for exchange chart endpoint"""
    
    def test_render_exchange_chart(self):
        """Test exchange chart generation endpoint"""
        now = datetime.now()
        timestamps = [
            (now - timedelta(hours=i)).isoformat() 
            for i in range(24, 0, -1)
        ]
        
        request_data = {
            "entity_name": "Binance",
            "timestamps": timestamps,
            "inflows": [100.0 + i * 10 for i in range(24)],
            "outflows": [80.0 + i * 8 for i in range(24)],
            "net_flows": [20.0 + i * 2 for i in range(24)],
            "size": "desktop"
        }
        
        response = client.post("/render/exchange", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "chart_url" in data
        assert data["size_bytes"] > 0


class TestMinerEndpoint:
    """Tests for miner chart endpoint"""
    
    def test_render_miner_chart(self):
        """Test miner chart generation endpoint"""
        now = datetime.now()
        timestamps = [
            (now - timedelta(days=i)).isoformat() 
            for i in range(30, 0, -1)
        ]
        
        request_data = {
            "entity_name": "Foundry USA",
            "timestamps": timestamps,
            "balances": [10000.0 + i * 50 for i in range(30)],
            "daily_changes": [50.0 if i % 3 == 0 else -20.0 for i in range(30)],
            "size": "desktop"
        }
        
        response = client.post("/render/miner", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "chart_url" in data


class TestWhaleEndpoint:
    """Tests for whale chart endpoint"""
    
    def test_render_whale_chart(self):
        """Test whale chart generation endpoint"""
        now = datetime.now()
        timestamps = [
            (now - timedelta(days=i)).isoformat() 
            for i in range(30, 0, -1)
        ]
        
        request_data = {
            "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "timestamps": timestamps,
            "balances": [5000.0 + i * 100 for i in range(30)],
            "seven_day_changes": [100.0 if i % 2 == 0 else -50.0 for i in range(30)],
            "accumulation_streak_days": 7,
            "size": "desktop"
        }
        
        response = client.post("/render/whale", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "chart_url" in data


class TestPredictiveEndpoint:
    """Tests for predictive chart endpoint"""
    
    def test_render_predictive_chart(self):
        """Test predictive chart generation endpoint"""
        now = datetime.now()
        historical_times = [
            (now - timedelta(hours=i)).isoformat() 
            for i in range(24, 0, -1)
        ]
        predicted_times = [
            (now + timedelta(hours=i)).isoformat() 
            for i in range(1, 7)
        ]
        all_times = historical_times + predicted_times
        
        request_data = {
            "signal_type": "fee_forecast",
            "timestamps": all_times,
            "historical_values": [20.0 + i * 2 for i in range(24)],
            "predicted_values": [70.0 + i * 5 for i in range(6)],
            "confidence_intervals": [[60.0 + i * 4, 80.0 + i * 6] for i in range(6)],
            "forecast_horizon": "6h",
            "size": "desktop"
        }
        
        response = client.post("/render/predictive", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "chart_url" in data


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_invalid_mempool_data(self):
        """Test error handling for invalid data"""
        request_data = {
            "block_height": -1,  # Invalid
            "timestamp": datetime.now().isoformat(),
            "fee_quantiles": {},
            "avg_fee_rate": 25.0,
            "transaction_count": 2500
        }
        
        response = client.post("/render/mempool", json=request_data)
        assert response.status_code == 422  # Validation error
