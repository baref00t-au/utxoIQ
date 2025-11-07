"""Email preferences resource for utxoIQ API."""
from typing import List, Optional, Dict
from ..models import EmailPreferences


class EmailPreferencesResource:
    """Resource for managing email preferences."""
    
    def __init__(self, client):
        self.client = client
    
    def get(self) -> EmailPreferences:
        """
        Get current user email preferences.
        
        Returns:
            EmailPreferences object
        """
        response = self.client.get("/email/preferences")
        return EmailPreferences(**response.json())
    
    def update(
        self,
        daily_brief_enabled: Optional[bool] = None,
        frequency: Optional[str] = None,
        signal_filters: Optional[List[str]] = None,
        quiet_hours: Optional[Dict[str, str]] = None
    ) -> EmailPreferences:
        """
        Update email preferences.
        
        Args:
            daily_brief_enabled: Enable/disable daily brief emails
            frequency: Email frequency (daily, weekly, never)
            signal_filters: List of signal types to include
            quiet_hours: Dictionary with start and end times
        
        Returns:
            Updated EmailPreferences object
        """
        payload = {}
        if daily_brief_enabled is not None:
            payload["daily_brief_enabled"] = daily_brief_enabled
        if frequency is not None:
            payload["frequency"] = frequency
        if signal_filters is not None:
            payload["signal_filters"] = signal_filters
        if quiet_hours is not None:
            payload["quiet_hours"] = quiet_hours
        
        response = self.client.put("/email/preferences", json=payload)
        return EmailPreferences(**response.json())
