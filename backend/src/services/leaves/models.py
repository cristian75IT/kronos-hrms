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
    
    # Enterprise: Rejection reason (for audit)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Enterprise: Has interruptions (sickness, partial recall)
    has_interruptions: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    
    # Enterprise: Interruptions relationship
    interruptions: Mapped[list["LeaveInterruption"]] = relationship(
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


class LeaveInterruption(Base):
    """
    Records interruptions during an approved leave period.
    
    Use cases:
    - Sickness during vacation (Art. 6 D.Lgs 66/2003)
    - Partial recall for specific days
    - Emergency work during leave
    """
    
    __tablename__ = "leave_interruptions"
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
    
    # Interruption type
    interruption_type: Mapped[str] = mapped_column(
        String(30), 
        nullable=False
    )  # SICKNESS, PARTIAL_RECALL, EMERGENCY_WORK, OTHER
    
    # Interruption period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # OR specific days (for partial recall of non-contiguous days)
    specific_days: Mapped[Optional[list]] = mapped_column(JSONB)  # ["2026-01-05", "2026-01-08"]
    
    # Days refunded to balance
    days_refunded: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # For sickness: INPS protocol
    protocol_number: Mapped[Optional[str]] = mapped_column(String(50))
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Who initiated
    initiated_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    initiated_by_role: Mapped[str] = mapped_column(String(20), default="EMPLOYEE")  # EMPLOYEE, MANAGER, SYSTEM
    
    # Reason/notes
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, CANCELLED, COMPLETED
    
    # Wallet transaction reference
    refund_transaction_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationship
    leave_request: Mapped["LeaveRequest"] = relationship(back_populates="interruptions")




class ApprovalDelegation(Base):
    """
    Manages temporary delegation of approval authority.
    
    Use cases:
    - Manager on vacation delegates to backup
    - Out of office delegation
    - Role-based temporary handover
    """
    
    __tablename__ = "approval_delegations"
    __table_args__ = {"schema": "leaves"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Who is delegating
    delegator_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # Who receives delegation
    delegate_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # Delegation period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Type of delegation
    delegation_type: Mapped[str] = mapped_column(
        String(20), 
        default="FULL"
    )  # FULL (can approve/reject), READONLY (can view only)
    
    # Optional: limit to specific team or leave types
    scope_team_ids: Mapped[Optional[list]] = mapped_column(JSONB)  # List of team UUIDs
    scope_leave_types: Mapped[Optional[list]] = mapped_column(JSONB)  # List of leave type codes
    
    # Reason for delegation
    reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class BalanceReservation(Base):
    """
    Tracks balance reservations for pending leave requests.
    
    Workflow:
    1. Employee submits request → reservation created
    2. Manager approves → reservation confirmed (becomes deduction)
    3. Manager rejects → reservation cancelled
    
    Prevents double-booking of insufficient balance.
    """
    
    __tablename__ = "balance_reservations"
    __table_args__ = {"schema": "leaves"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Reference to leave request
    leave_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("leaves.leave_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # What is being reserved
    balance_type: Mapped[str] = mapped_column(String(30), nullable=False)  # vacation, rol, permits
    amount: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    
    # Breakdown for multi-bucket types (vacation_ap + vacation_ac)
    breakdown: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default="PENDING"
    )  # PENDING, CONFIRMED, CANCELLED, EXPIRED
    
    # Resolution
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Expiry for auto-cleanup of abandoned reservations
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# LeaveBalance and BalanceTransaction moved to specialized leaves_wallet microservice.

