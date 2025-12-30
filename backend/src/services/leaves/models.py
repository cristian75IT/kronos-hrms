"""KRONOS Leave Service - SQLAlchemy Models."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.core.database import Base


class LeaveRequestStatus(str, enum.Enum):
    """Leave request status enum."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_CONDITIONAL = "approved_conditional"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RECALLED = "recalled"
    COMPLETED = "completed"


class ConditionType(str, enum.Enum):
    """Conditional approval type."""
    RIC = "ric"  # Riserva di Richiamo
    REP = "rep"  # Reperibilità
    PAR = "par"  # Approvazione Parziale
    MOD = "mod"  # Modifica Date
    ALT = "alt"  # Altra Condizione


class LeaveRequest(Base):
    """Leave request model."""
    
    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_dates"),
        {"schema": "leaves"},
    )
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Requester
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    # Leave type (from config service)
    leave_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    leave_type_code: Mapped[str] = mapped_column(String(10), nullable=False)  # Denormalized for perf
    
    # Period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Half-day options
    start_half_day: Mapped[bool] = mapped_column(Boolean, default=False)  # Only afternoon
    end_half_day: Mapped[bool] = mapped_column(Boolean, default=False)    # Only morning
    
    # Calculated days/hours
    days_requested: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    hours_requested: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    
    # Status and workflow
    status: Mapped[LeaveRequestStatus] = mapped_column(
        SQLEnum(LeaveRequestStatus),
        default=LeaveRequestStatus.DRAFT,
    )
    
    # Notes
    employee_notes: Mapped[Optional[str]] = mapped_column(Text)
    approver_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Approval
    approver_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Conditional approval
    has_conditions: Mapped[bool] = mapped_column(Boolean, default=False)
    condition_type: Mapped[Optional[ConditionType]] = mapped_column(SQLEnum(ConditionType))
    condition_details: Mapped[Optional[str]] = mapped_column(Text)
    condition_accepted: Mapped[Optional[bool]] = mapped_column(Boolean)
    condition_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Recall (for approved requests)
    recalled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    recall_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Sickness specific
    protocol_number: Mapped[Optional[str]] = mapped_column(String(50))  # INPS protocol
    
    # Attachment
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Balance consumption tracking
    balance_deducted: Mapped[bool] = mapped_column(Boolean, default=False)
    deduction_details: Mapped[Optional[dict]] = mapped_column(JSONB)  # AP/AC breakdown
    
    # Policy validation
    policy_violations: Mapped[Optional[dict]] = mapped_column(JSONB)  # Warning messages
    
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
    history: Mapped[list["LeaveRequestHistory"]] = relationship(
        back_populates="leave_request",
        cascade="all, delete-orphan",
    )


class LeaveRequestHistory(Base):
    """Leave request status history for audit trail."""
    
    __tablename__ = "leave_request_history"
    __table_args__ = {"schema": "leaves"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    leave_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("leaves.leave_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Status change
    from_status: Mapped[Optional[LeaveRequestStatus]] = mapped_column(SQLEnum(LeaveRequestStatus))
    to_status: Mapped[LeaveRequestStatus] = mapped_column(SQLEnum(LeaveRequestStatus), nullable=False)
    
    # Who and when
    changed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Details
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationship
    leave_request: Mapped["LeaveRequest"] = relationship(back_populates="history")


class LeaveBalance(Base):
    """User leave balance tracking."""
    
    __tablename__ = "leave_balances"
    __table_args__ = {"schema": "leaves"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Vacation days (Ferie)
    vacation_previous_year: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # AP
    vacation_current_year: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)   # AC
    vacation_accrued: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)        # Maturate AC
    vacation_used: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)           # Utilizzate totali
    vacation_used_ap: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)        # Usate da AP
    vacation_used_ac: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)        # Usate da AC
    
    # ROL hours
    rol_previous_year: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_current_year: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_accrued: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_used: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    
    # Permits hours (Ex Festività)
    permits_total: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    permits_used: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    
    # Metadata
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
        """Available vacation days from previous year."""
        return self.vacation_previous_year - self.vacation_used_ap
    
    @property
    def vacation_available_ac(self) -> Decimal:
        """Available vacation days from current year (accrued only)."""
        return self.vacation_accrued - self.vacation_used_ac
    
    @property
    def vacation_available_total(self) -> Decimal:
        """Total available vacation days."""
        return self.vacation_available_ap + self.vacation_available_ac
    
    @property
    def rol_available(self) -> Decimal:
        """Available ROL hours."""
        return (self.rol_previous_year + self.rol_accrued) - self.rol_used
    
    @property
    def permits_available(self) -> Decimal:
        """Available permit hours."""
        return self.permits_total - self.permits_used


class BalanceTransaction(Base):
    """Balance transaction log for audit."""
    
    __tablename__ = "balance_transactions"
    __table_args__ = {"schema": "leaves"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    balance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("leaves.leave_balances.id", ondelete="CASCADE"),
        nullable=False,
    )
    leave_request_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Transaction type
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # accrual, deduction, adjustment, carry_over
    
    # Balance affected
    balance_type: Mapped[str] = mapped_column(String(20), nullable=False)  # vacation_ap, vacation_ac, rol, permits
    
    # Amount (positive = add, negative = subtract)
    amount: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    
    # Balance after transaction
    balance_after: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    
    # Metadata
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
