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
    on_leave_today: int
    on_trip_today: int
    working_remotely: int = 0
    sick_today: int = 0
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
