from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import get_current_user, TokenPayload
from src.services.expensive_wallet.service import TripWalletService
from src.services.expensive_wallet.deps import get_wallet_service
from src.services.expensive_wallet.schemas import (
    TripWalletResponse,
    TripWalletTransactionResponse,
    WalletSummary
)

router = APIRouter()

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
