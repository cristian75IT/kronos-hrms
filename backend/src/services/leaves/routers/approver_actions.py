"""
KRONOS Leave Service - Approver Actions Router

Endpoints for managers/approvers to manage team leave requests.
Clear separation from user actions for enterprise audit compliance.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_approver as require_manager, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.services.leaves.service import LeaveService
from src.services.leaves.schemas import (
    LeaveRequestResponse,
    LeaveRequestListItem,
    ApproveRequest,
    ApproveConditionalRequest,
    RejectRequest,
    RecallRequest,
    PartialRecallRequest,
    SicknessInterruptionRequest,
    ModifyApprovedRequest,
    InterruptionResponse,
    BulkActionRequest,
    BulkActionResponse,
    BulkActionResult,
    VoluntaryWorkResponse,
)
from src.shared.schemas import DataTableRequest, DataTableResponse

router = APIRouter(prefix="/approver", tags=["Leave Approver Actions"])


def get_leave_service(db: AsyncSession = Depends(get_db)) -> LeaveService:
    return LeaveService(db)


# ═══════════════════════════════════════════════════════════════════
# Queue Management
# ═══════════════════════════════════════════════════════════════════

@router.get("/pending", response_model=list[LeaveRequestListItem])
async def get_pending_requests(
    token: TokenPayload = Depends(require_manager),
    include_delegated: bool = Query(default=True, description="Include requests from delegated approvals"),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Get all pending leave requests for approval.
    
    Includes:
    - Direct reports of the manager
    - Delegated requests (if another manager delegated to you)
    """
    requests = await service.get_pending_approval(approver_id=token.sub)
    
    if include_delegated:
        delegated = await service.get_delegated_pending_requests(token.sub)
        requests.extend(delegated)
    
    return [LeaveRequestListItem.model_validate(r, from_attributes=True) for r in requests]


@router.post("/pending/datatable", response_model=DataTableResponse[LeaveRequestListItem])
async def get_pending_datatable(
    request: DataTableRequest,
    token: TokenPayload = Depends(require_manager),
    include_delegated: bool = Query(default=True),
    service: LeaveService = Depends(get_leave_service),
):
    """Get pending requests for DataTable with pagination."""
    return await service.get_pending_datatable(
        request=request,
        approver_id=token.sub,
        include_delegated=include_delegated,
    )


