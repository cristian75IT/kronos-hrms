"""KRONOS Expense Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_admin, require_approver, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.shared.schemas import MessageResponse, DataTableRequest
from src.services.expenses.service import ExpenseService
from src.services.expenses.models import TripStatus, ExpenseReportStatus
from src.services.expenses.schemas import (
    BusinessTripResponse,
    BusinessTripListItem,
    TripDataTableResponse,
    BusinessTripCreate,
    BusinessTripUpdate,
    DailyAllowanceResponse,
    DailyAllowanceCreate,
    ExpenseReportResponse,
    ExpenseReportWithItems,
    ExpenseReportListItem,
    ExpenseReportCreate,
    ExpenseItemResponse,
    ExpenseItemCreate,
    ExpenseItemUpdate,
    ApproveTripRequest,
    RejectTripRequest,
    ApproveReportRequest,
    RejectReportRequest,
    MarkPaidRequest,
)


router = APIRouter()


async def get_expense_service(
    session: AsyncSession = Depends(get_db),
) -> ExpenseService:
    """Dependency for ExpenseService."""
    return ExpenseService(session)


# ═══════════════════════════════════════════════════════════
# Business Trip Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/trips", response_model=list[BusinessTripListItem])
async def get_my_trips(
    year: Optional[int] = None,
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get current user's trips."""
    user_id = UUID(token.keycloak_id)
    
    status_list = None
    if status:
        status_list = [TripStatus(s.strip()) for s in status.split(",")]
    
    trips = await service.get_user_trips(user_id, status_list, year)
    return [BusinessTripListItem.model_validate(t) for t in trips]


