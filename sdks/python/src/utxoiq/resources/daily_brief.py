"""Daily brief resource for utxoIQ API."""
from datetime import date
from ..models import DailyBrief


class DailyBriefResource:
    """Resource for accessing daily briefs."""
    
    def __init__(self, client):
        self.client = client
    
    def get_by_date(self, brief_date: date) -> DailyBrief:
        """
        Get daily brief for specific date.
        
        Args:
            brief_date: Date for the brief
        
        Returns:
            DailyBrief object
        """
        date_str = brief_date.isoformat()
        response = self.client.get(f"/daily-brief/{date_str}")
        return DailyBrief(**response.json())
    
    def get_latest(self) -> DailyBrief:
        """
        Get the latest daily brief.
        
        Returns:
            DailyBrief object
        """
        response = self.client.get("/daily-brief/latest")
        return DailyBrief(**response.json())
