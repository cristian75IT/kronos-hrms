"""KRONOS Leave Service - Pydantic Schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.shared.schemas import BaseSchema, IDMixin, DataTableRequest, DataTableResponse
from src.services.leaves.models import LeaveRequestStatus, ConditionType


# ═══════════════════════════════════════════════════════════
# Leave Request Schemas
# ═══════════════════════════════════════════════════════════

class LeaveRequestBase(BaseModel):
    """Base leave request schema."""
    
    leave_type_id: UUID
    start_date: date
    end_date: date
    start_half_day: bool = False
    end_half_day: bool = False
    employee_notes: Optional[str] = None
    
    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be >= start_date")
        return v


class LeaveRequestCreate(LeaveRequestBase):
    """Schema for creating leave request."""
    pass


class LeaveRequestUpdate(BaseModel):
    """Schema for updating leave request (draft only)."""
    
    leave_type_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_half_day: Optional[bool] = None
    end_half_day: Optional[bool] = None
    employee_notes: Optional[str] = None


class LeaveRequestResponse(LeaveRequestBase, IDMixin, BaseSchema):
    """Response schema for leave request."""
    
    user_id: UUID
    leave_type_code: str
    days_requested: Decimal
    hours_requested: Optional[Decimal] = None
    status: LeaveRequestStatus
    approver_notes: Optional[str] = None
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    has_conditions: bool
    condition_type: Optional[ConditionType] = None
    condition_details: Optional[str] = None
    condition_accepted: Optional[bool] = None
    protocol_number: Optional[str] = None
    attachment_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LeaveRequestListItem(BaseModel):
    """Simplified request for lists."""
    
    id: UUID
    user_id: UUID
    user_name: Optional[str] = None  # Full name of the requester
    leave_type_code: str
    start_date: date
    end_date: date
    days_requested: Decimal
    status: LeaveRequestStatus
    has_conditions: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LeaveRequestDataTableResponse(DataTableResponse[LeaveRequestListItem]):
    """DataTable response for leave requests."""
    pass


# ═══════════════════════════════════════════════════════════
# Workflow Actions
# ═══════════════════════════════════════════════════════════

class SubmitRequest(BaseModel):
    """Schema for submitting a draft request."""
    pass


class ApproveRequest(BaseModel):
    """Schema for approving a request."""
    
    notes: Optional[str] = None


class ApproveConditionalRequest(BaseModel):
    """Schema for conditional approval."""
    
    condition_type: ConditionType
    condition_details: str
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    """Schema for rejecting a request."""
    
    reason: str = Field(..., min_length=10)


class AcceptConditionRequest(BaseModel):
    """Schema for employee accepting conditions."""
    
    accept: bool


class CancelRequest(BaseModel):
    """Schema for cancelling own request."""
    
    reason: Optional[str] = None



class RecallRequest(BaseModel):
    """Schema for recalling an approved request during leave (richiamo in servizio)."""
    
    reason: str = Field(..., min_length=10, description="Reason for recall (justified business need)")
    recall_date: date = Field(..., description="Date when employee returns to work")


class DaysCalculationRequest(BaseModel):
    """Request to calculate working days."""
    
    start_date: date
    end_date: date
    start_half_day: bool = False
    end_half_day: bool = False
    leave_type_id: Optional[UUID] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be >= start_date")
        return v


class DaysCalculationResponse(BaseModel):
    """Response for days calculation."""
    
    days: Decimal
    hours: Decimal
    message: Optional[str] = None



# ═══════════════════════════════════════════════════════════
# Leave Balance Schemas
# ═══════════════════════════════════════════════════════════

class LeaveBalanceResponse(BaseModel):
    """Response schema for leave balance."""
    
    id: UUID
    user_id: UUID
    year: int
    
    # Vacation
    vacation_previous_year: Decimal
    vacation_current_year: Decimal
    vacation_accrued: Decimal
    vacation_used: Decimal
    vacation_available_ap: Decimal
    vacation_available_ac: Decimal
    vacation_available_total: Decimal
    
    # ROL
    rol_previous_year: Decimal
    rol_current_year: Decimal
    rol_accrued: Decimal
    rol_used: Decimal
    rol_available: Decimal
    
    # Permits
    permits_total: Decimal
    permits_used: Decimal
    permits_available: Decimal
    
    last_accrual_date: Optional[date] = None
    
    model_config = {"from_attributes": True}


class BalanceSummary(BaseModel):
    """Summary of user balances for dashboard."""
    
    vacation_total_available: Decimal
    vacation_available_ap: Decimal
    vacation_available_ac: Decimal
    vacation_used: Decimal
    vacation_pending: Decimal  # Requested but not yet approved
    
    ap_expiry_date: Optional[date] = None
    days_until_ap_expiry: Optional[int] = None
    
    rol_available: Decimal
    rol_used: Decimal
    rol_pending: Decimal
    
    permits_available: Decimal
    permits_used: Decimal
    permits_pending: Decimal

    # Deductions from mandatory company closures
    vacation_mandatory_deductions: Decimal = Decimal(0)
    rol_mandatory_deductions: Decimal = Decimal(0)
    permits_mandatory_deductions: Decimal = Decimal(0)


class BalanceAdjustment(BaseModel):
    """Schema for manual balance adjustment (admin only)."""
    
    balance_type: str = Field(..., pattern="^(vacation_ap|vacation_ac|rol|permits)$")
    amount: Decimal
    reason: str = Field(..., min_length=10)
    expiry_date: Optional[date] = None


class AccrualRequest(BaseModel):
    """Request to run accrual for a period."""
    
    year: int
    month: int = Field(..., ge=1, le=12)
    user_id: Optional[UUID] = None  # None = all users


class ExcludedDay(BaseModel):
    """A single excluded day."""
    
    date: date
    reason: str  # "weekend", "holiday", "closure"
    name: Optional[str] = None  # Holiday/closure name


class ExcludedDaysResponse(BaseModel):
    """Response with excluded days detail."""
    
    start_date: date
    end_date: date
    working_days: int
    excluded_days: list[ExcludedDay]

# ═══════════════════════════════════════════════════════════
# Calendar Schemas
# ═══════════════════════════════════════════════════════════

class CalendarEvent(BaseModel):
    """Event for FullCalendar."""
    
    id: str
    title: str
    start: date
    end: date
    allDay: bool = True
    color: str
    extendedProps: dict = {}


class CalendarRequest(BaseModel):
    """Request for calendar data."""
    
    start_date: date
    end_date: date
    user_id: Optional[UUID] = None  # None = current user or team for managers
    include_holidays: bool = True
    include_team: bool = False  # For managers


class CalendarResponse(BaseModel):
    """Response with calendar events."""
    
    events: list[CalendarEvent]
    holidays: list[CalendarEvent] = []
    closures: list[CalendarEvent] = []


# ═══════════════════════════════════════════════════════════
# Policy Validation
# ═══════════════════════════════════════════════════════════

class PolicyValidationResult(BaseModel):
    """Result of policy validation."""
    
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    requires_approval: bool = True
    balance_sufficient: bool = True
    balance_breakdown: dict = {}  # AP/AC breakdown for deduction


# ═══════════════════════════════════════════════════════════
# Preview Schemas for Admin Operations
# ═══════════════════════════════════════════════════════════

class EmployeePreviewItem(BaseModel):
    """Preview item for a single employee."""
    
    user_id: UUID
    name: str
    current_vacation: float = 0
    new_vacation: float = 0
    current_rol: float = 0
    new_rol: float = 0
    current_permits: float = 0
    new_permits: float = 0


class RecalculatePreviewResponse(BaseModel):
    """Response for recalculate preview."""
    
    year: int
    employees: list[EmployeePreviewItem]
    total_count: int


class RolloverPreviewResponse(BaseModel):
    """Response for rollover preview."""
    
    from_year: int
    to_year: int
    employees: list[EmployeePreviewItem]
    total_count: int


class ApplyChangesRequest(BaseModel):
    """Request to apply changes to selected employees."""
    
    user_ids: list[UUID]


# ═══════════════════════════════════════════════════════════
# Daily Attendance (HR)
# ═══════════════════════════════════════════════════════════

class DailyAttendanceRequest(BaseModel):
    """Request for daily attendance report."""
    date: date
    department: Optional[str] = None


class DailyAttendanceItem(BaseModel):
    """Attendance status for a single user."""
    user_id: UUID
    full_name: str
    status: str  # "Presente", "Assente (Ferie)", "Assente (Malattia)", "Permesso (1h)"
    hours_worked: Optional[Decimal] = None
    leave_request_id: Optional[UUID] = None
    leave_type_code: Optional[str] = None


class DailyAttendanceResponse(BaseModel):
    """Response including list of users and attendance stats."""
    date: date
    items: list[DailyAttendanceItem]
    total_present: int
    total_absent: int
# ═══════════════════════════════════════════════════════════
# Aggregate Reporting (HR)
# ═══════════════════════════════════════════════════════════

class AggregateReportRequest(BaseModel):
    """Request for aggregated attendance report."""
    start_date: date
    end_date: date
    department: Optional[str] = None


class AggregateReportItem(BaseModel):
    """Aggregated stats for a single user."""
    user_id: UUID
    full_name: str
    total_days: int
    worked_days: float
    vacation_days: Decimal
    holiday_days: Decimal
    rol_hours: Decimal
    permit_hours: Decimal
    sick_days: Optional[Decimal] = Decimal(0)
    other_absences: Decimal


class AggregateReportResponse(BaseModel):
    """Response for aggregated report."""
    start_date: date
    end_date: date
    items: list[AggregateReportItem]
