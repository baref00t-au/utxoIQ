"""
Configuration management for Feature Engine service

This module provides configuration management with hot-reload support
for signal processor settings, thresholds, and time windows.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # GCP Configuration
    gcp_project_id: str = Field(default="utxoiq-dev", validation_alias="PROJECT_ID")
    bigquery_dataset_btc: str = "btc"
    bigquery_dataset_intel: str = "intel"
    pubsub_topic_signals: str = "signal-generated"
    pubsub_subscription_blocks: str = "block-processed"
    
    # Processing Configuration
    confidence_threshold: float = 0.7
    mempool_spike_threshold: float = 3.0
    reorg_detection_depth: int = 6
    confirmation_blocks: int = 6
    
    # Signal Processing Configuration
    whale_threshold_btc: float = 100.0
    accumulation_window_days: int = 7
    exchange_flow_anomaly_threshold: float = 2.5
    
    # Predictive Analytics Configuration
    fee_forecast_horizon: str = "next_block"
    liquidity_pressure_window_hours: int = 24
    model_version: str = "v1.0.0"
    
    # API Configuration
    port: int = 8080
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env


settings = Settings()


class ProcessorConfig:
    """
    Configuration for individual signal processors.
    
    This class holds the configuration for a specific processor type,
    including enabled status, thresholds, and time windows.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        confidence_threshold: float = 0.7,
        time_window: str = "24h",
        **kwargs
    ):
        """
        Initialize processor configuration.
        
        Args:
            enabled: Whether the processor is enabled
            confidence_threshold: Minimum confidence score for signals
            time_window: Time window for historical comparisons
            **kwargs: Additional processor-specific configuration
        """
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        self.time_window = time_window
        
        # Store any additional config parameters
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __repr__(self) -> str:
        return (
            f"ProcessorConfig(enabled={self.enabled}, "
            f"threshold={self.confidence_threshold}, "
            f"time_window={self.time_window})"
        )


