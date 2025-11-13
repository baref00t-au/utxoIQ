"""
Simple test runner to verify signal processors work correctly
"""

import sys
sys.path.insert(0, 'src')

from datetime import datetime, timedelta
from src.processors.mempool_processor import MempoolProcessor
from src.processors.exchange_processor import ExchangeProcessor
from src.processors.miner_processor import MinerProcessor
from src.processors.whale_processor import WhaleProcessor
from src.processors.predictive_analytics import PredictiveAnalytics
from src.models import (
    MempoolData, ExchangeFlowData, MinerTreasuryData,
    WhaleActivityData, SignalType
)


def test_mempool_processor():
    """Test mempool signal processing"""
    print("Testing Mempool Processor...")
    
    processor = MempoolProcessor()
    
    # Test fee quantile calculation
    fee_rates = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    quantiles = processor.calculate_fee_quantiles(fee_rates)
    assert "p50" in quantiles
    assert quantiles["p50"] > 0
    print("✓ Fee quantile calculation works")
    
    # Test signal generation
    mempool_data = MempoolData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        transaction_count=5000,
        total_fees=2.5,
        fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 40.0, "p90": 80.0},
        avg_fee_rate=25.0,
        mempool_size_bytes=100000000
    )
    
    signal = processor.generate_mempool_signal(mempool_data)
    assert signal.type == SignalType.MEMPOOL
    assert 0.0 <= signal.strength <= 1.0
    print("✓ Mempool signal generation works")
    print(f"  Signal strength: {signal.strength:.2f}")


def test_exchange_processor():
    """Test exchange flow detection"""
    print("\nTesting Exchange Processor...")
    
    processor = ExchangeProcessor()
    
    flow_data = ExchangeFlowData(
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
    
    signal = processor.generate_exchange_signal(flow_data)
    assert signal.type == SignalType.EXCHANGE
    assert 0.0 <= signal.strength <= 1.0
    print("✓ Exchange signal generation works")
    print(f"  Signal strength: {signal.strength:.2f}")


def test_miner_processor():
    """Test miner treasury tracking"""
    print("\nTesting Miner Processor...")
    
    processor = MinerProcessor()
    
    miner_data = MinerTreasuryData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        entity_id="miner_001",
        entity_name="F2Pool",
        balance_btc=5000.0,
        daily_change_btc=-50.0,
        mining_rewards_btc=6.25,
        transaction_ids=[f"tx_{i}" for i in range(10)]
    )
    
    signal = processor.generate_miner_signal(miner_data)
    assert signal.type == SignalType.MINER
    assert 0.0 <= signal.strength <= 1.0
    print("✓ Miner signal generation works")
    print(f"  Signal strength: {signal.strength:.2f}")


def test_whale_processor():
    """Test whale accumulation detection"""
    print("\nTesting Whale Processor...")
    
    processor = WhaleProcessor()
    
    whale_data = WhaleActivityData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        balance_btc=500.0,
        seven_day_change_btc=25.0,
        accumulation_streak_days=7,
        transaction_ids=[f"tx_{i}" for i in range(5)]
    )
    
    signal = processor.generate_whale_signal(whale_data)
    assert signal.type == SignalType.WHALE
    assert 0.0 <= signal.strength <= 1.0
    print("✓ Whale signal generation works")
    print(f"  Signal strength: {signal.strength:.2f}")


def test_predictive_analytics():
    """Test predictive analytics models"""
    print("\nTesting Predictive Analytics...")
    
    analytics = PredictiveAnalytics()
    
    # Create historical mempool data
    historical_mempool = [
        MempoolData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            transaction_count=5000,
            total_fees=2.5,
            fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 40.0, "p90": 80.0},
            avg_fee_rate=25.0,
            mempool_size_bytes=100000000
        )
        for i in range(50)
    ]
    
    current_mempool = MempoolData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        transaction_count=5000,
        total_fees=2.5,
        fee_quantiles={"p10": 5.0, "p25": 10.0, "p50": 20.0, "p75": 40.0, "p90": 80.0},
        avg_fee_rate=26.0,
        mempool_size_bytes=100000000
    )
    
    # Test fee forecast
    forecast = analytics.forecast_next_block_fees(historical_mempool, current_mempool)
    assert "prediction" in forecast
    assert forecast["prediction"] > 0
    print("✓ Fee forecasting works")
    print(f"  Predicted fee: {forecast['prediction']:.2f} sat/vB")
    
    # Test liquidity pressure
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
    
    pressure = analytics.compute_liquidity_pressure_index(historical_flows, current_flow)
    assert "pressure_index" in pressure
    assert 0.0 <= pressure["pressure_index"] <= 1.0
    print("✓ Liquidity pressure calculation works")
    print(f"  Pressure index: {pressure['pressure_index']:.2f}")
    print(f"  Pressure level: {pressure['pressure_level']}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Feature Engine Signal Processor Tests")
    print("=" * 60)
    
    try:
        test_mempool_processor()
        test_exchange_processor()
        test_miner_processor()
        test_whale_processor()
        test_predictive_analytics()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
