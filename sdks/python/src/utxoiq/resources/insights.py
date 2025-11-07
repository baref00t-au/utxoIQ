"""Insights resource for utxoIQ API."""
from typing import List, Optional
from ..models import Insight


class InsightsResource:
    """Resource for managing insights."""
    
    def __init__(self, client):
        self.client = client
    
    def get_latest(
        self,
        limit: int = 20,
        category: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[Insight]:
        """
        Get latest insights.
        
        Args:
            limit: Maximum number of insights to return
            category: Filter by signal category (mempool, exchange, miner, whale)
            min_confidence: Minimum confidence score filter
        
        Returns:
            List of Insight objects
        """
        params = {"limit": limit}
        if category:
            params["category"] = category
        if min_confidence is not None:
            params["min_confidence"] = min_confidence
        
        response = self.client.get("/insights/latest", params=params)
        data = response.json()
        return [Insight(**item) for item in data.get("insights", [])]
    
    def get_public(self, limit: int = 20) -> List[Insight]:
        """
        Get public insights (Guest Mode - no authentication required).
        
        Args:
            limit: Maximum number of insights to return (max 20)
        
        Returns:
            List of Insight objects
        """
        response = self.client.get("/insights/public", params={"limit": min(limit, 20)})
        data = response.json()
        return [Insight(**item) for item in data.get("insights", [])]
    
    def get_by_id(self, insight_id: str) -> Insight:
        """
        Get specific insight by ID.
        
        Args:
            insight_id: Unique insight identifier
        
        Returns:
            Insight object
        """
        response = self.client.get(f"/insight/{insight_id}")
        return Insight(**response.json())
    
    def search(
        self,
        query: str,
        limit: int = 20,
        category: Optional[str] = None
    ) -> List[Insight]:
        """
        Search insights by query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            category: Filter by signal category
        
        Returns:
            List of Insight objects
        """
        params = {"q": query, "limit": limit}
        if category:
            params["category"] = category
        
        response = self.client.get("/insights/search", params=params)
        data = response.json()
        return [Insight(**item) for item in data.get("insights", [])]
