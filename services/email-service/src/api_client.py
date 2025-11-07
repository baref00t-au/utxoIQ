"""Client for fetching data from Web API."""
import httpx
from typing import Optional
import logging
from datetime import datetime, timedelta

from .config import settings
from .models import DailyBrief, Insight, Citation

logger = logging.getLogger(__name__)


class APIClient:
    """Client for Web API operations."""
    
    def __init__(self):
        """Initialize API client."""
        self.base_url = settings.web_api_url
        self.api_key = settings.web_api_key
        self.headers = {}
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
    
    async def get_daily_brief(self, date: Optional[str] = None) -> Optional[DailyBrief]:
        """
        Fetch daily brief from Web API.
        
        Args:
            date: Date in YYYY-MM-DD format. Defaults to yesterday.
        
        Returns:
            DailyBrief object or None if not found
        """
        try:
            # Default to yesterday's date
            if not date:
                yesterday = datetime.utcnow() - timedelta(days=1)
                date = yesterday.strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/daily-brief/{date}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=30.0)
                
                if response.status_code == 404:
                    logger.warning(f"Daily brief not found for date: {date}")
                    return None
                
                response.raise_for_status()
                data = response.json()
                
                # Parse insights
                insights = []
                for insight_data in data.get("insights", []):
                    citations = [
                        Citation(**c) for c in insight_data.get("evidence", [])
                    ]
                    
                    insights.append(Insight(
                        id=insight_data["id"],
                        signal_type=insight_data["signal_type"],
                        headline=insight_data["headline"],
                        summary=insight_data["summary"],
                        confidence=insight_data["confidence"],
                        timestamp=datetime.fromisoformat(insight_data["timestamp"].replace("Z", "+00:00")),
                        block_height=insight_data["block_height"],
                        evidence=citations,
                        chart_url=insight_data.get("chart_url"),
                        tags=insight_data.get("tags", [])
                    ))
                
                return DailyBrief(
                    date=date,
                    insights=insights,
                    summary=data.get("summary")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching daily brief: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching daily brief: {str(e)}")
            return None
