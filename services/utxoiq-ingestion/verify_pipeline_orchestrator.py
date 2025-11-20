"""
Verification script for Pipeline Orchestrator implementation.

This script verifies that the Pipeline Orchestrator, Monitoring Module,
and Error Handler are correctly implemented and can be instantiated.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline_orchestrator import PipelineOrchestrator, PipelineResult
from src.monitoring import MonitoringModule
from src.error_handler import ErrorHandler
from src.signal_persistence import SignalPersistenceModule
from src.processors.base_processor import SignalProcessor, ProcessorConfig, ProcessingContext
from src.models import BlockData, Signal, SignalType


class MockProcessor(SignalProcessor):
    """Mock processor for testing."""
    
    def __init__(self, config: ProcessorConfig, should_fail: bool = False):
        super().__init__(config)
        self.signal_type = "mempool"
        self.should_fail = should_fail
    
    async def process_block(self, block: BlockData, context: ProcessingContext):
        """Generate a mock signal."""
        if self.should_fail:
            raise Exception("Mock processor failure")
        
        return [
            Signal(
                type=SignalType.MEMPOOL,
                strength=0.85,
                data={"test": "data"},
                block_height=block.height,
                transaction_ids=["tx1", "tx2"],
                entity_ids=[]
            )
        ]


class MockBigQueryClient:
    """Mock BigQuery client for testing."""
    
    def insert_rows_json(self, table_id, rows):
        """Mock insert operation."""
        print(f"  ✓ Mock BigQuery insert: {len(rows)} rows to {table_id}")
        return []  # No errors


async def test_monitoring_module():
    """Test Monitoring Module initialization and basic operations."""
    print("\n1. Testing Monitoring Module...")
    
    try:
        # Initialize monitoring module
        monitoring = MonitoringModule(
            project_id="utxoiq-dev",
            enabled=False  # Disable actual Cloud Monitoring for testing
        )
        print("  ✓ MonitoringModule initialized")
        
        # Test pipeline metrics emission
        await monitoring.emit_pipeline_metrics(
            correlation_id="test-123",
            block_height=800000,
            signal_count=5,
            signal_generation_ms=1500.0,
            signal_persistence_ms=500.0,
            total_duration_ms=2000.0
        )
        print("  ✓ Pipeline metrics emitted")
        
        # Test signal metrics emission
        await monitoring.emit_signal_metrics(
            signal_type="mempool",
            confidence=0.85
        )
        print("  ✓ Signal metrics emitted")
        
        # Test error metrics emission
        await monitoring.emit_error_metric(
            error_type="processor_failure",
            service_name="utxoiq-ingestion",
            processor="MempoolProcessor"
        )
        print("  ✓ Error metrics emitted")
        
        print("  ✓ Monitoring Module: PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ Monitoring Module: FAILED - {e}")
        return False


async def test_error_handler():
    """Test Error Handler initialization and basic operations."""
    print("\n2. Testing Error Handler...")
    
    try:
        # Initialize error handler
        monitoring = MonitoringModule(project_id="utxoiq-dev", enabled=False)
        error_handler = ErrorHandler(
            monitoring=monitoring,
            max_retries=3,
            base_delay=0.1  # Short delay for testing
        )
        print("  ✓ ErrorHandler initialized")
        
        # Test processor error handling
        await error_handler.handle_processor_error(
            error=Exception("Test error"),
            processor_name="TestProcessor",
            block_height=800000,
            correlation_id="test-123"
        )
        print("  ✓ Processor error handled")
        
        # Test retry with backoff (successful operation)
        async def successful_operation():
            return "success"
        
        result = await error_handler.retry_with_backoff(
            successful_operation,
            "test_operation",
            "test-123"
        )
        assert result == "success"
        print("  ✓ Retry with backoff (success case)")
        
        # Test retry with backoff (failing operation)
        attempt_count = 0
        
        async def failing_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Temporary failure")
            return "success after retries"
        
        result = await error_handler.retry_with_backoff(
            failing_operation,
            "test_operation",
            "test-123"
        )
        assert result == "success after retries"
        assert attempt_count == 3
        print("  ✓ Retry with backoff (retry case)")
        
        print("  ✓ Error Handler: PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ Error Handler: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pipeline_orchestrator():
    """Test Pipeline Orchestrator initialization and basic operations."""
    print("\n3. Testing Pipeline Orchestrator...")
    
    try:
        # Initialize components
        monitoring = MonitoringModule(project_id="utxoiq-dev", enabled=False)
        mock_bq_client = MockBigQueryClient()
        persistence = SignalPersistenceModule(
            bigquery_client=mock_bq_client,
            project_id="utxoiq-dev"
        )
        
        # Create mock processors
        config_enabled = ProcessorConfig(enabled=True, confidence_threshold=0.7)
        config_disabled = ProcessorConfig(enabled=False, confidence_threshold=0.7)
        
        processors = [
            MockProcessor(config_enabled, should_fail=False),
            MockProcessor(config_enabled, should_fail=False),
            MockProcessor(config_disabled, should_fail=False),  # Disabled
        ]
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(
            signal_processors=processors,
            signal_persistence=persistence,
            monitoring_module=monitoring
        )
        print("  ✓ PipelineOrchestrator initialized")
        
        # Create mock block data
        block = BlockData(
            block_hash="00000000000000000001234567890abcdef",
            height=800000,
            timestamp=datetime.utcnow(),
            size=1500000,
            tx_count=2500,
            fees_total=0.5
        )
        
        # Process block
        result = await orchestrator.process_new_block(block)
        print(f"  ✓ Block processed: {result}")
        
        # Verify result
        assert result.success, "Pipeline should succeed"
        assert result.block_height == 800000, "Block height should match"
        assert len(result.signals) == 2, "Should generate 2 signals (1 disabled)"
        assert result.correlation_id is not None, "Should have correlation ID"
        assert "signal_generation_ms" in result.timing_metrics, "Should have timing metrics"
        print("  ✓ Pipeline result validated")
        
        # Test with failing processor
        processors_with_failure = [
            MockProcessor(config_enabled, should_fail=True),
            MockProcessor(config_enabled, should_fail=False),
        ]
        
        orchestrator_with_failure = PipelineOrchestrator(
            signal_processors=processors_with_failure,
            signal_persistence=persistence,
            monitoring_module=monitoring
        )
        
        result_with_failure = await orchestrator_with_failure.process_new_block(block)
        print(f"  ✓ Block processed with failure: {result_with_failure}")
        
        # Verify graceful failure handling
        assert result_with_failure.success, "Pipeline should succeed despite processor failure"
        assert len(result_with_failure.signals) == 1, "Should generate 1 signal (1 failed)"
        print("  ✓ Graceful failure handling validated")
        
        print("  ✓ Pipeline Orchestrator: PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ Pipeline Orchestrator: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Pipeline Orchestrator Verification")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_monitoring_module())
    results.append(await test_error_handler())
    results.append(await test_pipeline_orchestrator())
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All verification tests PASSED!")
        print("\nImplementation Summary:")
        print("  • PipelineOrchestrator: Orchestrates signal generation pipeline")
        print("  • MonitoringModule: Emits metrics to Cloud Monitoring")
        print("  • ErrorHandler: Handles errors with retry logic and alerting")
        print("\nKey Features:")
        print("  • Parallel processor execution with asyncio")
        print("  • Graceful error handling (processors don't block each other)")
        print("  • Correlation IDs for request tracing")
        print("  • Timing metrics for each pipeline stage")
        print("  • Exponential backoff retry (1s, 2s, 4s)")
        print("  • Cloud Monitoring integration")
        return 0
    else:
        print(f"\n✗ {total - passed} verification test(s) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
