"""Configuration management for email service."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # SendGrid Configuration
    sendgrid_api_key: str
    sendgrid_from_email: str = "noreply@utxoiq.com"
    sendgrid_from_name: str = "utxoIQ"
    
    # BigQuery Configuration
    gcp_project_id: str
    bigquery_dataset: str = "intel"
    
    # Web API Configuration
    web_api_url: str = "http://localhost:8000"
    web_api_key: Optional[str] = None
    
    # Service Configuration
    service_port: int = 8080
    log_level: str = "INFO"
    
    # Frontend URL
    frontend_url: str = "https://utxoiq.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
