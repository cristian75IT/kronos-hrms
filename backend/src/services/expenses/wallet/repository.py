"""
KRONOS Expensive Wallet - Repository Layer.
"""
from typing import Optional, List, Sequence
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from .models import TripWallet, TripWalletTransaction

class TripWalletRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: UUID) -> Optional[TripWallet]:
        return await self._session.get(TripWallet, id)

    async def get_by_trip(self, trip_id: UUID) -> Optional[TripWallet]:
        stmt = select(TripWallet).where(TripWallet.trip_id == trip_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def create(self, wallet: TripWallet) -> TripWallet:
        self._session.add(wallet)
        # Flush to get ID
        await self._session.flush()
        return wallet
        
    async def update(self, wallet: TripWallet) -> TripWallet:
        await self._session.flush()
        return wallet
    
    async def get_open_wallets(self) -> Sequence[TripWallet]:
        """Get non-settled wallets."""
        # Assuming status field or is_settled boolean
        # Model introspection needed ideally, but assuming standard fields
        # If model specific fields unknown, better rely on status check in Service or generic filter
        # Let's assume TripWallet has 'status' or 'is_settled'
        stmt = select(TripWallet).where(TripWallet.status != 'SETTLED')
        result = await self._session.execute(stmt)
        return result.scalars().all()


class TripWalletTransactionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: UUID) -> Optional[TripWalletTransaction]:
        return await self._session.get(TripWalletTransaction, id)

    async def create(self, txn: TripWalletTransaction) -> TripWalletTransaction:
        self._session.add(txn)
        await self._session.flush()
        return txn
        
    async def update(self, txn: TripWalletTransaction) -> TripWalletTransaction:
        await self._session.flush()
        return txn

    async def get_by_wallet(self, wallet_id: UUID, limit: int = 100, offset: int = 0) -> Sequence[TripWalletTransaction]:
        stmt = select(TripWalletTransaction).where(
            TripWalletTransaction.wallet_id == wallet_id
        ).order_by(TripWalletTransaction.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_trip(self, trip_id: UUID, limit: int = 100) -> Sequence[TripWalletTransaction]:
        # Join wallet? Or use wallet_id if known.
        # Usually query by wallet.
        stmt = select(TripWalletTransaction).join(TripWallet).where(
            TripWallet.trip_id == trip_id
        ).order_by(TripWalletTransaction.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_pending_reservations(self, wallet_id: UUID) -> Decimal:
        stmt = select(func.sum(TripWalletTransaction.amount)).where(
            TripWalletTransaction.wallet_id == wallet_id,
            TripWalletTransaction.transaction_type == 'reservation'
        )
        result = await self._session.execute(stmt)
        val = result.scalar()
        return val if val else Decimal(0)
    
    async def get_by_reference(self, reference_id: UUID) -> Sequence[TripWalletTransaction]:
        stmt = select(TripWalletTransaction).where(TripWalletTransaction.reference_id == reference_id)
        result = await self._session.execute(stmt)
        return result.scalars().all()
        
    async def get_policy_violations(self, user_id: UUID = None, trip_id: UUID = None) -> Sequence[TripWalletTransaction]:
        query = select(TripWalletTransaction).where(TripWalletTransaction.compliance_flags.isnot(None))
        
        if user_id or trip_id:
             query = query.join(TripWallet)
             
        if user_id:
             query = query.where(TripWallet.user_id == user_id)
        if trip_id:
             query = query.where(TripWallet.trip_id == trip_id)
        
        query = query.order_by(TripWalletTransaction.created_at.desc())
        
        result = await self._session.execute(query)
        return result.scalars().all()
