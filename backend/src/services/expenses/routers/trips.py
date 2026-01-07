from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile

from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.shared.schemas import MessageResponse, DataTableRequest, DataTableResponse
from src.services.expenses.services import ExpenseService
from src.services.expenses.deps import get_expense_service
from src.services.expenses.schemas import (
    BusinessTripResponse,
    BusinessTripListItem,
    BusinessTripCreate,
    BusinessTripUpdate,
    TripDataTableRequest,
    TripAdminDataTableResponse,
    ApproveTripRequest,
    RejectTripRequest,
    DailyAllowanceResponse,
    DailyAllowanceUpdate
)

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# Business Trip Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/trips", response_model=list[BusinessTripListItem])
async def get_my_trips(
    year: Optional[int] = None,
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get current user's trips."""
    status_list = None
    if status:
        status_list = [TripStatus(s.strip()) for s in status.split(",")]
        
    return await service.get_user_trips(
        user_id=token.user_id, 
        year=year, 
        status=status_list
    )


@router.post("/trips/datatable", response_model=DataTableResponse[BusinessTripListItem])
async def trips_datatable(
    request: DataTableRequest,
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trips for DataTable."""
    status_list = None
    if status:
        status_list = [TripStatus(s.strip()) for s in status.split(",")]

    items, total, filtered = await service.get_trips_datatable(
        request=request,
        user_id=token.user_id, 
        status=status_list
    )
    
    return DataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=items,
    )


@router.post("/trips/admin/datatable", response_model=TripAdminDataTableResponse)
async def trips_admin_datatable(
    request: TripDataTableRequest,
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trips for Admin DataTable (includes names)."""
    items, total, filtered = await service.get_admin_trips_datatable(request)
    
    return TripAdminDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=items,
    )


@router.get("/trips/pending", response_model=list[BusinessTripListItem])
async def get_pending_trips(
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trips pending approval. Approver only."""
    return await service.get_pending_trips()


@router.get("/trips/{id}", response_model=BusinessTripResponse)
async def get_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trip by ID."""
    return await service.get_trip(id)


@router.post("/trips", response_model=BusinessTripResponse, status_code=201)
async def create_trip(
    data: BusinessTripCreate,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Create business trip."""
    return await service.create_trip(token.user_id, data)


@router.put("/trips/{id}", response_model=BusinessTripResponse)
async def update_trip(
    id: UUID,
    data: BusinessTripUpdate,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Update trip (draft only)."""
    return await service.update_trip(id, token.user_id, data)


@router.post("/trips/{id}/submit", response_model=BusinessTripResponse)
async def submit_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Submit trip for approval."""
    return await service.submit_trip(id, token.user_id)


@router.post("/trips/{id}/approve", response_model=BusinessTripResponse)
async def approve_trip(
    id: UUID,
    data: ApproveTripRequest = ApproveTripRequest(),
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Approve trip. Approver only."""
    approver_id = token.user_id
    return await service.approve_trip(id, approver_id, data)


@router.post("/trips/{id}/reject", response_model=BusinessTripResponse)
async def reject_trip(
    id: UUID,
    data: RejectTripRequest,
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Reject trip. Approver only."""
    approver_id = token.user_id
    return await service.reject_trip(id, approver_id, data)


@router.post("/trips/{id}/complete", response_model=BusinessTripResponse)
async def complete_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Mark trip as completed."""
    return await service.complete_trip(id, token.user_id)


@router.delete("/trips/{id}", response_model=MessageResponse)
async def delete_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Delete trip (draft only)."""
    await service.delete_trip(id, token.user_id)
    return MessageResponse(message="Trip deleted")


@router.post("/trips/{id}/cancel", response_model=BusinessTripResponse)
async def cancel_trip(
    id: UUID,
    reason: str = Query(...),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Cancel trip request."""
    return await service.cancel_trip(id, token.user_id, reason)


@router.post("/trips/{id}/attachment", response_model=BusinessTripResponse)
async def upload_trip_attachment(
    id: UUID,
    file: UploadFile = File(...),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Upload PDF attachment for a trip."""
    user_id = token.user_id
    content = await file.read()
    
    return await service.update_trip_attachment(
        id, user_id, content, file.filename, file.content_type
    )


# ═══════════════════════════════════════════════════════════
# Daily Allowance Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/trips/{trip_id}/allowances", response_model=list[DailyAllowanceResponse])
async def get_trip_allowances(
    trip_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get daily allowances for a trip."""
    return await service.get_trip_allowances(trip_id, token.user_id)


@router.put("/allowances/{id}", response_model=DailyAllowanceResponse)
async def update_allowance(
    id: UUID,
    data: DailyAllowanceUpdate,
    token: TokenPayload = Depends(require_permission("expenses:manage")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Update daily allowance. Admin only."""
    return await service.update_allowance(id, data)
