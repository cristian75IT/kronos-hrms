from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import get_current_user, require_approver, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.shared.schemas import DataTableRequest
from src.services.leaves.service import LeaveService
from src.services.leaves.models import LeaveRequestStatus
from src.services.leaves.schemas import (
    LeaveRequestResponse,
    LeaveRequestListItem,
    LeaveRequestDataTableResponse,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    ApproveRequest,
    ApproveConditionalRequest,
    RejectRequest,
    AcceptConditionRequest,
    CancelRequest,
    RecallRequest,
    PolicyValidationResult,
)
from src.services.leaves.deps import get_leave_service

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# Leave Request Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/leaves", response_model=list[LeaveRequestListItem])
async def get_my_requests(
    year: Optional[int] = None,
    status: Optional[str] = Query(None, description="Comma-separated statuses"),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get current user's leave requests."""
    user_id = token.user_id
    
    status_list = None
    if status:
        status_list = [LeaveRequestStatus(s.strip()) for s in status.split(",")]
    
    requests = await service.get_user_requests(user_id, year, status_list)
    return [LeaveRequestListItem.model_validate(r) for r in requests]


@router.post("/leaves/datatable", response_model=LeaveRequestDataTableResponse)
async def leaves_datatable(
    request: DataTableRequest,
    year: Optional[int] = None,
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get leave requests for DataTable."""
    user_id = token.user_id
    
    status_list = None
    if status:
        status_list = [LeaveRequestStatus(s.strip()) for s in status.split(",")]
    
    requests, total, filtered = await service.get_requests_datatable(
        request, user_id, status_list, year
    )
    
    return LeaveRequestDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=[LeaveRequestListItem.model_validate(r) for r in requests],
    )



# Schema for body-based filtering
class LeaveDataTableRequest(DataTableRequest):
    status: Optional[str] = None
    year: Optional[int] = None


@router.post("/leaves/admin/datatable", response_model=LeaveRequestDataTableResponse)
async def leaves_admin_datatable(
    request: LeaveDataTableRequest,
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveService = Depends(get_leave_service),
):
    """Get ALL leave requests for DataTable (Admin/HR)."""
    # No user_id filter -> get all
    
    status_list = None
    if request.status:
        status_list = [LeaveRequestStatus(s.strip()) for s in request.status.split(",")]
    
    requests, total, filtered = await service.get_requests_datatable(
        request, None, status_list, request.year
    )
    
    # Enrich with user names
    data = []
    for r in requests:
        item = LeaveRequestListItem.model_validate(r)
        # Fetch user info for display
        user_info = await service._get_user_info(r.user_id)
        if user_info:
            item.user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        data.append(item)
    
    return LeaveRequestDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=data,
    )


@router.get("/leaves/pending", response_model=list[LeaveRequestListItem])
async def get_pending_approval(
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Get requests pending approval. Approver only."""
    requests = await service.get_pending_approval()
    
    # Enrich with user names
    result = []
    for r in requests:
        item = LeaveRequestListItem.model_validate(r)
        # Fetch user name from auth service
        user_info = await service._get_user_info(r.user_id)
        if user_info:
            item.user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        result.append(item)
    
    return result


@router.get("/leaves/history", response_model=list[LeaveRequestListItem])
async def get_approval_history(
    status: Optional[str] = Query(None, description="Filter by status: approved, rejected, cancelled, all"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(50, ge=1, le=200),
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Get approval history (all processed requests). Approver only."""
    # Get all requests (not just pending)
    status_filter = None
    if status and status != "all":
        status_map = {
            "approved": [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL],
            "rejected": [LeaveRequestStatus.REJECTED],
            "cancelled": [LeaveRequestStatus.CANCELLED],
        }
        status_filter = status_map.get(status)
    
    requests = await service.get_all_requests(status=status_filter, year=year, limit=limit)
    
    # Enrich with user names
    result = []
    for r in requests:
        item = LeaveRequestListItem.model_validate(r)
        user_info = await service._get_user_info(r.user_id)
        if user_info:
            item.user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        result.append(item)
    
    return result


@router.get("/leaves/{id}", response_model=LeaveRequestResponse)
async def get_request(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get leave request by ID."""
    try:
        request = await service.get_request(id)
        
        # Build response with approval_request_id from centralized approvals service
        response_data = LeaveRequestResponse.model_validate(request)
        
        # Fetch approval_request_id if request is pending or has been processed
        if request.status in (LeaveRequestStatus.PENDING,):
            approval_info = await service._approval_client.check_status("LEAVE", id)
            if approval_info and approval_info.get("approval_request_id"):
                response_data.approval_request_id = UUID(approval_info["approval_request_id"])
        
        return response_data
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leaves", response_model=LeaveRequestResponse, status_code=201)
async def create_request(
    data: LeaveRequestCreate,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Create a new leave request (as draft)."""
    user_id = token.user_id
    
    try:
        return await service.create_request(user_id, data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/leaves/{id}", response_model=LeaveRequestResponse)
async def update_request(
    id: UUID,
    data: LeaveRequestUpdate,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Update a draft request."""
    user_id = token.user_id
    
    try:
        return await service.update_request(id, user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/submit", response_model=LeaveRequestResponse)
async def submit_request(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Submit a draft request for approval."""
    user_id = token.user_id
    
    try:
        return await service.submit_request(id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/leaves/{id}/approve", response_model=LeaveRequestResponse)
async def approve_request(
    id: UUID,
    data: ApproveRequest = ApproveRequest(),
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Approve a pending request. Approver only."""
    approver_id = token.user_id
    
    try:
        return await service.approve_request(id, approver_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/approve-conditional", response_model=LeaveRequestResponse)
async def approve_conditional(
    id: UUID,
    data: ApproveConditionalRequest,
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Approve with conditions. Approver only."""
    approver_id = token.user_id
    
    try:
        return await service.approve_conditional(id, approver_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/accept-condition", response_model=LeaveRequestResponse)
async def accept_condition(
    id: UUID,
    data: AcceptConditionRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Accept or reject approval conditions."""
    user_id = token.user_id
    
    try:
        return await service.accept_condition(id, user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/reject", response_model=LeaveRequestResponse)
async def reject_request(
    id: UUID,
    data: RejectRequest,
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Reject a pending request. Approver only."""
    approver_id = token.user_id
    
    try:
        return await service.reject_request(id, approver_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/revoke", response_model=LeaveRequestResponse)
async def revoke_approval(
    id: UUID,
    reason: str = Query(..., min_length=5, description="Reason for revocation"),
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Revoke an already approved request. Only within legal deadlines (before start_date)."""
    approver_id = token.user_id
    
    try:
        return await service.revoke_approval(id, approver_id, reason)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/reopen", response_model=LeaveRequestResponse)
async def reopen_request(
    id: UUID,
    notes: str = Query(None, description="Optional notes for reopening"),
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Reopen a rejected/cancelled request back to pending. Only before the original start_date."""
    approver_id = token.user_id
    
    try:
        return await service.reopen_request(id, approver_id, notes)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/cancel", response_model=LeaveRequestResponse)
async def cancel_request(
    id: UUID,
    data: CancelRequest = CancelRequest(),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Cancel own request."""
    user_id = token.user_id
    
    try:
        return await service.cancel_request(id, user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/recall", response_model=LeaveRequestResponse)
async def recall_request(
    id: UUID,
    data: RecallRequest,
    token: TokenPayload = Depends(require_permission("leaves:approve")),
    service: LeaveService = Depends(get_leave_service),
):
    """Recall an approved request. Manager only."""
    manager_id = token.user_id
    
    try:
        return await service.recall_request(id, manager_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/leaves/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_request(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Delete a draft request."""
    user_id = token.user_id
    
    try:
        await service.delete_request(id, user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/validate", response_model=PolicyValidationResult)
async def validate_request(
    data: LeaveRequestCreate,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Validate a request against policies before submission."""
    user_id = token.user_id
    
    # Calculate days first
    days = await service._calculate_days(
        data.start_date,
        data.end_date,
        data.start_half_day,
        data.end_half_day,
        user_id,
    )
    
    return await service._policy_engine.validate_request(
        user_id=user_id,
        leave_type_id=data.leave_type_id,
        start_date=data.start_date,
        end_date=data.end_date,
        days_requested=days,
    )


# ═══════════════════════════════════════════════════════════
# Internal Endpoints (for inter-service communication)
# ═══════════════════════════════════════════════════════════

@router.get("/leaves/internal/pending-count", response_model=int)
async def get_pending_count_internal(
    service: LeaveService = Depends(get_leave_service),
):
    """Internal endpoint for pending count (HR Dashboard)."""
    requests = await service.get_pending_approval()
    return len(requests)


@router.get("/leaves/internal/requests", response_model=list[LeaveRequestListItem])
async def get_requests_internal(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    user_id: Optional[UUID] = Query(None, description="Filter by user"),
    status: Optional[str] = Query(None, description="Comma-separated statuses"),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Internal endpoint to fetch requests by date range without authentication 
    (assumed protected by network/gateway).
    Used by HR Reporting service.
    """
    status_list = None
    if status:
        status_list = [LeaveRequestStatus(s.strip()) for s in status.split(",")]
    
    user_ids = [user_id] if user_id else None
    
    requests = await service.get_requests_by_range(
        start_date=start_date,
        end_date=end_date,
        user_ids=user_ids,
        status=status_list
    )
    
    return [LeaveRequestListItem.model_validate(r) for r in requests]


@router.post("/leaves/internal/recalculate-for-closure")
async def recalculate_for_closure(
    closure_start: date = Query(..., description="Closure start date"),
    closure_end: date = Query(..., description="Closure end date"),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Recalculate leave days for approved requests that overlap with a closure.
    
    This is an internal endpoint called by the calendar service when a 
    company closure is created or modified.
    """
    updates = await service.recalculate_for_closure(closure_start, closure_end)
    return {
        "message": f"Recalculated {len(updates)} leave requests",
        "updates": updates,
    }
