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
    
    Stores national and local holidays.
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
    location_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))  # NULL = national
    is_national: Mapped[bool] = mapped_column(Boolean, default=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
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
