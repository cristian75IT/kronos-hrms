"""KRONOS Trip Wallet Service - Business Logic."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import TripWallet, TripWalletTransaction


class TripWalletService:
    """Service for managing Trip Wallets."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_wallet(self, trip_id: UUID) -> Optional[TripWallet]:
        """Get wallet for a trip."""
        stmt = (
            select(TripWallet)
            .where(TripWallet.trip_id == trip_id)
            .options(selectinload(TripWallet.transactions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_wallet(self, trip_id: UUID, user_id: UUID, budget: Decimal) -> TripWallet:
        """Initialize a new wallet for a trip."""
        wallet = await self.get_wallet(trip_id)
        if wallet:
            return wallet

        wallet = TripWallet(
            trip_id=trip_id,
            user_id=user_id,
            total_budget=budget,
            total_advances=Decimal(0),
            total_expenses=Decimal(0),
        )
        self.session.add(wallet)
        
        # Initial transaction
        tx = TripWalletTransaction(
            wallet=wallet,
            transaction_type="budget_allocation",
            amount=budget,
            description=f"Initial budget allocation for trip {trip_id}",
        )
        self.session.add(tx)
        
        await self.session.flush()
        return wallet

    async def process_transaction(self, trip_id: UUID, transaction_type: str, amount: Decimal, 
                               reference_id: Optional[UUID] = None, description: Optional[str] = None,
                               created_by: Optional[UUID] = None) -> TripWallet:
        """Process a movement in the wallet (Expense, Advance, Allocation)."""
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            # Maybe it should be created on demand if not exists?
            # For now we expect it to exist.
            raise ValueError(f"Wallet for trip {trip_id} not found")

        # Create Transaction record
        tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type=transaction_type,
            amount=amount,
            reference_id=reference_id,
            description=description,
            created_by=created_by
        )
        self.session.add(tx)

        # Update Wallet Ledgers
        if transaction_type == "expense_approval":
            wallet.total_expenses += amount
        elif transaction_type == "advance_payment":
            wallet.total_advances += amount
        elif transaction_type == "budget_allocation":
            wallet.total_budget += amount
        elif transaction_type == "refund":
            # Refund of an expense
            wallet.total_expenses -= amount
        
        await self.session.flush()
        return wallet

    async def get_transactions(self, wallet_id: UUID) -> List[TripWalletTransaction]:
        """Get all transactions for a wallet."""
        stmt = select(TripWalletTransaction).where(
            TripWalletTransaction.wallet_id == wallet_id
        ).order_by(TripWalletTransaction.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
