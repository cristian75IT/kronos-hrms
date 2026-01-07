from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import ValidationError
from src.shared.schemas import MessageResponse

from src.services.leaves.balance_service import LeaveBalanceService
from src.services.leaves.accrual_service import AccrualService
from src.services.leaves.schemas import (
    LeaveBalanceResponse,
    BalanceSummary,
    BalanceAdjustment,
    RecalculatePreviewResponse,
    RolloverPreviewResponse,
    ApplyChangesRequest,
    ApplyChangesRequest,
    EmployeePreviewItem,
    ImportBalanceRequest,
)
from src.services.leaves.deps import get_balance_service, get_accrual_service

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# Balance Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/balances/me", response_model=LeaveBalanceResponse)
async def get_my_balance(
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Get current user's balance."""
    user_id = token.user_id
    balance = await service.get_balance(user_id, year)
    if not balance:
        raise HTTPException(status_code=404, detail="Balance not found")
    return balance


@router.get("/balances/me/summary", response_model=BalanceSummary)
async def get_my_balance_summary(
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Get current user's balance summary with pending."""
    user_id = token.user_id
    return await service.get_balance_summary(user_id, year)


@router.get("/balances/{user_id}", response_model=LeaveBalanceResponse)
async def get_user_balance(
    user_id: UUID,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Get a user's balance. Admin only."""
    balance = await service.get_balance(user_id, year)
    if not balance:
        raise HTTPException(status_code=404, detail="Balance not found")
    return balance


@router.get("/balances/{user_id}/summary", response_model=BalanceSummary)
async def get_user_balance_summary(
    user_id: UUID,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Get a user's balance summary. Admin only."""
    return await service.get_balance_summary(user_id, year)


@router.post("/balances/{user_id}/adjust", response_model=LeaveBalanceResponse)
async def adjust_balance(
    user_id: UUID,
    data: BalanceAdjustment,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Manually adjust a user's balance. Admin only."""
    admin_id = token.user_id
    
    try:
        return await service.adjust_balance(user_id, year, data, admin_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balances/transactions/{balance_id}")
async def get_balance_transactions(
    balance_id: UUID,
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Get transactions for a balance. Admin only."""
    return await service.get_transactions(balance_id)


@router.post("/balances/accrual/recalculate", status_code=status.HTTP_204_NO_CONTENT)
async def recalculate_accruals(
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: AccrualService = Depends(get_accrual_service),
):
    """Admin only: Recalculate accruals for all users based on contracts."""
    await service.recalculate_all_balances(year)


@router.post("/balances/{user_id}/accrual/recalculate", status_code=status.HTTP_204_NO_CONTENT)
async def recalculate_user_accruals(
    user_id: UUID,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: AccrualService = Depends(get_accrual_service),
):
    """Admin only: Recalculate accruals for a specific user."""
    await service.recalculate_user_accrual(user_id, year)


@router.get("/balances/accrual/preview", response_model=RecalculatePreviewResponse)
async def preview_recalculate(
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: AccrualService = Depends(get_accrual_service),
):
    """Admin only: Preview recalculation changes before applying."""
    previews = await service.preview_recalculate(year)
    employees = [EmployeePreviewItem(**p) for p in previews]
    return RecalculatePreviewResponse(year=year, employees=employees, total_count=len(employees))


@router.post("/balances/accrual/apply-selected", response_model=MessageResponse)
async def apply_recalculate_selected(
    data: ApplyChangesRequest,
    year: int = Query(default_factory=lambda: date.today().year),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: AccrualService = Depends(get_accrual_service),
):
    """Admin only: Apply recalculation to selected users only."""
    await service.apply_recalculate_selected(year, data.user_ids)
    return MessageResponse(message=f"Ricalcolo applicato a {len(data.user_ids)} dipendenti.")


@router.get("/balances/rollover/preview", response_model=RolloverPreviewResponse)
async def preview_rollover(
    year: int = Query(..., description="Year to close (e.g. 2024)"),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Admin only: Preview rollover changes before applying."""
    previews = await service.preview_rollover(year)
    employees = [EmployeePreviewItem(**p) for p in previews]
    return RolloverPreviewResponse(from_year=year, to_year=year+1, employees=employees, total_count=len(employees))


@router.post("/balances/rollover/apply-selected", response_model=MessageResponse)
async def apply_rollover_selected(
    data: ApplyChangesRequest,
    year: int = Query(..., description="Year to close (e.g. 2024)"),
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Admin only: Apply rollover to selected users only."""
    count = await service.apply_rollover_selected(year, data.user_ids)
    return MessageResponse(message=f"Rollover applicato a {count} dipendenti.")


@router.post("/balances/process-accruals", response_model=MessageResponse, dependencies=[Depends(require_permission("leaves:manage"))])
async def process_monthly_accruals(
    year: int = Query(..., description="Year to process"),
    month: int = Query(..., description="Month to process"),
    service: AccrualService = Depends(get_accrual_service),
):
    """Trigger monthly accrual calculation for all active employees. (Admin only)"""
    count = await service.run_monthly_accruals(year, month)
    return MessageResponse(message=f"Elaborazione completata per {count} dipendenti.")


@router.post("/balances/process-expirations", response_model=MessageResponse, dependencies=[Depends(require_permission("leaves:manage"))])
async def process_expirations(
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Find and expire leave/ROL buckets that have passed their expiry date. (Admin only)"""
    count = await service.process_expirations()
    return MessageResponse(message=f"Elaborazione completata. Scaduti {count} pacchetti di ore/giorni.")


@router.post("/balances/process-rollover", response_model=MessageResponse, dependencies=[Depends(require_permission("leaves:manage"))])
async def process_rollover(
    year: int = Query(..., description="Year to close (e.g. 2024)"),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """Close a year and transfer remaining balances to the next year. (Admin only)"""
    count = await service.run_year_end_rollover(year)
    return MessageResponse(message=f"Chiusura anno {year} completata per {count} dipendenti. I residui sono stati trasferiti al {year+1}.")


@router.post("/balances/reconciliation/check", response_model=MessageResponse, dependencies=[Depends(require_permission("leaves:manage"))])
async def run_reconciliation_check(
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """
    Trigger manual reconciliation check between wallet and ledger. (Admin only)
    
    Runs the reconciliation check synchronously and returns results.
    """
    from sqlalchemy import text
    
    try:
        # Check for approved requests without ledger entries
        query = text("""
            SELECT COUNT(*) FROM leaves.leave_requests lr
            WHERE lr.status = 'APPROVED'
            AND lr.balance_deducted = true
            AND NOT EXISTS (
                SELECT 1 FROM leaves.time_ledger tl
                WHERE tl.reference_type = 'LEAVE_REQUEST'
                AND tl.reference_id = lr.id
                AND tl.entry_type = 'USAGE'
            )
        """)
        
        result = await service._session.execute(query)
        missing_ledger_count = result.scalar() or 0
        
        if missing_ledger_count > 0:
            return MessageResponse(
                message=f"⚠️ Rilevate {missing_ledger_count} anomalie: richieste approvate senza entry nel ledger. Verificare i log per dettagli."
            )
        

        return MessageResponse(message="✅ Nessuna anomalia rilevata. Wallet e Ledger sono sincronizzati.")
        
    except Exception as e:
        return MessageResponse(message=f"❌ Errore durante la verifica: {str(e)}")


@router.post("/balances/import", response_model=MessageResponse)
async def import_historical_balances(
    data: ImportBalanceRequest,
    token: TokenPayload = Depends(require_permission("leaves:manage")),
    service: LeaveBalanceService = Depends(get_balance_service),
):
    """
    Import historical balances from CSV/JSON. (Admin only)
    """
    admin_id = token.user_id
    results = await service.import_balances(admin_id, data.items, data.mode)
    
    msg = f"Import completato: {results['success']} successi, {results['failed']} falliti."
    if results['errors']:
        # Log errors or return them? For now just summarize.
        # Maybe returning detailed response is better but MessageResponse is standard here.
        pass
        
    return MessageResponse(message=msg)

