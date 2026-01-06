"""
KRONOS - Wallet Router (Integrated in Leaves Service)

Endpoints:
- User: View own balance and transactions
- Admin: Adjustments, accruals, expirations
"""
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload
from src.services.leaves.wallet import WalletService, WalletResponse, WalletTransactionResponse, TransactionCreate

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
    
    # Need wallet_id to fetch transactions. 
    # The service method uses wallet_id.
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
# Admin Endpoints
# ═══════════════════════════════════════════════════════════

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


@router.get("/transactions/{wallet_id}", response_model=list[WalletTransactionResponse])
async def get_wallet_transactions_by_id(
    wallet_id: UUID,
    limit: int = Query(default=100, le=500),
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get transactions by wallet ID (admin or owner)."""
    service = WalletService(session)
    
    if not current_user.is_admin:
        # Check if wallet belongs to user
        owner_id = await service.get_wallet_owner(wallet_id)
        if owner_id != current_user.sub and "leaves:view" not in current_user.permissions:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return await service.get_transactions(wallet_id, limit)


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

# ═══════════════════════════════════════════════════════════
# Internal Endpoints (Backward Compatibility)
# ═══════════════════════════════════════════════════════════

@router.get("/internal/wallets/{user_id}", response_model=WalletResponse)
async def get_wallet_internal(
    user_id: UUID, 
    year: int = None,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Get wallet for a user."""
    return await service.get_wallet(user_id, year or datetime.now().year)


@router.get("/internal/wallets/{user_id}/summary")
async def get_balance_summary_internal(
    user_id: UUID,
    year: int = None,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Get balance summary."""
    return await service.get_balance_summary(user_id, year)


@router.get("/internal/check")
async def check_balance_internal(
    user_id: UUID,
    balance_type: str,
    amount: float,
    year: int = None,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Check if balance is sufficient."""
    sufficient, available = await service.check_balance_sufficient(user_id, balance_type, Decimal(str(amount)), year)
    return {"sufficient": sufficient, "available": float(available)}


@router.post("/internal/transactions", response_model=WalletTransactionResponse)
async def create_transaction_internal(
    transaction: TransactionCreate,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Create a transaction."""
    return await service.process_transaction(transaction)


@router.post("/internal/reserve")
async def reserve_balance_internal(
    user_id: UUID,
    balance_type: str,
    amount: float,
    reference_id: UUID,
    expiry_date: date = None,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Reserve balance."""
    return await service.reserve_balance(user_id, balance_type, Decimal(str(amount)), reference_id, expiry_date)


@router.post("/internal/confirm/{reference_id}")
async def confirm_reservation_internal(
    reference_id: UUID,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Confirm reservation."""
    success = await service.confirm_reservation(reference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"status": "confirmed"}


@router.post("/internal/cancel/{reference_id}")
async def cancel_reservation_internal(
    reference_id: UUID,
    service: WalletService = Depends(get_wallet_service),
):
    """Internal: Cancel reservation."""
    success = await service.cancel_reservation(reference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"status": "cancelled"}
