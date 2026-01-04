"""KRONOS Config Service - SQLAlchemy Models."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Numeric,
    UniqueConstraint,
    Float,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SystemConfig(Base):
    """System configuration key-value store.
    
    All business parameters must be stored here, not hardcoded.
    """
    
    __tablename__ = "system_config"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)  # string, integer, boolean, float, json
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class LeaveType(Base):
    """Leave type configuration.
    
    Defines all types of leave (Ferie, ROL, Malattia, etc.)
    with their business rules.
    """
    
    __tablename__ = "leave_types"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Balance behavior
    scales_balance: Mapped[bool] = mapped_column(Boolean, default=True)
    balance_type: Mapped[Optional[str]] = mapped_column(String(20))  # vacation, rol, permits
    
    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_attachment: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_protocol: Mapped[bool] = mapped_column(Boolean, default=False)  # For sickness (INPS)
    
    # Policy rules
    min_notice_days: Mapped[Optional[int]] = mapped_column(Integer)
    max_consecutive_days: Mapped[Optional[int]] = mapped_column(Integer)
    max_per_month: Mapped[Optional[int]] = mapped_column(Integer)
    allow_past_dates: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_half_day: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_negative_balance: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # UI configuration
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Holiday(Base):
    """Holiday calendar.
    
    Stores national, regional, and local holidays.
    Supports year-to-year confirmation mechanism.
    """
    
    __tablename__ = "holidays"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))  # NULL = not local
    is_national: Mapped[bool] = mapped_column(Boolean, default=True)
    is_regional: Mapped[bool] = mapped_column(Boolean, default=False)
    region_code: Mapped[Optional[str]] = mapped_column(String(10))  # SAR = Sardegna
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True)  # For year-to-year confirmation
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CompanyClosure(Base):
    """Company closure calendar.
    
    Stores company-wide closures (total or partial).
    Can affect all employees or specific departments.
    """
    
    __tablename__ = "company_closures"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Date range
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Closure type: total (entire company) or partial (specific departments)
    closure_type: Mapped[str] = mapped_column(String(20), nullable=False, default="total")  # total, partial
    
    # For partial closures, list of affected department codes
    affected_departments: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # For partial closures, list of affected location IDs
    affected_locations: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Whether employees are still paid (e.g., company holiday vs unpaid closure)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Whether this closure consumes employee leave balance
    consumes_leave_balance: Mapped[bool] = mapped_column(Boolean, default=False)
    leave_type_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))  # If consumes balance, which leave type
    
    # Year for filtering
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ExpenseType(Base):
    """Expense type configuration.
    
    Defines reimbursable expense categories.
    """
    
    __tablename__ = "expense_types"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))  # transport, lodging, meals, other
    max_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    requires_receipt: Mapped[bool] = mapped_column(Boolean, default=True)
    km_reimbursement_rate: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))  # For AUT type
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class DailyAllowanceRule(Base):
    """Daily allowance rules for business trips.
    
    Configures per-diem rates by destination type.
    """
    
    __tablename__ = "daily_allowance_rules"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    destination_type: Mapped[str] = mapped_column(String(20), nullable=False)  # national, eu, extra_eu
    full_day_amount: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    half_day_amount: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    threshold_hours: Mapped[int] = mapped_column(Integer, default=8)
    meals_deduction: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class PolicyRule(Base):
    """Policy rules for complex business logic.
    
    Stores condition-based rules evaluated at runtime.
    """
    
    __tablename__ = "policy_rules"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)  # leave_validation, approval_flow, notification
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ContractType(Base):
    """Employee Contract Type (e.g. Full Time, Part Time, Stage)."""
    
    __tablename__ = "contract_types"
    __table_args__ = {"schema": "config", "extend_existing": True}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200))
    
    is_part_time: Mapped[bool] = mapped_column(Boolean, default=False)
    part_time_percentage: Mapped[float] = mapped_column(Float, default=100.0)
    
    # Default parameters (fallback if not specified in CCNL version config)
    annual_vacation_days: Mapped[int] = mapped_column(Integer, default=26)
    annual_rol_hours: Mapped[int] = mapped_column(Integer, default=72)
    annual_permit_hours: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )



class CalculationMode(Base):
    """Defines flexible calculation logic for accruals."""
    
    __tablename__ = "calculation_modes"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # The algo identifier (mapped to code logic)
    function_name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Default parameters for this mode
    default_parameters: Mapped[dict] = mapped_column(JSONB, default={})
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class NationalContract(Base):
    """National Collective Labor Agreement (CCNL).
    
    Represents Italian CCNL contracts like Commercio, Metalmeccanico, etc.
    Each CCNL can have multiple versions with different parameters over time.
    """
    
    __tablename__ = "national_contracts"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(100))  # Settore economico
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)  # Link to official text
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    versions: Mapped[list["NationalContractVersion"]] = relationship(
        back_populates="national_contract",
        order_by="desc(NationalContractVersion.valid_from)",
        cascade="all, delete-orphan",
    )

    levels: Mapped[list["NationalContractLevel"]] = relationship(
        back_populates="national_contract",
        order_by="NationalContractLevel.sort_order",
        cascade="all, delete-orphan",
    )


class NationalContractVersion(Base):
    """Historical version of CCNL parameters.
    
    Each version contains all parameters valid from a specific date.
    This ensures historical calculations use the correct parameters.
    """
    
    __tablename__ = "national_contract_versions"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    national_contract_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.national_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Rinnovo 2024-2027"
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    
    # Working Hours Parameters
    weekly_hours_full_time: Mapped[float] = mapped_column(Numeric(4, 1), default=40.0)
    working_days_per_week: Mapped[int] = mapped_column(Integer, default=5)
    daily_hours: Mapped[float] = mapped_column(Numeric(4, 2), default=8.0)
    
    # Vacation Parameters (in working days per year)
    annual_vacation_days: Mapped[int] = mapped_column(Integer, default=26)
    vacation_accrual_method: Mapped[str] = mapped_column(String(20), default="monthly")
    vacation_carryover_months: Mapped[int] = mapped_column(Integer, default=18)
    vacation_carryover_deadline_month: Mapped[int] = mapped_column(Integer, default=6)
    vacation_carryover_deadline_day: Mapped[int] = mapped_column(Integer, default=30)
    
    # ROL Parameters (in hours per year)
    annual_rol_hours: Mapped[int] = mapped_column(Integer, default=72)
    rol_accrual_method: Mapped[str] = mapped_column(String(20), default="monthly")
    rol_carryover_months: Mapped[int] = mapped_column(Integer, default=24)
    
    # Ex-Festività (in hours per year, typically 32h = 4 days)
    annual_ex_festivita_hours: Mapped[int] = mapped_column(Integer, default=32)
    ex_festivita_accrual_method: Mapped[str] = mapped_column(String(20), default="yearly")

    # Calculation Modes (Dynamic)
    vacation_calc_mode_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.calculation_modes.id"),
        nullable=True
    )
    rol_calc_mode_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.calculation_modes.id"),
        nullable=True
    )
    
    # Parameter overrides for the selected mode
    vacation_calc_params: Mapped[Optional[dict]] = mapped_column(JSONB)
    rol_calc_params: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Relationships to Modes
    vacation_calc_mode: Mapped["CalculationMode"] = relationship(foreign_keys=[vacation_calc_mode_id])
    rol_calc_mode: Mapped["CalculationMode"] = relationship(foreign_keys=[rol_calc_mode_id])
    
    # Other Paid Leave
    annual_study_leave_hours: Mapped[Optional[int]] = mapped_column(Integer)
    blood_donation_paid_hours: Mapped[Optional[int]] = mapped_column(Integer)
    marriage_leave_days: Mapped[Optional[int]] = mapped_column(Integer)
    bereavement_leave_days: Mapped[Optional[int]] = mapped_column(Integer)
    l104_monthly_days: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Sick Leave Parameters
    sick_leave_carenza_days: Mapped[int] = mapped_column(Integer, default=3)
    sick_leave_max_days_year: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Seniority Bonuses (JSONB with progression rules)
    seniority_vacation_bonus: Mapped[Optional[dict]] = mapped_column(JSONB)
    seniority_rol_bonus: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
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
    contract_type_configs: Mapped[list["NationalContractTypeConfig"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
    )

    national_contract: Mapped["NationalContract"] = relationship(back_populates="versions")

class NationalContractLevel(Base):
    """Level of a National Contract (e.g. Livello 1, Quadro)."""
    
    __tablename__ = "national_contract_levels"
    __table_args__ = {"schema": "config"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    national_contract_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.national_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    national_contract: Mapped["NationalContract"] = relationship(back_populates="levels")


class NationalContractTypeConfig(Base):
    """Configuration of a Contract Type within a specific CCNL Version."""
    
    __tablename__ = "national_contract_type_configs"
    __table_args__ = (
        UniqueConstraint('national_contract_version_id', 'contract_type_id', name='uq_nc_version_contract_type'),
        {"schema": "config"}
    )
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    national_contract_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.national_contract_versions.id", ondelete="CASCADE"),
        nullable=False
    )
    contract_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.contract_types.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Specific Parameters (Overrides)
    weekly_hours: Mapped[float] = mapped_column(Float, nullable=False) # e.g. 40.0, 20.0
    annual_vacation_days: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_rol_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_ex_festivita_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Optional metadata
    description: Mapped[Optional[str]] = mapped_column(String(200)) # e.g. "Part Time Orizzontale al 50%"
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    version: Mapped["NationalContractVersion"] = relationship(back_populates="contract_type_configs")
    contract_type: Mapped["ContractType"] = relationship()  # Unidirectional is fine for now, or add backref if needed

