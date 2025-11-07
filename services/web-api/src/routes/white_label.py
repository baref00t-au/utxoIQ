"""White-Label API tier endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from ..models import InsightListResponse, User, UserSubscriptionTier
from ..middleware import verify_firebase_token, require_subscription_tier, rate_limit_dependency
from ..services.white_label_service import WhiteLabelService
from ..services.insights_service import InsightsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/custom", tags=["white-label"])


@router.get(
    "/{client_id}/insights",
    response_model=InsightListResponse,
    summary="Get custom branded insights",
    description="White-Label API endpoint with custom branding and formatting"
)
async def get_custom_insights(
    client_id: str,
    request: Request,
    limit: int = 20,
    page: int = 1,
    user: User = Depends(require_subscription_tier(UserSubscriptionTier.WHITE_LABEL)),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get insights with custom branding for White-Label clients.
    
    Requires White-Label subscription tier.
    """
    try:
        # Verify client configuration
        wl_service = WhiteLabelService()
        config = await wl_service.get_client_config(client_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"White-Label client {client_id} not found"
            )
        
        # Verify user has access to this client
        if not await wl_service.verify_client_access(user.uid, client_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this White-Label client"
            )
        
        # Fetch insights
        insights_service = InsightsService()
        insights, total = await insights_service.get_latest_insights(
            limit=limit,
            page=page,
            user=user
        )
        
        # Apply custom formatting
        formatted_insights = await wl_service.format_insights(insights, config)
        
        # Track SLA metrics
        await wl_service.track_request(client_id, request)
        
        return InsightListResponse(
            insights=formatted_insights,
            total=total,
            page=page,
            page_size=limit,
            has_more=(page * limit) < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching custom insights for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch custom insights"
        )


@router.get(
    "/{client_id}/config",
    summary="Get White-Label configuration",
    description="Retrieve branding and configuration for a White-Label client"
)
async def get_client_config(
    client_id: str,
    user: User = Depends(require_subscription_tier(UserSubscriptionTier.WHITE_LABEL)),
    _: None = Depends(rate_limit_dependency)
):
    """Get White-Label client configuration."""
    try:
        wl_service = WhiteLabelService()
        
        # Verify user has access
        if not await wl_service.verify_client_access(user.uid, client_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this White-Label client"
            )
        
        config = await wl_service.get_client_config(client_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"White-Label client {client_id} not found"
            )
        
        return {"config": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching config for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch configuration"
        )


@router.get(
    "/{client_id}/sla-metrics",
    summary="Get SLA metrics",
    description="Retrieve SLA monitoring metrics for White-Label tier (99.95% uptime)"
)
async def get_sla_metrics(
    client_id: str,
    user: User = Depends(require_subscription_tier(UserSubscriptionTier.WHITE_LABEL)),
    _: None = Depends(rate_limit_dependency)
):
    """Get SLA metrics for White-Label client."""
    try:
        wl_service = WhiteLabelService()
        
        # Verify user has access
        if not await wl_service.verify_client_access(user.uid, client_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this White-Label client"
            )
        
        metrics = await wl_service.get_sla_metrics(client_id)
        
        return {
            "client_id": client_id,
            "sla_target": 99.95,
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SLA metrics for {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch SLA metrics"
        )
