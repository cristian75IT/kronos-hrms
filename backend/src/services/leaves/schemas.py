"""KRONOS Leave Service - Pydantic Schemas."""
import enum
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
    condition_accepted_at: Optional[datetime] = None
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
    
    vacation_total_available: Decimal = Decimal(0)
    vacation_available_ap: Decimal = Decimal(0)
    vacation_available_ac: Decimal = Decimal(0)
    vacation_used: Decimal = Decimal(0)
    vacation_pending: Decimal = Decimal(0)  # Requested but not yet approved
    
    ap_expiry_date: Optional[date] = None
    days_until_ap_expiry: Optional[int] = None
    
    rol_available: Decimal = Decimal(0)
    rol_used: Decimal = Decimal(0)
    rol_pending: Decimal = Decimal(0)
    
    permits_available: Decimal = Decimal(0)
    permits_used: Decimal = Decimal(0)
    permits_pending: Decimal = Decimal(0)

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


# ═══════════════════════════════════════════════════════════
# Enterprise Features - Interruptions
# ═══════════════════════════════════════════════════════════

class InterruptionType(str, enum.Enum):
    """Type of leave interruption."""
    SICKNESS = "SICKNESS"
    PARTIAL_RECALL = "PARTIAL_RECALL"
    EMERGENCY_WORK = "EMERGENCY_WORK"
    OTHER = "OTHER"


class SicknessInterruptionRequest(BaseModel):
    """
    Request to interrupt vacation due to sickness.
    Per Art. 6 D.Lgs 66/2003, sick days during vacation are not counted.
    """
    
    sick_start_date: date
    sick_end_date: date
    protocol_number: str = Field(..., min_length=5, description="INPS protocol number")
    attachment_path: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator("sick_end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("sick_start_date")
        if start and v < start:
            raise ValueError("sick_end_date must be >= sick_start_date")
        return v


class PartialRecallRequest(BaseModel):
    """
    Request to recall employee for specific days during vacation.
    Unlike full recall (ends vacation), partial recall only interrupts specific days.
    """
    
    recall_days: list[date] = Field(..., min_length=1, description="Specific days to work")
    reason: str = Field(..., min_length=10, description="Business justification")
    
    @field_validator("recall_days")
    @classmethod
    def validate_days(cls, v: list[date]) -> list[date]:
        if len(v) != len(set(v)):
            raise ValueError("Duplicate dates not allowed")
        return sorted(v)


class VoluntaryWorkRequest(BaseModel):
    """
    Request from employee to convert vacation day(s) to working day(s).
    
    Use case: Employee has approved vacation but wants to work specific days
    (e.g., personal reasons, project deadline, save vacation for later).
    
    This creates an interruption request that requires manager approval.
    Upon approval, the vacation days are refunded to balance.
    """
    
    work_days: list[date] = Field(
        ..., 
        min_length=1, 
        max_length=5,
        description="Days within approved vacation to convert to working days"
    )
    reason: str = Field(
        ..., 
        min_length=20, 
        description="Detailed reason for wanting to work these days"
    )
    
    @field_validator("work_days")
    @classmethod
    def validate_days(cls, v: list[date]) -> list[date]:
        if len(v) != len(set(v)):
            raise ValueError("Duplicate dates not allowed")
        return sorted(v)


class VoluntaryWorkResponse(BaseModel):
    """Response for voluntary work request."""
    
    id: UUID
    leave_request_id: UUID
    work_days: list[date]
    days_to_refund: Decimal
    reason: str
    status: str  # PENDING_APPROVAL, APPROVED, REJECTED
    created_at: datetime
    approved_at: Optional[datetime] = None
    approver_notes: Optional[str] = None
    
    model_config = {"from_attributes": True}




class InterruptionResponse(BaseModel):
    """Response schema for leave interruption."""
    
    id: UUID
    leave_request_id: UUID
    interruption_type: str
    start_date: date
    end_date: date
    specific_days: Optional[list[date]] = None
    days_refunded: Decimal
    protocol_number: Optional[str] = None
    initiated_by: UUID
    initiated_by_role: str
    reason: Optional[str] = None
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Enterprise Features - Delegation
# ═══════════════════════════════════════════════════════════

class DelegationType(str, enum.Enum):
    """Type of approval delegation."""
    FULL = "FULL"       # Can approve and reject
    READONLY = "READONLY"  # Can only view


class CreateDelegationRequest(BaseModel):
    """Request to create approval delegation."""
    
    delegate_id: UUID = Field(..., description="User receiving delegation")
    start_date: date
    end_date: date
    delegation_type: DelegationType = DelegationType.FULL
    scope_leave_types: Optional[list[str]] = None  # e.g., ["FER", "ROL"]
    reason: Optional[str] = None
    
    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be >= start_date")
        return v


class DelegationResponse(BaseModel):
    """Response schema for delegation."""
    
    id: UUID
    delegator_id: UUID
    delegate_id: UUID
    start_date: date
    end_date: date
    delegation_type: str
    scope_leave_types: Optional[list[str]] = None
    reason: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Enterprise Features - Balance Reservation
# ═══════════════════════════════════════════════════════════

class ReservationStatus(str, enum.Enum):
    """Status of balance reservation."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ReservationResponse(BaseModel):
    """Response schema for balance reservation."""
    
    id: UUID
    leave_request_id: UUID
    user_id: UUID
    balance_type: str
    amount: Decimal
    breakdown: Optional[dict] = None
    status: str
    expires_at: datetime
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Enterprise Features - Modify Approved Request
# ═══════════════════════════════════════════════════════════

class ModifyApprovedRequest(BaseModel):
    """
    Request to modify an already approved leave request.
    Only allowed for future dates and by approvers.
    """
    
    new_start_date: Optional[date] = None
    new_end_date: Optional[date] = None
    new_start_half_day: Optional[bool] = None
    new_end_half_day: Optional[bool] = None
    reason: str = Field(..., min_length=10, description="Reason for modification")


# ═══════════════════════════════════════════════════════════
# Enterprise Features - Extended Actions
# ═══════════════════════════════════════════════════════════

class BulkActionRequest(BaseModel):
    """Request for bulk actions on multiple requests."""
    
    request_ids: list[UUID] = Field(..., min_length=1, max_length=50)
    action: str = Field(..., pattern="^(approve|reject|cancel)$")
    notes: Optional[str] = None
    reason: Optional[str] = None  # Required for reject


class BulkActionResult(BaseModel):
    """Result of a bulk action."""
    
    request_id: UUID
    success: bool
    error_message: Optional[str] = None


class BulkActionResponse(BaseModel):
    """Response for bulk action."""
    
    action: str
    total: int
    successful: int
    failed: int
    results: list[BulkActionResult]


