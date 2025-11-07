"""Alerts resource for utxoIQ API."""
from typing import List, Optional
from ..models import Alert


class AlertsResource:
    """Resource for managing user alerts."""
    
    def __init__(self, client):
        self.client = client
    
    def list(self, user_id: Optional[str] = None) -> List[Alert]:
        """
        List user alerts.
        
        Args:
            user_id: Optional user ID filter
        
        Returns:
            List of Alert objects
        """
        params = {}
        if user_id:
            params["user_id"] = user_id
        
        response = self.client.get("/alerts", params=params)
        data = response.json()
        return [Alert(**item) for item in data.get("alerts", [])]
    
    def create(
        self,
        signal_type: str,
        threshold: float,
        operator: str,
        notification_channel: str = "email",
        is_active: bool = True
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            signal_type: Type of signal to monitor
            threshold: Threshold value for alert
            operator: Comparison operator (gt, lt, eq)
            notification_channel: Channel for notifications (email, push)
            is_active: Whether alert is active
        
        Returns:
            Created Alert object
        """
        payload = {
            "signal_type": signal_type,
            "threshold": threshold,
            "operator": operator,
            "notification_channel": notification_channel,
            "is_active": is_active
        }
        
        response = self.client.post("/alerts", json=payload)
        return Alert(**response.json())
    
    def get(self, alert_id: str) -> Alert:
        """
        Get specific alert by ID.
        
        Args:
            alert_id: Alert identifier
        
        Returns:
            Alert object
        """
        response = self.client.get(f"/alerts/{alert_id}")
        return Alert(**response.json())
    
    def update(
        self,
        alert_id: str,
        threshold: Optional[float] = None,
        is_active: Optional[bool] = None,
        notification_channel: Optional[str] = None
    ) -> Alert:
        """
        Update an existing alert.
        
        Args:
            alert_id: Alert identifier
            threshold: New threshold value
            is_active: New active status
            notification_channel: New notification channel
        
        Returns:
            Updated Alert object
        """
        payload = {}
        if threshold is not None:
            payload["threshold"] = threshold
        if is_active is not None:
            payload["is_active"] = is_active
        if notification_channel is not None:
            payload["notification_channel"] = notification_channel
        
        response = self.client.put(f"/alerts/{alert_id}", json=payload)
        return Alert(**response.json())
    
    def delete(self, alert_id: str) -> bool:
        """
        Delete an alert.
        
        Args:
            alert_id: Alert identifier
        
        Returns:
            True if successful
        """
        self.client.delete(f"/alerts/{alert_id}")
        return True
