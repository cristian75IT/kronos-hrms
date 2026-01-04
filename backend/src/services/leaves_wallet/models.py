"""KRONOS Wallet Service - SQLAlchemy Models."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class EmployeeWallet(Base):
    """Employee time wallet containing Vacation, ROL, and Permits balances."""
    
    __tablename__ = "employee_wallets"
    __table_args__ = {"schema": "time_wallet"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Vacation days (Ferie)
    vacation_previous_year: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # AP
    vacation_current_year: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)   # AC
    vacation_accrued: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)        # Maturate Year-to-Date
    vacation_used: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)           # Total Used
    vacation_used_ap: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)        # Used from AP
    vacation_used_ac: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)        # Used from AC
    
    # ROL hours (Permessi ROL)
    rol_previous_year: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_current_year: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_accrued: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_used: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    
    # Permits hours (Ex Festività)
    permits_total: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    permits_used: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    
    # Bank Hours (Banca Ore) - Future extension
    # bank_hours_total: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    
    # Metadata
    # Wellbeing & Compliance (EU Standards)
    legal_minimum_required: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=20) # e.g. 20 days/year
    legal_minimum_taken: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Financial Metadata (HR Liabilities)
    hourly_rate_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Metadata
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE") # ACTIVE, FROZEN, CLOSED
    ap_expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    last_accrual_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    @property
    def vacation_available_ap(self) -> Decimal:
        return self.vacation_previous_year - self.vacation_used_ap
    
    @property
    def vacation_available_ac(self) -> Decimal:
        return self.vacation_accrued - self.vacation_used_ac

    @property
    def vacation_available_total(self) -> Decimal:
        return self.vacation_available_ap + self.vacation_available_ac
    
    @property
    def rol_available(self) -> Decimal:
        return (self.rol_previous_year + self.rol_accrued) - self.rol_used
    
    @property
    def permits_available(self) -> Decimal:
        return self.permits_total - self.permits_used


class WalletTransaction(Base):
    """Audit log for all wallet movements (accruals, deductions, adjustments)."""
    
    __tablename__ = "wallet_transactions"
    __table_args__ = {"schema": "time_wallet"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    wallet_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("time_wallet.employee_wallets.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Reference to external request (e.g., LeaveRequest ID)
    reference_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Transaction type
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  
    # e.g., 'monthly_accrual', 'leave_deduction', 'leave_refund', 'manual_adjustment', 'rollover'
    
    # Balance bucket affected
    balance_type: Mapped[str] = mapped_column(String(50), nullable=False)  
    # e.g., 'vacation_ap', 'vacation_ac', 'rol', 'permits'
    
    # Amount (positive = add, negative = subtract)
    amount: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    
    # Financial impact (ISO 30414 mapping)
    monetary_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    exchange_rate_to_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    
    # Snapshot after transaction
    balance_after: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    
    # For FIFO tracking and expiration
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Codified Category for BI Reporting
    category: Mapped[Optional[str]] = mapped_column(String(30)) 
    # e.g., ACCRUAL, CONSUMPTION, EXPIRATION, REIMBURSEMENT, TRANSFER
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))  # User ID or System (None)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
