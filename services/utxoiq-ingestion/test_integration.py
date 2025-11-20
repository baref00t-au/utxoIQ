"""
Quick integration test to verify PredictiveAnalyticsModule is working.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing PredictiveAnalyticsModule integration...")
print("=" * 60)

# Test 1: Import the module
print("\n1. Testing imports...")
try:
    from src.processors import PredictiveAnalyticsModule
    print("   ✓ PredictiveAnalyticsModule imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Check it's in the processors list
try:
    from src.processors import __all__
    assert "PredictiveAnalyticsModule" in __all__
    print("   ✓ PredictiveAnalyticsModule in __all__")
except AssertionError:
    print("   ✗ PredictiveAnalyticsModule not in __all__")
    sys.exit(1)

# Test 3: Instantiate the module
print("\n2. Testing instantiation...")
try:
    from src.processors.base_processor import ProcessorConfig
    config = ProcessorConfig(enabled=True, confidence_threshold=0.5)
    module = PredictiveAnalyticsModule(config)
    print(f"   ✓ Module instantiated: {module}")
    print(f"   ✓ Signal type: {module.signal_type}")
    print(f"   ✓ Model version: {module.model_version}")
    print(f"   ✓ Min confidence: {module.min_confidence}")
except Exception as e:
    print(f"   ✗ Failed to instantiate: {e}")
    sys.exit(1)

# Test 4: Check main.py integration
print("\n3. Checking main.py integration...")
try:
    with open('src/main.py', 'r') as f:
        main_content = f.read()
    
    checks = [
        ("PredictiveAnalyticsModule import", "PredictiveAnalyticsModule" in main_content),
        ("signal_processors list", "signal_processors = [" in main_content),
        ("PredictiveAnalyticsModule in list", "PredictiveAnalyticsModule(processor_config)" in main_content),
        ("pipeline_orchestrator", "pipeline_orchestrator = PipelineOrchestrator" in main_content),
        ("/process/signals endpoint", "@app.post(\"/process/signals\")" in main_content),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
    
    if not all_passed:
        print("\n   ⚠️  Some integration checks failed")
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ Failed to check main.py: {e}")
    sys.exit(1)

# Test 5: Verify processor methods exist
print("\n4. Verifying processor methods...")
try:
    methods = [
        "process_block",
        "forecast_next_block_fees",
        "compute_liquidity_pressure_index",
        "generate_fee_forecast_signal",
        "generate_liquidity_pressure_signal"
    ]
    
    for method_name in methods:
        assert hasattr(module, method_name), f"Missing method: {method_name}"
        print(f"   ✓ {method_name}()")
        
except AssertionError as e:
    print(f"   ✗ {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✓ Integration test PASSED!")
print("\nPredictiveAnalyticsModule is successfully integrated:")
print("  • Module can be imported and instantiated")
print("  • Registered in processors __all__")
print("  • Added to main.py signal_processors list")
print("  • Pipeline orchestrator configured")
print("  • /process/signals endpoint available")
print("  • All required methods present")
print("\nNext steps:")
print("  1. Deploy to Cloud Run")
print("  2. Test /process/signals endpoint")
print("  3. Monitor predictive signal generation")
print("=" * 60)
