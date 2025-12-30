"""KRONOS Config Service - Pydantic Schemas."""
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.shared.schemas import BaseSchema, TimestampMixin, IDMixin


# ═══════════════════════════════════════════════════════════
# System Config
# ═══════════════════════════════════════════════════════════

class SystemConfigBase(BaseModel):
    """Base schema for system config."""
    
    key: str = Field(..., max_length=100)
    value: Any
    value_type: str = Field(..., pattern="^(string|integer|boolean|float|json)$")
    category: str = Field(..., max_length=50)
    description: Optional[str] = None
    is_sensitive: bool = False


class SystemConfigCreate(SystemConfigBase):
    """Schema for creating system config."""
    pass


class SystemConfigUpdate(BaseModel):
    """Schema for updating system config."""
    
    value: Any
    description: Optional[str] = None


class SystemConfigResponse(SystemConfigBase, IDMixin, TimestampMixin, BaseSchema):
    """Response schema for system config."""
    pass


class ConfigValueResponse(BaseModel):
    """Simple key-value response."""
    
    key: str
    value: Any


# ═══════════════════════════════════════════════════════════
# Leave Types
# ═══════════════════════════════════════════════════════════

class LeaveTypeBase(BaseModel):
    """Base schema for leave type."""
    
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    
    # Balance behavior
    scales_balance: bool = True
    balance_type: Optional[str] = Field(None, pattern="^(vacation|rol|permits)$")
    
    # Approval workflow
    requires_approval: bool = True
    requires_attachment: bool = False
    requires_protocol: bool = False
    
    # Policy rules
    min_notice_days: Optional[int] = Field(None, ge=0)
    max_consecutive_days: Optional[int] = Field(None, ge=1)
    max_per_month: Optional[int] = Field(None, ge=1)
    allow_past_dates: bool = False
    allow_half_day: bool = True
    allow_negative_balance: bool = False
    
    # UI
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    sort_order: int = 0


class LeaveTypeCreate(LeaveTypeBase):
    """Schema for creating leave type."""
    pass


class LeaveTypeUpdate(BaseModel):
    """Schema for updating leave type."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    scales_balance: Optional[bool] = None
    balance_type: Optional[str] = None
    requires_approval: Optional[bool] = None
    requires_attachment: Optional[bool] = None
    min_notice_days: Optional[int] = None
    max_consecutive_days: Optional[int] = None
    max_per_month: Optional[int] = None
    allow_past_dates: Optional[bool] = None
    allow_half_day: Optional[bool] = None
    allow_negative_balance: Optional[bool] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(LeaveTypeBase, IDMixin, BaseSchema):
    """Response schema for leave type."""
    
    is_active: bool


class LeaveTypeListResponse(BaseModel):
    """List response for leave types."""
    
    items: list[LeaveTypeResponse]
    total: int


# ═══════════════════════════════════════════════════════════
# Holidays
# ═══════════════════════════════════════════════════════════

class HolidayBase(BaseModel):
    """Base schema for holiday."""
    
    date: date
    name: str = Field(..., max_length=100)
    location_id: Optional[UUID] = None
    is_national: bool = True


class HolidayCreate(HolidayBase):
    """Schema for creating holiday."""
    pass


class HolidayResponse(HolidayBase, IDMixin, BaseSchema):
    """Response schema for holiday."""
    
    year: int


class HolidayListResponse(BaseModel):
    """List response for holidays."""
    
    items: list[HolidayResponse]
    year: int
    total: int


class GenerateHolidaysRequest(BaseModel):
    """Request to generate holidays for a year."""
    
    year: int = Field(..., ge=2020, le=2100)
    include_local: bool = False
    location_id: Optional[UUID] = None


# ═══════════════════════════════════════════════════════════
# Expense Types
# ═══════════════════════════════════════════════════════════

class ExpenseTypeBase(BaseModel):
    """Base schema for expense type."""
    
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, pattern="^(transport|lodging|meals|other)$")
    max_amount: Optional[float] = Field(None, ge=0)
    requires_receipt: bool = True
    km_reimbursement_rate: Optional[float] = Field(None, ge=0)


class ExpenseTypeCreate(ExpenseTypeBase):
    """Schema for creating expense type."""
    pass


class ExpenseTypeResponse(ExpenseTypeBase, IDMixin, BaseSchema):
    """Response schema for expense type."""
    
    is_active: bool


# ═══════════════════════════════════════════════════════════
# Daily Allowance Rules
# ═══════════════════════════════════════════════════════════

class DailyAllowanceRuleBase(BaseModel):
    """Base schema for daily allowance rule."""
    
    name: str = Field(..., max_length=100)
    destination_type: str = Field(..., pattern="^(national|eu|extra_eu)$")
    full_day_amount: float = Field(..., ge=0)
    half_day_amount: float = Field(..., ge=0)
    threshold_hours: int = Field(default=8, ge=1, le=24)
    meals_deduction: float = Field(default=0, ge=0)


class DailyAllowanceRuleCreate(DailyAllowanceRuleBase):
    """Schema for creating daily allowance rule."""
    pass


class DailyAllowanceRuleResponse(DailyAllowanceRuleBase, IDMixin, BaseSchema):
    """Response schema for daily allowance rule."""
    
    is_active: bool
