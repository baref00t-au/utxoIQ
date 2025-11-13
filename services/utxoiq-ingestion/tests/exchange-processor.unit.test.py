"""
Unit tests for exchange flow detection
"""

import pytest
from datetime import datetime, timedelta
from src.processors.exchange_processor import ExchangeProcessor
from src.models import ExchangeFlowData, SignalType


@pytest.fixture
def exchange_processor():
    """Create exchange processor instance"""
    return ExchangeProcessor()


@pytest.fixture
def sample_exchange_flow():
    """Create sample exchange flow data"""
    return ExchangeFlowData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        entity_id="exchange_001",
        entity_name="Binance",
        inflow_btc=150.0,
        outflow_btc=100.0,
        net_flow_btc=50.0,
        transaction_count=25,
        transaction_ids=[f"tx_{i}" for i in range(25)]
    )


def test_analyze_entity_flows_no_anomaly(exchange_processor, sample_exchange_flow):
    """Test entity flow analysis without anomaly"""
    historical_flows = [
        ExchangeFlowData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            entity_id="exchange_001",
            entity_name="Binance",
            inflow_btc=140.0 + i,
            outflow_btc=100.0,
            net_flow_btc=40.0 + i,
            transaction_count=20,
            transaction_ids=[f"tx_{j}" for j in range(20)]
        )
        for i in range(20)
    ]
    
    analysis = exchange_processor.analyze_entity_flows(
        sample_exchange_flow,
        historical_flows
    )
    
    assert analysis["entity_id"] == "exchange_001"
    assert analysis["current_inflow"] == 150.0
    assert "z_score" in analysis
    assert "is_anomaly" in analysis


def test_analyze_entity_flows_with_anomaly(exchange_processor):
    """Test entity flow analysis with anomaly detection"""
    # Create flow with significant spike
    spike_flow = ExchangeFlowData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        entity_id="exchange_001",
        entity_name="Binance",
        inflow_btc=1000.0,  # Large spike
        outflow_btc=100.0,
        net_flow_btc=900.0,
        transaction_count=50,
        transaction_ids=[f"tx_{i}" for i in range(50)]
    )
    
    # Historical data with normal flows
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
        for i in range(20)
    ]
    
    analysis = exchange_processor.analyze_entity_flows(
        spike_flow,
        historical_flows
    )
    
    assert analysis["is_anomaly"] is True
    assert analysis["anomaly_type"] == "inflow_spike"
    assert abs(analysis["z_score"]) > 2.5


def test_detect_unusual_patterns(exchange_processor, sample_exchange_flow):
    """Test unusual pattern detection"""
    historical_flows = [
        ExchangeFlowData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            entity_id="exchange_001",
            entity_name="Binance",
            inflow_btc=50.0,
            outflow_btc=40.0,
            net_flow_btc=10.0,
            transaction_count=10,
            transaction_ids=[f"tx_{j}" for j in range(10)]
        )
        for i in range(20)
    ]
    
    patterns = exchange_processor.detect_unusual_patterns(
        sample_exchange_flow,
        historical_flows
    )
    
    assert isinstance(patterns, dict)
    assert "volume_spike" in patterns
    assert patterns["volume_spike"] is True  # 150 vs historical 50


def test_calculate_confidence_score(exchange_processor, sample_exchange_flow):
    """Test confidence score calculation"""
    analysis = {"is_anomaly": True, "z_score": 3.5}
    patterns = {"volume_spike": True, "large_single_transaction": False}
    
    confidence = exchange_processor.calculate_confidence_score(
        sample_exchange_flow,
        analysis,
        patterns
    )
    
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.5  # Should have high confidence with anomaly


def test_generate_exchange_signal(exchange_processor, sample_exchange_flow):
    """Test exchange signal generation"""
    signal = exchange_processor.generate_exchange_signal(sample_exchange_flow)
    
    assert signal.type == SignalType.EXCHANGE
    assert 0.0 <= signal.strength <= 1.0
    assert signal.block_height == 800000
    assert signal.entity_ids == ["exchange_001"]
    assert len(signal.transaction_ids) <= 10
    assert "entity_name" in signal.data
    assert signal.is_predictive is False
