"""
KRONOS - Time Ledger Models

Immutable ledger for time-based balance tracking (Vacation, ROL, Permits).
Following the double-entry bookkeeping pattern for enterprise audit compliance.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TimeLedgerEntryType:
    """Valid entry types for time ledger."""
    ACCRUAL = "ACCRUAL"              # Monthly accrual (maturazione)
    USAGE = "USAGE"                  # Time used (approvato)
    ADJUSTMENT_ADD = "ADJUSTMENT_ADD"  # Manual addition
    ADJUSTMENT_SUB = "ADJUSTMENT_SUB"  # Manual subtraction
    CARRY_OVER = "CARRY_OVER"        # Year-end carry over
    EXPIRED = "EXPIRED"              # Balance expiration


class TimeLedgerBalanceType:
    """Valid balance types."""
    VACATION_AP = "VACATION_AP"      # Ferie anno precedente
    VACATION_AC = "VACATION_AC"      # Ferie anno corrente
    ROL = "ROL"                       # Permessi ROL
    PERMITS = "PERMITS"              # Ex festività


class TimeLedgerReferenceType:
    """Valid reference types."""
    LEAVE_REQUEST = "LEAVE_REQUEST"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    ACCRUAL_JOB = "ACCRUAL_JOB"
    YEAR_END_JOB = "YEAR_END_JOB"
    EXPIRATION_JOB = "EXPIRATION_JOB"


class TimeLedgerEntry(Base):
    """
    Immutable ledger entry for time balances.
    
    Design principles:
    - Append-only: entries are NEVER updated or deleted
    - Balances are COMPUTED from entries, not stored
    - Full audit trail with reference to originating entity
    """
    
    __tablename__ = "time_ledger"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_time_ledger_amount_positive"),
        {"schema": "leaves"},
    )
    
    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Who
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # What type of movement
    entry_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    
    # What balance type
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    # How much (always positive, entry_type determines direction)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
    )
    
    # Immutable reference to causing entity
    reference_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    reference_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    reference_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    # Audit
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    def is_credit(self) -> bool:
        """Returns True if this entry adds to balance."""
        return self.entry_type in (
            TimeLedgerEntryType.ACCRUAL,
            TimeLedgerEntryType.ADJUSTMENT_ADD,
            TimeLedgerEntryType.CARRY_OVER,
        )
    
    def is_debit(self) -> bool:
        """Returns True if this entry subtracts from balance."""
        return self.entry_type in (
            TimeLedgerEntryType.USAGE,
            TimeLedgerEntryType.ADJUSTMENT_SUB,
            TimeLedgerEntryType.EXPIRED,
        )
    
    def signed_amount(self) -> Decimal:
        """Returns amount with sign based on entry type."""
        if self.is_credit():
            return self.amount
        elif self.is_debit():
            return -self.amount
        return Decimal(0)
