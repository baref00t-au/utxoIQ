"""
Unit tests for predictive analytics models
"""

import pytest
from datetime import datetime, timedelta
from src.processors.predictive_analytics import PredictiveAnalytics
from src.models import MempoolData, ExchangeFlowData, SignalType


@pytest.fixture
def predictive_analytics():
    """Create predictive analytics instance"""
    return PredictiveAnalytics()


@pytest.fixture
def historical_mempool_data():
    """Create historical mempool data"""
    return [
        MempoolData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            transaction_count=5000,
            total_fees=2.5,
            fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 40.0, "p90": 80.0},
            avg_fee_rate=25.0 + (i % 5),
            mempool_size_bytes=100000000
        )
        for i in range(50)
    ]


@pytest.fixture
def current_mempool_data():
    """Create current mempool data"""
    return MempoolData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        transaction_count=5000,
        total_fees=2.5,
        fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 40.0, "p90": 80.0},
        avg_fee_rate=26.0,
        mempool_size_bytes=100000000
    )


def test_forecast_next_block_fees(predictive_analytics, historical_mempool_data, current_mempool_data):
    """Test next block fee forecasting"""
    forecast = predictive_analytics.forecast_next_block_fees(
        historical_mempool_data,
        current_mempool_data
    )
    
    assert "prediction" in forecast
    assert "confidence_interval" in forecast
    assert "model_confidence" in forecast
    assert forecast["prediction"] > 0
    assert forecast["confidence_interval"][0] < forecast["confidence_interval"][1]
    assert 0.0 <= forecast["model_confidence"] <= 1.0


def test_forecast_with_insufficient_data(predictive_analytics, current_mempool_data):
    """Test forecasting with insufficient historical data"""
    forecast = predictive_analytics.forecast_next_block_fees(
        [],
        current_mempool_data
    )
    
    assert forecast["method"] == "fallback"
    assert forecast["prediction"] == current_mempool_data.avg_fee_rate


def test_exponential_smoothing(predictive_analytics):
    """Test exponential smoothing algorithm"""
    data = [10.0, 12.0, 11.0, 13.0, 14.0]
    alpha = 0.3
    
    result = predictive_analytics._exponential_smoothing(data, alpha)
    
    assert result > 0
    assert 10.0 <= result <= 15.0


def test_compute_liquidity_pressure_index(predictive_analytics):
    """Test liquidity pressure index computation"""
    historical_flows = [
        ExchangeFlowData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            entity_id="exchange_001",
            entity_name="Binance",
            inflow_btc=100.0,
            outflow_btc=90.0,
            net_flow_btc=10.0,
            transaction_count=20,
            transaction_ids=[f"tx_{j}" for j in range(20)]
        )
        for i in range(50)
    ]
    
    current_flow = ExchangeFlowData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        entity_id="exchange_001",
        entity_name="Binance",
        inflow_btc=200.0,
        outflow_btc=50.0,
        net_flow_btc=150.0,
        transaction_count=30,
        transaction_ids=[f"tx_{i}" for i in range(30)]
    )
    
    pressure = predictive_analytics.compute_liquidity_pressure_index(
        historical_flows,
        current_flow
    )
    
    assert "pressure_index" in pressure
    assert "pressure_level" in pressure
    assert "confidence" in pressure
    assert 0.0 <= pressure["pressure_index"] <= 1.0
    assert pressure["pressure_level"] in [
        "high_selling_pressure",
        "moderate_selling_pressure",
        "neutral",
        "moderate_buying_pressure",
        "high_buying_pressure"
    ]


def test_track_prediction_accuracy(predictive_analytics):
    """Test prediction accuracy tracking"""
    accuracy = predictive_analytics.track_prediction_accuracy(
        prediction=25.0,
        actual=27.0,
        prediction_type="fee_forecast"
    )
    
    assert "prediction" in accuracy
    assert "actual" in accuracy
    assert "absolute_error" in accuracy
    assert "percentage_error" in accuracy
    assert "accuracy_score" in accuracy
    assert accuracy["absolute_error"] == 2.0
    assert 0.0 <= accuracy["accuracy_score"] <= 1.0


def test_generate_fee_forecast_signal(predictive_analytics, historical_mempool_data, current_mempool_data):
    """Test fee forecast signal generation"""
    signal = predictive_analytics.generate_fee_forecast_signal(
        historical_mempool_data,
        current_mempool_data
    )
    
    assert signal.type == SignalType.PREDICTIVE
    assert signal.is_predictive is True
    assert signal.prediction_confidence_interval is not None
    assert 0.0 <= signal.strength <= 1.0
    assert "predictive_signal" in signal.data
    assert "forecast_details" in signal.data


def test_generate_liquidity_pressure_signal(predictive_analytics):
    """Test liquidity pressure signal generation"""
    historical_flows = [
        ExchangeFlowData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            entity_id="exchange_001",
            entity_name="Binance",
            inflow_btc=100.0,
            outflow_btc=90.0,
            net_flow_btc=10.0,
            transaction_count=20,
            transaction_ids=[f"tx_{j}" for j in range(20)]
        )
        for i in range(50)
    ]
    
    current_flow = ExchangeFlowData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        entity_id="exchange_001",
        entity_name="Binance",
        inflow_btc=200.0,
        outflow_btc=50.0,
        net_flow_btc=150.0,
        transaction_count=30,
        transaction_ids=[f"tx_{i}" for i in range(30)]
    )
    
    signal = predictive_analytics.generate_liquidity_pressure_signal(
        historical_flows,
        current_flow
    )
    
    assert signal.type == SignalType.PREDICTIVE
    assert signal.is_predictive is True
    assert signal.prediction_confidence_interval is not None
    assert 0.0 <= signal.strength <= 1.0
    assert "predictive_signal" in signal.data
    assert "pressure_details" in signal.data
