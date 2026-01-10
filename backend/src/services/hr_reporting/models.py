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


# ============================================================================
# Training and Safety Models (D.Lgs. 81/08 Compliance)
# ============================================================================

class TrainingType(str, enum.Enum):
    """Types of training per D.Lgs. 81/08."""
    GENERALE = "generale"              # Formazione generale (4h)
    SPECIFICA_BASSO = "specifica_basso"  # Rischio basso (4h)
    SPECIFICA_MEDIO = "specifica_medio"  # Rischio medio (8h)
    SPECIFICA_ALTO = "specifica_alto"    # Rischio alto (12h)
    ANTINCENDIO = "antincendio"         # Antincendio
    PRIMO_SOCCORSO = "primo_soccorso"   # Primo soccorso
    PREPOSTO = "preposto"               # Formazione preposti
    DIRIGENTE = "dirigente"             # Formazione dirigenti
    RLS = "rls"                         # Rappresentante lavoratori sicurezza
    RSPP = "rspp"                       # Responsabile SPP
    LAVORO_ALTEZZA = "lavoro_altezza"   # Lavori in quota
    CARRELLI = "carrelli"               # Carrelli elevatori
    PLE = "ple"                         # Piattaforme elevabili
    ELETTRICO = "elettrico"             # Rischio elettrico
    ALTRO = "altro"                     # Altra formazione


class TrainingStatus(str, enum.Enum):
    """Training record status."""
    VALIDO = "valido"
    IN_SCADENZA = "in_scadenza"   # Expiring within 60 days
    SCADUTO = "scaduto"
    PROGRAMMATO = "programmato"   # Scheduled but not completed


class TrainingRecord(Base):
    """
    Employee training record.
    
    Tracks all safety training per D.Lgs. 81/08 with expiration dates,
    certification documents, and renewal requirements.
    """
    __tablename__ = "training_records"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Employee reference
    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False, 
        index=True
    )
    
    # Training type and details
    training_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    training_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Training provider
    provider_name: Mapped[Optional[str]] = mapped_column(String(200))
    provider_code: Mapped[Optional[str]] = mapped_column(String(50))  # Ente accreditato
    
    # Dates
    training_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    hours: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="valido", index=True)
    
    # Certification
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100))
    certificate_path: Mapped[Optional[str]] = mapped_column(String(500))  # MinIO path
    
    # Audit info
    recorded_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
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


class MedicalVisitType(str, enum.Enum):
    """Types of medical visits (Sorveglianza sanitaria)."""
    PREVENTIVA = "preventiva"           # Visita preventiva
    PERIODICA = "periodica"             # Visita periodica
    STRAORDINARIA = "straordinaria"     # Visita straordinaria
    CAMBIO_MANSIONE = "cambio_mansione" # Cambio mansione
    FINE_RAPPORTO = "fine_rapporto"     # Cessazione rapporto


class MedicalFitnessType(str, enum.Enum):
    """Medical fitness judgements."""
    IDONEO = "idoneo"                   # Fully fit
    IDONEO_PARZIALE = "idoneo_parziale" # Partially fit with restrictions
    IDONEO_TEMPORANEO = "idoneo_temporaneo"  # Temporarily fit
    NON_IDONEO_TEMP = "non_idoneo_temp"      # Temporarily unfit
    NON_IDONEO_PERM = "non_idoneo_perm"      # Permanently unfit


class MedicalRecord(Base):
    """
    Employee medical visit record.
    
    Tracks sorveglianza sanitaria visits, fitness judgements, and 
    any work restrictions per D.Lgs. 81/08.
    """
    __tablename__ = "medical_records"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False, 
        index=True
    )
    
    # Visit details
    visit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_visit_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    
    # Fitness result
    fitness_result: Mapped[str] = mapped_column(String(50), nullable=False)
    restrictions: Mapped[Optional[str]] = mapped_column(Text)  # Prescrizioni/limitazioni
    
    # Doctor info
    doctor_name: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Document path
    document_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Audit
    recorded_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
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


class SafetyCompliance(Base):
    """
    Employee safety compliance overview.
    
    Aggregated compliance status per employee for D.Lgs. 81/08.
    Updated via background task periodically.
    """
    __tablename__ = "safety_compliance"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False, 
        unique=True,
        index=True
    )
    
    # Overall status
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    compliance_score: Mapped[int] = mapped_column(Integer, default=100)  # 0-100
    
    # Training status
    has_formazione_generale: Mapped[bool] = mapped_column(Boolean, default=False)
    has_formazione_specifica: Mapped[bool] = mapped_column(Boolean, default=False)
    trainings_expiring_soon: Mapped[int] = mapped_column(Integer, default=0)
    trainings_expired: Mapped[int] = mapped_column(Integer, default=0)
    
    # Medical status
    medical_fitness_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_next_visit: Mapped[Optional[date]] = mapped_column(Date)
    medical_restrictions: Mapped[Optional[str]] = mapped_column(Text)
    
    # Last check and issues
    last_check_date: Mapped[Optional[date]] = mapped_column(Date)
    issues: Mapped[Optional[dict]] = mapped_column(JSONB)  # List of compliance issues
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================================
# Monthly Timesheet Models
# ============================================================================

class TimesheetStatus(str, enum.Enum):
    """
    Status of the monthly timesheet.
    """
    DRAFT = "draft"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    APPROVED = "approved"
    REJECTED = "rejected"


class MonthlyTimesheet(Base):
    """
    Monthly attendance sheet (Giornaliero Presenze).
    
    Lists daily attendance/absence status for employee confirmation.
    """
    __tablename__ = "monthly_timesheets"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False, 
        index=True
    )
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status flow
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    
    # Detailed data (Daily list)
    days: Mapped[Optional[list[dict]]] = mapped_column(JSONB)
    
    # Summary data (Totals)
    summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Confirmation info
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    confirmed_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Approval info
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # User comments
    employee_notes: Mapped[Optional[str]] = mapped_column(Text)
    hr_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class HRReportingSettings(Base):
    """
    Global settings for HR Reporting service.
    """
    __tablename__ = "hr_reporting_settings"
    __table_args__ = {"schema": "hr_reporting"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Timesheet Configuration
    # Day of month for confirmation deadline
    timesheet_confirmation_day: Mapped[int] = mapped_column(Integer, default=27)
    
    # 0 = same month (e.g., 27th Jan for Jan timesheet)
    # 1 = next month (e.g., 5th Feb for Jan timesheet)
    timesheet_confirmation_month_offset: Mapped[int] = mapped_column(Integer, default=1)
    
    updated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
