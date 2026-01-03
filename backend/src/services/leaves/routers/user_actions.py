"""
KRONOS Leave Service - User Actions Router

Endpoints for employees to manage their own leave requests.
Clear separation from approver actions for enterprise audit compliance.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.services.leaves.service import LeaveService
from src.services.leaves.schemas import (
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestResponse,
    LeaveRequestListItem,
    AcceptConditionRequest,
    CancelRequest,
    DaysCalculationRequest,
    DaysCalculationResponse,
    SicknessInterruptionRequest,
    InterruptionResponse,
    CalendarRequest,
    CalendarResponse,
    BalanceSummary,
    ExcludedDaysResponse,
    VoluntaryWorkRequest,
    VoluntaryWorkResponse,
)
from src.shared.schemas import DataTableRequest, DataTableResponse

router = APIRouter(prefix="/my", tags=["My Leave Requests"])


def get_leave_service(db: AsyncSession = Depends(get_db)) -> LeaveService:
    return LeaveService(db)


# ═══════════════════════════════════════════════════════════════════
# Request Management (CRUD)
# ═══════════════════════════════════════════════════════════════════

@router.get("/requests", response_model=list[LeaveRequestListItem])
async def get_my_requests(
    year: Optional[int] = None,
    status: Optional[str] = None,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get all my leave requests."""
    status_list = None
    if status:
        from src.services.leaves.models import LeaveRequestStatus
        status_list = [LeaveRequestStatus(s.strip()) for s in status.split(",")]
    
    requests = await service.get_user_requests(token.sub, year=year, status=status_list)
    return [LeaveRequestListItem.model_validate(r, from_attributes=True) for r in requests]


