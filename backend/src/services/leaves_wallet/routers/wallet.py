"""
KRONOS Wallet Service - Enterprise Router

Endpoints:
- User: View own balance and transactions
- Internal: Reserve/Confirm/Cancel (for Leave Service)
- Admin: Adjustments, accruals, expirations
"""
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload
from ..service import WalletService
from ..models import EmployeeWallet
from ..schemas import WalletResponse, TransactionCreate, WalletTransactionResponse

router = APIRouter()


def get_wallet_service(session: AsyncSession = Depends(get_db)) -> WalletService:
    return WalletService(session)


# ═══════════════════════════════════════════════════════════
# User Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/{user_id}", response_model=WalletResponse)
async def get_user_wallet(
    user_id: UUID, 
    year: int = None,
    current_user: TokenPayload = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service),
):
    """Get wallet for a user (self or admin)."""
    if current_user.sub != user_id and not current_user.is_admin and "leaves:view" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized to view this wallet")
    
    wallet = await service.get_wallet(user_id, year or datetime.now().year)
    return wallet


@router.get("/{user_id}/summary")
async def get_balance_summary(
    user_id: UUID,
    year: int = None,
    current_user: TokenPayload = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service),
):
    """Get comprehensive balance summary."""
    if current_user.sub != user_id and not current_user.is_admin and "leaves:view" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_balance_summary(user_id, year)


@router.get("/{user_id}/transactions", response_model=list[WalletTransactionResponse])
async def get_user_transactions(
    user_id: UUID,
    year: int = None,
    limit: int = Query(default=100, le=500),
    current_user: TokenPayload = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service),
):
    """Get transactions for a user."""
    if current_user.sub != user_id and not current_user.is_admin and "leaves:view" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized to view these transactions")
    
    wallet = await service.get_wallet(user_id, year or datetime.now().year)
    return await service.get_transactions(wallet.id, limit)


@router.get("/{user_id}/available/{balance_type}")
async def get_available_balance(
    user_id: UUID,
    balance_type: str,
    year: int = None,
    exclude_reserved: bool = Query(default=True),
    current_user: TokenPayload = Depends(get_current_user),
    service: WalletService = Depends(get_wallet_service),
):
    """Get available balance for a specific type."""
    if current_user.sub != user_id and not current_user.is_admin and "leaves:view" not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    available = await service.get_available_balance(user_id, balance_type, year, exclude_reserved)
    return {"balance_type": balance_type, "available": float(available)}


# ═══════════════════════════════════════════════════════════
# Internal API (for Leave Service)
# ═══════════════════════════════════════════════════════════

@router.get("/internal/wallets/{user_id}", response_model=WalletResponse)
async def get_internal_wallet(
    user_id: UUID,
    year: int = None,
    service: WalletService = Depends(get_wallet_service),
):
    """Get user wallet (internal system only)."""
    return await service.get_wallet(user_id, year or datetime.now().year)


@router.get("/internal/wallets/{user_id}/summary")
async def get_internal_balance_summary(
    user_id: UUID, 
    year: int = None,
    service: WalletService = Depends(get_wallet_service),
):
    """Get balance summary (internal system only)."""
    return await service.get_balance_summary(user_id, year)


@router.post("/internal/transactions", response_model=WalletTransactionResponse)
async def create_internal_transaction(
    transaction: TransactionCreate,
    service: WalletService = Depends(get_wallet_service),
):
    """Create a wallet transaction (internal system only)."""
    # Note: In production, this should be protected by network policies or a shared secret.
    # Since specific user context is not available in background tasks, we allow this for internal use.
    return await service.process_transaction(transaction)


@router.post("/{user_id}/transactions", response_model=WalletTransactionResponse)
async def create_transaction(
    user_id: UUID,
    transaction: TransactionCreate,
    current_user: TokenPayload = Depends(require_permission("leaves:manage")),
    service: WalletService = Depends(get_wallet_service),
):
    """Create a wallet transaction (admin/system only)."""
    if transaction.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    transaction.created_by = current_user.sub
    return await service.process_transaction(transaction)





