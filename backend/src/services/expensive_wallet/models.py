"""KRONOS Trip Wallet Service - SQLAlchemy Models."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class TripWallet(Base):
    """Wallet associated with a Business Trip."""
    
    __tablename__ = "trip_wallets"
    __table_args__ = {"schema": "wallet"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Reference to original Trip ID in Expense Service
    trip_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # Financial Ledgers
    total_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_advances: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_taxable: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_non_taxable: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # HR Compliance & Localization
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    status: Mapped[str] = mapped_column(String(20), default="OPEN") # OPEN, SUBMITTED, SETTLED, AUDIT_PENDING
    policy_violations_count: Mapped[int] = mapped_column(Integer, default=0)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    transactions: Mapped[list["TripWalletTransaction"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    @property
    def current_balance(self) -> Decimal:
        """Remaining budget (Budget - Expenses)."""
        return self.total_budget - self.total_expenses

    @property
    def net_to_pay(self) -> Decimal:
        """Amount to be paid to employee (Expenses - Advances)."""
        return self.total_expenses - self.total_advances


class TripWalletTransaction(Base):
    """Individual movements in the Trip Wallet."""
    
    __tablename__ = "trip_wallet_transactions"
    __table_args__ = {"schema": "wallet"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    wallet_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("wallet.trip_wallets.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Transaction Info
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: 'budget_allocation', 'advance_payment', 'expense_approval', 'reimbursement_payment'
    
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Financial Standards (VAT/Taxation)
    category: Mapped[Optional[str]] = mapped_column(String(30)) # FOOD, HOTEL, TRANSPORT, OTHER
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    
    # HR Policy
    is_reimbursable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    has_receipt: Mapped[bool] = mapped_column(Boolean, default=True)
    compliance_flags: Mapped[Optional[str]] = mapped_column(Text) # JSON or Comma separated strings
    
    # Reference to external entities (e.g. ExpenseItem ID, Payment ID)
    reference_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationship
    wallet: Mapped["TripWallet"] = relationship(back_populates="transactions")
