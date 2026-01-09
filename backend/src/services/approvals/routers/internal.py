"""
KRONOS Approval Service - Internal Router.

Inter-service endpoints for approval operations.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db

from ..services import ApprovalService
from ..schemas import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalStatusCheck,
    ApprovalCallbackPayload,
)

router = APIRouter(prefix="/internal", tags=["Internal"])


class InternalApproveRequest(BaseModel):
    """Request body for internal approve endpoint."""
    approver_id: UUID
    notes: Optional[str] = None


class InternalRejectRequest(BaseModel):
    """Request body for internal reject endpoint."""
    approver_id: UUID
    notes: str


def get_service(session: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(session)


@router.post("/request", status_code=status.HTTP_201_CREATED)
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
        # Return simple dict to avoid lazy loading issues
        return {
            "id": str(request.id),
            "entity_type": request.entity_type,
            "entity_id": str(request.entity_id),
            "status": request.status,
            "title": request.title,
            "created_at": request.created_at.isoformat() if request.created_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Error in create_internal_request: {e}", exc_info=True)
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
    request = await service.get_approval_by_entity(entity_type, entity_id)
    if not request:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": "none",
            "has_pending_request": False
        }
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "status": request.status,
        "id": str(request.id),
        "approval_request_id": str(request.id),
        "has_pending_request": request.status == "PENDING"
    }


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


@router.get("/by-entity/{entity_type}/{entity_id}")
async def get_by_entity(
    entity_type: str,
    entity_id: UUID,
    service: ApprovalService = Depends(get_service),
):
    """
    Get approval request by entity type and ID (internal use).
    
    Returns the approval request for the specified entity, or 404 if not found.
    """
    request = await service.get_approval_by_entity(entity_type, entity_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return {
        "id": str(request.id),
        "entity_type": request.entity_type,
        "entity_id": str(request.entity_id),
        "status": request.status,
        "title": request.title,
        "requester_id": str(request.requester_id) if request.requester_id else None,
        "requester_name": request.requester_name,
        "created_at": request.created_at.isoformat() if request.created_at else None,
    }


@router.post("/approve/{request_id}")
async def approve_internal(
    request_id: UUID,
    body: InternalApproveRequest,
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve an approval request (internal use).
    
    Called by other services to approve requests through the centralized system.
    """
    try:
        request = await service.approve_request(
            request_id=request_id,
            approver_id=body.approver_id,
            notes=body.notes,
        )
        await db.commit()
        return {
            "id": str(request.id),
            "status": request.status,
            "resolved_at": request.resolved_at.isoformat() if request.resolved_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject/{request_id}")
async def reject_internal(
    request_id: UUID,
    body: InternalRejectRequest,
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Reject an approval request (internal use).
    
    Called by other services to reject requests through the centralized system.
    """
    if not body.notes:
        raise HTTPException(status_code=400, detail="Notes are required when rejecting")
    
    try:
        request = await service.reject_request(
            request_id=request_id,
            approver_id=body.approver_id,
            notes=body.notes,
        )
        await db.commit()
        return {
            "id": str(request.id),
            "status": request.status,
            "resolved_at": request.resolved_at.isoformat() if request.resolved_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Health Check - Configuration Status
# ═══════════════════════════════════════════════════════════

class ConfigHealthItem(BaseModel):
    """Single configuration health check result."""
    config_type: str
    name: str
    status: str  # "ok" | "missing"
    message: Optional[str] = None


class ConfigHealthResponse(BaseModel):
    """Configuration health check response."""
    overall_status: str  # "ok" | "warning" | "critical"
    items: list[ConfigHealthItem]
    missing_count: int


REQUIRED_WORKFLOWS = ["LEAVE", "EXPENSE", "TRIP", "SMART_WORKING"]
WORKFLOW_NAMES = {
    "LEAVE": "Workflow Ferie/Permessi",
    "EXPENSE": "Workflow Note Spese",
    "TRIP": "Workflow Trasferte",
    "SMART_WORKING": "Workflow Smart Working",
}


@router.get("/health/config", response_model=ConfigHealthResponse)
async def check_config_health(
    db: AsyncSession = Depends(get_db),
):
    """
    Check system configuration health.
    
    Returns status of all required configurations (workflows, etc.).
    Used by admin dashboard to show configuration status.
    """
    from sqlalchemy import select
    from ..models import WorkflowConfig
    
    # Fetch existing workflow configs
    result = await db.execute(
        select(WorkflowConfig.entity_type).where(WorkflowConfig.is_active == True)
    )
    existing_workflows = {row[0] for row in result.fetchall()}
    
    items = []
    missing_count = 0
    
    for workflow_type in REQUIRED_WORKFLOWS:
        if workflow_type in existing_workflows:
            items.append(ConfigHealthItem(
                config_type=f"WORKFLOW_{workflow_type}",
                name=WORKFLOW_NAMES.get(workflow_type, workflow_type),
                status="ok",
            ))
        else:
            missing_count += 1
            items.append(ConfigHealthItem(
                config_type=f"WORKFLOW_{workflow_type}",
                name=WORKFLOW_NAMES.get(workflow_type, workflow_type),
                status="missing",
                message="Configura in Admin → Workflow Approvazioni",
            ))
    
    # Determine overall status
    if missing_count == 0:
        overall_status = "ok"
    elif missing_count < len(REQUIRED_WORKFLOWS):
        overall_status = "warning"
    else:
        overall_status = "critical"
    
    return ConfigHealthResponse(
        overall_status=overall_status,
        items=items,
        missing_count=missing_count,
    )
