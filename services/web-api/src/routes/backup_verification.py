"""
Backup Verification API Routes
Endpoints for managing and monitoring backup verification
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import os

from ..services.backup_verification_service import (
    BackupVerificationService,
    BackupVerificationError
)
from ..middleware.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backup", tags=["backup-verification"])


class VerificationRequest(BaseModel):
    """Request to trigger backup verification"""
    instance_name: Optional[str] = None


class VerificationResponse(BaseModel):
    """Response from backup verification"""
    verification_id: str
    timestamp: str
    instance_name: str
    test_instance_name: str
    status: str
    steps: List[dict]
    error: Optional[str] = None


class VerificationHistoryResponse(BaseModel):
    """Response with verification history"""
    verifications: List[dict]
    total: int


def get_verification_service() -> BackupVerificationService:
    """Dependency to get backup verification service"""
    project_id = os.getenv("GCP_PROJECT_ID", "utxoiq-project")
    instance_name = os.getenv("CLOUDSQL_INSTANCE", "utxoiq-postgres")
    backup_bucket = os.getenv("BACKUP_BUCKET", "utxoiq-backups")
    
    return BackupVerificationService(
        project_id=project_id,
        instance_name=instance_name,
        backup_bucket=backup_bucket
    )


@router.post("/verify", response_model=VerificationResponse)
async def trigger_backup_verification(
    request: VerificationRequest,
    background_tasks: BackgroundTasks,
    service: BackupVerificationService = Depends(get_verification_service),
    _: dict = Depends(require_admin)
):
    """
    Trigger backup verification process
    
    This endpoint initiates a backup verification by:
    1. Getting the latest backup
    2. Creating a test instance from the backup
    3. Verifying data integrity
    4. Scheduling cleanup
    
    Requires admin authentication.
    """
    try:
        logger.info("Backup verification triggered via API")
        
        # Run verification in background
        result = await service.verify_latest_backup()
        
        # Schedule cleanup of expired instances
        background_tasks.add_task(service.cleanup_expired_instances)
        
        return VerificationResponse(**result)
        
    except BackupVerificationError as e:
        logger.error(f"Backup verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during backup verification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Backup verification failed")


@router.get("/verify/history", response_model=VerificationHistoryResponse)
async def get_verification_history(
    limit: int = 10,
    service: BackupVerificationService = Depends(get_verification_service),
    _: dict = Depends(require_admin)
):
    """
    Get backup verification history
    
    Returns recent verification results with status and details.
    Requires admin authentication.
    """
    try:
        verifications = await service.get_verification_history(limit=limit)
        
        return VerificationHistoryResponse(
            verifications=verifications,
            total=len(verifications)
        )
        
    except Exception as e:
        logger.error(f"Failed to get verification history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve verification history")


@router.post("/cleanup")
async def cleanup_expired_instances(
    service: BackupVerificationService = Depends(get_verification_service),
    _: dict = Depends(require_admin)
):
    """
    Manually trigger cleanup of expired test instances
    
    This endpoint cleans up test instances that have exceeded their retention period.
    Requires admin authentication.
    """
    try:
        logger.info("Manual cleanup triggered via API")
        await service.cleanup_expired_instances()
        
        return {"status": "success", "message": "Cleanup completed"}
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Cleanup failed")


@router.get("/status")
async def get_backup_status(
    service: BackupVerificationService = Depends(get_verification_service),
    _: dict = Depends(require_admin)
):
    """
    Get current backup status and configuration
    
    Returns information about backup configuration and recent verification status.
    Requires admin authentication.
    """
    try:
        # Get latest verification
        history = await service.get_verification_history(limit=1)
        latest_verification = history[0] if history else None
        
        return {
            "instance_name": service.instance_name,
            "project_id": service.project_id,
            "backup_bucket": service.backup_bucket,
            "latest_verification": latest_verification,
            "verification_schedule": "Weekly on Sunday at 03:00 UTC"
        }
        
    except Exception as e:
        logger.error(f"Failed to get backup status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve backup status")