@router.post("/requests/datatable", response_model=DataTableResponse[LeaveRequestListItem])
async def get_my_requests_datatable(
    request: DataTableRequest,
    year: Optional[int] = None,
    status: Optional[str] = None,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get my requests for DataTable with pagination."""
    status_list = None
    if status:
        from src.services.leaves.models import LeaveRequestStatus
        status_list = [LeaveRequestStatus(s.strip()) for s in status.split(",")]
    
    return await service.get_requests_datatable(request, user_id=token.sub, status=status_list, year=year)


@router.get("/requests/{request_id}", response_model=LeaveRequestResponse)
async def get_my_request(
    request_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get a specific leave request (must be mine)."""
    try:
        request = await service.get_request(request_id)
        if request.user_id != token.sub:
            raise HTTPException(status_code=403, detail="Cannot view another user's request")
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/requests", response_model=LeaveRequestResponse, status_code=201)
async def create_request(
    data: LeaveRequestCreate,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Create a new leave request (as draft)."""
    try:
        request = await service.create_request(token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/requests/{request_id}", response_model=LeaveRequestResponse)
async def update_request(
    request_id: UUID,
    data: LeaveRequestUpdate,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Update a draft request."""
    try:
        request = await service.update_request(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/requests/{request_id}", status_code=204)
async def delete_request(
    request_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Delete a draft request."""
    try:
        await service.delete_request(request_id, token.sub)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Workflow Actions
# ═══════════════════════════════════════════════════════════════════

@router.post("/requests/{request_id}/submit", response_model=LeaveRequestResponse)
async def submit_request(
    request_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Submit a draft request for approval."""
    try:
        request = await service.submit_request(request_id, token.sub)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/accept-condition", response_model=LeaveRequestResponse)
async def accept_condition(
    request_id: UUID,
    data: AcceptConditionRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Accept or reject conditions on a conditionally approved request."""
    try:
        request = await service.accept_condition(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_request(
    request_id: UUID,
    data: CancelRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Cancel a pending or approved request."""
    try:
        request = await service.cancel_request(request_id, token.sub, data)
        return LeaveRequestResponse.model_validate(request, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Enterprise: Employee-Initiated Interruptions
# ═══════════════════════════════════════════════════════════════════

@router.post("/requests/{request_id}/report-sickness", response_model=InterruptionResponse)
async def report_sickness_during_leave(
    request_id: UUID,
    data: SicknessInterruptionRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Report sickness during your approved vacation.
    
    Per Italian law (Art. 6 D.Lgs 66/2003), if you get sick during 
    your vacation, those days should NOT count as vacation.
    
    You need to:
    1. Report sickness to INPS (get protocol number)
    2. Submit this request with the protocol number
    3. HR will verify and refund the vacation days
    """
    try:
        interruption = await service.report_user_sickness(request_id, token.sub, data)
        return InterruptionResponse.model_validate(interruption, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/{request_id}/request-work", response_model=VoluntaryWorkResponse)
async def request_voluntary_work(
    request_id: UUID,
    data: VoluntaryWorkRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """
    Request to convert vacation day(s) to working day(s).
    
    Use this when you have approved vacation but want to work specific days.
    Common reasons:
    - Important project deadline
    - Need to save vacation days for later
    - Personal preference to work on that day
    
    Process:
    1. Submit this request specifying the days you want to work
    2. Your manager will review and approve/reject
    3. Upon approval, the vacation days are refunded to your balance
    4. You are expected to work on those days
    
    Note: This request requires manager approval. The vacation remains
    approved for the other days not included in this request.
    """
    try:
        voluntary_work = await service.request_voluntary_work(request_id, token.sub, data)
        return VoluntaryWorkResponse.model_validate(voluntary_work, from_attributes=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests/{request_id}/voluntary-work", response_model=list[VoluntaryWorkResponse])
async def get_my_voluntary_work_requests(
    request_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get all voluntary work requests for my leave request."""
    try:
        # Verify ownership
        request = await service.get_request(request_id)
        if request.user_id != token.sub:
            raise HTTPException(status_code=403, detail="Cannot view another user's request")
        
        voluntary_works = await service.get_voluntary_work_requests(request_id)
        return [VoluntaryWorkResponse.model_validate(v, from_attributes=True) for v in voluntary_works]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/requests/{request_id}/interruptions", response_model=list[InterruptionResponse])
async def get_my_request_interruptions(
    request_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get all interruptions for my leave request."""
    try:
        # Verify ownership
        request = await service.get_request(request_id)
        if request.user_id != token.sub:
            raise HTTPException(status_code=403, detail="Cannot view another user's request")
        
        interruptions = await service.get_request_interruptions(request_id)
        return [InterruptionResponse.model_validate(i, from_attributes=True) for i in interruptions]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# Balance & Calendar
# ═══════════════════════════════════════════════════════════════════

@router.get("/balance", response_model=BalanceSummary)
async def get_my_balance(
    year: Optional[int] = None,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get my leave balance summary."""
    from datetime import date
    target_year = year or date.today().year
    return await service._balance_service.get_balance_summary(token.sub, target_year)


@router.get("/calendar", response_model=CalendarResponse)
async def get_my_calendar(
    start_date: date,
    end_date: date,
    include_holidays: bool = Query(default=True),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get my leave calendar with holidays and closures."""
    return await service.get_user_calendar(
        user_id=token.sub,
        start_date=start_date,
        end_date=end_date,
        include_holidays=include_holidays,
    )


@router.get("/excluded-days", response_model=ExcludedDaysResponse)
async def get_excluded_days(
    start_date: date,
    end_date: date,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get excluded days (weekends, holidays, closures) for date range."""
    return await service.get_excluded_days(start_date, end_date, token.sub)


# ═══════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════

@router.post("/calculate-days", response_model=DaysCalculationResponse)
async def calculate_days(
    data: DaysCalculationRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Calculate working days for a date range (preview)."""
    return await service.calculate_preview(data)


@router.get("/history")
async def get_my_request_history(
    limit: int = Query(default=50, le=200),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveService = Depends(get_leave_service),
):
    """Get history of all my requests (for personal records)."""
    requests = await service.get_user_requests(token.sub)
    
    # Return simplified history
    return [
        {
            "id": str(r.id),
            "type": r.leave_type_code,
            "period": f"{r.start_date.isoformat()} - {r.end_date.isoformat()}",
            "days": float(r.days_requested),
            "status": r.status.value,
            "has_conditions": r.has_conditions,
            "created_at": r.created_at.isoformat(),
        }
        for r in requests[:limit]
    ]
