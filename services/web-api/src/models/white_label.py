"""White label configuration models."""
from pydantic import BaseModel, Field
from typing import Optional


class WhiteLabelConfig(BaseModel):
    """White label configuration for custom branding."""
    
    organization_id: str
    organization_name: str
    logo_url: Optional[str] = None
    primary_color: str = "#FF5A21"
    secondary_color: str = "#0B0B0C"
    custom_domain: Optional[str] = None
    api_key: str
    enabled: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_abc123",
                "organization_name": "Acme Corp",
                "logo_url": "https://example.com/logo.png",
                "primary_color": "#FF5A21",
                "secondary_color": "#0B0B0C",
                "custom_domain": "insights.acme.com",
                "api_key": "wl_key_abc123",
                "enabled": True
            }
        }


class WhiteLabelConfigResponse(BaseModel):
    """White label configuration response."""
    config: WhiteLabelConfig
