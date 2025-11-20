"""
Verification script for ConfigurationModule

This script verifies that the ConfigurationModule works correctly
without requiring pytest to be installed.
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import ConfigurationModule, ProcessorConfig


def test_processor_config():
    """Test ProcessorConfig initialization"""
    print("Testing ProcessorConfig...")
    
    # Test default values
    config = ProcessorConfig()
    assert config.enabled is True, "Default enabled should be True"
    assert config.confidence_threshold == 0.7, "Default threshold should be 0.7"
    assert config.time_window == "24h", "Default time window should be 24h"
    
    # Test custom values
    config = ProcessorConfig(
        enabled=False,
        confidence_threshold=0.8,
        time_window="1h",
        custom_param="test"
    )
    assert config.enabled is False, "Custom enabled should be False"
    assert config.confidence_threshold == 0.8, "Custom threshold should be 0.8"
    assert config.time_window == "1h", "Custom time window should be 1h"
    assert config.custom_param == "test", "Custom param should be 'test'"
    
    print("✓ ProcessorConfig tests passed")


def test_configuration_module_initialization():
    """Test ConfigurationModule initialization"""
    print("\nTesting ConfigurationModule initialization...")
    
    config_module = ConfigurationModule()
    
    assert config_module.config is not None, "Config should not be None"
    assert isinstance(config_module.config, dict), "Config should be a dict"
    assert config_module.last_reload is not None, "Last reload should not be None"
    assert config_module.reload_interval == timedelta(minutes=5), "Reload interval should be 5 minutes"
    
    print("✓ ConfigurationModule initialization tests passed")


def test_default_processor_configs():
    """Test that all expected processors are configured"""
    print("\nTesting default processor configurations...")
    
    config_module = ConfigurationModule()
    
    expected_processors = [
        "mempool", "exchange", "miner", 
        "whale", "treasury", "predictive"
    ]
    
    for processor in expected_processors:
        assert processor in config_module.config, f"Processor {processor} should be configured"
        assert isinstance(config_module.config[processor], ProcessorConfig), \
            f"Processor {processor} config should be ProcessorConfig instance"
    
    print(f"✓ All {len(expected_processors)} processors configured correctly")


def test_environment_variable_loading():
    """Test loading configuration from environment variables"""
    print("\nTesting environment variable loading...")
    
    # Set test environment variables
    os.environ["MEMPOOL_PROCESSOR_ENABLED"] = "false"
    os.environ["EXCHANGE_PROCESSOR_ENABLED"] = "true"
    os.environ["CONFIDENCE_THRESHOLD"] = "0.8"
    os.environ["WHALE_THRESHOLD_BTC"] = "500"
    os.environ["MEMPOOL_TIME_WINDOW"] = "2h"
    
    config_module = ConfigurationModule()
    
    # Verify mempool is disabled
    assert config_module.config["mempool"].enabled is False, \
        "Mempool processor should be disabled"
    
    # Verify exchange is enabled
    assert config_module.config["exchange"].enabled is True, \
        "Exchange processor should be enabled"
    
    # Verify global confidence threshold
    assert config_module.config["exchange"].confidence_threshold == 0.8, \
        "Exchange should use global confidence threshold"
    
    # Verify whale threshold
    assert config_module.config["whale"].threshold_btc == 500.0, \
        "Whale threshold should be 500 BTC"
    
    # Verify mempool time window
    assert config_module.config["mempool"].time_window == "2h", \
        "Mempool time window should be 2h"
    
    # Clean up
    del os.environ["MEMPOOL_PROCESSOR_ENABLED"]
    del os.environ["EXCHANGE_PROCESSOR_ENABLED"]
    del os.environ["CONFIDENCE_THRESHOLD"]
    del os.environ["WHALE_THRESHOLD_BTC"]
    del os.environ["MEMPOOL_TIME_WINDOW"]
    
    print("✓ Environment variable loading tests passed")


def test_should_reload():
    """Test should_reload functionality"""
    print("\nTesting should_reload...")
    
    config_module = ConfigurationModule()
    
    # Should not reload immediately
    assert config_module.should_reload() is False, \
        "Should not reload immediately after initialization"
    
    # Simulate time passing
    config_module.last_reload = datetime.utcnow() - timedelta(minutes=6)
    
    # Should reload after 6 minutes
    assert config_module.should_reload() is True, \
        "Should reload after 6 minutes"
    
    print("✓ should_reload tests passed")


def test_reload_config():
    """Test configuration hot-reload"""
    print("\nTesting reload_config...")
    
    # Set initial state
    os.environ["MEMPOOL_PROCESSOR_ENABLED"] = "true"
    config_module = ConfigurationModule()
    
    assert config_module.config["mempool"].enabled is True, \
        "Mempool should be enabled initially"
    
    initial_reload_time = config_module.last_reload
    
    # Small delay to ensure time difference
    import time
    time.sleep(0.01)
    
    # Change environment variable
    os.environ["MEMPOOL_PROCESSOR_ENABLED"] = "false"
    config_module.reload_config()
    
    # Verify reload happened
    assert config_module.config["mempool"].enabled is False, \
        "Mempool should be disabled after reload"
    assert config_module.last_reload >= initial_reload_time, \
        "Last reload time should be updated"
    
    # Clean up
    del os.environ["MEMPOOL_PROCESSOR_ENABLED"]
    
    print("✓ reload_config tests passed")


def test_helper_methods():
    """Test helper methods"""
    print("\nTesting helper methods...")
    
    config_module = ConfigurationModule()
    
    # Test get_processor_config
    mempool_config = config_module.get_processor_config("mempool")
    assert mempool_config is not None, "Should get mempool config"
    assert isinstance(mempool_config, ProcessorConfig), "Should be ProcessorConfig instance"
    
    invalid_config = config_module.get_processor_config("invalid")
    assert invalid_config is None, "Should return None for invalid processor"
    
    # Test get_all_configs
    all_configs = config_module.get_all_configs()
    assert isinstance(all_configs, dict), "Should return dict"
    assert len(all_configs) == 6, "Should have 6 processors"
    
    # Test get_enabled_processors
    enabled = config_module.get_enabled_processors()
    assert isinstance(enabled, dict), "Should return dict"
    
    # Test is_processor_enabled
    # All should be enabled by default
    assert config_module.is_processor_enabled("mempool") is True, \
        "Mempool should be enabled by default"
    assert config_module.is_processor_enabled("invalid") is False, \
        "Invalid processor should return False"
    
    # Test get_confidence_threshold
    threshold = config_module.get_confidence_threshold("mempool")
    assert threshold == 0.7, "Default threshold should be 0.7"
    
    invalid_threshold = config_module.get_confidence_threshold("invalid")
    assert invalid_threshold == 0.7, "Invalid processor should return default 0.7"
    
    print("✓ Helper method tests passed")


def test_parse_bool():
    """Test boolean parsing"""
    print("\nTesting _parse_bool...")
    
    config_module = ConfigurationModule()
    
    # Test true values
    assert config_module._parse_bool("true") is True
    assert config_module._parse_bool("TRUE") is True
    assert config_module._parse_bool("1") is True
    assert config_module._parse_bool("yes") is True
    assert config_module._parse_bool("on") is True
    
    # Test false values
    assert config_module._parse_bool("false") is False
    assert config_module._parse_bool("0") is False
    assert config_module._parse_bool("no") is False
    assert config_module._parse_bool("anything") is False
    
    print("✓ _parse_bool tests passed")


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("ConfigurationModule Verification")
    print("=" * 60)
    
    try:
        test_processor_config()
        test_configuration_module_initialization()
        test_default_processor_configs()
        test_environment_variable_loading()
        test_should_reload()
        test_reload_config()
        test_helper_methods()
        test_parse_bool()
        
        print("\n" + "=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