class ConfigurationModule:
    """
    Configuration module with hot-reload support.
    
    This module loads signal processor settings from environment variables
    and supports hot-reload without service restart. Configuration is
    automatically reloaded every 5 minutes.
    
    Responsibilities:
    - Load processor settings from environment variables
    - Enable/disable processors dynamically
    - Configure confidence thresholds
    - Support hot-reload without service restart (poll every 5 minutes)
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    def __init__(self):
        """
        Initialize Configuration Module.
        
        Loads initial configuration from environment variables and
        sets up reload tracking.
        """
        self.config: Dict[str, ProcessorConfig] = {}
        self.last_reload: datetime = datetime.utcnow()
        self.reload_interval: timedelta = timedelta(minutes=5)
        
        # Load initial configuration
        self._load_config()
        
        logger.info(
            "ConfigurationModule initialized",
            extra={
                "reload_interval_minutes": 5,
                "processors_configured": len(self.config)
            }
        )
    
    def _load_config(self) -> None:
        """
        Load configuration from environment variables.
        
        This method reads environment variables for each processor type
        and creates ProcessorConfig objects with the appropriate settings.
        
        Environment variables follow the pattern:
        - {PROCESSOR}_ENABLED: Enable/disable processor (default: true)
        - {PROCESSOR}_CONFIDENCE_THRESHOLD: Confidence threshold (default: 0.7)
        - {PROCESSOR}_TIME_WINDOW: Time window for comparisons (default: varies)
        
        Additional processor-specific variables:
        - WHALE_THRESHOLD_BTC: Minimum BTC for whale detection (default: 1000)
        - MEMPOOL_SPIKE_THRESHOLD: Fee spike threshold multiplier (default: 1.2)
        
        Requirements: 7.1, 7.2
        """
        # Global confidence threshold (can be overridden per processor)
        global_confidence_threshold = float(
            os.getenv("CONFIDENCE_THRESHOLD", "0.7")
        )
        
        # Mempool Processor Configuration
        self.config["mempool"] = ProcessorConfig(
            enabled=self._parse_bool(
                os.getenv("MEMPOOL_PROCESSOR_ENABLED", "true")
            ),
            confidence_threshold=float(
                os.getenv("MEMPOOL_CONFIDENCE_THRESHOLD", str(global_confidence_threshold))
            ),
            time_window=os.getenv("MEMPOOL_TIME_WINDOW", "1h"),
            spike_threshold=float(
                os.getenv("MEMPOOL_SPIKE_THRESHOLD", "1.2")
            )
        )
        
        # Exchange Processor Configuration
        self.config["exchange"] = ProcessorConfig(
            enabled=self._parse_bool(
                os.getenv("EXCHANGE_PROCESSOR_ENABLED", "true")
            ),
            confidence_threshold=float(
                os.getenv("EXCHANGE_CONFIDENCE_THRESHOLD", str(global_confidence_threshold))
            ),
            time_window=os.getenv("EXCHANGE_TIME_WINDOW", "24h")
        )
        
        # Miner Processor Configuration
        self.config["miner"] = ProcessorConfig(
            enabled=self._parse_bool(
                os.getenv("MINER_PROCESSOR_ENABLED", "true")
            ),
            confidence_threshold=float(
                os.getenv("MINER_CONFIDENCE_THRESHOLD", str(global_confidence_threshold))
            ),
            time_window=os.getenv("MINER_TIME_WINDOW", "7d")
        )
        
        # Whale Processor Configuration
        self.config["whale"] = ProcessorConfig(
            enabled=self._parse_bool(
                os.getenv("WHALE_PROCESSOR_ENABLED", "true")
            ),
            confidence_threshold=float(
                os.getenv("WHALE_CONFIDENCE_THRESHOLD", str(global_confidence_threshold))
            ),
            time_window=os.getenv("WHALE_TIME_WINDOW", "24h"),
            threshold_btc=float(
                os.getenv("WHALE_THRESHOLD_BTC", "1000")
            )
        )
        
        # Treasury Processor Configuration
        self.config["treasury"] = ProcessorConfig(
            enabled=self._parse_bool(
                os.getenv("TREASURY_PROCESSOR_ENABLED", "true")
            ),
            confidence_threshold=float(
                os.getenv("TREASURY_CONFIDENCE_THRESHOLD", str(global_confidence_threshold))
            ),
            time_window=os.getenv("TREASURY_TIME_WINDOW", "24h")
        )
        
        # Predictive Processor Configuration
        self.config["predictive"] = ProcessorConfig(
            enabled=self._parse_bool(
                os.getenv("PREDICTIVE_PROCESSOR_ENABLED", "true")
            ),
            confidence_threshold=float(
                os.getenv("PREDICTIVE_CONFIDENCE_THRESHOLD", "0.5")
            ),
            time_window=os.getenv("PREDICTIVE_TIME_WINDOW", "24h"),
            min_confidence=float(
                os.getenv("PREDICTIVE_MIN_CONFIDENCE", "0.5")
            )
        )
        
        logger.debug(
            "Configuration loaded from environment variables",
            extra={
                "mempool_enabled": self.config["mempool"].enabled,
                "exchange_enabled": self.config["exchange"].enabled,
                "miner_enabled": self.config["miner"].enabled,
                "whale_enabled": self.config["whale"].enabled,
                "treasury_enabled": self.config["treasury"].enabled,
                "predictive_enabled": self.config["predictive"].enabled,
                "global_confidence_threshold": global_confidence_threshold
            }
        )
    
    def _parse_bool(self, value: str) -> bool:
        """
        Parse boolean value from string.
        
        Accepts: "true", "1", "yes", "on" (case-insensitive) as True
        Everything else is False
        
        Args:
            value: String value to parse
            
        Returns:
            Boolean value
        """
        return value.lower() in ("true", "1", "yes", "on")
    
    def should_reload(self) -> bool:
        """
        Check if configuration should be reloaded.
        
        Configuration is reloaded every 5 minutes to support hot-reload
        without service restart.
        
        Returns:
            True if reload interval has elapsed, False otherwise
            
        Requirements: 7.4
        """
        elapsed = datetime.utcnow() - self.last_reload
        should_reload = elapsed >= self.reload_interval
        
        if should_reload:
            logger.debug(
                "Configuration reload interval elapsed",
                extra={
                    "elapsed_minutes": elapsed.total_seconds() / 60,
                    "reload_interval_minutes": self.reload_interval.total_seconds() / 60
                }
            )
        
        return should_reload
    
    def reload_config(self) -> None:
        """
        Hot-reload configuration from environment variables.
        
        This method reloads all processor configurations from environment
        variables without requiring a service restart. It's called automatically
        when the reload interval (5 minutes) has elapsed.
        
        The reload is logged with details about which processors changed state.
        
        Requirements: 7.4, 7.5
        """
        logger.info("Reloading configuration from environment variables")
        
        # Store old config for comparison
        old_config = {
            name: {
                "enabled": cfg.enabled,
                "confidence_threshold": cfg.confidence_threshold,
                "time_window": cfg.time_window
            }
            for name, cfg in self.config.items()
        }
        
        # Reload configuration
        self._load_config()
        self.last_reload = datetime.utcnow()
        
        # Log changes
        changes = []
        for name, cfg in self.config.items():
            if name in old_config:
                old = old_config[name]
                if old["enabled"] != cfg.enabled:
                    changes.append(
                        f"{name}: enabled={old['enabled']} -> {cfg.enabled}"
                    )
                if old["confidence_threshold"] != cfg.confidence_threshold:
                    changes.append(
                        f"{name}: threshold={old['confidence_threshold']} -> {cfg.confidence_threshold}"
                    )
                if old["time_window"] != cfg.time_window:
                    changes.append(
                        f"{name}: time_window={old['time_window']} -> {cfg.time_window}"
                    )
        
        if changes:
            logger.info(
                "Configuration changes detected",
                extra={
                    "changes": changes,
                    "change_count": len(changes)
                }
            )
        else:
            logger.info("Configuration reloaded with no changes")
    
    def get_processor_config(self, processor_type: str) -> Optional[ProcessorConfig]:
        """
        Get configuration for a specific processor type.
        
        Args:
            processor_type: Type of processor (mempool, exchange, miner, whale, treasury, predictive)
            
        Returns:
            ProcessorConfig for the specified type, or None if not found
        """
        return self.config.get(processor_type)
    
    def get_all_configs(self) -> Dict[str, ProcessorConfig]:
        """
        Get all processor configurations.
        
        Returns:
            Dictionary mapping processor type to ProcessorConfig
        """
        return self.config.copy()
    
    def get_enabled_processors(self) -> Dict[str, ProcessorConfig]:
        """
        Get only enabled processor configurations.
        
        Returns:
            Dictionary mapping processor type to ProcessorConfig for enabled processors only
            
        Requirements: 7.2
        """
        return {
            name: cfg
            for name, cfg in self.config.items()
            if cfg.enabled
        }
    
    def is_processor_enabled(self, processor_type: str) -> bool:
        """
        Check if a specific processor is enabled.
        
        Args:
            processor_type: Type of processor to check
            
        Returns:
            True if processor is enabled, False otherwise
            
        Requirements: 7.2
        """
        config = self.config.get(processor_type)
        return config.enabled if config else False
    
    def get_confidence_threshold(self, processor_type: str) -> float:
        """
        Get confidence threshold for a specific processor.
        
        Args:
            processor_type: Type of processor
            
        Returns:
            Confidence threshold (0.0 to 1.0), or 0.7 as default
            
        Requirements: 7.3
        """
        config = self.config.get(processor_type)
        return config.confidence_threshold if config else 0.7
    
    def __repr__(self) -> str:
        """String representation of configuration module."""
        enabled_count = sum(1 for cfg in self.config.values() if cfg.enabled)
        return (
            f"ConfigurationModule("
            f"processors={len(self.config)}, "
            f"enabled={enabled_count}, "
            f"last_reload={self.last_reload.isoformat()})"
        )
