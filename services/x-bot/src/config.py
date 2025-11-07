"""Configuration management for X Bot service."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # X API Credentials
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_token_secret: str
    x_bearer_token: str
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # GCP Configuration
    gcp_project_id: str
    gcs_bucket_name: str = "utxoiq-charts"
    
    # API Configuration
    web_api_url: str = "http://localhost:8000"
    web_api_key: str
    
    # Bot Configuration
    confidence_threshold: float = 0.7
    duplicate_prevention_window: int = 900  # 15 minutes in seconds
    daily_brief_time: str = "07:00"
    hourly_check_enabled: bool = True
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
