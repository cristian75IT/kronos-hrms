"""
KRONOS - Time Ledger Service

Business logic for time balance operations.
Single source of truth for all balance calculations.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from src.shared.audit_client import get_audit_logger
from src.services.leaves.ledger.models import (
    TimeLedgerEntry,
    TimeLedgerEntryType,
    TimeLedgerBalanceType,
    TimeLedgerReferenceType,
)
from src.services.leaves.ledger.repository import TimeLedgerRepository


logger = logging.getLogger(__name__)


class BalanceResult(BaseModel):
    """Result of balance calculation."""
    balance_type: str
    year: int
    total_credited: Decimal
    total_debited: Decimal
    current_balance: Decimal
    pending_reservations: Decimal
    available: Decimal
    
    class Config:
        json_encoders = {Decimal: float}


class BalanceSummary(BaseModel):
    """Complete balance summary for a user."""
    user_id: UUID
    year: int
    vacation_ap: BalanceResult
    vacation_ac: BalanceResult
    rol: BalanceResult
    permits: BalanceResult
    total_vacation_available: Decimal
    
    class Config:
        json_encoders = {Decimal: float}


class TimeLedgerService:
    """
    Enterprise Time Ledger Service.
    
    Responsibilities:
    - Calculate balances from ledger entries
    - Record time usage on approval
    - Reverse usage on cancellation
    - Idempotent operations
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = TimeLedgerRepository(session)
        self._audit = get_audit_logger("time-ledger")
    
    async def get_balance(
        self,
        user_id: UUID,
        balance_type: str,
        year: Optional[int] = None,
        pending_requests_amount: Decimal = Decimal(0),
    ) -> BalanceResult:
        """
        Get balance for a specific type.
        
        Args:
            user_id: User ID
            balance_type: Type of balance (VACATION_AP, VACATION_AC, ROL, PERMITS)
            year: Year (defaults to current)
            pending_requests_amount: Amount from pending requests to subtract
        
        Returns:
            BalanceResult with credited, debited, current, pending, available
        """
        year = year or datetime.utcnow().year
        
        balances = await self._repo.calculate_all_balances(user_id, year)
        
        data = balances.get(balance_type, {
            "credited": Decimal(0),
            "debited": Decimal(0),
            "balance": Decimal(0),
        })
        
        return BalanceResult(
            balance_type=balance_type,
            year=year,
            total_credited=data["credited"],
            total_debited=data["debited"],
            current_balance=data["balance"],
            pending_reservations=pending_requests_amount,
            available=data["balance"] - pending_requests_amount,
        )
    
    async def get_balance_summary(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        pending_by_type: Optional[dict[str, Decimal]] = None,
    ) -> BalanceSummary:
        """
        Get complete balance summary for a user.
        
        Args:
            user_id: User ID
            year: Year (defaults to current)
            pending_by_type: Dict of pending amounts by balance type
        
        Returns:
            BalanceSummary with all balance types
        """
        year = year or datetime.utcnow().year
        pending = pending_by_type or {}
        
        balances = await self._repo.calculate_all_balances(user_id, year)
        
        def make_result(bt: str) -> BalanceResult:
            data = balances.get(bt, {"credited": Decimal(0), "debited": Decimal(0), "balance": Decimal(0)})
            pend = pending.get(bt, Decimal(0))
            return BalanceResult(
                balance_type=bt,
                year=year,
                total_credited=data["credited"],
                total_debited=data["debited"],
                current_balance=data["balance"],
                pending_reservations=pend,
                available=data["balance"] - pend,
            )
        
        vap = make_result(TimeLedgerBalanceType.VACATION_AP)
        vac = make_result(TimeLedgerBalanceType.VACATION_AC)
        rol = make_result(TimeLedgerBalanceType.ROL)
        permits = make_result(TimeLedgerBalanceType.PERMITS)
        
        return BalanceSummary(
            user_id=user_id,
            year=year,
            vacation_ap=vap,
            vacation_ac=vac,
            rol=rol,
            permits=permits,
            total_vacation_available=vap.available + vac.available,
        )
    
    async def record_usage(
        self,
        user_id: UUID,
        leave_request_id: UUID,
        breakdown: dict[str, Decimal],
        actor_id: UUID,
        notes: Optional[str] = None,
    ) -> List[TimeLedgerEntry]:
        """
        Record balance usage when leave is approved.
        
        Idempotent: checks if already recorded.
        
        Args:
            user_id: User whose balance is affected
            leave_request_id: ID of the approved leave request
            breakdown: Dict of {balance_type: amount}
            actor_id: User who approved
            notes: Optional notes
        
        Returns:
            List of created ledger entries
        """
        # Idempotency check
        existing = await self._repo.get_by_reference(
            reference_type=TimeLedgerReferenceType.LEAVE_REQUEST,
            reference_id=leave_request_id,
            entry_type=TimeLedgerEntryType.USAGE,
        )
        if existing:
            logger.info(f"Usage already recorded for leave request {leave_request_id}")
            return existing
        
        entries = []
        year = datetime.utcnow().year
        
        # VISIBILITY: Log if breakdown is empty (potential sync issue)
        if not breakdown:
            logger.warning(
                f"LEDGER_NO_BREAKDOWN: Empty breakdown for leave_request={leave_request_id}, user={user_id}. "
                f"No ledger entries will be created. This may indicate a policy or sync issue."
            )
            return entries
        
        for balance_type, amount in breakdown.items():
            if amount <= 0:
                continue
                
            entry = TimeLedgerEntry(
                user_id=user_id,
                year=year,
                entry_type=TimeLedgerEntryType.USAGE,
                balance_type=balance_type,
                amount=amount,
                reference_type=TimeLedgerReferenceType.LEAVE_REQUEST,
                reference_id=leave_request_id,
                reference_status="APPROVED",
                created_by=actor_id,
                notes=notes,
            )
            await self._repo.create(entry)
            entries.append(entry)
            
            logger.info(
                f"Recorded USAGE: user={user_id}, type={balance_type}, "
                f"amount={amount}, ref={leave_request_id}"
            )
        
        # VISIBILITY: Warn if all amounts were zero/negative
        if not entries and breakdown:
            logger.warning(
                f"LEDGER_ZERO_AMOUNTS: Breakdown had {len(breakdown)} items but no entries created "
                f"for leave_request={leave_request_id}. All amounts were <= 0: {breakdown}"
            )
        
        # Audit
        await self._audit.log_action(
            user_id=actor_id,
            action="BALANCE_DEDUCTION",
            resource_type="LEAVE_REQUEST",
            resource_id=str(leave_request_id),
            request_data={"entries": [str(e.id) for e in entries]},
        )
        
        return entries
    
    async def reverse_usage(
        self,
        user_id: UUID,
        leave_request_id: UUID,
        actor_id: UUID,
        reason: str,
    ) -> List[TimeLedgerEntry]:
        """
        Reverse usage when leave is cancelled after approval.
        
        Creates ADJUSTMENT_ADD entries (never deletes).
        
        Args:
            user_id: User whose balance is affected
            leave_request_id: ID of the cancelled leave request
            actor_id: User who cancelled
            reason: Reason for cancellation
        
        Returns:
            List of created reversal entries
        """
        # Find original usage entries
        original_entries = await self._repo.get_by_reference(
            reference_type=TimeLedgerReferenceType.LEAVE_REQUEST,
            reference_id=leave_request_id,
            entry_type=TimeLedgerEntryType.USAGE,
        )
        
        if not original_entries:
            logger.warning(
                f"LEDGER_NO_ENTRIES_TO_REVERSE: No usage entries found to reverse for leave_request={leave_request_id}. "
                f"This may indicate the leave was never properly approved or balance wasn't deducted."
            )
            return []
        
        # Check for existing reversals (idempotency)
        existing_reversals = await self._repo.get_by_reference(
            reference_type="LEAVE_CANCELLATION",
            reference_id=leave_request_id,
            entry_type=TimeLedgerEntryType.ADJUSTMENT_ADD,
        )
        if existing_reversals:
            logger.info(f"Reversal already recorded for {leave_request_id}")
            return existing_reversals
        
        reversal_entries = []
        
        for orig in original_entries:
            reversal = TimeLedgerEntry(
                user_id=user_id,
                year=orig.year,
                entry_type=TimeLedgerEntryType.ADJUSTMENT_ADD,
                balance_type=orig.balance_type,
                amount=orig.amount,
                reference_type="LEAVE_CANCELLATION",
                reference_id=leave_request_id,
                reference_status="CANCELLED",
                created_by=actor_id,
                notes=f"Reversal of {orig.id}: {reason}",
            )
            await self._repo.create(reversal)
            reversal_entries.append(reversal)
            
            logger.info(
                f"Recorded REVERSAL: user={user_id}, type={orig.balance_type}, "
                f"amount={orig.amount}, ref={leave_request_id}"
            )
        
        # Audit
        await self._audit.log_action(
            user_id=actor_id,
            action="BALANCE_REVERSAL",
            resource_type="LEAVE_REQUEST",
            resource_id=str(leave_request_id),
            request_data={"entries": [str(e.id) for e in reversal_entries]},
        )
        
        return reversal_entries
    
    async def record_accrual(
        self,
        user_id: UUID,
        balance_type: str,
        amount: Decimal,
        year: int,
        job_id: UUID,
        notes: Optional[str] = None,
    ) -> TimeLedgerEntry:
        """
        Record monthly accrual.
        
        Args:
            user_id: User ID
            balance_type: Type (VACATION_AC, ROL, etc.)
            amount: Amount to add
            year: Year
            job_id: Accrual job ID
            notes: Optional notes
        
        Returns:
            Created ledger entry
        """
        entry = TimeLedgerEntry(
            user_id=user_id,
            year=year,
            entry_type=TimeLedgerEntryType.ACCRUAL,
            balance_type=balance_type,
            amount=amount,
            reference_type=TimeLedgerReferenceType.ACCRUAL_JOB,
            reference_id=job_id,
            reference_status="COMPLETED",
            notes=notes,
        )
        await self._repo.create(entry)
        
        logger.info(
            f"Recorded ACCRUAL: user={user_id}, type={balance_type}, "
            f"amount={amount}, year={year}"
        )
        
        return entry
    
    async def record_carry_over(
        self,
        user_id: UUID,
        amount_ap: Decimal,
        year: int,
        job_id: UUID,
    ) -> TimeLedgerEntry:
        """
        Record year-end carry over to AP.
        
        Args:
            user_id: User ID
            amount_ap: Amount to carry over as AP
            year: Target year
            job_id: Year-end job ID
        
        Returns:
            Created ledger entry
        """
        entry = TimeLedgerEntry(
            user_id=user_id,
            year=year,
            entry_type=TimeLedgerEntryType.CARRY_OVER,
            balance_type=TimeLedgerBalanceType.VACATION_AP,
            amount=amount_ap,
            reference_type=TimeLedgerReferenceType.YEAR_END_JOB,
            reference_id=job_id,
            reference_status="COMPLETED",
            notes=f"Carry over from {year - 1}",
        )
        await self._repo.create(entry)
        
        logger.info(
            f"Recorded CARRY_OVER: user={user_id}, amount={amount_ap}, year={year}"
        )
        
        return entry
    
    async def get_entries(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        balance_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[TimeLedgerEntry]:
        """Get ledger entries for a user."""
        return await self._repo.get_entries_by_user(
            user_id=user_id,
            year=year,
            balance_type=balance_type,
            limit=limit,
        )
