from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from ..service import TripWalletService
from ..schemas import TripWalletResponse, TransactionCreate, TripWalletTransactionResponse

router = APIRouter()

@router.get("/{trip_id}", response_model=TripWalletResponse)
async def get_wallet(trip_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get trip wallet status."""
    service = TripWalletService(db)
    wallet = await service.get_wallet(trip_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found for this trip"
        )
    return wallet

@router.post("/{trip_id}/transactions", response_model=TripWalletResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    trip_id: UUID, 
    data: TransactionCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Update wallet with a new transaction (advance, expense, etc.)."""
    service = TripWalletService(db)
    try:
        wallet = await service.process_transaction(
            trip_id=trip_id,
            transaction_type=data.transaction_type,
            amount=data.amount,
            reference_id=data.reference_id,
            description=data.description,
            created_by=data.created_by
        )
        await db.commit()
        return wallet
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/initialize/{trip_id}", response_model=TripWalletResponse)
async def initialize_wallet(
    trip_id: UUID,
    user_id: UUID,
    budget: float,
    db: AsyncSession = Depends(get_db)
):
    """Initialize a wallet for a trip (budget allocation)."""
    service = TripWalletService(db)
    from decimal import Decimal
    wallet = await service.create_wallet(trip_id, user_id, Decimal(str(budget)))
    await db.commit()
    return wallet
