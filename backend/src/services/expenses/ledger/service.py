"""
KRONOS - Expense Ledger Service

Business logic for expense/trip financial operations.
Single source of truth for all expense calculations.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from src.shared.audit_client import get_audit_logger
from src.services.expenses.ledger.models import (
    ExpenseLedgerEntry,
    ExpenseLedgerEntryType,
    ExpenseLedgerCategory,
    ExpenseLedgerReferenceType,
)
from src.services.expenses.ledger.repository import ExpenseLedgerRepository


logger = logging.getLogger(__name__)


class TripFinancialSummary(BaseModel):
    """Financial summary for a trip."""
    trip_id: UUID
    total_budget: Decimal
    total_advances: Decimal
    total_expenses: Decimal
    total_reimbursed: Decimal
    remaining_budget: Decimal
    net_to_pay: Decimal
    by_category: dict[str, Decimal]
    
    class Config:
        json_encoders = {Decimal: float}


class ExpenseLedgerService:
    """
    Enterprise Expense Ledger Service.
    
    Responsibilities:
    - Track budget allocations
    - Record advances
    - Record approved expenses
    - Track reimbursements
    - Idempotent operations
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = ExpenseLedgerRepository(session)
        self._audit = get_audit_logger("expense-ledger")
    
    async def get_trip_summary(
        self,
        trip_id: UUID,
    ) -> TripFinancialSummary:
        """
        Get complete financial summary for a trip.
        
        Args:
            trip_id: Trip ID
        
        Returns:
            TripFinancialSummary with all financial data
        """
        summary = await self._repo.calculate_trip_summary(trip_id)
        categories = await self._repo.calculate_category_breakdown(trip_id)
        
        return TripFinancialSummary(
            trip_id=trip_id,
            total_budget=summary["total_budget"],
            total_advances=summary["total_advances"],
            total_expenses=summary["total_expenses"],
            total_reimbursed=summary["total_reimbursed"],
            remaining_budget=summary["remaining_budget"],
            net_to_pay=summary["net_to_pay"],
            by_category=categories,
        )
    
    async def record_budget_allocation(
        self,
        trip_id: UUID,
        user_id: UUID,
        amount: Decimal,
        actor_id: UUID,
        notes: Optional[str] = None,
    ) -> ExpenseLedgerEntry:
        """
        Record budget allocation when trip is approved.
        
        Idempotent: checks if already recorded.
        """
        # Idempotency check
        existing = await self._repo.get_by_reference(
            reference_type=ExpenseLedgerReferenceType.TRIP,
            reference_id=trip_id,
            entry_type=ExpenseLedgerEntryType.BUDGET_ALLOCATION,
        )
        if existing:
            logger.info(f"Budget already allocated for trip {trip_id}")
            return existing[0]
        
        entry = ExpenseLedgerEntry(
            user_id=user_id,
            trip_id=trip_id,
            entry_type=ExpenseLedgerEntryType.BUDGET_ALLOCATION,
            amount=amount,
            reference_type=ExpenseLedgerReferenceType.TRIP,
            reference_id=trip_id,
            reference_status="APPROVED",
            created_by=actor_id,
            description=notes or f"Budget allocation for trip {trip_id}",
        )
        await self._repo.create(entry)
        
        logger.info(f"Recorded BUDGET_ALLOCATION: trip={trip_id}, amount={amount}")
        
        await self._audit.log_action(
            user_id=actor_id,
            action="BUDGET_ALLOCATION",
            resource_type="TRIP",
            resource_id=str(trip_id),
            request_data={"amount": float(amount)},
        )
        
        return entry
    
    async def record_advance(
        self,
        trip_id: UUID,
        user_id: UUID,
        amount: Decimal,
        payment_id: UUID,
        actor_id: UUID,
        notes: Optional[str] = None,
    ) -> ExpenseLedgerEntry:
        """
        Record advance payment to employee.
        
        Idempotent: checks if already recorded for this payment.
        """
        # Idempotency check
        existing = await self._repo.get_by_reference(
            reference_type=ExpenseLedgerReferenceType.PAYMENT,
            reference_id=payment_id,
            entry_type=ExpenseLedgerEntryType.ADVANCE_PAYMENT,
        )
        if existing:
            logger.info(f"Advance already recorded for payment {payment_id}")
            return existing[0]
        
        entry = ExpenseLedgerEntry(
            user_id=user_id,
            trip_id=trip_id,
            entry_type=ExpenseLedgerEntryType.ADVANCE_PAYMENT,
            amount=amount,
            reference_type=ExpenseLedgerReferenceType.PAYMENT,
            reference_id=payment_id,
            reference_status="PAID",
            created_by=actor_id,
            description=notes or f"Advance payment for trip {trip_id}",
        )
        await self._repo.create(entry)
        
        logger.info(f"Recorded ADVANCE_PAYMENT: trip={trip_id}, amount={amount}")
        
        return entry
    
    async def record_expense_approval(
        self,
        trip_id: UUID,
        user_id: UUID,
        expense_item_id: UUID,
        amount: Decimal,
        category: str,
        actor_id: UUID,
        is_taxable: bool = False,
        vat_rate: Optional[Decimal] = None,
        vat_amount: Optional[Decimal] = None,
        is_reimbursable: bool = True,
        has_receipt: bool = True,
        description: Optional[str] = None,
    ) -> ExpenseLedgerEntry:
        """
        Record approved expense item.
        
        Idempotent: checks if already recorded.
        """
        # Idempotency check
        existing = await self._repo.get_by_reference(
            reference_type=ExpenseLedgerReferenceType.EXPENSE_ITEM,
            reference_id=expense_item_id,
            entry_type=ExpenseLedgerEntryType.EXPENSE_APPROVED,
        )
        if existing:
            logger.info(f"Expense already recorded for item {expense_item_id}")
            return existing[0]
        
        entry = ExpenseLedgerEntry(
            user_id=user_id,
            trip_id=trip_id,
            entry_type=ExpenseLedgerEntryType.EXPENSE_APPROVED,
            category=category,
            amount=amount,
            is_taxable=is_taxable,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            is_reimbursable=is_reimbursable,
            has_receipt=has_receipt,
            reference_type=ExpenseLedgerReferenceType.EXPENSE_ITEM,
            reference_id=expense_item_id,
            reference_status="APPROVED",
            created_by=actor_id,
            description=description,
        )
        await self._repo.create(entry)
        
        logger.info(
            f"Recorded EXPENSE_APPROVED: trip={trip_id}, item={expense_item_id}, "
            f"category={category}, amount={amount}"
        )
        
        return entry
    
    async def record_expense_report_approval(
        self,
        expense_report_id: UUID,
        trip_id: Optional[UUID],
        user_id: UUID,
        items: List[dict],
        actor_id: UUID,
    ) -> List[ExpenseLedgerEntry]:
        """
        Record all items when an expense report is approved.
        
        Args:
            expense_report_id: Expense report ID
            trip_id: Related trip ID (optional)
            user_id: Employee ID
            items: List of expense item dicts
            actor_id: Approver ID
        
        Returns:
            List of created ledger entries
        """
        entries = []
        
        # VISIBILITY: Warn if no items to process
        if not items:
            logger.warning(
                f"LEDGER_NO_ITEMS: Empty items list for expense_report={expense_report_id}. "
                f"No ledger entries will be created. This may indicate a sync issue."
            )
            return entries
        
        for item in items:
            entry = await self.record_expense_approval(
                trip_id=trip_id,
                user_id=user_id,
                expense_item_id=item["id"],
                amount=Decimal(str(item["amount"])),
                category=item.get("category", ExpenseLedgerCategory.OTHER),
                actor_id=actor_id,
                is_taxable=item.get("is_taxable", False),
                vat_rate=Decimal(str(item["vat_rate"])) if item.get("vat_rate") else None,
                vat_amount=Decimal(str(item["vat_amount"])) if item.get("vat_amount") else None,
                is_reimbursable=item.get("is_reimbursable", True),
                has_receipt=item.get("has_receipt", True),
                description=item.get("description"),
            )
            entries.append(entry)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="EXPENSE_REPORT_APPROVED",
            resource_type="EXPENSE_REPORT",
            resource_id=str(expense_report_id),
            request_data={"entries": [str(e.id) for e in entries]},
        )
        
        return entries
    
    async def record_reimbursement(
        self,
        trip_id: UUID,
        user_id: UUID,
        amount: Decimal,
        payment_id: UUID,
        actor_id: UUID,
        notes: Optional[str] = None,
    ) -> ExpenseLedgerEntry:
        """
        Record reimbursement payment to employee.
        
        Idempotent: checks if already recorded for this payment.
        """
        # Idempotency check
        existing = await self._repo.get_by_reference(
            reference_type=ExpenseLedgerReferenceType.PAYMENT,
            reference_id=payment_id,
            entry_type=ExpenseLedgerEntryType.REIMBURSEMENT,
        )
        if existing:
            logger.info(f"Reimbursement already recorded for payment {payment_id}")
            return existing[0]
        
        entry = ExpenseLedgerEntry(
            user_id=user_id,
            trip_id=trip_id,
            entry_type=ExpenseLedgerEntryType.REIMBURSEMENT,
            amount=amount,
            reference_type=ExpenseLedgerReferenceType.PAYMENT,
            reference_id=payment_id,
            reference_status="PAID",
            created_by=actor_id,
            description=notes or f"Reimbursement for trip {trip_id}",
        )
        await self._repo.create(entry)
        
        logger.info(f"Recorded REIMBURSEMENT: trip={trip_id}, amount={amount}")
        
        return entry
    
    async def reverse_expense(
        self,
        expense_item_id: UUID,
        actor_id: UUID,
        reason: str,
    ) -> Optional[ExpenseLedgerEntry]:
        """
        Reverse an approved expense (e.g., cancelled after approval).
        
        Creates EXPENSE_REJECTED entry (never deletes).
        """
        # Find original entry
        original = await self._repo.get_by_reference(
            reference_type=ExpenseLedgerReferenceType.EXPENSE_ITEM,
            reference_id=expense_item_id,
            entry_type=ExpenseLedgerEntryType.EXPENSE_APPROVED,
        )
        
        if not original:
            logger.warning(
                f"LEDGER_NO_ENTRY_TO_REVERSE: No expense entry found to reverse for expense_item={expense_item_id}. "
                f"This may indicate the expense was never properly approved."
            )
            return None
        
        orig = original[0]
        
        # Check for existing reversal
        existing_reversal = await self._repo.get_by_reference(
            reference_type=ExpenseLedgerReferenceType.EXPENSE_ITEM,
            reference_id=expense_item_id,
            entry_type=ExpenseLedgerEntryType.EXPENSE_REJECTED,
        )
        if existing_reversal:
            logger.info(f"Reversal already recorded for {expense_item_id}")
            return existing_reversal[0]
        
        reversal = ExpenseLedgerEntry(
            user_id=orig.user_id,
            trip_id=orig.trip_id,
            entry_type=ExpenseLedgerEntryType.EXPENSE_REJECTED,
            category=orig.category,
            amount=orig.amount,
            reference_type=ExpenseLedgerReferenceType.EXPENSE_ITEM,
            reference_id=expense_item_id,
            reference_status="REJECTED",
            created_by=actor_id,
            description=f"Reversal of {orig.id}: {reason}",
        )
        await self._repo.create(reversal)
        
        logger.info(f"Recorded EXPENSE_REJECTED: item={expense_item_id}, amount={orig.amount}")
        
        return reversal
    
    async def get_entries(
        self,
        trip_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[ExpenseLedgerEntry]:
        """Get ledger entries."""
        if trip_id:
            return await self._repo.get_entries_by_trip(trip_id, limit)
        elif user_id:
            return await self._repo.get_entries_by_user(user_id, limit=limit)
        return []
