"""Tests for Stripe webhook integration and subscription management."""
import pytest
import json
import stripe
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime
from uuid import uuid4

from src.models.db_models import User
from src.models.auth import UserSubscriptionTier, Role
from src.database import AsyncSessionLocal


@pytest.fixture
async def stripe_customer_user(clean_database):
    """Create a test user with Stripe customer ID."""
    user = User(
        id=uuid4(),
        firebase_uid="stripe_user_123",
        email="stripe@example.com",
        display_name="Stripe User",
        role=Role.USER.value,
        subscription_tier=UserSubscriptionTier.FREE.value,
        stripe_customer_id="cus_test123",
        created_at=datetime.utcnow(),
        last_login_at=datetime.utcnow()
    )
    
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user


@pytest.fixture
def stripe_signature():
    """Mock Stripe signature header."""
    return "t=1234567890,v1=mock_signature"


@pytest.fixture
def subscription_created_payload():
    """Mock Stripe subscription.created webhook payload."""
    return {
        "id": "evt_test123",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "metadata": {
                    "tier": "pro"
                }
            }
        }
    }


@pytest.fixture
def subscription_updated_payload():
    """Mock Stripe subscription.updated webhook payload."""
    return {
        "id": "evt_test456",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "metadata": {
                    "tier": "power"
                }
            }
        }
    }


@pytest.fixture
def subscription_deleted_payload():
    """Mock Stripe subscription.deleted webhook payload."""
    return {
        "id": "evt_test789",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "canceled"
            }
        }
    }


@pytest.fixture
def subscription_trial_payload():
    """Mock Stripe subscription with trial period."""
    return {
        "id": "evt_trial123",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_trial123",
                "customer": "cus_test123",
                "status": "trialing",
                "metadata": {
                    "tier": "pro"
                }
            }
        }
    }


@pytest.mark.asyncio
class TestStripeWebhookSignatureVerification:
    """Test Stripe webhook signature verification."""
    
    async def test_webhook_without_signature_fails(self, async_client):
        """Test that webhook without signature is rejected."""
        payload = {"type": "customer.subscription.created"}
        
        response = await async_client.post(
            "/billing/webhook",
            json=payload
        )
        
        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]
    
    async def test_webhook_with_invalid_signature_fails(
        self, 
        async_client, 
        subscription_created_payload,
        stripe_signature
    ):
        """Test that webhook with invalid signature is rejected."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", 
                sig_header=stripe_signature
            )
            
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_created_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]
    
    async def test_webhook_with_invalid_payload_fails(
        self, 
        async_client, 
        stripe_signature
    ):
        """Test that webhook with invalid payload is rejected."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = ValueError("Invalid payload")
            
            response = await async_client.post(
                "/billing/webhook",
                json={"invalid": "data"},
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 400
            assert "Invalid payload" in response.json()["detail"]
    
    async def test_webhook_with_valid_signature_succeeds(
        self, 
        async_client, 
        subscription_created_payload,
        stripe_signature,
        stripe_customer_user
    ):
        """Test that webhook with valid signature is accepted."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_created_payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_created_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"


@pytest.mark.asyncio
class TestSubscriptionCreated:
    """Test subscription.created webhook event handling."""
    
    async def test_subscription_created_upgrades_user_to_pro(
        self, 
        async_client, 
        subscription_created_payload,
        stripe_signature,
        stripe_customer_user
    ):
        """Test that subscription.created upgrades user to Pro tier."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_created_payload
            
            # Verify user starts at free tier
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "free"
            
            # Send webhook
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_created_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user upgraded to pro
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "pro"
    
    async def test_subscription_created_with_trial_period(
        self, 
        async_client, 
        subscription_trial_payload,
        stripe_signature,
        stripe_customer_user
    ):
        """Test that subscription with trial period upgrades user."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_trial_payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_trial_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user upgraded during trial
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "pro"
    
    async def test_subscription_created_for_nonexistent_customer(
        self, 
        async_client, 
        stripe_signature
    ):
        """Test that webhook for nonexistent customer is handled gracefully."""
        payload = {
            "id": "evt_test999",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test999",
                    "customer": "cus_nonexistent",
                    "status": "active",
                    "metadata": {"tier": "pro"}
                }
            }
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            # Should return 200 even if user not found (webhook acknowledged)
            assert response.status_code == 200


@pytest.mark.asyncio
class TestSubscriptionUpdated:
    """Test subscription.updated webhook event handling."""
    
    async def test_subscription_updated_upgrades_tier(
        self, 
        async_client, 
        subscription_updated_payload,
        stripe_signature,
        stripe_customer_user
    ):
        """Test that subscription.updated upgrades user tier."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_updated_payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_updated_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user upgraded to power
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "power"
    
    async def test_subscription_updated_handles_cancellation(
        self, 
        async_client, 
        stripe_signature,
        stripe_customer_user
    ):
        """Test that cancelled subscription downgrades user to free."""
        # First upgrade user to pro
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == stripe_customer_user.id)
            )
            user = result.scalar_one()
            user.subscription_tier = "pro"
            await session.commit()
        
        # Send cancellation webhook
        payload = {
            "id": "evt_cancel",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "canceled",
                    "metadata": {"tier": "pro"}
                }
            }
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user downgraded to free
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "free"
    
    async def test_subscription_updated_handles_past_due(
        self, 
        async_client, 
        stripe_signature,
        stripe_customer_user
    ):
        """Test that past_due subscription downgrades user to free."""
        # First upgrade user to pro
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == stripe_customer_user.id)
            )
            user = result.scalar_one()
            user.subscription_tier = "pro"
            await session.commit()
        
        # Send past_due webhook
        payload = {
            "id": "evt_past_due",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "past_due",
                    "metadata": {"tier": "pro"}
                }
            }
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user downgraded to free
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "free"
    
    async def test_subscription_trial_to_active_transition(
        self, 
        async_client, 
        stripe_signature,
        stripe_customer_user
    ):
        """Test that trial to active transition maintains tier."""
        # Set user to pro during trial
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == stripe_customer_user.id)
            )
            user = result.scalar_one()
            user.subscription_tier = "pro"
            await session.commit()
        
        # Send trial to active webhook
        payload = {
            "id": "evt_trial_end",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "active",
                    "metadata": {"tier": "pro"}
                }
            }
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user still at pro tier
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "pro"


