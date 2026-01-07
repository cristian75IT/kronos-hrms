"""
KRONOS - Expense Ledger Repository

Data access layer for expense ledger operations.
Follows the immutable ledger pattern - only INSERT operations.
"""
import logging
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.expenses.ledger.models import (
    ExpenseLedgerEntry,
    ExpenseLedgerEntryType,
)


logger = logging.getLogger(__name__)


class ExpenseLedgerRepository:
    """
    Repository for expense ledger operations.
    
    Note: This repository ONLY supports INSERT operations.
    Ledger entries are IMMUTABLE once created.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, entry: ExpenseLedgerEntry) -> ExpenseLedgerEntry:
        """Insert a new ledger entry."""
        self._session.add(entry)
        await self._session.flush()
        return entry
    
    async def get_by_id(self, entry_id: UUID) -> Optional[ExpenseLedgerEntry]:
        """Get entry by ID (read-only)."""
        result = await self._session.execute(
            select(ExpenseLedgerEntry).where(ExpenseLedgerEntry.id == entry_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_reference(
        self,
        reference_type: str,
        reference_id: UUID,
        entry_type: Optional[str] = None,
    ) -> List[ExpenseLedgerEntry]:
        """Get entries by reference (for idempotency checks)."""
        query = select(ExpenseLedgerEntry).where(
            and_(
                ExpenseLedgerEntry.reference_type == reference_type,
                ExpenseLedgerEntry.reference_id == reference_id,
            )
        )
        if entry_type:
            query = query.where(ExpenseLedgerEntry.entry_type == entry_type)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_trip(
        self,
        trip_id: UUID,
        limit: int = 100,
    ) -> List[ExpenseLedgerEntry]:
        """Get all ledger entries for a trip."""
        query = select(ExpenseLedgerEntry).where(
            ExpenseLedgerEntry.trip_id == trip_id
        ).order_by(ExpenseLedgerEntry.created_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_entries_by_user(
        self,
        user_id: UUID,
        trip_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[ExpenseLedgerEntry]:
        """Get ledger entries for a user."""
        query = select(ExpenseLedgerEntry).where(
            ExpenseLedgerEntry.user_id == user_id
        )
        
        if trip_id:
            query = query.where(ExpenseLedgerEntry.trip_id == trip_id)
        
        query = query.order_by(ExpenseLedgerEntry.created_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def calculate_trip_summary(
        self,
        trip_id: UUID,
    ) -> dict[str, Decimal]:
        """
        Calculate financial summary for a trip.
        
        Returns: {
            total_budget, total_advances, total_expenses, 
            total_reimbursed, remaining_budget, net_to_pay
        }
        """
        # Entry types
        budget_types = [ExpenseLedgerEntryType.BUDGET_ALLOCATION]
        advance_types = [ExpenseLedgerEntryType.ADVANCE_PAYMENT]
        expense_types = [ExpenseLedgerEntryType.EXPENSE_APPROVED]
        reimbursement_types = [ExpenseLedgerEntryType.REIMBURSEMENT]
        
        async def sum_types(types: list[str]) -> Decimal:
            query = select(func.coalesce(func.sum(ExpenseLedgerEntry.amount), 0)).where(
                and_(
                    ExpenseLedgerEntry.trip_id == trip_id,
                    ExpenseLedgerEntry.entry_type.in_(types),
                )
            )
            result = await self._session.execute(query)
            return Decimal(str(result.scalar() or 0))
        
        total_budget = await sum_types(budget_types)
        total_advances = await sum_types(advance_types)
        total_expenses = await sum_types(expense_types)
        total_reimbursed = await sum_types(reimbursement_types)
        
        return {
            "total_budget": total_budget,
            "total_advances": total_advances,
            "total_expenses": total_expenses,
            "total_reimbursed": total_reimbursed,
            "remaining_budget": total_budget - total_expenses,
            "net_to_pay": total_expenses - total_advances - total_reimbursed,
        }
    
    async def calculate_category_breakdown(
        self,
        trip_id: UUID,
    ) -> dict[str, Decimal]:
        """Calculate expense breakdown by category."""
        query = select(
            ExpenseLedgerEntry.category,
            func.sum(ExpenseLedgerEntry.amount).label("total"),
        ).where(
            and_(
                ExpenseLedgerEntry.trip_id == trip_id,
                ExpenseLedgerEntry.entry_type == ExpenseLedgerEntryType.EXPENSE_APPROVED,
            )
        ).group_by(ExpenseLedgerEntry.category)
        
        result = await self._session.execute(query)
        rows = result.all()
        
        return {
            (cat or "OTHER"): Decimal(str(total or 0))
            for cat, total in rows
        }
    
    async def calculate_tax_summary(
        self,
        trip_id: UUID,
    ) -> dict[str, Decimal]:
        """Calculate tax/VAT summary for a trip."""
        query = select(
            func.coalesce(func.sum(ExpenseLedgerEntry.amount), 0).label("total"),
            func.coalesce(func.sum(ExpenseLedgerEntry.vat_amount), 0).label("total_vat"),
        ).where(
            and_(
                ExpenseLedgerEntry.trip_id == trip_id,
                ExpenseLedgerEntry.entry_type == ExpenseLedgerEntryType.EXPENSE_APPROVED,
            )
        )
        
        result = await self._session.execute(query)
        row = result.one()
        
        # Taxable vs non-taxable
        taxable_query = select(
            func.coalesce(func.sum(ExpenseLedgerEntry.amount), 0),
        ).where(
            and_(
                ExpenseLedgerEntry.trip_id == trip_id,
                ExpenseLedgerEntry.entry_type == ExpenseLedgerEntryType.EXPENSE_APPROVED,
                ExpenseLedgerEntry.is_taxable == True,
            )
        )
        taxable_result = await self._session.execute(taxable_query)
        total_taxable = Decimal(str(taxable_result.scalar() or 0))
        
        return {
            "total_expenses": Decimal(str(row.total or 0)),
            "total_vat": Decimal(str(row.total_vat or 0)),
            "total_taxable": total_taxable,
            "total_non_taxable": Decimal(str(row.total or 0)) - total_taxable,
        }
