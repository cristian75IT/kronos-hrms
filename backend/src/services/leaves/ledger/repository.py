"""
KRONOS - Time Ledger Repository

Data access layer for time ledger operations.
Follows the immutable ledger pattern - only INSERT operations.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.leaves.ledger.models import (
    TimeLedgerEntry,
    TimeLedgerEntryType,
)


logger = logging.getLogger(__name__)


class TimeLedgerRepository:
    """
    Repository for time ledger operations.
    
    Note: This repository ONLY supports INSERT operations.
    Ledger entries are IMMUTABLE once created.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, entry: TimeLedgerEntry) -> TimeLedgerEntry:
        """Insert a new ledger entry."""
        self._session.add(entry)
        await self._session.flush()
        return entry
    
    async def get_by_id(self, entry_id: UUID) -> Optional[TimeLedgerEntry]:
        """Get entry by ID (read-only)."""
        result = await self._session.execute(
            select(TimeLedgerEntry).where(TimeLedgerEntry.id == entry_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_reference(
        self,
        reference_type: str,
        reference_id: UUID,
        entry_type: Optional[str] = None,
    ) -> List[TimeLedgerEntry]:
        """Get entries by reference (for idempotency checks)."""
        query = select(TimeLedgerEntry).where(
            and_(
                TimeLedgerEntry.reference_type == reference_type,
                TimeLedgerEntry.reference_id == reference_id,
            )
        )
        if entry_type:
            query = query.where(TimeLedgerEntry.entry_type == entry_type)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_user(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        balance_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[TimeLedgerEntry]:
        """Get ledger entries for a user."""
        query = select(TimeLedgerEntry).where(
            TimeLedgerEntry.user_id == user_id
        )
        
        if year:
            query = query.where(TimeLedgerEntry.year == year)
        if balance_type:
            query = query.where(TimeLedgerEntry.balance_type == balance_type)
        
        query = query.order_by(TimeLedgerEntry.created_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def calculate_balance(
        self,
        user_id: UUID,
        year: int,
        balance_type: str,
    ) -> Decimal:
        """
        Calculate current balance from ledger entries.
        
        Returns: net balance (credits - debits)
        """
        # Credit entry types
        credit_types = [
            TimeLedgerEntryType.ACCRUAL,
            TimeLedgerEntryType.ADJUSTMENT_ADD,
            TimeLedgerEntryType.CARRY_OVER,
        ]
        
        # Debit entry types
        debit_types = [
            TimeLedgerEntryType.USAGE,
            TimeLedgerEntryType.ADJUSTMENT_SUB,
            TimeLedgerEntryType.EXPIRED,
        ]
        
        # Sum credits
        credits_query = select(func.coalesce(func.sum(TimeLedgerEntry.amount), 0)).where(
            and_(
                TimeLedgerEntry.user_id == user_id,
                TimeLedgerEntry.year == year,
                TimeLedgerEntry.balance_type == balance_type,
                TimeLedgerEntry.entry_type.in_(credit_types),
            )
        )
        credits_result = await self._session.execute(credits_query)
        total_credits = Decimal(str(credits_result.scalar() or 0))
        
        # Sum debits
        debits_query = select(func.coalesce(func.sum(TimeLedgerEntry.amount), 0)).where(
            and_(
                TimeLedgerEntry.user_id == user_id,
                TimeLedgerEntry.year == year,
                TimeLedgerEntry.balance_type == balance_type,
                TimeLedgerEntry.entry_type.in_(debit_types),
            )
        )
        debits_result = await self._session.execute(debits_query)
        total_debits = Decimal(str(debits_result.scalar() or 0))
        
        return total_credits - total_debits
    
    async def calculate_all_balances(
        self,
        user_id: UUID,
        year: int,
    ) -> dict[str, dict[str, Decimal]]:
        """
        Calculate all balances for a user/year.
        
        Returns: {balance_type: {credited, debited, balance}}
        """
        credit_types = [
            TimeLedgerEntryType.ACCRUAL,
            TimeLedgerEntryType.ADJUSTMENT_ADD,
            TimeLedgerEntryType.CARRY_OVER,
        ]
        
        debit_types = [
            TimeLedgerEntryType.USAGE,
            TimeLedgerEntryType.ADJUSTMENT_SUB,
            TimeLedgerEntryType.EXPIRED,
        ]
        
        # Query grouped by balance_type
        query = select(
            TimeLedgerEntry.balance_type,
            TimeLedgerEntry.entry_type,
            func.sum(TimeLedgerEntry.amount).label("total"),
        ).where(
            and_(
                TimeLedgerEntry.user_id == user_id,
                TimeLedgerEntry.year == year,
            )
        ).group_by(
            TimeLedgerEntry.balance_type,
            TimeLedgerEntry.entry_type,
        )
        
        result = await self._session.execute(query)
        rows = result.all()
        
        # Aggregate results
        balances: dict[str, dict[str, Decimal]] = {}
        
        for balance_type, entry_type, total in rows:
            if balance_type not in balances:
                balances[balance_type] = {
                    "credited": Decimal(0),
                    "debited": Decimal(0),
                    "balance": Decimal(0),
                }
            
            if entry_type in credit_types:
                balances[balance_type]["credited"] += Decimal(str(total or 0))
            elif entry_type in debit_types:
                balances[balance_type]["debited"] += Decimal(str(total or 0))
        
        # Calculate net balance
        for bt in balances:
            balances[bt]["balance"] = balances[bt]["credited"] - balances[bt]["debited"]
        
        return balances