@pytest.mark.asyncio
class TestSubscriptionDeleted:
    """Test subscription.deleted webhook event handling."""
    
    async def test_subscription_deleted_downgrades_to_free(
        self, 
        async_client, 
        subscription_deleted_payload,
        stripe_signature,
        stripe_customer_user
    ):
        """Test that subscription.deleted downgrades user to free tier."""
        # First upgrade user to pro
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == stripe_customer_user.id)
            )
            user = result.scalar_one()
            user.subscription_tier = "pro"
            await session.commit()
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_deleted_payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_deleted_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user downgraded to free
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "free"
    
    async def test_subscription_deleted_from_power_tier(
        self, 
        async_client, 
        subscription_deleted_payload,
        stripe_signature,
        stripe_customer_user
    ):
        """Test that power tier user is downgraded to free on cancellation."""
        # Upgrade user to power
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.id == stripe_customer_user.id)
            )
            user = result.scalar_one()
            user.subscription_tier = "power"
            await session.commit()
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_deleted_payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=subscription_deleted_payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            
            # Verify user downgraded to free
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).where(User.id == stripe_customer_user.id)
                )
                user = result.scalar_one()
                assert user.subscription_tier == "free"


@pytest.mark.asyncio
class TestWebhookErrorHandling:
    """Test webhook error handling and resilience."""
    
    async def test_webhook_handles_database_errors_gracefully(
        self, 
        async_client, 
        subscription_created_payload,
        stripe_signature
    ):
        """Test that database errors don't cause webhook to fail."""
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = subscription_created_payload
            
            with patch('src.routes.billing.handle_subscription_created') as mock_handler:
                mock_handler.side_effect = Exception("Database error")
                
                # Should still return 200 to acknowledge webhook
                response = await async_client.post(
                    "/billing/webhook",
                    json=subscription_created_payload,
                    headers={"Stripe-Signature": stripe_signature}
                )
                
                assert response.status_code == 200
    
    async def test_webhook_handles_unknown_event_types(
        self, 
        async_client, 
        stripe_signature
    ):
        """Test that unknown event types are handled gracefully."""
        payload = {
            "id": "evt_unknown",
            "type": "customer.unknown.event",
            "data": {"object": {}}
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = payload
            
            response = await async_client.post(
                "/billing/webhook",
                json=payload,
                headers={"Stripe-Signature": stripe_signature}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "success"
