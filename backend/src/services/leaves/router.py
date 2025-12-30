"""KRONOS Leave Service - API Router."""
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_admin, require_approver, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.shared.schemas import MessageResponse, DataTableRequest
from src.services.leaves.service import LeaveService
from src.services.leaves.models import LeaveRequestStatus
from src.services.leaves.schemas import (
    LeaveRequestResponse,
    LeaveRequestListItem,
    LeaveRequestDataTableResponse,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    SubmitRequest,
    ApproveRequest,
    ApproveConditionalRequest,
    RejectRequest,
    AcceptConditionRequest,
    CancelRequest,
    RecallRequest,
    LeaveBalanceResponse,
    BalanceSummary,
    BalanceAdjustment,
    CalendarRequest,
    CalendarResponse,
    PolicyValidationResult,
)


router = APIRouter()


async def get_leave_service(
    session: AsyncSession = Depends(get_db),
) -> LeaveService:
    """Dependency for LeaveService."""
    return LeaveService(session)


async def get_current_user_id(
    token: TokenPayload = Depends(get_current_token),
) -> UUID:
    """Get current user's ID from Keycloak token.
    
    The keycloak_id is used as the primary user identifier across all services.
    This approach ensures consistency with the auth-service user sync.
    """
    return UUID(token.keycloak_id)


# ═══════════════════════════════════════════════════════════
# Leave Request Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/leaves", response_model=list[LeaveRequestListItem])
async def get_my_requests(
    year: Optional[int] = None,
    status: Optional[str] = Query(None, description="Comma-separated statuses"),
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Get current user's leave requests."""
    user_id = UUID(token.keycloak_id)
    
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
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Get leave requests for DataTable."""
    user_id = UUID(token.keycloak_id)
    
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


@router.get("/leaves/pending", response_model=list[LeaveRequestListItem])
async def get_pending_approval(
    token: TokenPayload = Depends(require_approver),
    service: LeaveService = Depends(get_leave_service),
):
    """Get requests pending approval. Approver only."""
    requests = await service.get_pending_approval()
    return [LeaveRequestListItem.model_validate(r) for r in requests]


@router.get("/leaves/{id}", response_model=LeaveRequestResponse)
async def get_request(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Get leave request by ID."""
    try:
        return await service.get_request(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leaves", response_model=LeaveRequestResponse, status_code=201)
async def create_request(
    data: LeaveRequestCreate,
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Create a new leave request (as draft)."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.create_request(user_id, data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/leaves/{id}", response_model=LeaveRequestResponse)
async def update_request(
    id: UUID,
    data: LeaveRequestUpdate,
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Update a draft request."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.update_request(id, user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/submit", response_model=LeaveRequestResponse)
async def submit_request(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Submit a draft request for approval."""
    user_id = UUID(token.keycloak_id)
    
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
    token: TokenPayload = Depends(require_approver),
    service: LeaveService = Depends(get_leave_service),
):
    """Approve a pending request. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
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
    token: TokenPayload = Depends(require_approver),
    service: LeaveService = Depends(get_leave_service),
):
    """Approve with conditions. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
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
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Accept or reject approval conditions."""
    user_id = UUID(token.keycloak_id)
    
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
    token: TokenPayload = Depends(require_approver),
    service: LeaveService = Depends(get_leave_service),
):
    """Reject a pending request. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
    try:
        return await service.reject_request(id, approver_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/leaves/{id}/cancel", response_model=LeaveRequestResponse)
async def cancel_request(
    id: UUID,
    data: CancelRequest = CancelRequest(),
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Cancel own request."""
    user_id = UUID(token.keycloak_id)
    
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
    token: TokenPayload = Depends(require_approver),
    service: LeaveService = Depends(get_leave_service),
):
    """Recall an approved request. Manager only."""
    manager_id = UUID(token.keycloak_id)
    
    try:
        return await service.recall_request(id, manager_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Balance Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/balances/me", response_model=LeaveBalanceResponse)
async def get_my_balance(
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Get current user's balance."""
    user_id = UUID(token.keycloak_id)
    return await service.get_balance(user_id, year)


@router.get("/balances/me/summary", response_model=BalanceSummary)
async def get_my_balance_summary(
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Get current user's balance summary with pending."""
    user_id = UUID(token.keycloak_id)
    return await service.get_balance_summary(user_id, year)


@router.get("/balances/{user_id}", response_model=LeaveBalanceResponse)
async def get_user_balance(
    user_id: UUID,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_admin),
    service: LeaveService = Depends(get_leave_service),
):
    """Get a user's balance. Admin only."""
    return await service.get_balance(user_id, year)


@router.post("/balances/{user_id}/adjust", response_model=LeaveBalanceResponse)
async def adjust_balance(
    user_id: UUID,
    data: BalanceAdjustment,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_admin),
    service: LeaveService = Depends(get_leave_service),
):
    """Manually adjust a user's balance. Admin only."""
    admin_id = UUID(token.keycloak_id)
    
    try:
        return await service.adjust_balance(user_id, year, data, admin_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Calendar Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/leaves/calendar", response_model=CalendarResponse)
async def get_calendar(
    request: CalendarRequest,
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Get calendar events for FullCalendar."""
    user_id = UUID(token.keycloak_id)
    is_manager = token.is_manager
    
    return await service.get_calendar(request, user_id, is_manager)


# ═══════════════════════════════════════════════════════════
# Validation Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/leaves/validate", response_model=PolicyValidationResult)
async def validate_request(
    data: LeaveRequestCreate,
    token: TokenPayload = Depends(get_current_token),
    service: LeaveService = Depends(get_leave_service),
):
    """Validate a request against policies before submission."""
    user_id = UUID(token.keycloak_id)
    
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
