"""
KRONOS - Expense Ledger Models

Immutable ledger for expense/trip financial tracking.
Supports budget allocation, advances, expenses, and reimbursements.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ExpenseLedgerEntryType:
    """Valid entry types for expense ledger."""
    BUDGET_ALLOCATION = "BUDGET_ALLOCATION"      # Budget assegnato alla trasferta
    ADVANCE_PAYMENT = "ADVANCE_PAYMENT"          # Anticipo erogato
    EXPENSE_APPROVED = "EXPENSE_APPROVED"        # Spesa approvata
    EXPENSE_REJECTED = "EXPENSE_REJECTED"        # Spesa rifiutata (reversal)
    REIMBURSEMENT = "REIMBURSEMENT"              # Rimborso effettuato
    ADJUSTMENT_ADD = "ADJUSTMENT_ADD"            # Aggiustamento positivo
    ADJUSTMENT_SUB = "ADJUSTMENT_SUB"            # Aggiustamento negativo


class ExpenseLedgerCategory:
    """Expense categories."""
    TRANSPORT = "TRANSPORT"          # Trasporto (treno, aereo, auto)
    HOTEL = "HOTEL"                  # Alloggio
    MEALS = "MEALS"                  # Pasti
    PARKING = "PARKING"              # Parcheggio
    TOLL = "TOLL"                    # Pedaggi
    FUEL = "FUEL"                    # Carburante
    PER_DIEM = "PER_DIEM"            # Diaria
    OTHER = "OTHER"                  # Altro


class ExpenseLedgerReferenceType:
    """Valid reference types."""
    TRIP = "TRIP"
    EXPENSE_REPORT = "EXPENSE_REPORT"
    EXPENSE_ITEM = "EXPENSE_ITEM"
    PAYMENT = "PAYMENT"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"


class ExpenseLedgerEntry(Base):
    """
    Immutable ledger entry for expense tracking.
    
    Design principles:
    - Append-only: entries are NEVER updated or deleted
    - Balances are COMPUTED from entries, not stored
    - Full audit trail with reference to originating entity
    - Supports VAT/Tax tracking for compliance
    """
    
    __tablename__ = "expense_ledger"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_expense_ledger_amount_positive"),
        {"schema": "expenses"},
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
    
    # Related trip (nullable for standalone expenses)
    trip_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        index=True,
    )
    
    # What type of movement
    entry_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    
    # Category (for expenses)
    category: Mapped[Optional[str]] = mapped_column(String(30))
    
    # Amount (EUR, always positive)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    
    # Tax/VAT tracking
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    vat_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    
    # Compliance flags
    is_reimbursable: Mapped[bool] = mapped_column(Boolean, default=True)
    has_receipt: Mapped[bool] = mapped_column(Boolean, default=True)
    compliance_notes: Mapped[Optional[str]] = mapped_column(Text)
    
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
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    def is_inflow(self) -> bool:
        """Returns True if this entry represents money flowing TO the company."""
        return self.entry_type in (
            ExpenseLedgerEntryType.EXPENSE_REJECTED,
        )
    
    def is_outflow(self) -> bool:
        """Returns True if this entry represents money flowing FROM the company."""
        return self.entry_type in (
            ExpenseLedgerEntryType.BUDGET_ALLOCATION,
            ExpenseLedgerEntryType.ADVANCE_PAYMENT,
            ExpenseLedgerEntryType.EXPENSE_APPROVED,
            ExpenseLedgerEntryType.REIMBURSEMENT,
        )
    
    def signed_amount(self) -> Decimal:
        """Returns amount with sign based on entry type."""
        if self.is_outflow():
            return -self.amount
        return self.amount
