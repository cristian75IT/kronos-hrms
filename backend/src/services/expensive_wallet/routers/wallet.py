"""
KRONOS Trip Wallet Service - Enterprise Router

Endpoints:
- User/Employee: View wallet summary
- Internal: Budget reserve/confirm/cancel, policy check (for Expense Service)
- Admin/Finance: Reconciliation, settlement, void transactions
"""
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload
from ..service import TripWalletService
from ..schemas import TripWalletResponse, TransactionCreate, TripWalletTransactionResponse, WalletSummary

router = APIRouter()


def get_wallet_service(session: AsyncSession = Depends(get_db)) -> TripWalletService:
    return TripWalletService(session)


# ═══════════════════════════════════════════════════════════
# Request/Response Schemas for Enterprise Endpoints
# ═══════════════════════════════════════════════════════════

class BudgetReserveRequest(BaseModel):
    amount: Decimal
    reference_id: UUID
    category: Optional[str] = None
    description: Optional[str] = None


class PolicyCheckRequest(BaseModel):
    category: str
    amount: Decimal


class ReconcileRequest(BaseModel):
    notes: Optional[str] = None
    adjustments: Optional[List[Dict]] = None


class SettleRequest(BaseModel):
    payment_reference: Optional[str] = None


class UpdateBudgetRequest(BaseModel):
    new_budget: Decimal
    reason: str


class VoidTransactionRequest(BaseModel):
    reason: str


# ═══════════════════════════════════════════════════════════
# User/Employee Endpoints
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


@router.get("/{trip_id}/summary")
async def get_wallet_summary(
    trip_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Get comprehensive wallet summary."""
    summary = await service.get_wallet_summary(trip_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
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
        # Return empty list if wallet doesn't exist yet (no transactions)
        return []
    
    return await service.get_transactions(wallet.id, limit)


# ═══════════════════════════════════════════════════════════
# Internal API (for Expense Service)
# ═══════════════════════════════════════════════════════════

@router.post("/initialize/{trip_id}", response_model=TripWalletResponse)
async def initialize_wallet(
    trip_id: UUID,
    user_id: UUID,
    budget: float,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Initialize a wallet for a trip (budget allocation)."""
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
    try:
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
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/internal/{trip_id}/reserve")
async def reserve_budget(
    trip_id: UUID,
    data: BudgetReserveRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Reserve budget for a pending expense (internal API)."""
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
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a reserved expense (internal API)."""
    tx = await service.confirm_expense(trip_id, reference_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Reservation not found")
    await db.commit()
    return {"status": "confirmed", "transaction_id": str(tx.id)}


@router.post("/internal/{trip_id}/cancel/{reference_id}")
async def cancel_expense(
    trip_id: UUID,
    reference_id: UUID,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a reserved expense (internal API)."""
    success = await service.cancel_expense(trip_id, reference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")
    await db.commit()
    return {"status": "cancelled"}


@router.get("/internal/{trip_id}/check-budget")
async def check_budget_available(
    trip_id: UUID,
    amount: Decimal,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Check if budget is available for an expense (internal API)."""
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
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
):
    """Check if expense exceeds policy limits (internal API)."""
    result = await service.check_policy_limit(trip_id, data.category, data.amount)
    return result


# ═══════════════════════════════════════════════════════════
# Admin/Finance Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/admin/{trip_id}/reconcile", response_model=TripWalletResponse)
async def reconcile_wallet(
    trip_id: UUID,
    data: ReconcileRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Reconcile a trip wallet (finance only)."""
    try:
        wallet = await service.reconcile_wallet(
            trip_id=trip_id,
            reconciled_by=current_user.sub,
            notes=data.notes,
            adjustments=data.adjustments,
        )
        await db.commit()
        return wallet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/{trip_id}/settle", response_model=TripWalletResponse)
async def settle_wallet(
    trip_id: UUID,
    data: SettleRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Final settlement of a trip wallet (finance only)."""
    try:
        wallet = await service.settle_wallet(
            trip_id=trip_id,
            settled_by=current_user.sub,
            payment_reference=data.payment_reference,
        )
        await db.commit()
        return wallet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/{trip_id}/update-budget", response_model=TripWalletResponse)
async def update_budget(
    trip_id: UUID,
    data: UpdateBudgetRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Update trip budget (admin only)."""
    try:
        wallet = await service.update_budget(
            trip_id=trip_id,
            new_budget=data.new_budget,
            reason=data.reason,
            updated_by=current_user.sub,
        )
        await db.commit()
        return wallet
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/void-transaction/{transaction_id}")
async def void_transaction(
    transaction_id: UUID,
    data: VoidTransactionRequest,
    current_user: TokenPayload = Depends(require_permission("wallet:manage")),
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """Void a transaction (admin only)."""
    try:
        reversal = await service.void_transaction(
            transaction_id=transaction_id,
            reason=data.reason,
            voided_by=current_user.sub,
        )
        await db.commit()
        return {"status": "voided", "reversal_id": str(reversal.id)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


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

