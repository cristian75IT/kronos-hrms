"""
KRONOS Leaves Wallet - Repository Layer.
"""
from typing import Optional, List, Sequence
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from src.services.leaves_wallet.models import EmployeeWallet, WalletTransaction

class WalletRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: UUID) -> Optional[EmployeeWallet]:
        return await self._session.get(EmployeeWallet, id)

    async def get_by_user_year(self, user_id: UUID, year: int) -> Optional[EmployeeWallet]:
        stmt = select(EmployeeWallet).where(
            EmployeeWallet.user_id == user_id,
            EmployeeWallet.year == year
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_owner_id(self, wallet_id: UUID) -> Optional[UUID]:
        """Get the user_id that owns this wallet."""
        stmt = select(EmployeeWallet.user_id).where(EmployeeWallet.id == wallet_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def create(self, wallet: EmployeeWallet) -> EmployeeWallet:
        self._session.add(wallet)
        await self._session.flush()
        return wallet
        
    async def update(self, wallet: EmployeeWallet) -> EmployeeWallet:
        # Assuming object is attached to session and modified
        # Explicit update might not be needed if ORM tracking is used, 
        # but good for explicit intent or if dealing with detached objects.
        # Here we just flush.
        await self._session.flush()
        return wallet
    
    async def get_wallets_for_year(self, year: int) -> Sequence[EmployeeWallet]:
        stmt = select(EmployeeWallet).where(EmployeeWallet.year == year)
        result = await self._session.execute(stmt)
        return result.scalars().all()


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: UUID) -> Optional[WalletTransaction]:
        return await self._session.get(WalletTransaction, id)

    async def create(self, txn: WalletTransaction) -> WalletTransaction:
        self._session.add(txn)
        await self._session.flush()
        return txn

    async def get_by_wallet(self, wallet_id: UUID, limit: int = 100, offset: int = 0) -> Sequence[WalletTransaction]:
        stmt = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet_id
        ).order_by(WalletTransaction.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()
        
    async def get_pending_reservations(self, wallet_id: UUID, balance_type: str) -> Decimal:
        # NOTE: is_confirmed column was added to model but not migrated to DB yet
        # For now, return 0 as there's no active reservation system without the column
        # TODO: Run migration to add is_confirmed column, then restore filter
        return Decimal(0)

    
    async def get_by_reference(self, reference_id: UUID) -> Sequence[WalletTransaction]:
        stmt = select(WalletTransaction).where(WalletTransaction.reference_id == reference_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_available_buckets(self, wallet_id: UUID, balance_type: str) -> Sequence[WalletTransaction]:
        """Get positive transactions with remaining amount > 0 (FIFO candidates)."""
        stmt = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet_id,
            WalletTransaction.balance_type == balance_type,
            WalletTransaction.remaining_amount > 0,
            # Usually only ACCRUAL or MANUAL_ADD have remaining amount used for deductions
            # But let's rely on remaining_amount > 0
        ).order_by(WalletTransaction.created_at.asc()) # FIFO: Oldest first
        result = await self._session.execute(stmt)
        return result.scalars().all()
        
    async def get_expiring(self, expiry_date: date) -> Sequence[WalletTransaction]:
        stmt = select(WalletTransaction).where(
            WalletTransaction.expires_at <= expiry_date,
            WalletTransaction.remaining_amount > 0
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
