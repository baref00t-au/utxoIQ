"""Client for interacting with Web API service."""
import httpx
import logging
from typing import List, Optional
from datetime import datetime, date
from .models import Insight, DailyBrief
from .config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """Client for Web API interactions."""
    
    def __init__(self):
        """Initialize API client."""
        self.base_url = settings.web_api_url
        self.api_key = settings.web_api_key
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        logger.info(f"API client initialized for {self.base_url}")
    
    async def get_publishable_insights(self, limit: int = 10) -> List[Insight]:
        """
        Fetch insights ready for publication (confidence >= threshold).
        
        Args:
            limit: Maximum number of insights to fetch
            
        Returns:
            List of Insight objects
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/insights/latest",
                    headers=self.headers,
                    params={
                        "limit": limit,
                        "min_confidence": settings.confidence_threshold
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                insights = [Insight(**item) for item in data.get("insights", [])]
                
                logger.info(f"Fetched {len(insights)} publishable insights")
                return insights
                
        except Exception as e:
            logger.error(f"Failed to fetch publishable insights: {e}")
            return []
    
    async def get_daily_brief(self, brief_date: Optional[date] = None) -> Optional[DailyBrief]:
        """
        Fetch daily brief for a specific date.
        
        Args:
            brief_date: Date for the brief (default: today)
            
        Returns:
            DailyBrief object or None if not available
        """
        if brief_date is None:
            brief_date = date.today()
        
        date_str = brief_date.isoformat()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/daily-brief/{date_str}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Parse top insights
                top_insights = [Insight(**item) for item in data.get("top_insights", [])]
                
                brief = DailyBrief(
                    date=date_str,
                    top_insights=top_insights,
                    summary=data.get("summary", "")
                )
                
                logger.info(f"Fetched daily brief for {date_str}")
                return brief
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Daily brief not available for {date_str}")
            else:
                logger.error(f"Failed to fetch daily brief: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch daily brief: {e}")
            return None
    
    async def download_chart_image(self, chart_url: str) -> Optional[bytes]:
        """
        Download chart image from GCS URL.
        
        Args:
            chart_url: URL to chart image
            
        Returns:
            Image bytes or None if download fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(chart_url, timeout=30.0)
                response.raise_for_status()
                
                logger.info(f"Downloaded chart image from {chart_url}")
                return response.content
                
        except Exception as e:
            logger.error(f"Failed to download chart image: {e}")
            return None
