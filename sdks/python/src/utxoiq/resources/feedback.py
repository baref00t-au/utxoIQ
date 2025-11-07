"""Feedback resource for utxoIQ API."""
from typing import List, Optional
from ..models import UserFeedback, AccuracyLeaderboard


class FeedbackResource:
    """Resource for managing user feedback."""
    
    def __init__(self, client):
        self.client = client
    
    def submit(
        self,
        insight_id: str,
        rating: str,
        comment: Optional[str] = None
    ) -> UserFeedback:
        """
        Submit feedback for an insight.
        
        Args:
            insight_id: Insight identifier
            rating: Rating value (useful, not_useful)
            comment: Optional comment
        
        Returns:
            UserFeedback object
        """
        payload = {
            "rating": rating
        }
        if comment:
            payload["comment"] = comment
        
        response = self.client.post(f"/insights/{insight_id}/feedback", json=payload)
        return UserFeedback(**response.json())
    
    def get_accuracy_leaderboard(self) -> List[AccuracyLeaderboard]:
        """
        Get public accuracy leaderboard by model version.
        
        Returns:
            List of AccuracyLeaderboard objects
        """
        response = self.client.get("/insights/accuracy-leaderboard")
        data = response.json()
        return [AccuracyLeaderboard(**item) for item in data.get("leaderboard", [])]
