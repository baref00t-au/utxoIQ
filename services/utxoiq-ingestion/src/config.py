"""
Configuration management for Feature Engine service
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


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


settings = Settings()