@router.post("/internal/reserve", response_model=WalletTransactionResponse)
async def reserve_balance(
    user_id: UUID,
    balance_type: str,
    amount: Decimal,
    reference_id: UUID,
    expiry_date: Optional[date] = None,
    service: WalletService = Depends(get_wallet_service),
):
    """
    Reserve balance for a pending leave request.
    
    Internal API called by Leave Service when request is submitted.
    """
    try:
        tx = await service.reserve_balance(user_id, balance_type, amount, reference_id, expiry_date)
        return tx
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/internal/confirm/{reference_id}")
async def confirm_reservation(
    reference_id: UUID,
    service: WalletService = Depends(get_wallet_service),
):
    """
    Confirm a reservation when leave is approved.
    
    Internal API called by Leave Service.
    """
    tx = await service.confirm_reservation(reference_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"status": "confirmed", "transaction_id": str(tx.id)}


@router.post("/internal/cancel/{reference_id}")
async def cancel_reservation(
    reference_id: UUID,
    service: WalletService = Depends(get_wallet_service),
):
    """
    Cancel a reservation when leave is rejected.
    
    Internal API called by Leave Service.
    """
    success = await service.cancel_reservation(reference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"status": "cancelled"}


@router.get("/internal/check")
async def check_balance_sufficient(
    user_id: UUID,
    balance_type: str,
    amount: Decimal,
    year: int = None,
    # current_user: TokenPayload = Depends(require_permission("leaves:manage")), # Removed for internal access
    service: WalletService = Depends(get_wallet_service),
):
    """
    Check if balance is sufficient for a request.
    
    Internal API for Leave Service validation.
    """
    is_sufficient, available = await service.check_balance_sufficient(user_id, balance_type, amount, year)
    return {
        "sufficient": is_sufficient,
        "available": float(available),
        "requested": float(amount),
    }


# ═══════════════════════════════════════════════════════════
# Admin Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/transactions/{wallet_id}", response_model=list[WalletTransactionResponse])
async def get_wallet_transactions(
    wallet_id: UUID,
    limit: int = Query(default=100, le=500),
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get transactions by wallet ID (admin or owner)."""
    service = WalletService(session)
    
    if not current_user.is_admin:
        # Check if wallet belongs to user
        stmt = select(EmployeeWallet.user_id).where(EmployeeWallet.id == wallet_id)
        res = await session.execute(stmt)
        owner_id = res.scalar_one_or_none()
        if owner_id != current_user.sub and "leaves:view" not in current_user.permissions:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_transactions(wallet_id, limit)


@router.post("/admin/process-expiration/{wallet_id}")
async def admin_process_expiration(
    wallet_id: UUID,
    balance_type: str,
    amount: Decimal,
    current_user: TokenPayload = Depends(require_permission("leaves:manage")),
    service: WalletService = Depends(get_wallet_service),
):
    """Process balance expiration (admin only)."""
    tx = await service.process_expiration(wallet_id, balance_type, amount)
    return {"status": "expired", "transaction_id": str(tx.id)}


@router.get("/admin/expiring-balances")
async def get_expiring_balances(
    expiry_date: date = Query(default=None),
    current_user: TokenPayload = Depends(require_permission("leaves:manage")),
    service: WalletService = Depends(get_wallet_service),
):
    """Get all balances expiring on or before a date."""
    if not expiry_date:
        expiry_date = date.today()
    
    transactions = await service.get_expiring_balances(expiry_date)
    return [
        {
            "wallet_id": str(tx.wallet_id),
            "balance_type": tx.balance_type,
            "remaining_amount": float(tx.remaining_amount),
            "expiry_date": tx.expiry_date.isoformat() if tx.expiry_date else None,
        }
        for tx in transactions
    ]


@router.get("/admin/wallets-for-accrual")
async def get_wallets_for_accrual(
    year: int = None,
    current_user: TokenPayload = Depends(require_permission("leaves:manage")),
    service: WalletService = Depends(get_wallet_service),
):
    """Get all wallets needing monthly accrual."""
    wallets = await service.get_wallets_for_accrual(year or datetime.now().year)
    return [{"wallet_id": str(w.id), "user_id": str(w.user_id)} for w in wallets]

