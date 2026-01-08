"""KRONOS Config Service - Pydantic Schemas."""
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.shared.schemas import BaseSchema, TimestampMixin, IDMixin


# ═══════════════════════════════════════════════════════════
# System Config
# ═══════════════════════════════════════════════════════════

class SystemConfigBase(BaseModel):
    """Base schema for system config."""
    
    key: str = Field(..., max_length=100)
    value: Any
    value_type: str = Field(..., pattern="^(string|integer|boolean|float|decimal|json)$")
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
    balance_type: Optional[str] = None  # vacation, rol, permits, ex_festivita, vacation_ac, rol_hours, etc.
    
    # Approval workflow
    requires_approval: bool = True
    requires_attachment: bool = False
    requires_protocol: bool = False
    
    # Policy rules
    min_notice_days: Optional[int] = Field(None, ge=0)
    max_consecutive_days: Optional[int] = Field(None, ge=1)
    max_per_month: Optional[int] = Field(None, ge=1)
    max_single_request_days: Optional[int] = Field(None, ge=1)  # Max days per single request
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
    max_single_request_days: Optional[int] = None
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
    is_regional: bool = False
    region_code: Optional[str] = Field(None, max_length=10)


class HolidayCreate(HolidayBase):
    """Schema for creating holiday."""
    pass


class HolidayUpdate(BaseModel):
    """Schema for updating holiday."""
    
    name: Optional[str] = Field(None, max_length=100)
    is_national: Optional[bool] = None
    is_regional: Optional[bool] = None
    region_code: Optional[str] = Field(None, max_length=10)
    is_confirmed: Optional[bool] = None


class HolidayResponse(HolidayBase, IDMixin, BaseSchema):
    """Response schema for holiday."""
    
    year: int
    is_confirmed: bool = True


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
# Company Closures
# ═══════════════════════════════════════════════════════════

class CompanyClosureBase(BaseModel):
    """Base schema for company closure."""
    
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    start_date: date
    end_date: date
    closure_type: str = Field(default="total", pattern="^(total|partial)$")
    affected_departments: Optional[list[str]] = None
    affected_locations: Optional[list[UUID]] = None
    is_paid: bool = True
    consumes_leave_balance: bool = False
    leave_type_id: Optional[UUID] = None


class CompanyClosureCreate(CompanyClosureBase):
    """Schema for creating company closure."""
    pass


class CompanyClosureUpdate(BaseModel):
    """Schema for updating company closure."""
    
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    closure_type: Optional[str] = Field(None, pattern="^(total|partial)$")
    affected_departments: Optional[list[str]] = None
    affected_locations: Optional[list[UUID]] = None
    is_paid: Optional[bool] = None
    consumes_leave_balance: Optional[bool] = None
    leave_type_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class CompanyClosureResponse(CompanyClosureBase, IDMixin, BaseSchema):
    """Response schema for company closure."""
    
    year: int
    is_active: bool
    created_by: Optional[UUID] = None


class CompanyClosureListResponse(BaseModel):
    """List response for company closures."""
    
    items: list[CompanyClosureResponse]
    year: int
    total: int


# ═══════════════════════════════════════════════════════════
# Expense Types
# ═══════════════════════════════════════════════════════════

class ExpenseTypeBase(BaseModel):
    """Base schema for expense type."""
    
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, pattern="^(transport|accommodation|lodging|meals|communication|supplies|other)$")
    max_amount: Optional[float] = Field(None, ge=0)
    requires_receipt: bool = True
    km_reimbursement_rate: Optional[float] = Field(None, ge=0)


class ExpenseTypeCreate(ExpenseTypeBase):
    """Schema for creating expense type."""
    pass


class ExpenseTypeResponse(ExpenseTypeBase, IDMixin, BaseSchema):
    """Response schema for expense type."""
    
    is_active: bool
    is_taxable: bool = False
    sort_order: int = 0


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


# ═══════════════════════════════════════════════════════════
# National Contracts (CCNL)
# ═══════════════════════════════════════════════════════════

class NationalContractBase(BaseModel):
    """Base schema for National Contract (CCNL)."""
    
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    sector: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    source_url: Optional[str] = None


class NationalContractCreate(NationalContractBase):
    """Schema for creating National Contract."""
    pass


class NationalContractUpdate(BaseModel):
    """Schema for updating National Contract."""
    
    name: Optional[str] = Field(None, max_length=200)
    sector: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None



class NationalContractLevelBase(BaseModel):
    """Base schema for National Contract Level."""
    
    level_name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    sort_order: int = Field(default=0)


class NationalContractLevelCreate(NationalContractLevelBase):
    """Schema for creating National Contract Level."""
    
    national_contract_id: UUID


class NationalContractLevelUpdate(BaseModel):
    """Schema for updating National Contract Level."""
    
    level_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None


class NationalContractLevelResponse(NationalContractLevelBase, IDMixin, BaseSchema):
    """Response schema for National Contract Level."""
    
    national_contract_id: UUID
    created_at: datetime



