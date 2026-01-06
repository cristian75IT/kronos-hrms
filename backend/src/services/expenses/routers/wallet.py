from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload, require_permission
from src.services.expenses.wallet.service import TripWalletService
from src.services.expenses.wallet.schemas import (
    TripWalletResponse,
    TripWalletTransactionResponse,
    WalletSummary,
    BudgetReserveRequest,
    PolicyCheckRequest,
    UpdateBudgetRequest,
    ProcessTransactionRequest,
    ReconciliationRequest,
    SettlementRequest,
    VoidTransactionRequest
)

router = APIRouter()

# Dependency to get WalletService
async def get_wallet_service(session: AsyncSession = Depends(get_db)) -> TripWalletService:
    return TripWalletService(session)

# ═══════════════════════════════════════════════════════════
# User Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/{trip_id}", response_model=TripWalletResponse)
async def get_wallet(
    trip_id: UUID, 
    current_user: TokenPayload = Depends(get_current_user),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get trip wallet (owner or admin)."""
    wallet = await service.get_wallet(trip_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found for this trip"
        )
    
    # Check authorization
    if wallet.user_id != current_user.sub and not current_user.is_admin and "wallet:view" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized to view this wallet")
    
    return wallet


@router.get("/{trip_id}/summary", response_model=WalletSummary)
async def get_wallet_summary(
    trip_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get comprehensive wallet summary."""
    summary = await service.get_wallet_summary(trip_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Auth check would go here if needed (e.g. check trip owner)
    return summary


@router.get("/{trip_id}/transactions", response_model=List[TripWalletTransactionResponse])
async def get_transactions(
    trip_id: UUID,
    limit: int = Query(default=100, le=500),
    current_user: TokenPayload = Depends(get_current_user),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get all transactions for a trip wallet."""
    wallet = await service.get_wallet(trip_id)
    if not wallet:
        return []
    
    return await service.get_transactions(wallet.id, limit)

# ═══════════════════════════════════════════════════════════
# Internal Endpoints (Backward Compatibility)
# ═══════════════════════════════════════════════════════════

@router.post("/internal/initialize/{trip_id}", response_model=TripWalletResponse)
async def internal_initialize_wallet(
    trip_id: UUID,
    user_id: UUID,
    budget: float,
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Initialize a wallet for a trip (internal system only)."""
    wallet = await service.create_wallet(trip_id, user_id, Decimal(str(budget)))
    await db.commit()
    return wallet


@router.get("/internal/{trip_id}/wallet")
async def internal_get_wallet(
    trip_id: UUID,
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get wallet for a trip (internal system only)."""
    wallet = await service.get_wallet(trip_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.post("/internal/{trip_id}/reserve")
async def reserve_budget(
    trip_id: UUID,
    data: BudgetReserveRequest,
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Reserve budget (internal system only)."""
    try:
        tx = await service.reserve_budget(
            trip_id=trip_id,
            amount=data.amount,
            reference_id=data.reference_id,
            category=data.category,
            description=data.description,
        )
        await db.commit()
        return {"status": "reserved", "transaction_id": str(tx.id)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/internal/{trip_id}/confirm/{reference_id}")
async def confirm_expense(
    trip_id: UUID,
    reference_id: UUID,
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a reserved expense (internal system only)."""
    tx = await service.confirm_expense(trip_id, reference_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Reservation not found")
    await db.commit()
    return {"status": "confirmed", "transaction_id": str(tx.id)}


@router.post("/internal/{trip_id}/cancel/{reference_id}")
async def cancel_expense(
    trip_id: UUID,
    reference_id: UUID,
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a reserved expense (internal system only)."""
    success = await service.cancel_expense(trip_id, reference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")
    await db.commit()
    return {"status": "cancelled"}


@router.get("/internal/{trip_id}/check-budget")
async def check_budget_available(
    trip_id: UUID,
    amount: Decimal,
    service: TripWalletService = Depends(get_wallet_service),
):
    """Check budget availability (internal system only)."""
    is_available, available = await service.check_budget_available(trip_id, amount)
    return {
        "available": is_available,
        "available_amount": float(available),
        "requested_amount": float(amount),
    }


@router.post("/internal/{trip_id}/check-policy")
async def check_policy_limit(
    trip_id: UUID,
    data: PolicyCheckRequest,
    service: TripWalletService = Depends(get_wallet_service),
):
    """Check policy policy limit (internal system only)."""
    return await service.check_policy_limit(trip_id, data.category, data.amount)

# ═══════════════════════════════════════════════════════════
# Admin Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/{trip_id}/transactions", response_model=TripWalletResponse)
async def process_transaction(
    trip_id: UUID,
    data: ProcessTransactionRequest,
    current_user: TokenPayload = Depends(require_permission("wallet", "manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Add manual transaction (admin)."""
    wallet = await service.process_transaction(
        trip_id=trip_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        reference_id=data.reference_id,
        description=data.description,
        created_by=current_user.sub,
        category=data.category,
        tax_rate=data.tax_rate,
        is_taxable=data.is_taxable,
        has_receipt=data.has_receipt,
        is_reimbursable=data.is_reimbursable,
    )
    await db.commit()
    return wallet


@router.patch("/{trip_id}/budget", response_model=TripWalletResponse)
async def update_budget(
    trip_id: UUID,
    data: UpdateBudgetRequest,
    current_user: TokenPayload = Depends(require_permission("wallet", "manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Adjust trip budget (admin)."""
    wallet = await service.update_budget(
        trip_id=trip_id,
        new_budget=data.new_budget,
        reason=data.reason,
        updated_by=current_user.sub,
    )
    await db.commit()
    return wallet


@router.post("/{trip_id}/reconcile", response_model=TripWalletResponse)
async def reconcile_wallet(
    trip_id: UUID,
    data: ReconciliationRequest,
    current_user: TokenPayload = Depends(require_permission("wallet", "manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Verify and reconcile wallet (admin)."""
    wallet = await service.reconcile_wallet(
        trip_id=trip_id,
        reconciled_by=current_user.sub,
        notes=data.notes,
        adjustments=data.adjustments,
    )
    await db.commit()
    return wallet


@router.post("/{trip_id}/settle", response_model=TripWalletResponse)
async def settle_wallet(
    trip_id: UUID,
    data: SettlementRequest,
    current_user: TokenPayload = Depends(require_permission("wallet", "manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Final settlement (admin/finance)."""
    wallet = await service.settle_wallet(
        trip_id=trip_id,
        settled_by=current_user.sub,
        payment_reference=data.payment_reference,
    )
    await db.commit()
    return wallet


@router.post("/transactions/{transaction_id}/void", response_model=TripWalletTransactionResponse)
async def void_transaction(
    transaction_id: UUID,
    data: VoidTransactionRequest,
    current_user: TokenPayload = Depends(require_permission("wallet", "manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Void a transaction (admin)."""
    reversal = await service.void_transaction(
        transaction_id=transaction_id,
        reason=data.reason,
        voided_by=current_user.sub,
    )
    await db.commit()
    return reversal
