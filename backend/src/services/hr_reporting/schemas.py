"""
KRONOS HR Reporting Service - Pydantic Schemas.

Request/Response schemas for HR dashboard, reports, and exports.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Dashboard Schemas
# ═══════════════════════════════════════════════════════════

class WorkforceStatus(BaseModel):
    """Current workforce status."""
    total_employees: int
    active_now: int
    on_leave: int
    on_trip: int
    remote_working: int = 0
    sick_leave: int = 0
    absence_rate: float


class PendingApprovals(BaseModel):
    """Pending approval counts."""
    leave_requests: int
    expense_reports: int
    trip_requests: int
    total: int


class AlertItem(BaseModel):
    """Single alert item."""
    id: UUID
    type: str
    title: str
    description: Optional[str] = None
    severity: str  # info, warning, critical
    employee_id: Optional[UUID] = None
    employee_name: Optional[str] = None
    action_required: bool = False
    action_deadline: Optional[date] = None
    created_at: datetime


class DashboardOverview(BaseModel):
    """Complete HR dashboard overview."""
    date: date
    workforce: WorkforceStatus
    pending_approvals: PendingApprovals
    alerts: List[AlertItem] = []
    quick_stats: Dict[str, Any] = {}


class TeamStats(BaseModel):
    """Team-specific statistics."""
    team_id: UUID
    team_name: str
    manager_id: UUID
    manager_name: str
    employee_count: int
    on_leave_today: int
    pending_requests: int
    absence_rate_mtd: float  # Month-to-date
    leave_days_used_mtd: float


# ═══════════════════════════════════════════════════════════
# Monthly Report Schemas
# ═══════════════════════════════════════════════════════════

class AbsenceSummary(BaseModel):
    """Absence summary by type."""
    vacation: Dict[str, float]  # {"days": X, "hours": Y}
    rol: Dict[str, float]
    permits: Dict[str, float]
    sick_leave: Dict[str, float]
    other: Dict[str, float]


class BalanceSummary(BaseModel):
    """Leave balance summary."""
    vacation_remaining: Dict[str, float]  # {"ap": X, "ac": Y}
    rol_remaining: float
    permits_remaining: float


class TripSummary(BaseModel):
    """Trip/expense summary."""
    count: int
    total_days: int
    total_expenses: float
    total_allowances: float


class PayrollCodes(BaseModel):
    """Payroll codes for LUL export."""
    FERIE: float = 0
    ROL: float = 0
    PERM: float = 0
    MALATTIA: float = 0
    ALTRO: float = 0


class EmployeeMonthlyReport(BaseModel):
    """Single employee monthly report."""
    employee_id: UUID
    fiscal_code: Optional[str] = None
    full_name: str
    department: Optional[str] = None
    absences: AbsenceSummary
    balances: BalanceSummary
    trips: TripSummary
    payroll_codes: PayrollCodes


class MonthlyReportResponse(BaseModel):
    """Complete monthly report response."""
    period: str  # YYYY-MM
    generated_at: datetime
    generated_by: Optional[UUID] = None
    employee_count: int
    employees: List[EmployeeMonthlyReport]
    summary: Dict[str, Any]


# ═══════════════════════════════════════════════════════════
# Compliance Report Schemas
# ═══════════════════════════════════════════════════════════

class ComplianceIssue(BaseModel):
    """Single compliance issue."""
    employee_id: UUID
    employee_name: str
    type: str
    description: str
    deadline: Optional[date] = None
    days_missing: Optional[float] = None
    severity: str = "warning"
    resolved: bool = False

class ComplianceCheck(BaseModel):
    """Detailed compliance check result."""
    id: str  # e.g. "VACATION_AP", "LUL", "SAFETY"
    name: str
    description: str
    status: str  # PASS, WARN, CRIT
    result_value: Optional[str] = None
    details: Optional[List[str]] = None


class ComplianceStatistics(BaseModel):
    """Compliance statistics."""
    employees_compliant: int
    employees_at_risk: int
    employees_critical: int
    compliance_rate: float


class ComplianceReportResponse(BaseModel):
    """Complete compliance report."""
    period: str
    compliance_status: str  # OK, WARNING, CRITICAL
    issues: List[ComplianceIssue]
    checks: List[ComplianceCheck]
    statistics: ComplianceStatistics


# ═══════════════════════════════════════════════════════════
# Budget Report Schemas
# ═══════════════════════════════════════════════════════════

class DepartmentBudget(BaseModel):
    """Department budget status."""
    department_id: UUID
    department_name: str
    budget: float
    spent: float
    remaining: float
    utilization: float


class ExpenseBudgetSummary(BaseModel):
    """Expense budget summary."""
    trips_budget: float
    trips_spent: float
    trips_utilization: float
    by_department: List[DepartmentBudget]


class LeaveCostSummary(BaseModel):
    """Leave cost estimation."""
    vacation_days_taken: float
    estimated_vacation_cost: float
    sick_leave_days: float
    sick_leave_cost: float
    total_absence_cost: float


class BudgetReportResponse(BaseModel):
    """Complete budget report."""
    period: str
    expenses: ExpenseBudgetSummary
    leave_cost: LeaveCostSummary
    total_hr_cost: float


# ═══════════════════════════════════════════════════════════
# Request Schemas
# ═══════════════════════════════════════════════════════════

class ReportRequest(BaseModel):
    """Request for generating a report."""
    period_start: date
    period_end: date
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    include_details: bool = True


class CustomReportRequest(BaseModel):
    """Request for custom report."""
    report_type: str
    period_start: date
    period_end: date
    filters: Dict[str, Any] = {}
    group_by: Optional[str] = None  # department, team, role
    format: str = "json"  # json, pdf, excel


# ═══════════════════════════════════════════════════════════
# Export Schemas
# ═══════════════════════════════════════════════════════════

class ExportResponse(BaseModel):
    """Response for export request."""
    report_id: UUID
    format: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════
# Alert Management
# ═══════════════════════════════════════════════════════════

class AlertCreate(BaseModel):
    """Create new alert."""
    alert_type: str
    severity: str = "info"
    title: str
    description: Optional[str] = None
    employee_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    action_required: bool = False
    action_deadline: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertAcknowledge(BaseModel):
    """Acknowledge alert request."""
    notes: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert response."""
    id: UUID
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    employee_id: Optional[UUID]
    action_required: bool
    action_deadline: Optional[date]
    is_active: bool
    acknowledged_by: Optional[UUID]
    acknowledged_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════
