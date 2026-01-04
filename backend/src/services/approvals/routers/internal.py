"""
KRONOS Approval Service - Internal Router.

Inter-service endpoints for approval operations.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

from ..service import ApprovalService
from ..schemas import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalStatusCheck,
    ApprovalCallbackPayload,
)

router = APIRouter(prefix="/internal", tags=["Internal"])


def get_service(session: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(session)


@router.post("/request", response_model=ApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_request(
    data: ApprovalRequestCreate,
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Create approval request (internal use by other services).
    
    No authentication required - only accessible within internal network.
    """
    try:
        request = await service.create_approval_request(data)
        await db.commit()
        return request
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{entity_type}/{entity_id}", response_model=ApprovalStatusCheck)
async def check_internal_status(
    entity_type: str,
    entity_id: UUID,
    service: ApprovalService = Depends(get_service),
):
    """
    Check approval status for an entity (internal use).
    
    Used by other services to check if an entity is pending approval.
    """
    return await service.check_approval_status(entity_type, entity_id)


@router.post("/webhook")
async def receive_webhook(
    payload: ApprovalCallbackPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive webhook callbacks (for future use).
    
    This endpoint can be used to receive external approval callbacks.
    """
    # Log the webhook for now
    return {"status": "received", "approval_request_id": str(payload.approval_request_id)}
