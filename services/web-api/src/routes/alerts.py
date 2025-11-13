"""Alert API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models import (
    Alert,
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    User,
    UserSubscriptionTier
)
from ..middleware import get_current_user, require_subscription_tier, rate_limit_dependency
from ..services.alerts_service import AlertsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert",
    description="Create a new custom alert for blockchain metrics (Pro/Power tier required)"
)
async def create_alert(
    alert_data: AlertCreate,
    user: User = Depends(require_subscription_tier(UserSubscriptionTier.PRO)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Create a new alert for the authenticated user.
    
    Requires Pro or Power subscription tier.
    """
    try:
        service = AlertsService()
        alert = await service.create_alert(user.uid, alert_data)
        return AlertResponse(alert=alert)
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )


@router.get(
    "",
    response_model=List[Alert],
    summary="Get user alerts",
    description="Retrieve all alerts for the authenticated user"
)
async def get_user_alerts(
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """Get all alerts for the authenticated user."""
    try:
        service = AlertsService()
        alerts = await service.get_user_alerts(user.uid)
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts"
        )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get alert by ID",
    description="Retrieve a specific alert"
)
async def get_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """Get a specific alert by ID."""
    try:
        service = AlertsService()
        alert = await service.get_alert(alert_id, user.uid)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        return AlertResponse(alert=alert)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alert"
        )


@router.put(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Update alert",
    description="Update an existing alert"
)
async def update_alert(
    alert_id: str,
    alert_data: AlertUpdate,
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """Update an existing alert."""
    try:
        service = AlertsService()
        alert = await service.update_alert(alert_id, user.uid, alert_data)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        return AlertResponse(alert=alert)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert",
    description="Delete an existing alert"
)
async def delete_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency)
):
    """Delete an existing alert."""
    try:
        service = AlertsService()
        success = await service.delete_alert(alert_id, user.uid)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )
