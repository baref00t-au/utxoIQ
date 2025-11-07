"""
Configuration for Chart Renderer Service
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Service configuration"""
    
    # Google Cloud Storage
    gcs_bucket_name: str = "utxoiq-charts"
    gcs_project_id: Optional[str] = None
    
    # Chart Configuration
    chart_dpi: int = 150
    chart_mobile_width: int = 800
    chart_desktop_width: int = 1200
    chart_height_ratio: float = 0.375  # 16:6 aspect ratio
    
    # Brand Colors (hex without #)
    brand_color: str = "FF5A21"
    mempool_color: str = "FB923C"
    exchange_color: str = "38BDF8"
    miner_color: str = "10B981"
    whale_color: str = "8B5CF6"
    background_color: str = "0B0B0C"
    surface_color: str = "131316"
    text_color: str = "F4F4F5"
    grid_color: str = "2A2A2E"
    
    # Service Configuration
    port: int = 8080
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_color(self, color_name: str) -> str:
        """Get color as hex string with # prefix"""
        color_value = getattr(self, f"{color_name}_color", "FFFFFF")
        return f"#{color_value}"


# Global settings instance
settings = Settings()
