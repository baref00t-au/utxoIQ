"""Daily brief API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date
from ..models import DailyBriefResponse
from ..middleware import rate_limit_dependency
from ..services.daily_brief_service import DailyBriefService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-brief", tags=["daily-brief"])


@router.get(
    "/{brief_date}",
    response_model=DailyBriefResponse,
    summary="Get daily brief",
    description="Retrieve the daily brief for a specific date"
)
async def get_daily_brief(
    brief_date: date,
    _: None = Depends(rate_limit_dependency)
):
    """Get daily brief for a specific date."""
    try:
        service = DailyBriefService()
        brief = await service.get_daily_brief(brief_date)
        
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Daily brief for {brief_date} not found"
            )
        
        return DailyBriefResponse(brief=brief)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching daily brief: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch daily brief"
        )