# Training & Safety Schemas (D.Lgs. 81/08)
# ═══════════════════════════════════════════════════════════

class TrainingRecordBase(BaseModel):
    """Base training record."""
    training_type: str
    training_name: str
    description: Optional[str] = None
    provider_name: Optional[str] = None
    provider_code: Optional[str] = None
    training_date: date
    expiry_date: Optional[date] = None
    hours: Optional[int] = None
    certificate_number: Optional[str] = None
    notes: Optional[str] = None


class TrainingRecordCreate(TrainingRecordBase):
    """Create training record request."""
    employee_id: UUID


class TrainingRecordUpdate(BaseModel):
    """Update training record request."""
    training_type: Optional[str] = None
    training_name: Optional[str] = None
    description: Optional[str] = None
    provider_name: Optional[str] = None
    provider_code: Optional[str] = None
    training_date: Optional[date] = None
    expiry_date: Optional[date] = None
    hours: Optional[int] = None
    certificate_number: Optional[str] = None
    certificate_path: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TrainingRecordResponse(TrainingRecordBase):
    """Training record response."""
    id: UUID
    employee_id: UUID
    status: str
    certificate_path: Optional[str] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    days_until_expiry: Optional[int] = None
    is_expired: bool = False
    is_expiring_soon: bool = False

    class Config:
        from_attributes = True


class MedicalRecordBase(BaseModel):
    """Base medical record."""
    visit_type: str
    visit_date: date
    next_visit_date: Optional[date] = None
    fitness_result: str
    restrictions: Optional[str] = None
    doctor_name: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordCreate(MedicalRecordBase):
    """Create medical record request."""
    employee_id: UUID


class MedicalRecordUpdate(BaseModel):
    """Update medical record."""
    visit_type: Optional[str] = None
    visit_date: Optional[date] = None
    next_visit_date: Optional[date] = None
    fitness_result: Optional[str] = None
    restrictions: Optional[str] = None
    doctor_name: Optional[str] = None
    document_path: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordResponse(MedicalRecordBase):
    """Medical record response."""
    id: UUID
    employee_id: UUID
    document_path: Optional[str] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    days_until_next_visit: Optional[int] = None

    class Config:
        from_attributes = True


class SafetyComplianceResponse(BaseModel):
    """Employee safety compliance summary."""
    id: UUID
    employee_id: UUID
    employee_name: Optional[str] = None
    
    # Overall status
    is_compliant: bool
    compliance_score: int
    
    # Training status
    has_formazione_generale: bool
    has_formazione_specifica: bool
    trainings_expiring_soon: int
    trainings_expired: int
    
    # Medical status
    medical_fitness_valid: bool
    medical_next_visit: Optional[date] = None
    medical_restrictions: Optional[str] = None
    
    # Issues
    last_check_date: Optional[date] = None
    issues: Optional[List[Dict[str, Any]]] = None
    
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingOverviewResponse(BaseModel):
    """Training overview for all employees."""
    total_employees: int
    fully_compliant: int
    partially_compliant: int
    non_compliant: int
    
    trainings_expiring_30_days: int
    trainings_expired: int
    medical_visits_due: int
    
    compliance_by_type: Dict[str, int]  # {training_type: count_with_valid}
    employees: List[SafetyComplianceResponse]


