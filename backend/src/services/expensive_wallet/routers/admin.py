from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload
from src.services.expensive_wallet.service import TripWalletService
from src.services.expensive_wallet.deps import get_wallet_service
from src.services.expensive_wallet.schemas import (
    TripWalletResponse,
    TransactionCreate,
    ReconcileRequest,
    SettleRequest,
    UpdateBudgetRequest,
    VoidTransactionRequest
)

router = APIRouter()

@router.post("/initialize/{trip_id}", response_model=TripWalletResponse)
async def initialize_wallet(
    trip_id: UUID,
    user_id: UUID,
    budget: float,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Initialize a wallet for a trip (budget allocation) - requires auth."""
    wallet = await service.create_wallet(trip_id, user_id, Decimal(str(budget)))
    await db.commit()
    return wallet


@router.post("/{trip_id}/transactions", response_model=TripWalletResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    trip_id: UUID, 
    data: TransactionCreate,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Create a wallet transaction (admin/system only)."""
    wallet = await service.process_transaction(
        trip_id=trip_id,
        transaction_type=data.transaction_type,
        amount=data.amount,
        reference_id=data.reference_id,
        description=data.description,
        created_by=data.created_by or current_user.sub,
        category=data.category,
        tax_rate=data.tax_rate,
        is_taxable=data.is_taxable,
        is_reimbursable=data.is_reimbursable,
        has_receipt=data.has_receipt
    )
    await db.commit()
    return wallet


@router.post("/admin/{trip_id}/reconcile", response_model=TripWalletResponse)
async def reconcile_wallet(
    trip_id: UUID,
    data: ReconcileRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Reconcile a trip wallet (finance only)."""
    wallet = await service.reconcile_wallet(
        trip_id=trip_id,
        reconciled_by=current_user.sub,
        notes=data.notes,
        adjustments=data.adjustments,
    )
    await db.commit()
    return wallet


@router.post("/admin/{trip_id}/settle", response_model=TripWalletResponse)
async def settle_wallet(
    trip_id: UUID,
    data: SettleRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Final settlement of a trip wallet (finance only)."""
    wallet = await service.settle_wallet(
        trip_id=trip_id,
        settled_by=current_user.sub,
        payment_reference=data.payment_reference,
    )
    await db.commit()
    return wallet


@router.post("/admin/{trip_id}/update-budget", response_model=TripWalletResponse)
async def update_budget(
    trip_id: UUID,
    data: UpdateBudgetRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Update trip budget (admin only)."""
    wallet = await service.update_budget(
        trip_id=trip_id,
        new_budget=data.new_budget,
        reason=data.reason,
        updated_by=current_user.sub,
    )
    await db.commit()
    return wallet


@router.post("/admin/void-transaction/{transaction_id}")
async def void_transaction(
    transaction_id: UUID,
    data: VoidTransactionRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Void a transaction (admin only)."""
    reversal = await service.void_transaction(
        transaction_id=transaction_id,
        reason=data.reason,
        voided_by=current_user.sub,
    )
    await db.commit()
    return {"status": "voided", "reversal_id": str(reversal.id)}


@router.get("/admin/open-wallets", response_model=List[TripWalletResponse])
async def get_open_wallets(
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get all open (non-settled) wallets."""
    return await service.get_open_wallets()


@router.get("/admin/policy-violations")
async def get_policy_violations(
    user_id: Optional[UUID] = None,
    trip_id: Optional[UUID] = None,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get transactions with policy violations."""
    violations = await service.get_policy_violations(user_id=user_id, trip_id=trip_id)
    return [
        {
            "id": str(v.id),
            "wallet_id": str(v.wallet_id),
            "transaction_type": v.transaction_type,
            "amount": float(v.amount),
            "category": v.category,
            "compliance_flags": v.compliance_flags,
            "created_at": v.created_at.isoformat(),
        }
        for v in violations
    ]