@router.get("/voluntary-work/pending", response_model=list[VoluntaryWorkResponse])
async def get_pending_voluntary_work(
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Get all pending voluntary work requests for approval.
    
    These are requests from employees who want to convert vacation days
    to working days within their approved leave.
    """
    voluntary_works = await service.get_pending_voluntary_work_requests(token.sub)
    return [VoluntaryWorkResponse.model_validate(v, from_attributes=True) for v in voluntary_works]


# ═══════════════════════════════════════════════════════════════════
# Approval Actions
# ═══════════════════════════════════════════════════════════════════

@router.post("/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_request(
    request_id: UUID,
    data: ApproveRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """Approve a pending leave request."""
    try:
        request = await service.approve_request(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/approve-conditional", response_model=LeaveRequestResponse)
async def approve_conditional(
    request_id: UUID,
    data: ApproveConditionalRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """Approve with conditions (RIC, REP, PAR, etc.)."""
    try:
        request = await service.approve_conditional(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_request(
    request_id: UUID,
    data: RejectRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """Reject a pending leave request."""
    try:
        request = await service.reject_request(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/revoke", response_model=LeaveRequestResponse)
async def revoke_approval(
    request_id: UUID,
    reason: str = Query(..., min_length=10),
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Revoke an approved request (before it starts).
    
    Only allowed before the leave start date.
    """
    try:
        request = await service.revoke_approval(request_id, token.sub, reason)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/reopen", response_model=LeaveRequestResponse)
async def reopen_request(
    request_id: UUID,
    notes: Optional[str] = None,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """Reopen a rejected/cancelled request for reconsideration."""
    try:
        request = await service.reopen_request(request_id, token.sub, notes)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Recall Actions (Enterprise)
# ═══════════════════════════════════════════════════════════════════

@router.post("/{request_id}/recall", response_model=LeaveRequestResponse)
async def recall_full(
    request_id: UUID,
    data: RecallRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Full recall - terminate leave entirely from recall_date.
    
    Use when employee needs to return permanently from vacation.
    Unused days are automatically refunded.
    """
    try:
        request = await service.recall_request(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/recall/partial", response_model=InterruptionResponse)
async def recall_partial(
    request_id: UUID,
    data: PartialRecallRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Partial recall - call employee for specific days only.
    
    Use when you need the employee for 1-3 days during a longer vacation.
    The vacation continues after the recalled day(s).
    
    Example: Employee on 10-day vacation, you need them for a meeting on day 5.
    They work day 5, then continue vacation for remaining 5 days.
    """
    try:
        interruption = await service.create_partial_recall(request_id, token.sub, data)
        return InterruptionResponse.model_validate(interruption, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Interruption Actions (Enterprise)
# ═══════════════════════════════════════════════════════════════════

@router.post("/{request_id}/interrupt/sickness", response_model=InterruptionResponse)
async def interrupt_for_sickness(
    request_id: UUID,
    data: SicknessInterruptionRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Record sickness during vacation.
    
    Per Italian law (Art. 6 D.Lgs 66/2003), if an employee gets sick
    during vacation, sick days are NOT counted as vacation days.
    
    Requires INPS protocol number for verification.
    Balance is automatically refunded for sick days.
    """
    try:
        interruption = await service.create_sickness_interruption(request_id, token.sub, data)
        return InterruptionResponse.model_validate(interruption, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{request_id}/interruptions", response_model=list[InterruptionResponse])
async def get_request_interruptions(
    request_id: UUID,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """Get all interruptions for a leave request."""
    try:
        interruptions = await service.get_request_interruptions(request_id)
        return [InterruptionResponse.model_validate(i, from_attributes=True) for i in interruptions]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Voluntary Work Actions (Enterprise)
# Employee requests to convert vacation days to working days
# ═══════════════════════════════════════════════════════════════════

@router.post("/voluntary-work/{vw_id}/approve", response_model=VoluntaryWorkResponse)
async def approve_voluntary_work(
    vw_id: UUID,
    notes: Optional[str] = None,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Approve employee's request to work during approved vacation.
    
    Upon approval:
    - The specified vacation days are converted to working days
    - Vacation days are refunded to the employee's balance
    - Employee is expected to work on those days
    """
    try:
        voluntary_work = await service.approve_voluntary_work(vw_id, token.sub, notes)
        return VoluntaryWorkResponse.model_validate(voluntary_work, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/voluntary-work/{vw_id}/reject")
async def reject_voluntary_work(
    vw_id: UUID,
    reason: str = Query(..., min_length=10, description="Reason for rejection"),
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Reject employee's request to work during approved vacation.
    
    The vacation remains as originally approved.
    """
    try:
        await service.reject_voluntary_work(vw_id, token.sub, reason)
        return {"message": "Richiesta di lavoro volontario rifiutata", "id": str(vw_id)}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{request_id}/voluntary-work", response_model=list[VoluntaryWorkResponse])
async def get_leave_voluntary_work_requests(
    request_id: UUID,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """Get all voluntary work requests for a specific leave request."""
    try:
        voluntary_works = await service.get_voluntary_work_requests(request_id)
        return [VoluntaryWorkResponse.model_validate(v, from_attributes=True) for v in voluntary_works]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Modify Approved Request (Enterprise)
# ═══════════════════════════════════════════════════════════════════

@router.patch("/{request_id}/modify", response_model=LeaveRequestResponse)
async def modify_approved_request(
    request_id: UUID,
    data: ModifyApprovedRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Modify an already approved request (before start date).
    
    Use when employee needs to change dates after approval.
    Creates full audit trail of original and new values.
    """
    try:
        request = await service.modify_approved_request(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Bulk Actions (Enterprise)
# ═══════════════════════════════════════════════════════════════════

@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_action(
    data: BulkActionRequest,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Perform bulk approve/reject on multiple requests.
    
    Useful for end-of-month or vacation period processing.
    Each request is processed independently; failures don't stop the batch.
    """
    results = []
    
    for request_id in data.request_ids:
        try:
            if data.action == "approve":
                await service.approve_request(request_id, token.sub, ApproveRequest(notes=data.notes))
                results.append(BulkActionResult(request_id=request_id, success=True))
            elif data.action == "reject":
                if not data.reason:
                    results.append(BulkActionResult(
                        request_id=request_id, 
                        success=False, 
                        error_message="Reason required for reject"
                    ))
                    continue
                await service.reject_request(request_id, token.sub, RejectRequest(reason=data.reason))
                results.append(BulkActionResult(request_id=request_id, success=True))
        except Exception as e:
            results.append(BulkActionResult(request_id=request_id, success=False, error_message=str(e)))
    
    successful = sum(1 for r in results if r.success)
    
    return BulkActionResponse(
        action=data.action,
        total=len(data.request_ids),
        successful=successful,
        failed=len(data.request_ids) - successful,
        results=results,
    )


# ═══════════════════════════════════════════════════════════════════
# Team Calendar View
# ═══════════════════════════════════════════════════════════════════

@router.get("/team/calendar")
async def get_team_calendar(
    start_date: date,
    end_date: date,
    token: TokenPayload = Depends(require_manager),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Get calendar view of all team members' leave.
    
    Shows approved and pending requests for planning purposes.
    """
    # This would call a method that aggregates team data
    # Implementation depends on how teams are structured in auth service
    return await service.get_team_calendar(token.sub, start_date, end_date)
