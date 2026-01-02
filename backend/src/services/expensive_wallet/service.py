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
            total_taxable=Decimal(0),
            total_non_taxable=Decimal(0),
            status="OPEN",
            currency="EUR"
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
                               created_by: Optional[UUID] = None, category: Optional[str] = None,
                               tax_rate: Optional[Decimal] = None, is_taxable: bool = False,
                               has_receipt: bool = True, is_reimbursable: bool = True) -> TripWallet:
        """Process a movement in the wallet (Expense, Advance, Allocation)."""
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            # Maybe it should be created on demand if not exists?
            # For now we expect it to exist.
            raise ValueError(f"Wallet for trip {trip_id} not found")

        # Calculate tax if rate provided
        tax_amount = Decimal(0)
        if tax_rate and amount:
            tax_amount = (amount * tax_rate / (Decimal(100) + tax_rate)).quantize(Decimal("0.01"))

        # Create Transaction record
        tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type=transaction_type,
            amount=amount,
            category=category,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            is_taxable=is_taxable,
            is_reimbursable=is_reimbursable,
            has_receipt=has_receipt,
            reference_id=reference_id,
            description=description,
            created_by=created_by
        )
        self.session.add(tx)

        # Update Wallet Ledgers
        if transaction_type == "expense_approval":
            wallet.total_expenses += amount
            if is_taxable:
                wallet.total_taxable += amount
            else:
                wallet.total_non_taxable += amount
            
            # Policy audit
            if not has_receipt:
                wallet.policy_violations_count += 1
                tx.compliance_flags = "MISSING_RECEIPT"
                
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
