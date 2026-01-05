"""KRONOS Expense Service - SQLAlchemy Models."""
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
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.core.database import Base


class TripStatus(str, enum.Enum):
    """Business trip status."""
    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"  # Alias for pending, used by frontend
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ExpenseReportStatus(str, enum.Enum):
    """Expense report status."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PAID = "paid"


class DestinationType(str, enum.Enum):
    """Trip destination type for per-diem calculation."""
    NATIONAL = "national"
    EU = "eu"
    EXTRA_EU = "extra_eu"


class BusinessTrip(Base):
    """Business trip (Trasferta)."""
    
    __tablename__ = "business_trips"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_trip_dates"),
        {"schema": "expenses"},
    )
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Employee
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    # Trip details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    destination_type: Mapped[DestinationType] = mapped_column(
        SQLEnum(DestinationType, native_enum=False),
        default=DestinationType.NATIONAL,
    )
    
    # Period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Purpose
    purpose: Mapped[Optional[str]] = mapped_column(Text)
    project_code: Mapped[Optional[str]] = mapped_column(String(50))
    client_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Pre-approved budget
    estimated_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Status
    status: Mapped[TripStatus] = mapped_column(
        SQLEnum(TripStatus, native_enum=False),
        default=TripStatus.DRAFT,
    )
    
    # Approval
    approver_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approver_notes: Mapped[Optional[str]] = mapped_column(Text)
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    
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
    daily_allowances: Mapped[list["DailyAllowance"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    expense_reports: Mapped[list["ExpenseReport"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list["TripAttachment"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    
    @property
    def total_days(self) -> int:
        """Calculate total trip days."""
        return (self.end_date - self.start_date).days + 1


class DailyAllowance(Base):
    """Daily allowance (Diaria) for a trip day."""
    
    __tablename__ = "daily_allowances"
    __table_args__ = {"schema": "expenses"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    trip_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("expenses.business_trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Day
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Allowance
    is_full_day: Mapped[bool] = mapped_column(Boolean, default=True)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    
    # Deductions for provided meals
    breakfast_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    lunch_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    dinner_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    meals_deduction: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    
    # Final amount
    final_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationship
    trip: Mapped["BusinessTrip"] = relationship(back_populates="daily_allowances")


class ExpenseReport(Base):
    """Expense report (Nota Spese) for a trip."""
    
    __tablename__ = "expense_reports"
    __table_args__ = {"schema": "expenses"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    trip_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("expenses.business_trips.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_standalone: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    # Report info
    report_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Period covered
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Totals
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    
    # Status
    status: Mapped[ExpenseReportStatus] = mapped_column(
        SQLEnum(ExpenseReportStatus, native_enum=False),
        default=ExpenseReportStatus.DRAFT,
    )
    
    # Notes
    employee_notes: Mapped[Optional[str]] = mapped_column(Text)
    approver_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Approval
    approver_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Payment
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    
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
    trip: Mapped[Optional["BusinessTrip"]] = relationship(back_populates="expense_reports")
    items: Mapped[list["ExpenseItem"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list["ReportAttachment"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class ExpenseItem(Base):
    """Single expense item in a report."""
    
    __tablename__ = "expense_items"
    __table_args__ = {"schema": "expenses"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("expenses.expense_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Expense details
    expense_type_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    expense_type_code: Mapped[str] = mapped_column(String(10), nullable=False)  # Denormalized
    
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=1)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # For mileage reimbursement (AUT type)
    km_distance: Mapped[Optional[int]] = mapped_column(Integer)
    km_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    
    # Merchant
    merchant_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Receipt
    receipt_path: Mapped[Optional[str]] = mapped_column(String(500))
    receipt_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationship
    report: Mapped["ExpenseReport"] = relationship(back_populates="items")


class TripAttachment(Base):
    """Attachment for a business trip."""
    
    __tablename__ = "trip_attachments"
    __table_args__ = {"schema": "expenses"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    trip_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("expenses.business_trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationship
    trip: Mapped["BusinessTrip"] = relationship(back_populates="attachments")


class ReportAttachment(Base):
    """Attachment for an expense report."""
    
    __tablename__ = "report_attachments"
    __table_args__ = {"schema": "expenses"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("expenses.expense_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationship
    report: Mapped["ExpenseReport"] = relationship(back_populates="attachments")
