"""Email preferences API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ..models import EmailPreferences, EmailPreferencesUpdate, User
from ..middleware import verify_firebase_token, rate_limit_dependency
from ..services.email_preferences_service import EmailPreferencesService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])


@router.get(
    "/preferences",
    response_model=EmailPreferences,
    summary="Get email preferences",
    description="Retrieve email preferences for the authenticated user"
)
async def get_email_preferences(
    user: User = Depends(verify_firebase_token),
    _: None = Depends(rate_limit_dependency)
):
    """Get email preferences for the authenticated user."""
    try:
        service = EmailPreferencesService()
        preferences = await service.get_preferences(user.uid)
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email preferences not found"
            )
        
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch email preferences"
        )


@router.put(
    "/preferences",
    response_model=EmailPreferences,
    summary="Update email preferences",
    description="Update email preferences for the authenticated user"
)
async def update_email_preferences(
    preferences_data: EmailPreferencesUpdate,
    user: User = Depends(verify_firebase_token),
    _: None = Depends(rate_limit_dependency)
):
    """Update email preferences for the authenticated user."""
    try:
        service = EmailPreferencesService()
        preferences = await service.update_preferences(user.uid, preferences_data)
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email preferences not found"
            )
        
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email preferences"
        )
