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
    firebase_project_id: str = "utxoiq-local"
    firebase_credentials_path: str = "./firebase-credentials.json"
    
    # Google Cloud
    gcp_project_id: str = "utxoiq-local"
    bigquery_dataset_intel: str = "intel"
    bigquery_dataset_btc: str = "btc"
    
    # Cloud Storage
    archive_bucket_name: str = "utxoiq-archives"
    
    # Cloud SQL
    cloud_sql_connection_name: str = ""  # Empty for local development
    db_user: str = "utxoiq"
    db_password: str = "utxoiq_dev_password"
    db_name: str = "utxoiq_db"
    db_host: str = "localhost"
    db_port: int = 5432
    
    # Database Connection Pool
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    @property
    def database_url(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        # When Cloud SQL connection is configured, Cloud Run's proxy makes it available on 127.0.0.1
        # asyncpg uses TCP connections (doesn't support Unix sockets)
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Stripe
    stripe_secret_key: str = "sk_test_dummy"
    stripe_webhook_secret: str = "whsec_dummy"
    
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
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
