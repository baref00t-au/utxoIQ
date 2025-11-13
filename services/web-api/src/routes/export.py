"""Export API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from datetime import datetime
from ..models.export import ExportRequest, ExportResponse
from ..middleware import get_optional_user, rate_limit_dependency
from ..services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post(
    "/insights",
    summary="Export insights data",
    description="Export insights in CSV or JSON format with optional filtering",
    operation_id="exportInsights",
    responses={
        200: {
            "description": "Successfully generated export",
            "content": {
                "text/csv": {},
                "application/json": {}
            }
        },
        400: {"description": "Invalid request or export limit exceeded"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def export_insights(
    export_request: ExportRequest,
    user = Depends(get_optional_user),
    _: None = Depends(rate_limit_dependency)
):
    """
    Export insights data in CSV or JSON format.
    
    Supports filtering by signal type, confidence, and date range.
    Export limits are enforced based on subscription tier:
    - Free: 100 records
    - Pro: 1,000 records
    - Power: 10,000 records
    """
    try:
        service = ExportService()
        
        # Generate export
        content, content_type, record_count = await service.export_insights(
            export_request,
            user
        )
        
        # Generate filename
        filename = service.generate_filename(
            export_request.format,
            export_request.filters
        )
        
        # Return file response
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Record-Count": str(record_count),
                "X-Generated-At": datetime.utcnow().isoformat()
            }
        )
        
    except ValueError as e:
        logger.warning(f"Export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate export"
        )
