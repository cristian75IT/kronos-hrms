"""
KRONOS Approval Service - Decisions Router.

Endpoints for approvers to view and make decisions.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload

from ..service import ApprovalService
from ..schemas import (
    ApprovalDecisionCreate,
    ApprovalDecisionConditionalCreate,
    ApprovalDecisionResponse,
    ApprovalRequestResponse,
    PendingApprovalsResponse,
    PendingCountResponse,
)

router = APIRouter(prefix="/decisions", tags=["Approval Decisions"])


def get_service(session: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(session)


# ═══════════════════════════════════════════════════════════
# Pending Approvals (for approvers)
# ═══════════════════════════════════════════════════════════

@router.get("/pending", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    entity_type: Optional[str] = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get pending approvals for current user."""
    return await service.get_pending_approvals(
        approver_id=current_user.sub,
        entity_type=entity_type,
        include_all=current_user.is_admin,
    )


@router.get("/pending/count", response_model=PendingCountResponse)
async def get_pending_count(
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get count of pending approvals for current user."""
    return await service.get_pending_count(current_user.sub)


# ═══════════════════════════════════════════════════════════
# Make Decisions
# ═══════════════════════════════════════════════════════════

@router.post("/{request_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    request_id: UUID,
    notes: Optional[str] = Body(default=None, embed=True),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Approve an approval request."""
    try:
        await service.approve_request(
            request_id=request_id,
            approver_id=current_user.sub,
            notes=notes,
            override_authority=current_user.is_admin,
        )
        await db.commit()
        # Re-fetch to ensure relationships are loaded and object is not expired
        result = await service.get_approval_request(request_id)
        if not result:
            import logging
            logging.error(f"CRITICAL: Request {request_id} not found after approval commit")
            raise ValueError("Request lost after approval")
        return result
    except ValueError as e:
        import logging
        logging.error(f"ValueError asserting approval: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Unexpected error in approve_request: {e}")
        logging.error(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.post("/{request_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    request_id: UUID,
    notes: Optional[str] = Body(default=None, embed=True),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Reject an approval request."""
    if not notes:
        raise HTTPException(
            status_code=400,
            detail="Notes are required when rejecting a request"
        )
    
    try:
        await service.reject_request(
            request_id=request_id,
            approver_id=current_user.sub,
            notes=notes,
            override_authority=current_user.is_admin,
        )
        await db.commit()
        # Re-fetch to ensure relationships are loaded and object is not expired
        result = await service.get_approval_request(request_id)
        if not result:
            import logging
            logging.error(f"CRITICAL: Request {request_id} not found after reject commit")
            raise ValueError("Request lost after rejection")
        return result
    except ValueError as e:
        import logging
        logging.error(f"ValueError rejecting: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Unexpected error in reject_request: {e}")
        logging.error(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.post("/{request_id}/approve-conditional", response_model=ApprovalRequestResponse)
async def approve_conditional_request(
    request_id: UUID,
    data: ApprovalDecisionConditionalCreate = Body(...),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Approve an approval request with conditions."""
    try:
        await service.approve_conditional_request(
            request_id=request_id,
            approver_id=current_user.sub,
            condition_type=data.condition_type,
            condition_details=data.condition_details,
            notes=data.notes,
            override_authority=current_user.is_admin,
        )
        await db.commit()
        # Re-fetch to ensure relationships are loaded and object is not expired
        result = await service.get_approval_request(request_id)
        if not result:
            import logging
            logging.error(f"CRITICAL: Request {request_id} not found after conditional approval commit")
            raise ValueError("Request lost after conditional approval")
        return result
    except ValueError as e:
        import logging
        logging.error(f"ValueError conditional approval: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Unexpected error in approve_conditional_request: {e}")
        logging.error(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.post("/{request_id}/delegate", response_model=ApprovalRequestResponse)
async def delegate_request(
    request_id: UUID,
    delegate_to_id: UUID = Body(..., embed=True),
    delegate_to_name: Optional[str] = Body(default=None, embed=True),
    notes: Optional[str] = Body(default=None, embed=True),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Delegate approval to another user."""
    if delegate_to_id == current_user.sub:
        raise HTTPException(
            status_code=400,
            detail="Cannot delegate to yourself"
        )
    
    try:
        await service.delegate_request(
            request_id=request_id,
            approver_id=current_user.sub,
            delegate_to_id=delegate_to_id,
            delegate_to_name=delegate_to_name,
            notes=notes,
            override_authority=current_user.is_admin,
        )
        await db.commit()
        # Re-fetch to ensure relationships are loaded and object is not expired
        result = await service.get_approval_request(request_id)
        if not result:
            import logging
            logging.error(f"CRITICAL: Request {request_id} not found after delegate commit")
            raise ValueError("Request lost after delegation")
        return result
    except ValueError as e:
        import logging
        logging.error(f"ValueError delegating: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Unexpected error in delegate_request: {e}")
        logging.error(traceback.format_exc())
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


# ═══════════════════════════════════════════════════════════
# Decision History
# ═══════════════════════════════════════════════════════════

@router.get("/my/history", response_model=list[ApprovalDecisionResponse])
async def get_my_decision_history(
    limit: int = Query(default=50, le=200),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get history of decisions made by current user."""
    # TODO: Implement decision history query
    return []


@router.get("/archived")
async def get_archived_approvals(
    status_filter: Optional[str] = Query(default=None, description="Filter by decision: approved, rejected, delegated, or all"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    current_user: TokenPayload = Depends(get_current_user),
    service: ApprovalService = Depends(get_service),
):
    """Get archived (decided) approvals for current user."""
    return await service.get_archived_approvals(
        approver_id=current_user.sub,
        status_filter=status_filter,
        entity_type=entity_type,
    )
