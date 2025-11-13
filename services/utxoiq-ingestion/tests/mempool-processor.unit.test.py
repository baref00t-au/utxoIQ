"""
Unit tests for mempool signal processing
"""

import pytest
from datetime import datetime, timedelta
from src.processors.mempool_processor import MempoolProcessor
from src.models import MempoolData, SignalType


@pytest.fixture
def mempool_processor():
    """Create mempool processor instance"""
    return MempoolProcessor()


@pytest.fixture
def sample_mempool_data():
    """Create sample mempool data"""
    return MempoolData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        transaction_count=5000,
        total_fees=2.5,
        fee_quantiles={
            "p10": 5.0,
            "p25": 10.0,
            "p50": 20.0,
            "p75": 40.0,
            "p90": 80.0
        },
        avg_fee_rate=25.0,
        mempool_size_bytes=100000000
    )


def test_calculate_fee_quantiles(mempool_processor):
    """Test fee quantile calculation"""
    fee_rates = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    
    quantiles = mempool_processor.calculate_fee_quantiles(fee_rates)
    
    assert "p10" in quantiles
    assert "p50" in quantiles
    assert "p90" in quantiles
    assert quantiles["p50"] == 27.5  # Median of the list
    assert quantiles["p10"] < quantiles["p50"] < quantiles["p90"]


def test_calculate_fee_quantiles_empty_list(mempool_processor):
    """Test fee quantile calculation with empty list"""
    quantiles = mempool_processor.calculate_fee_quantiles([])
    
    assert all(v == 0.0 for v in quantiles.values())


def test_estimate_block_inclusion_time(mempool_processor):
    """Test block inclusion time estimation"""
    quantiles = {
        "p10": 5.0,
        "p25": 10.0,
        "p50": 20.0,
        "p75": 40.0,
        "p90": 80.0
    }
    
    # High priority fee
    high_fee_estimate = mempool_processor.estimate_block_inclusion_time(
        fee_rate=85.0,
        current_quantiles=quantiles
    )
    assert high_fee_estimate["estimated_blocks"] == 1.0
    assert high_fee_estimate["priority_tier"] == "high"
    
    # Medium priority fee
    medium_fee_estimate = mempool_processor.estimate_block_inclusion_time(
        fee_rate=25.0,
        current_quantiles=quantiles
    )
    assert medium_fee_estimate["estimated_blocks"] == 3.0
    assert medium_fee_estimate["priority_tier"] == "medium"
    
    # Low priority fee
    low_fee_estimate = mempool_processor.estimate_block_inclusion_time(
        fee_rate=3.0,
        current_quantiles=quantiles
    )
    assert low_fee_estimate["estimated_blocks"] == 12.0
    assert low_fee_estimate["priority_tier"] == "low"


def test_calculate_confidence_score(mempool_processor, sample_mempool_data):
    """Test confidence score calculation"""
    confidence = mempool_processor.calculate_confidence_score(
        sample_mempool_data,
        historical_avg=20.0
    )
    
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.5  # Should have decent confidence with good data


def test_generate_mempool_signal(mempool_processor, sample_mempool_data):
    """Test mempool signal generation"""
    signal = mempool_processor.generate_mempool_signal(sample_mempool_data)
    
    assert signal.type == SignalType.MEMPOOL
    assert 0.0 <= signal.strength <= 1.0
    assert signal.block_height == 800000
    assert "fee_quantiles" in signal.data
    assert "avg_fee_rate" in signal.data
    assert signal.is_predictive is False


def test_generate_mempool_signal_with_spike(mempool_processor):
    """Test mempool signal generation with fee spike"""
    current_data = MempoolData(
        block_height=800001,
        timestamp=datetime.utcnow(),
        transaction_count=5000,
        total_fees=10.0,
        fee_quantiles={"p10": 50.0, "p25": 100.0, "p50": 200.0, "p75": 400.0, "p90": 800.0},
        avg_fee_rate=250.0,
        mempool_size_bytes=100000000
    )
    
    historical_data = [
        MempoolData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            transaction_count=5000,
            total_fees=2.5,
            fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 40.0, "p90": 80.0},
            avg_fee_rate=25.0,
            mempool_size_bytes=100000000
        )
        for i in range(1, 11)
    ]
    
    signal = mempool_processor.generate_mempool_signal(
        current_data,
        historical_data
    )
    
    assert signal.data["is_spike"] is True
    assert signal.data["spike_magnitude"] > 0
