from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.expensive_wallet.service import TripWalletService
from src.services.expensive_wallet.deps import get_wallet_service
from src.services.expensive_wallet.schemas import (
    TripWalletResponse,
    BudgetReserveRequest,
    PolicyCheckRequest
)

router = APIRouter()

@router.post("/internal/initialize/{trip_id}", response_model=TripWalletResponse)
async def internal_initialize_wallet(
    trip_id: UUID,
    user_id: UUID,
    budget: float,
    service: TripWalletService = Depends(get_wallet_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize a wallet for a trip (internal system only).
    
    Called by Expense Service when trip is approved.
    """
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
    """
    Reserve budget for a pending expense (internal system only).
    
    Called by Expense Service when expense item is added.
    """
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
    """
    Confirm a reserved expense when approved (internal system only).
    
    Called by Expense Service.
    """
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
    """
    Cancel a reserved expense when rejected (internal system only).
    
    Called by Expense Service.
    """
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
    """
    Check if budget is available for an expense (internal system only).
    
    Called by Expense Service for validation.
    """
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
    """
    Check if expense exceeds policy limits (internal system only).
    
    Called by Expense Service.
    """
    result = await service.check_policy_limit(trip_id, data.category, data.amount)
    return result