@router.post("/trips/datatable", response_model=TripDataTableResponse)
async def trips_datatable(
    request: DataTableRequest,
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trips for DataTable."""
    user_id = UUID(token.keycloak_id)
    
    status_list = None
    if status:
        status_list = [TripStatus(s.strip()) for s in status.split(",")]
    
    trips, total, filtered = await service.get_trips_datatable(request, user_id, status_list)
    
    return TripDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=[BusinessTripListItem.model_validate(t) for t in trips],
    )


@router.get("/trips/pending", response_model=list[BusinessTripListItem])
async def get_pending_trips(
    token: TokenPayload = Depends(require_approver),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trips pending approval. Approver only."""
    trips = await service.get_pending_trips()
    return [BusinessTripListItem.model_validate(t) for t in trips]


@router.get("/trips/{id}", response_model=BusinessTripResponse)
async def get_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get trip by ID."""
    try:
        return await service.get_trip(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips", response_model=BusinessTripResponse, status_code=201)
async def create_trip(
    data: BusinessTripCreate,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Create business trip."""
    user_id = UUID(token.keycloak_id)
    return await service.create_trip(user_id, data)


@router.put("/trips/{id}", response_model=BusinessTripResponse)
async def update_trip(
    id: UUID,
    data: BusinessTripUpdate,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Update trip (draft only)."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.update_trip(id, user_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trips/{id}/submit", response_model=BusinessTripResponse)
async def submit_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Submit trip for approval."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.submit_trip(id, user_id)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trips/{id}/approve", response_model=BusinessTripResponse)
async def approve_trip(
    id: UUID,
    data: ApproveTripRequest = ApproveTripRequest(),
    token: TokenPayload = Depends(require_approver),
    service: ExpenseService = Depends(get_expense_service),
):
    """Approve trip. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
    try:
        return await service.approve_trip(id, approver_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trips/{id}/reject", response_model=BusinessTripResponse)
async def reject_trip(
    id: UUID,
    data: RejectTripRequest,
    token: TokenPayload = Depends(require_approver),
    service: ExpenseService = Depends(get_expense_service),
):
    """Reject trip. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
    try:
        return await service.reject_trip(id, approver_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trips/{id}/complete", response_model=BusinessTripResponse)
async def complete_trip(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Mark trip as completed."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.complete_trip(id, user_id)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trips/{id}/attachment", response_model=BusinessTripResponse)
async def upload_trip_attachment(
    id: UUID,
    file: UploadFile = File(...),
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Upload PDF attachment for a trip."""
    user_id = UUID(token.keycloak_id)
    content = await file.read()
    
    try:
        return await service.update_trip_attachment(
            id, user_id, content, file.filename, file.content_type
        )
    except (BusinessRuleError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ═══════════════════════════════════════════════════════════
# Daily Allowance Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/trips/{trip_id}/allowances", response_model=list[DailyAllowanceResponse])
async def get_trip_allowances(
    trip_id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get daily allowances for a trip."""
    return await service.get_trip_allowances(trip_id)


@router.post("/trips/{trip_id}/allowances/generate", response_model=list[DailyAllowanceResponse])
async def generate_allowances(
    trip_id: UUID,
    token: TokenPayload = Depends(require_admin),
    service: ExpenseService = Depends(get_expense_service),
):
    """Regenerate allowances for a trip. Admin only."""
    try:
        return await service.generate_allowances(trip_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/allowances/{id}", response_model=DailyAllowanceResponse)
async def update_allowance(
    id: UUID,
    data: DailyAllowanceCreate,
    token: TokenPayload = Depends(require_admin),
    service: ExpenseService = Depends(get_expense_service),
):
    """Update daily allowance. Admin only."""
    return await service.update_allowance(id, data)


# ═══════════════════════════════════════════════════════════
# Expense Report Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/expenses", response_model=list[ExpenseReportListItem])
async def get_my_reports(
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get current user's expense reports."""
    user_id = UUID(token.keycloak_id)
    
    status_list = None
    if status:
        status_list = [ExpenseReportStatus(s.strip()) for s in status.split(",")]
    
    reports = await service.get_user_reports(user_id, status_list)
    return [ExpenseReportListItem.model_validate(r) for r in reports]


@router.get("/expenses/pending", response_model=list[ExpenseReportListItem])
async def get_pending_reports(
    token: TokenPayload = Depends(require_approver),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get reports pending approval. Approver only."""
    reports = await service.get_pending_reports()
    return [ExpenseReportListItem.model_validate(r) for r in reports]


@router.get("/expenses/{id}", response_model=ExpenseReportWithItems)
async def get_report(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get expense report with items."""
    try:
        return await service.get_report(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/expenses", response_model=ExpenseReportResponse, status_code=201)
async def create_report(
    data: ExpenseReportCreate,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Create expense report."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.create_report(user_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expenses/{id}/submit", response_model=ExpenseReportResponse)
async def submit_report(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Submit report for approval."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.submit_report(id, user_id)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expenses/{id}/approve", response_model=ExpenseReportResponse)
async def approve_report(
    id: UUID,
    data: ApproveReportRequest = ApproveReportRequest(),
    token: TokenPayload = Depends(require_approver),
    service: ExpenseService = Depends(get_expense_service),
):
    """Approve expense report. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
    try:
        return await service.approve_report(id, approver_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expenses/{id}/reject", response_model=ExpenseReportResponse)
async def reject_report(
    id: UUID,
    data: RejectReportRequest,
    token: TokenPayload = Depends(require_approver),
    service: ExpenseService = Depends(get_expense_service),
):
    """Reject expense report. Approver only."""
    approver_id = UUID(token.keycloak_id)
    
    try:
        return await service.reject_report(id, approver_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expenses/{id}/paid", response_model=ExpenseReportResponse)
async def mark_paid(
    id: UUID,
    data: MarkPaidRequest,
    token: TokenPayload = Depends(require_admin),
    service: ExpenseService = Depends(get_expense_service),
):
    """Mark report as paid. Admin only."""
    try:
        return await service.mark_paid(id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expenses/{id}/attachment", response_model=ExpenseReportResponse)
async def upload_report_attachment(
    id: UUID,
    file: UploadFile = File(...),
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Upload PDF attachment for an expense report."""
    user_id = UUID(token.keycloak_id)
    content = await file.read()
    
    try:
        return await service.update_report_attachment(
            id, user_id, content, file.filename, file.content_type
        )
    except (BusinessRuleError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ═══════════════════════════════════════════════════════════
# Expense Item Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/expenses/items", response_model=ExpenseItemResponse, status_code=201)
async def add_item(
    data: ExpenseItemCreate,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Add expense item."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.add_item(user_id, data)
    except (NotFoundError, BusinessRuleError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/expenses/items/{id}", response_model=ExpenseItemResponse)
async def update_item(
    id: UUID,
    data: ExpenseItemUpdate,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Update expense item."""
    user_id = UUID(token.keycloak_id)
    
    try:
        return await service.update_item(id, user_id, data)
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/expenses/items/{id}", response_model=MessageResponse)
async def delete_item(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: ExpenseService = Depends(get_expense_service),
):
    """Delete expense item."""
    user_id = UUID(token.keycloak_id)
    
    try:
        await service.delete_item(id, user_id)
        return MessageResponse(message="Item deleted")
    except (NotFoundError, BusinessRuleError) as e:
        raise HTTPException(status_code=400, detail=str(e))
