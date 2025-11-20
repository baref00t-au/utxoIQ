"""
Integration script to add PredictiveAnalyticsModule to Pipeline Orchestrator.

This script demonstrates how to integrate the PredictiveAnalyticsModule
into the existing pipeline orchestrator setup.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline_orchestrator import PipelineOrchestrator
from src.monitoring import MonitoringModule
from src.signal_persistence import SignalPersistenceModule
from src.processors import (
    MempoolProcessor,
    ExchangeProcessor,
    MinerProcessor,
    WhaleProcessor,
    TreasuryProcessor,
    PredictiveAnalyticsModule
)
from src.processors.base_processor import ProcessorConfig, ProcessingContext
from src.models import BlockData, MempoolData, ExchangeFlowData


class MockBigQueryClient:
    """Mock BigQuery client for testing."""
    
    def insert_rows_json(self, table_id, rows):
        """Mock insert operation."""
        print(f"  ✓ Inserted {len(rows)} rows to {table_id}")
        return []  # No errors


def create_sample_historical_data():
    """Create sample historical data for predictive analytics."""
    
    # Historical mempool data (last 50 blocks)
    historical_mempool = []
    for i in range(50):
        historical_mempool.append(MempoolData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            transaction_count=5000 + (i % 10) * 100,
            total_fees=2.5,
            fee_quantiles={
                "p10": 5.0,
                "p25": 10.0,
                "p50": 20.0 + (i % 5),
                "p75": 40.0,
                "p90": 80.0
            },
            avg_fee_rate=25.0 + (i % 5),
            mempool_size_bytes=100000000
        ))
    
    # Current mempool data
    current_mempool = MempoolData(
        block_height=800000,
        timestamp=datetime.utcnow(),
        transaction_count=5200,
        total_fees=2.8,
        fee_quantiles={
            "p10": 5.0,
            "p25": 10.0,
            "p50": 22.0,
            "p75": 42.0,
            "p90": 85.0
        },
        avg_fee_rate=28.0,
        mempool_size_bytes=105000000
    )
    
    # Historical exchange flows (last 50 blocks)
    historical_exchange_flows = []
    for i in range(50):
        historical_exchange_flows.append(ExchangeFlowData(
            block_height=800000 - i,
            timestamp=datetime.utcnow() - timedelta(minutes=10*i),
            entity_id="exchange_001",
            entity_name="Binance",
            inflow_btc=100.0 + (i % 10) * 5,
            outflow_btc=90.0 + (i % 8) * 3,
            net_flow_btc=10.0 + (i % 5),
            transaction_count=20,
            transaction_ids=[f"tx_{j}" for j in range(20)]
        ))
    
    # Current exchange flow
    current_exchange_flow = ExchangeFlowData(
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
    
    return {
        'historical_mempool': historical_mempool,
        'mempool_data': current_mempool,
        'historical_exchange_flows': historical_exchange_flows,
        'current_exchange_flow': current_exchange_flow
    }


async def main():
    """Demonstrate PredictiveAnalyticsModule integration."""
    
    print("=" * 80)
    print("PredictiveAnalyticsModule Integration Demo")
    print("=" * 80)
    
    # Step 1: Initialize all processors
    print("\n1. Initializing Signal Processors...")
    
    config = ProcessorConfig(
        enabled=True,
        confidence_threshold=0.5,  # Lower threshold for predictive signals
        time_window='24h'
    )
    
    processors = [
        MempoolProcessor(config),
        ExchangeProcessor(config),
        MinerProcessor(config),
        WhaleProcessor(config),
        TreasuryProcessor(config),
        PredictiveAnalyticsModule(config)  # ← NEW: Predictive analytics added!
    ]
    
    print(f"  ✓ Initialized {len(processors)} processors:")
    for processor in processors:
        status = "enabled" if processor.enabled else "disabled"
        print(f"    - {processor.__class__.__name__} ({status})")
    
    # Step 2: Initialize supporting modules
    print("\n2. Initializing Supporting Modules...")
    
    monitoring = MonitoringModule(
        project_id="utxoiq-dev",
        enabled=False  # Disable for demo
    )
    print("  ✓ MonitoringModule initialized")
    
    mock_bq_client = MockBigQueryClient()
    persistence = SignalPersistenceModule(
        bigquery_client=mock_bq_client,
        project_id="utxoiq-dev"
    )
    print("  ✓ SignalPersistenceModule initialized")
    
    # Step 3: Initialize Pipeline Orchestrator
    print("\n3. Initializing Pipeline Orchestrator...")
    
    orchestrator = PipelineOrchestrator(
        signal_processors=processors,
        signal_persistence=persistence,
        monitoring_module=monitoring
    )
    print("  ✓ PipelineOrchestrator initialized")
    
    # Step 4: Create sample block and historical data
    print("\n4. Preparing Test Data...")
    
    block = BlockData(
        block_hash="00000000000000000001234567890abcdef",
        height=800000,
        timestamp=datetime.utcnow(),
        size=1500000,
        tx_count=2500,
        fees_total=0.5
    )
    print(f"  ✓ Block data created (height: {block.height})")
    
    historical_data = create_sample_historical_data()
    print(f"  ✓ Historical data created:")
    print(f"    - {len(historical_data['historical_mempool'])} mempool snapshots")
    print(f"    - {len(historical_data['historical_exchange_flows'])} exchange flows")
    
    # Step 5: Process block through pipeline
    print("\n5. Processing Block Through Pipeline...")
    print("  (This will run all 6 processors in parallel)")
    
    result = await orchestrator.process_new_block(
        block=block,
        historical_data=historical_data
    )
    
    # Step 6: Display results
    print("\n6. Pipeline Results:")
    print("=" * 80)
    
    print(f"\n  Status: {'✓ SUCCESS' if result.success else '✗ FAILED'}")
    print(f"  Correlation ID: {result.correlation_id}")
    print(f"  Block Height: {result.block_height}")
    print(f"  Signals Generated: {len(result.signals)}")
    
    print(f"\n  Timing Metrics:")
    for metric, value in result.timing_metrics.items():
        print(f"    - {metric}: {value:.2f}ms")
    
    # Step 7: Analyze signals by type
    print("\n7. Signal Breakdown by Type:")
    print("=" * 80)
    
    signal_types = {}
    for signal in result.signals:
        signal_type = signal.type.value
        if signal_type not in signal_types:
            signal_types[signal_type] = []
        signal_types[signal_type].append(signal)
    
    for signal_type, signals in signal_types.items():
        print(f"\n  {signal_type.upper()} Signals: {len(signals)}")
        
        for i, signal in enumerate(signals, 1):
            print(f"\n    Signal {i}:")
            print(f"      - Confidence: {signal.strength:.3f}")
            print(f"      - Is Predictive: {signal.is_predictive}")
            
            # Show predictive signal details
            if signal.is_predictive and 'prediction_type' in signal.data:
                print(f"      - Prediction Type: {signal.data['prediction_type']}")
                print(f"      - Predicted Value: {signal.data['predicted_value']:.3f}")
                print(f"      - Confidence Interval: ({signal.data['confidence_interval'][0]:.3f}, {signal.data['confidence_interval'][1]:.3f})")
                print(f"      - Forecast Horizon: {signal.data['forecast_horizon']}")
                print(f"      - Model Version: {signal.data['model_version']}")
    
    # Step 8: Summary
    print("\n" + "=" * 80)
    print("Integration Summary")
    print("=" * 80)
    
    predictive_signals = [s for s in result.signals if s.is_predictive]
    
    print(f"\n✓ PredictiveAnalyticsModule successfully integrated!")
    print(f"\n  Total Signals: {len(result.signals)}")
    print(f"  Predictive Signals: {len(predictive_signals)}")
    print(f"  Other Signals: {len(result.signals) - len(predictive_signals)}")
    
    if predictive_signals:
        print(f"\n  Predictive Signal Types:")
        for signal in predictive_signals:
            pred_type = signal.data.get('prediction_type', 'unknown')
            confidence = signal.strength
            print(f"    - {pred_type}: {confidence:.1%} confidence")
    
    print("\n  Next Steps:")
    print("    1. Deploy updated service to Cloud Run")
    print("    2. Ensure historical data is available in production")
    print("    3. Monitor predictive signal quality")
    print("    4. Tune confidence thresholds if needed")
    
    print("\n" + "=" * 80)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
