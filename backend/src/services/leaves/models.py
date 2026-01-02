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
        SQLEnum(LeaveRequestStatus, native_enum=False),
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
    condition_type: Mapped[Optional[ConditionType]] = mapped_column(SQLEnum(ConditionType, native_enum=False))
    condition_details: Mapped[Optional[str]] = mapped_column(Text)
    condition_accepted: Mapped[Optional[bool]] = mapped_column(Boolean)
    condition_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Recall (for approved requests with RIC condition)
    recalled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    recall_reason: Mapped[Optional[str]] = mapped_column(Text)
    days_used_before_recall: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # Days actually used
    recall_date: Mapped[Optional[date]] = mapped_column(Date)  # Day of recall (first day back at work)

    
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
    from_status: Mapped[Optional[LeaveRequestStatus]] = mapped_column(SQLEnum(LeaveRequestStatus, native_enum=False))
    to_status: Mapped[LeaveRequestStatus] = mapped_column(SQLEnum(LeaveRequestStatus, native_enum=False), nullable=False)
    
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


# LeaveBalance and BalanceTransaction moved to specialized leaves_wallet microservice.
