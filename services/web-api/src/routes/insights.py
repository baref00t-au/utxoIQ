"""Insight API routes."""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, List
from datetime import datetime
from ..models import (
    Insight,
    InsightResponse,
    InsightListResponse,
    User,
    SignalType
)
from ..middleware import get_optional_user, get_current_user, rate_limit_dependency
from ..services.insights_service import InsightsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get(
    "/latest",
    response_model=InsightListResponse,
    summary="Get latest insights",
    description="Retrieve the latest insights with optional filtering and pagination",
    operation_id="getLatestInsights",
    responses={
        200: {"description": "Successfully retrieved insights"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def get_latest_insights(
    limit: int = Query(20, ge=1, le=100, description="Number of insights to return"),
    page: int = Query(1, ge=1, description="Page number"),
    category: Optional[SignalType] = Query(None, description="Filter by signal type"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    user = Depends(get_optional_user),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get latest insights with pagination and filtering.
    
    Supports both authenticated and guest access.
    """
    try:
        service = InsightsService()
        insights, total = await service.get_latest_insights(
            limit=limit,
            page=page,
            signal_type=category,
            min_confidence=min_confidence,
            user=user
        )
        
        has_more = (page * limit) < total
        
        return InsightListResponse(
            insights=insights,
            total=total,
            page=page,
            page_size=limit,
            has_more=has_more
        )
    except Exception as e:
        logger.error(f"Error fetching latest insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch insights"
        )


@router.get(
    "/public",
    response_model=InsightListResponse,
    summary="Get public insights (Guest Mode)",
    description="Retrieve the 20 most recent insights without authentication",
    operation_id="getPublicInsights",
    responses={
        200: {"description": "Successfully retrieved public insights"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def get_public_insights(
    _: None = Depends(rate_limit_dependency)
):
    """
    Get public insights for Guest Mode.
    
    Returns the 20 most recent insights without requiring authentication.
    """
    try:
        service = InsightsService()
        insights, total = await service.get_public_insights()
        
        return InsightListResponse(
            insights=insights,
            total=total,
            page=1,
            page_size=20,
            has_more=False
        )
    except Exception as e:
        logger.error(f"Error fetching public insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch public insights"
        )


@router.get(
    "/{insight_id}",
    response_model=InsightResponse,
    summary="Get insight by ID",
    description="Retrieve a specific insight with full details including explainability",
    operation_id="getInsightById",
    responses={
        200: {"description": "Successfully retrieved insight"},
        404: {"description": "Insight not found"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def get_insight(
    insight_id: str,
    user = Depends(get_optional_user),
    _: None = Depends(rate_limit_dependency)
):
    """
    Get a specific insight by ID.
    
    Includes explainability data and evidence citations.
    """
    try:
        service = InsightsService()
        insight = await service.get_insight_by_id(insight_id, user)
        
        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insight {insight_id} not found"
            )
        
        return InsightResponse(insight=insight)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching insight {insight_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch insight"
        )


@router.get(
    "/accuracy-leaderboard",
    summary="Get accuracy leaderboard",
    description="Public leaderboard showing insight accuracy by model version",
    operation_id="getAccuracyLeaderboard",
    responses={
        200: {"description": "Successfully retrieved leaderboard"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def get_accuracy_leaderboard(
    _: None = Depends(rate_limit_dependency)
):
    """
    Get public accuracy leaderboard.
    
    Shows aggregate accuracy ratings by model version based on user feedback.
    """
    try:
        service = InsightsService()
        leaderboard = await service.get_accuracy_leaderboard()
        
        return {
            "leaderboard": leaderboard,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching accuracy leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaderboard"
        )
