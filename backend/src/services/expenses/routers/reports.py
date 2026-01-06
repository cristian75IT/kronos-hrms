from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile

from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError, ValidationError
from src.shared.schemas import MessageResponse, DataTableRequest
from src.services.expenses.services import ExpenseService
from src.services.expenses.deps import get_expense_service
from src.services.expenses.schemas import (
    ExpenseReportResponse,
    ExpenseReportListItem,
    ExpenseReportCreate,
    ExpenseReportWithItems,
    ExpenseReportStatus,
    ApproveReportRequest,
    RejectReportRequest,
    MarkPaidRequest,
    ExpenseAdminDataTableResponse
)

router = APIRouter()

@router.get("/expenses", response_model=list[ExpenseReportListItem])
async def get_my_reports(
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get current user's expense reports (trip-linked only)."""
    user_id = token.user_id
    
    status_list = None
    if status:
        status_list = [ExpenseReportStatus(s.strip()) for s in status.split(",")]
    
    reports = await service.get_user_reports(user_id, status_list)
    return [ExpenseReportListItem.model_validate(r) for r in reports]


@router.get("/expenses/standalone", response_model=list[ExpenseReportListItem])
async def get_standalone_reports(
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get current user's standalone expense reports (not linked to trips)."""
    user_id = token.user_id
    
    status_list = None
    if status:
        status_list = [ExpenseReportStatus(s.strip()) for s in status.split(",")]
    
    reports = await service.get_standalone_reports(user_id, status_list)
    return [ExpenseReportListItem.model_validate(r) for r in reports]


@router.post("/expenses/admin/datatable", response_model=ExpenseAdminDataTableResponse)
async def expenses_admin_datatable(
    request: DataTableRequest,
    status: Optional[str] = Query(None),
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get expense reports for Admin DataTable."""
    items, total, filtered = await service.get_admin_expenses_datatable(request, status)
    
    return ExpenseAdminDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=items,
    )


@router.get("/expenses/pending", response_model=list[ExpenseReportListItem])
async def get_pending_reports(
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get reports pending approval. Approver only."""
    reports = await service.get_pending_reports()
    return [ExpenseReportListItem.model_validate(r) for r in reports]


@router.get("/expenses/{id}", response_model=ExpenseReportWithItems)
async def get_report(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Get expense report with items."""
    return await service.get_report(id)


@router.post("/expenses", response_model=ExpenseReportResponse, status_code=201)
async def create_report(
    data: ExpenseReportCreate,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Create expense report."""
    user_id = token.user_id
    
    return await service.create_report(user_id, data)


@router.post("/expenses/{id}/submit", response_model=ExpenseReportResponse)
async def submit_report(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Submit report for approval."""
    user_id = token.user_id
    
    return await service.submit_report(id, user_id)


@router.delete("/expenses/{id}", response_model=MessageResponse)
async def delete_report(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Delete expense report (draft only)."""
    user_id = token.user_id
    
    await service.delete_report(id, user_id)
    return MessageResponse(message="Report deleted")


@router.post("/expenses/{id}/cancel", response_model=ExpenseReportResponse)
async def cancel_report(
    id: UUID,
    reason: str = Query(...),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Cancel expense report."""
    user_id = token.user_id
    
    return await service.cancel_report(id, user_id, reason)


@router.post("/expenses/{id}/approve", response_model=ExpenseReportResponse)
async def approve_report(
    id: UUID,
    data: ApproveReportRequest = ApproveReportRequest(),
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Approve expense report. Approver only."""
    approver_id = token.user_id
    
    return await service.approve_report(id, approver_id, data)


@router.post("/expenses/{id}/reject", response_model=ExpenseReportResponse)
async def reject_report(
    id: UUID,
    data: RejectReportRequest,
    token: TokenPayload = Depends(require_permission("expenses:approve")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Reject expense report. Approver only."""
    approver_id = token.user_id
    
    return await service.reject_report(id, approver_id, data)


@router.post("/expenses/{id}/paid", response_model=ExpenseReportResponse)
async def mark_paid(
    id: UUID,
    data: MarkPaidRequest,
    token: TokenPayload = Depends(require_permission("expenses:manage")),
    service: ExpenseService = Depends(get_expense_service),
):
    """Mark report as paid. Admin only."""
    return await service.mark_paid(id, data)


@router.post("/expenses/{id}/attachment", response_model=ExpenseReportResponse)
async def upload_report_attachment(
    id: UUID,
    file: UploadFile = File(...),
    token: TokenPayload = Depends(get_current_user),
    service: ExpenseService = Depends(get_expense_service),
):
    """Upload PDF attachment for an expense report."""
    user_id = token.user_id
    content = await file.read()
    
    return await service.update_report_attachment(
        id, user_id, content, file.filename, file.content_type
    )
