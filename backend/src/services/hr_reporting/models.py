"""
KRONOS HR Reporting Service - SQLAlchemy Models.

Models for storing report snapshots, scheduled reports, and cached metrics.
"""
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
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.core.database import Base


class ReportType(str, enum.Enum):
    """Types of reports."""
    MONTHLY_ABSENCE = "monthly_absence"
    COMPLIANCE = "compliance"
    BUDGET = "budget"
    TEAM_SUMMARY = "team_summary"
    ANNUAL_SUMMARY = "annual_summary"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class GeneratedReport(Base):
    """
    Generated report record.
    
    Stores metadata and results of generated reports for caching
    and historical reference.
    """
    __tablename__ = "generated_reports"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Report type and period
    report_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Scope (optional department/team filter)
    department_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    team_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    
    # Report data (JSON)
    report_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    generated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # File exports
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    excel_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DailySnapshot(Base):
    """
    Daily workforce snapshot.
    
    Captures key metrics at end of each day for trend analysis
    and historical reporting.
    """
    __tablename__ = "daily_snapshots"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    
    # Workforce metrics
    total_employees: Mapped[int] = mapped_column(Integer, default=0)
    employees_on_leave: Mapped[int] = mapped_column(Integer, default=0)
    employees_on_trip: Mapped[int] = mapped_column(Integer, default=0)
    employees_sick: Mapped[int] = mapped_column(Integer, default=0)
    
    # Absence rates
    absence_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Leave metrics
    pending_leave_requests: Mapped[int] = mapped_column(Integer, default=0)
    approved_leave_today: Mapped[int] = mapped_column(Integer, default=0)
    
    # Expense metrics
    pending_expense_reports: Mapped[int] = mapped_column(Integer, default=0)
    total_expenses_submitted: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Detailed data
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class HRAlert(Base):
    """
    HR alerts and notifications.
    
    Tracks compliance issues, policy violations, and important events
    that require HR attention.
    """
    __tablename__ = "hr_alerts"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Alert type and severity
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    
    # Target (optional - can be org-wide)
    employee_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), index=True)
    department_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Alert details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    
    # Related entity
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Action required
    action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    action_deadline: Mapped[Optional[date]] = mapped_column(Date)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Extra data (previously 'metadata' - reserved by SQLAlchemy)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class EmployeeMonthlyStats(Base):
    """
    Monthly employee statistics snapshot.
    
    Pre-calculated monthly stats per employee for fast reporting
    and LUL export.
    """
    __tablename__ = "employee_monthly_stats"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    employee_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Leave metrics
    vacation_days_taken: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    vacation_hours_taken: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    rol_days_taken: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    rol_hours_taken: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    permit_hours_taken: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    sick_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    sick_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    other_absence_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    
    # Balance end of month
    vacation_balance_ap: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    vacation_balance_ac: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    rol_balance: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    permit_balance: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    
    # Expense metrics
    trips_count: Mapped[int] = mapped_column(Integer, default=0)
    trips_total_days: Mapped[int] = mapped_column(Integer, default=0)
    expenses_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    allowances_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Payroll codes (for LUL export)
    payroll_codes: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Full details
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
