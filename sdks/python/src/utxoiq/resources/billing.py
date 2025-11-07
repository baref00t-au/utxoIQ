"""Billing resource for utxoIQ API."""
from ..models import Subscription


class BillingResource:
    """Resource for managing billing and subscriptions."""
    
    def __init__(self, client):
        self.client = client
    
    def get_subscription(self) -> Subscription:
        """
        Get current user subscription information.
        
        Returns:
            Subscription object
        """
        response = self.client.get("/billing/subscription")
        return Subscription(**response.json())
    
    def create_checkout_session(self, tier: str, success_url: str, cancel_url: str) -> dict:
        """
        Create Stripe checkout session for subscription.
        
        Args:
            tier: Subscription tier (pro, power)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
        
        Returns:
            Dictionary with checkout session URL
        """
        payload = {
            "tier": tier,
            "success_url": success_url,
            "cancel_url": cancel_url
        }
        response = self.client.post("/billing/checkout", json=payload)
        return response.json()
    
    def cancel_subscription(self) -> Subscription:
        """
        Cancel current subscription at period end.
        
        Returns:
            Updated Subscription object
        """
        response = self.client.post("/billing/cancel")
        return Subscription(**response.json())
