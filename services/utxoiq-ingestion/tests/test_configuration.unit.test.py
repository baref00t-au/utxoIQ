"""
Unit tests for ConfigurationModule

Tests configuration loading, hot-reload, and processor settings.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.config import ConfigurationModule, ProcessorConfig


class TestProcessorConfig:
    """Test ProcessorConfig class"""
    
    def test_processor_config_initialization(self):
        """Test ProcessorConfig initialization with default values"""
        config = ProcessorConfig()
        
        assert config.enabled is True
        assert config.confidence_threshold == 0.7
        assert config.time_window == "24h"
    
    def test_processor_config_custom_values(self):
        """Test ProcessorConfig with custom values"""
        config = ProcessorConfig(
            enabled=False,
            confidence_threshold=0.8,
            time_window="1h",
            custom_param="test"
        )
        
        assert config.enabled is False
        assert config.confidence_threshold == 0.8
        assert config.time_window == "1h"
        assert config.custom_param == "test"
    
    def test_processor_config_repr(self):
        """Test ProcessorConfig string representation"""
        config = ProcessorConfig(enabled=True, confidence_threshold=0.75)
        repr_str = repr(config)
        
        assert "ProcessorConfig" in repr_str
        assert "enabled=True" in repr_str
        assert "threshold=0.75" in repr_str


class TestConfigurationModule:
    """Test ConfigurationModule class"""
    
    def test_initialization(self):
        """Test ConfigurationModule initialization"""
        config_module = ConfigurationModule()
        
        assert config_module.config is not None
        assert isinstance(config_module.config, dict)
        assert config_module.last_reload is not None
        assert config_module.reload_interval == timedelta(minutes=5)
    
    def test_default_processor_configs(self):
        """Test that all expected processors are configured by default"""
        config_module = ConfigurationModule()
        
        expected_processors = [
            "mempool", "exchange", "miner", 
            "whale", "treasury", "predictive"
        ]
        
        for processor in expected_processors:
            assert processor in config_module.config
            assert isinstance(config_module.config[processor], ProcessorConfig)
    
    @patch.dict(os.environ, {
        "MEMPOOL_PROCESSOR_ENABLED": "false",
        "EXCHANGE_PROCESSOR_ENABLED": "true",
        "CONFIDENCE_THRESHOLD": "0.8"
    })
    def test_load_config_from_environment(self):
        """Test loading configuration from environment variables"""
        config_module = ConfigurationModule()
        
        # Mempool should be disabled
        assert config_module.config["mempool"].enabled is False
        
        # Exchange should be enabled
        assert config_module.config["exchange"].enabled is True
        
        # Global confidence threshold should be applied
        assert config_module.config["exchange"].confidence_threshold == 0.8
    
    @patch.dict(os.environ, {
        "WHALE_THRESHOLD_BTC": "500",
        "MEMPOOL_SPIKE_THRESHOLD": "1.5",
        "MEMPOOL_TIME_WINDOW": "2h"
    })
    def test_processor_specific_settings(self):
        """Test processor-specific configuration settings"""
        config_module = ConfigurationModule()
        
        # Check whale threshold
        assert config_module.config["whale"].threshold_btc == 500.0
        
        # Check mempool spike threshold
        assert config_module.config["mempool"].spike_threshold == 1.5
        
        # Check mempool time window
        assert config_module.config["mempool"].time_window == "2h"
    
    def test_parse_bool(self):
        """Test boolean parsing from strings"""
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
        assert config_module._parse_bool("off") is False
        assert config_module._parse_bool("anything") is False
    
    def test_should_reload_false_initially(self):
        """Test that should_reload returns False immediately after initialization"""
        config_module = ConfigurationModule()
        
        assert config_module.should_reload() is False
    
    def test_should_reload_true_after_interval(self):
        """Test that should_reload returns True after reload interval"""
        config_module = ConfigurationModule()
        
        # Simulate time passing by setting last_reload to 6 minutes ago
        config_module.last_reload = datetime.utcnow() - timedelta(minutes=6)
        
        assert config_module.should_reload() is True
    
    @patch.dict(os.environ, {
        "MEMPOOL_PROCESSOR_ENABLED": "true",
        "CONFIDENCE_THRESHOLD": "0.7"
    })
    def test_reload_config(self):
        """Test configuration hot-reload"""
        config_module = ConfigurationModule()
        
        # Initial state
        assert config_module.config["mempool"].enabled is True
        initial_reload_time = config_module.last_reload
        
        # Change environment variable
        with patch.dict(os.environ, {"MEMPOOL_PROCESSOR_ENABLED": "false"}):
            config_module.reload_config()
        
        # Verify reload happened
        assert config_module.config["mempool"].enabled is False
        assert config_module.last_reload > initial_reload_time
    
    def test_get_processor_config(self):
        """Test getting configuration for specific processor"""
        config_module = ConfigurationModule()
        
        mempool_config = config_module.get_processor_config("mempool")
        assert mempool_config is not None
        assert isinstance(mempool_config, ProcessorConfig)
        
        # Test non-existent processor
        invalid_config = config_module.get_processor_config("invalid")
        assert invalid_config is None
    
    def test_get_all_configs(self):
        """Test getting all processor configurations"""
        config_module = ConfigurationModule()
        
        all_configs = config_module.get_all_configs()
        
        assert isinstance(all_configs, dict)
        assert len(all_configs) == 6  # 6 processor types
        assert "mempool" in all_configs
        assert "exchange" in all_configs
    
    @patch.dict(os.environ, {
        "MEMPOOL_PROCESSOR_ENABLED": "true",
        "EXCHANGE_PROCESSOR_ENABLED": "false",
        "MINER_PROCESSOR_ENABLED": "true"
    })
    def test_get_enabled_processors(self):
        """Test getting only enabled processors"""
        config_module = ConfigurationModule()
        
        enabled = config_module.get_enabled_processors()
        
        assert "mempool" in enabled
        assert "exchange" not in enabled
        assert "miner" in enabled
    
    @patch.dict(os.environ, {
        "WHALE_PROCESSOR_ENABLED": "true",
        "TREASURY_PROCESSOR_ENABLED": "false"
    })
    def test_is_processor_enabled(self):
        """Test checking if specific processor is enabled"""
        config_module = ConfigurationModule()
        
        assert config_module.is_processor_enabled("whale") is True
        assert config_module.is_processor_enabled("treasury") is False
        assert config_module.is_processor_enabled("invalid") is False
    
    @patch.dict(os.environ, {
        "CONFIDENCE_THRESHOLD": "0.8",
        "WHALE_CONFIDENCE_THRESHOLD": "0.9"
    })
    def test_get_confidence_threshold(self):
        """Test getting confidence threshold for processors"""
        config_module = ConfigurationModule()
        
        # Whale has custom threshold
        assert config_module.get_confidence_threshold("whale") == 0.9
        
        # Exchange uses global threshold
        assert config_module.get_confidence_threshold("exchange") == 0.8
        
        # Invalid processor returns default
        assert config_module.get_confidence_threshold("invalid") == 0.7
    
    def test_repr(self):
        """Test ConfigurationModule string representation"""
        config_module = ConfigurationModule()
        repr_str = repr(config_module)
        
        assert "ConfigurationModule" in repr_str
        assert "processors=" in repr_str
        assert "enabled=" in repr_str
        assert "last_reload=" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
