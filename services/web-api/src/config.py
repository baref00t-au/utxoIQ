"""Configuration management for the Web API service."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # Server
    port: int = 8080
    host: str = "0.0.0.0"
    environment: str = "development"
    
    # Firebase Auth
    firebase_project_id: str
    firebase_credentials_path: str = "./firebase-credentials.json"
    
    # Google Cloud
    gcp_project_id: str
    bigquery_dataset_intel: str = "intel"
    bigquery_dataset_btc: str = "btc"
    
    # Cloud SQL
    cloud_sql_connection_name: str
    db_user: str
    db_password: str
    db_name: str
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str
    
    # Vertex AI
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-pro"
    
    # Rate Limiting
    rate_limit_free_tier: int = 100
    rate_limit_pro_tier: int = 1000
    rate_limit_power_tier: int = 10000
    rate_limit_window: int = 3600
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 10000
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
