"""
Manual verification script for SignalPersistenceModule.

This script verifies the basic functionality of the SignalPersistenceModule
without requiring pytest or a real BigQuery connection.
"""

import sys
import os
from datetime import datetime
from unittest.mock import Mock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from signal_persistence import SignalPersistenceModule, PersistenceResult
from shared.types import Signal


def test_signal_id_generation():
    """Test signal ID generation."""
    print("Testing signal ID generation...")
    
    mock_client = Mock()
    module = SignalPersistenceModule(
        bigquery_client=mock_client,
        project_id="test-project"
    )
    
    # Generate multiple IDs
    ids = [module.generate_signal_id() for _ in range(10)]
    
    # Check all are strings
    assert all(isinstance(id, str) for id in ids), "All IDs should be strings"
    
    # Check all are unique
    assert len(ids) == len(set(ids)), "All IDs should be unique"
    
    # Check UUID format (36 chars with 4 hyphens)
    assert all(len(id) == 36 and id.count('-') == 4 for id in ids), "IDs should be valid UUIDs"
    
    print("✓ Signal ID generation works correctly")
    return True


def test_signal_to_bigquery_row():
    """Test signal to BigQuery row conversion."""
    print("\nTesting signal to BigQuery row conversion...")
    
    mock_client = Mock()
    module = SignalPersistenceModule(
        bigquery_client=mock_client,
        project_id="test-project"
    )
    
    # Create a test signal
    signal = Signal(
        signal_id="test-signal-123",
        signal_type="mempool",
        block_height=800000,
        confidence=0.85,
        metadata={
            "fee_rate_median": 50.5,
            "tx_count": 15000
        },
        created_at=datetime.utcnow(),
        processed=False,
        processed_at=None
    )
    
    # Convert to BigQuery row
    row = module._signal_to_bigquery_row(signal)
    
    # Verify all required fields
    required_fields = [
        "signal_id", "signal_type", "block_height", "confidence",
        "metadata", "created_at", "processed", "processed_at"
    ]
    for field in required_fields:
        assert field in row, f"Row should contain {field}"
    
    # Verify values
    assert row["signal_id"] == "test-signal-123"
    assert row["signal_type"] == "mempool"
    assert row["block_height"] == 800000
    assert row["confidence"] == 0.85
    assert row["processed"] is False
    assert row["processed_at"] is None
    
    # Verify metadata
    assert row["metadata"]["fee_rate_median"] == 50.5
    assert row["metadata"]["tx_count"] == 15000
    
    # Verify datetime serialization
    assert isinstance(row["created_at"], str), "created_at should be serialized to string"
    
    print("✓ Signal to BigQuery row conversion works correctly")
    return True


def test_module_initialization():
    """Test module initialization."""
    print("\nTesting module initialization...")
    
    mock_client = Mock()
    module = SignalPersistenceModule(
        bigquery_client=mock_client,
        project_id="test-project",
        dataset_id="intel",
        table_name="signals",
        max_retries=3,
        base_delay=1.0
    )
    
    # Verify attributes
    assert module.project_id == "test-project"
    assert module.dataset_id == "intel"
    assert module.table_name == "signals"
    assert module.table_id == "test-project.intel.signals"
    assert module.max_retries == 3
    assert module.base_delay == 1.0
    
    print("✓ Module initialization works correctly")
    return True


def test_persistence_result():
    """Test PersistenceResult class."""
    print("\nTesting PersistenceResult...")
    
    # Test success result
    result = PersistenceResult(
        success=True,
        signal_count=5,
        correlation_id="test-123"
    )
    assert result.success is True
    assert result.signal_count == 5
    assert result.error is None
    
    # Test failure result
    result = PersistenceResult(
        success=False,
        signal_count=0,
        error="Test error",
        correlation_id="test-456"
    )
    assert result.success is False
    assert result.signal_count == 0
    assert result.error == "Test error"
    
    print("✓ PersistenceResult works correctly")
    return True


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("SignalPersistenceModule Verification")
    print("=" * 60)
    
    tests = [
        test_module_initialization,
        test_signal_id_generation,
        test_signal_to_bigquery_row,
        test_persistence_result
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All verification tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