class NationalContractTypeConfigBase(BaseModel):
    """Base schema for Contract Type Configuration."""
    
    contract_type_id: UUID
    weekly_hours: float
    annual_vacation_days: int
    annual_rol_hours: int
    annual_ex_festivita_hours: int
    description: Optional[str] = None


class NationalContractTypeConfigCreate(NationalContractTypeConfigBase):
    """Schema for creating Contract Type Configuration."""
    national_contract_version_id: UUID




class NationalContractTypeConfigUpdate(BaseModel):
    """Schema for updating Contract Type Configuration."""
    
    weekly_hours: Optional[float] = None
    annual_vacation_days: Optional[int] = None
    annual_rol_hours: Optional[int] = None
    annual_ex_festivita_hours: Optional[int] = None
    description: Optional[str] = None


class ContractTypeBase(BaseModel):
    """Base schema for Contract Type."""
    
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_part_time: bool = False
    part_time_percentage: float = 100.0


class ContractTypeCreate(ContractTypeBase):
    """Schema for creating Contract Type."""
    pass



class ContractTypeMinimalResponse(BaseModel):
    """Minimal schema for Contract Type."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    code: str


class ContractTypeResponse(ContractTypeMinimalResponse, IDMixin, TimestampMixin, BaseSchema):
    """Full response for Contract Type."""
    description: Optional[str] = None
    is_part_time: bool = False
    part_time_percentage: float = 100.0
    is_active: bool = True


# ═══════════════════════════════════════════════════════════
# Calculation Modes
# ═══════════════════════════════════════════════════════════

class CalculationModeBase(BaseModel):
    """Base schema for Calculation Mode."""
    
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    function_name: str = Field(..., max_length=50)
    default_parameters: Optional[dict] = Field(default_factory=dict)
    is_active: bool = True


class CalculationModeCreate(CalculationModeBase):
    """Schema for creating Calculation Mode."""
    pass


class CalculationModeUpdate(BaseModel):
    """Schema for updating Calculation Mode."""
    
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    default_parameters: Optional[dict] = None
    is_active: Optional[bool] = None


class CalculationModeResponse(CalculationModeBase, IDMixin, TimestampMixin, BaseSchema):
    """Response schema for Calculation Mode."""
    pass


class CalculationModeListResponse(BaseModel):
    """List response for Calculation Modes."""
    items: list[CalculationModeResponse]
    total: int



class NationalContractTypeConfigResponse(NationalContractTypeConfigBase, IDMixin, TimestampMixin, BaseSchema):
    """Response schema for Contract Type Configuration."""
    
    national_contract_version_id: UUID
    contract_type: ContractTypeMinimalResponse


class NationalContractVersionBase(BaseModel):
    """Base schema for CCNL Version parameters."""
    
    version_name: str = Field(..., max_length=100)
    valid_from: date
    valid_to: Optional[date] = None
    
    # Working Hours
    weekly_hours_full_time: float = Field(default=40.0, ge=20, le=50)
    working_days_per_week: int = Field(default=5, ge=4, le=7)
    daily_hours: float = Field(default=8.0, ge=4, le=12)
    
    # Vacation Parameters
    annual_vacation_days: int = Field(default=26, ge=0, le=50)
    vacation_accrual_method: str = Field(default="monthly", pattern="^(monthly|yearly)$")
    vacation_carryover_months: int = Field(default=18, ge=0, le=36)
    vacation_carryover_deadline_month: int = Field(default=6, ge=1, le=12)
    vacation_carryover_deadline_day: int = Field(default=30, ge=1, le=31)
    
    # ROL Parameters
    annual_rol_hours: int = Field(default=72, ge=0, le=200)
    rol_accrual_method: str = Field(default="monthly", pattern="^(monthly|yearly)$")
    rol_carryover_months: int = Field(default=24, ge=0, le=36)
    
    # Ex-Festività
    annual_ex_festivita_hours: int = Field(default=32, ge=0, le=100)
    ex_festivita_accrual_method: str = Field(default="yearly", pattern="^(monthly|yearly)$")
    
    # Other Leave
    annual_study_leave_hours: Optional[int] = Field(None, ge=0)
    blood_donation_paid_hours: Optional[int] = Field(None, ge=0)
    marriage_leave_days: Optional[int] = Field(None, ge=0)
    bereavement_leave_days: Optional[int] = Field(None, ge=0)
    l104_monthly_days: Optional[int] = Field(None, ge=0)
    
    # Sick Leave
    sick_leave_carenza_days: int = Field(default=3, ge=0, le=10)
    sick_leave_max_days_year: Optional[int] = Field(None, ge=0)
    
    # Seniority Bonuses (JSON)
    seniority_vacation_bonus: Optional[list[dict]] = None
    seniority_rol_bonus: Optional[list[dict]] = None
    
    # Calculation Modes (Dynamic)
    vacation_calc_mode_id: Optional[UUID] = None
    rol_calc_mode_id: Optional[UUID] = None
    vacation_calc_params: Optional[dict] = None
    rol_calc_params: Optional[dict] = None
    
    # Notes
    notes: Optional[str] = None


class NationalContractVersionCreate(NationalContractVersionBase):
    """Schema for creating CCNL Version."""
    
    national_contract_id: UUID


class NationalContractVersionUpdate(BaseModel):
    """Schema for updating CCNL Version."""
    
    version_name: Optional[str] = Field(None, max_length=100)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    
    weekly_hours_full_time: Optional[float] = Field(None, ge=20, le=50)
    working_days_per_week: Optional[int] = Field(None, ge=4, le=7)
    daily_hours: Optional[float] = Field(None, ge=4, le=12)
    
    annual_vacation_days: Optional[int] = Field(None, ge=0, le=50)
    vacation_accrual_method: Optional[str] = None
    vacation_carryover_months: Optional[int] = Field(None, ge=0, le=36)
    vacation_carryover_deadline_month: Optional[int] = Field(None, ge=1, le=12)
    vacation_carryover_deadline_day: Optional[int] = Field(None, ge=1, le=31)
    
    annual_rol_hours: Optional[int] = Field(None, ge=0, le=200)
    rol_accrual_method: Optional[str] = None
    rol_carryover_months: Optional[int] = Field(None, ge=0, le=36)
    
    annual_ex_festivita_hours: Optional[int] = Field(None, ge=0, le=100)
    ex_festivita_accrual_method: Optional[str] = None
    
    annual_study_leave_hours: Optional[int] = Field(None, ge=0)
    blood_donation_paid_hours: Optional[int] = Field(None, ge=0)
    marriage_leave_days: Optional[int] = Field(None, ge=0)
    bereavement_leave_days: Optional[int] = Field(None, ge=0)
    l104_monthly_days: Optional[int] = Field(None, ge=0)
    
    sick_leave_carenza_days: Optional[int] = Field(None, ge=0, le=10)
    sick_leave_max_days_year: Optional[int] = Field(None, ge=0)
    
    seniority_vacation_bonus: Optional[list[dict]] = None
    seniority_rol_bonus: Optional[list[dict]] = None
    
    vacation_calc_mode_id: Optional[UUID] = None
    rol_calc_mode_id: Optional[UUID] = None
    vacation_calc_params: Optional[dict] = None
    rol_calc_params: Optional[dict] = None
    
    notes: Optional[str] = None


class NationalContractVersionResponse(NationalContractVersionBase, IDMixin, TimestampMixin, BaseSchema):
    """Response schema for CCNL Version."""
    
    national_contract_id: UUID
    created_by: Optional[UUID] = None
    contract_type_configs: list[NationalContractTypeConfigResponse] = []
    
    vacation_calc_mode: Optional[CalculationModeResponse] = None
    rol_calc_mode: Optional[CalculationModeResponse] = None


class NationalContractResponse(NationalContractBase, IDMixin, TimestampMixin, BaseSchema):
    """Response schema for National Contract."""
    
    is_active: bool
    versions: list[NationalContractVersionResponse] = []
    levels: list[NationalContractLevelResponse] = []


class NationalContractListResponse(BaseModel):
    """List response for National Contracts."""
    
    items: list[NationalContractResponse]
    total: int



class NationalContractVersionListResponse(BaseModel):
    """List response for CCNL Versions."""
    
    items: list[NationalContractVersionResponse]
    total: int


# ═══════════════════════════════════════════════════════════
# Setup / Bulk Import Schemas
# ═══════════════════════════════════════════════════════════

class SetupContractTypeConfig(BaseModel):
    """Setup schema for Contract Type Config."""
    contract_type_code: str
    weekly_hours: float
    annual_vacation_days: int
    annual_rol_hours: int
    annual_ex_festivita_hours: int
    description: Optional[str] = None

class SetupContractVersion(BaseModel):
    """Setup schema for Contract Version."""
    version_name: str
    valid_from: date
    valid_to: date
    weekly_hours_full_time: float = 40.0
    working_days_per_week: int = 5
    daily_hours: float = 8.0
    count_saturday_as_leave: bool = False
    vacation_days: int = 26
    rol_hours: int = 72
    ex_festivita_hours: int = 32
    notes: Optional[str] = None
    
    # Calculation Modes
    vacation_calc_mode_code: Optional[str] = None
    rol_calc_mode_code: Optional[str] = None
    vacation_calc_params: Optional[dict] = None
    rol_calc_params: Optional[dict] = None
    
    # Nested configs for contract types
    types: list[SetupContractTypeConfig] = []

class SetupContractLevel(BaseModel):
    """Setup schema for Contract Level."""
    code: str
    name: str
    order: int
    description: Optional[str] = None

class SetupContract(BaseModel):
    """Setup schema for National Contract."""
    code: str
    name: str
    sector: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    
    levels: list[SetupContractLevel] = []
    versions: list[SetupContractVersion] = []

class SetupContractsPayload(BaseModel):
    """Payload for bulk contract setup."""
    contracts: list[SetupContract]