class TrainingExpiringItem(BaseModel):
    """Training record expiring soon."""
    id: UUID
    employee_id: UUID
    employee_name: str
    training_type: str
    training_name: str
    expiry_date: date
    days_remaining: int


# ═══════════════════════════════════════════════════════════
# HR Management Schemas (DataTable endpoints)
# ═══════════════════════════════════════════════════════════

class HRLeaveItem(BaseModel):
    """Leave item for HR management view."""
    id: UUID
    employee_id: UUID
    employee_name: str
    employee_email: Optional[str] = None
    department: Optional[str] = None
    leave_type: str
    leave_type_name: str
    start_date: date
    end_date: date
    days_count: float
    hours_count: Optional[float] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


class HRTripItem(BaseModel):
    """Trip item for HR management view."""
    id: UUID
    employee_id: UUID
    employee_name: str
    employee_email: Optional[str] = None
    department: Optional[str] = None
    destination: str
    purpose: Optional[str] = None
    start_date: date
    end_date: date
    days_count: int
    daily_allowance: float
    total_allowance: float
    status: str
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class HRExpenseItem(BaseModel):
    """Expense report item for HR management view."""
    id: UUID
    employee_id: UUID
    employee_name: str
    employee_email: Optional[str] = None
    department: Optional[str] = None
    trip_id: Optional[UUID] = None
    trip_destination: Optional[str] = None
    total_amount: float
    items_count: int
    status: str
    submitted_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


class DataTableRequest(BaseModel):
    """DataTable server-side request."""
    draw: int = 1
    start: int = 0
    length: int = 25
    search_value: Optional[str] = None
    order_column: Optional[str] = None
    order_dir: str = "asc"
    filters: Dict[str, Any] = {}


class DataTableResponse(BaseModel):
    """DataTable server-side response."""
    draw: int
    recordsTotal: int
    recordsFiltered: int
    data: List[Any]


# ═══════════════════════════════════════════════════════════
# Attendance Report Schemas (moved from leaves)
# ═══════════════════════════════════════════════════════════

class AttendanceItem(BaseModel):
    """Single employee attendance record."""
    user_id: UUID
    full_name: str
    department: Optional[str] = None
    status: str  # "Presente", "Ferie", "Malattia", etc.
    hours_worked: float
    leave_request_id: Optional[UUID] = None
    leave_type: Optional[str] = None
    notes: Optional[str] = None


class DailyAttendanceResponse(BaseModel):
    """Daily attendance report response."""
    date: date
    total_employees: int
    total_present: int
    total_absent: int
    absence_rate: float
    items: List[AttendanceItem]


class AggregateAttendanceItem(BaseModel):
    """Aggregate attendance per employee."""
    user_id: UUID
    full_name: str
    department: Optional[str] = None
    worked_days: int
    total_days: int  # Working days in period
    vacation_days: float
    holiday_days: float
    rol_hours: float
    permit_hours: float
    sick_days: float
    other_absences: float


class AggregateAttendanceRequest(BaseModel):
    """Request for aggregate attendance."""
    start_date: date
    end_date: date
    department: Optional[str] = None


class AggregateAttendanceResponse(BaseModel):
    """Aggregate attendance report."""
    start_date: date
    end_date: date
    working_days: int
    items: List[AggregateAttendanceItem]


# ============================================================================
# Monthly Timesheet Schemas
# ============================================================================

class TimesheetDay(BaseModel):
    """Daily entry in monthly timesheet."""
    date: date
    status: str  # Present, Absent, Holiday, Weekend
    leave_type: Optional[str] = None
    hours_worked: float
    hours_expected: float
    notes: Optional[str] = None


class TimesheetSummary(BaseModel):
    """Summary of monthly timesheet."""
    total_days: int
    days_worked: float
    days_absent: float
    hours_worked: float
    hours_absence: float
    sickness_days: float
    vacation_days: float
    other_days: float


class MonthlyTimesheetResponse(BaseModel):
    """Monthly timesheet response."""
    id: UUID
    employee_id: UUID
    year: int
    month: int
    status: str
    days: List[TimesheetDay] = []
    summary: Optional[TimesheetSummary] = None
    confirmed_at: Optional[datetime] = None
    employee_notes: Optional[str] = None
    hr_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Confirmation window info
    can_confirm: bool = False
    confirmation_deadline: Optional[date] = None

    class Config:
        from_attributes = True


class TimesheetConfirmation(BaseModel):
    """Request to confirm timesheet."""
    notes: Optional[str] = None


class HRReportingSettingsUpdate(BaseModel):
    """Update HR settings."""
    timesheet_confirmation_day: int = Field(..., ge=1, le=31)
    timesheet_confirmation_month_offset: int = Field(..., ge=0, le=1)


class HRReportingSettingsResponse(BaseModel):
    """HR settings response."""
    timesheet_confirmation_day: int
    timesheet_confirmation_month_offset: int
    updated_at: datetime
    
    class Config:
        from_attributes = True
