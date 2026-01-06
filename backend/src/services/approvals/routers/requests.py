"""
KRONOS Approval Service - Requests Router.

Endpoints for creating and managing approval requests.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_hr, TokenPayload

from ..services import ApprovalService
from ..schemas import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalRequestSummary,
    ApprovalHistoryResponse,
    DataTableRequest,
    DataTableResponse,
)

router = APIRouter(prefix="/requests", tags=["Approval Requests"])


def get_service(session: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(session)


# ═══════════════════════════════════════════════════════════
# Approval Requests
# ═══════════════════════════════════════════════════════════

@router.post("", response_model=ApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    data: ApprovalRequestCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new approval request.
    
    Called by other services when an entity needs approval.
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


@router.get("/{request_id}", response_model=ApprovalRequestResponse)
async def get_approval_request(
    request_id: UUID,
    include_history: bool = Query(default=False),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get approval request details."""
    request = await service.get_approval_request(request_id, include_history)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    # Check authorization (requester, approver, or admin)
    is_requester = request.requester_id == current_user.sub
    is_approver = any(d.approver_id == current_user.sub for d in (request.decisions or []))
    
    if not is_requester and not is_approver and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    return request


@router.get("/entity/{entity_type}/{entity_id}", response_model=ApprovalRequestResponse)
async def get_approval_by_entity(
    entity_type: str,
    entity_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get approval request by entity reference."""
    request = await service.get_approval_by_entity(entity_type, entity_id)
    if not request:
        raise HTTPException(status_code=404, detail="No approval request found for this entity")
    
    return request


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_approval_request(
    request_id: UUID,
    reason: Optional[str] = Body(default=None, embed=True),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an approval request."""
    request = await service.get_approval_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    # Only requester or admin can cancel
    if request.requester_id != current_user.sub and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
    
    try:
        await service.cancel_request(request_id, current_user.sub, reason)
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/resubmit", response_model=ApprovalRequestResponse)
async def resubmit_approval_request(
    request_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Resubmit a rejected or cancelled approval request.
    
    Creates a new approval request for the same entity.
    """
    # Get original request
    original = await service.get_approval_request(request_id)
    if not original:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    # Only requester can resubmit
    if original.requester_id != current_user.sub and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to resubmit this request")
    
    if original.status not in ["REJECTED", "CANCELLED", "EXPIRED"]:
        raise HTTPException(
            status_code=400,
            detail="Can only resubmit rejected, cancelled, or expired requests"
        )
    
    # Create new request
    new_request = await service.create_approval_request(
        ApprovalRequestCreate(
            entity_type=original.entity_type,
            entity_id=original.entity_id,
            entity_ref=original.entity_ref,
            requester_id=original.requester_id,
            requester_name=original.requester_name,
            title=original.title,
            description=original.description,
            metadata=original.request_metadata,
            callback_url=original.callback_url,
        )
    )
    
    await db.commit()
    return new_request


@router.get("/{request_id}/history", response_model=list[ApprovalHistoryResponse])
async def get_approval_history(
    request_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get approval request history."""
    request = await service.get_approval_request(request_id, include_history=True)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return request.history or []


# ═══════════════════════════════════════════════════════════
# My Requests (for requesters)
# ═══════════════════════════════════════════════════════════

@router.get("/my/submitted", response_model=list[ApprovalRequestSummary])
async def get_my_submitted_requests(
    status_filter: Optional[str] = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get requests submitted by current user."""
    # This would need a new method in the service
    # For now, return empty until implemented
    return []


# ═══════════════════════════════════════════════════════════
# Admin DataTable
# ═══════════════════════════════════════════════════════════

@router.post("/datatable", response_model=DataTableResponse)
async def get_requests_datatable(
    request: DataTableRequest,
    current_user: TokenPayload = Depends(require_hr),
    service: ApprovalService = Depends(get_service),
):
    """Get all approval requests in DataTable format (admin/HR only)."""
    # TODO: Implement full datatable support
    # For now, return empty
    return DataTableResponse(
        draw=request.draw,
        recordsTotal=0,
        recordsFiltered=0,
        data=[],
    )
