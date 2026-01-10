"""
KRONOS HR Reporting Service - Business Logic.

Central service for HR analytics, reporting, and workforce management.
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.shared.audit_client import get_audit_logger

from .models import (
    GeneratedReport,
    DailySnapshot,
    HRAlert,
    ReportType,
    ReportStatus,
)
from .aggregator import HRDataAggregator
from .repository import (
    ReportRepository,
    DailySnapshotRepository,
    HRAlertRepository,
    # Additional repos if needed in future
    TrainingRecordRepository,
    MedicalRecordRepository,
    SafetyComplianceRepository,
    EmployeeMonthlyStatsRepository
)
from .schemas import (
    DashboardOverview,
    WorkforceStatus,
    PendingApprovals,
    AlertItem,
    MonthlyReportResponse,
    EmployeeMonthlyReport,
    ComplianceReportResponse,
    ComplianceIssue,
    ComplianceStatistics,
    BudgetReportResponse,
)

logger = logging.getLogger(__name__)


class HRReportingService:
    """
    Enterprise HR Reporting Service.
    
    Provides:
    - Real-time dashboard data
    - Monthly/periodic reports
    - Compliance monitoring
    - Budget tracking
    - Alert management
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._aggregator = HRDataAggregator()
        self._audit = get_audit_logger("hr-reporting-service")
        
        # Repositories
        self.report_repo = ReportRepository(session)
        self.snapshot_repo = DailySnapshotRepository(session)
        self.alert_repo = HRAlertRepository(session)
    
    # ═══════════════════════════════════════════════════════════
    # Dashboard Operations
    # ═══════════════════════════════════════════════════════════
    
    async def get_dashboard_overview(self, target_date: date = None) -> DashboardOverview:
        """Get complete HR dashboard overview."""
        target_date = target_date or date.today()
        
        # Get workforce status
        workforce_data = await self._aggregator.get_workforce_status(target_date)
        workforce = WorkforceStatus(**workforce_data)
        
        # Get pending approvals
        approvals_data = await self._aggregator.get_pending_approvals()
        pending_approvals = PendingApprovals(**approvals_data)
        
        # Get active alerts
        alerts = await self.get_active_alerts(limit=10)
        
        # Get quick stats
        quick_stats = await self._get_quick_stats(target_date)
        
        return DashboardOverview(
            date=target_date,
            workforce=workforce,
            pending_approvals=pending_approvals,
            alerts=alerts,
            quick_stats=quick_stats,
        )
    
    async def get_team_dashboard(
        self,
        team_id: UUID,
        manager_id: UUID,
    ) -> Dict[str, Any]:
        """Get team-specific dashboard."""
        # Team-scoped version of dashboard
        # Would filter all data by team/manager
        return {
            "team_id": str(team_id),
            "manager_id": str(manager_id),
            "employee_count": 0,
            "on_leave_today": 0,
            "pending_requests": 0,
            "alerts": [],
        }
    
    # ═══════════════════════════════════════════════════════════
    # Monthly Report Operations
    # ═══════════════════════════════════════════════════════════
    
    async def generate_monthly_report(
        self,
        year: int,
        month: int,
        department_id: Optional[UUID] = None,
        generated_by: Optional[UUID] = None,
    ) -> MonthlyReportResponse:
        """Generate monthly absence report."""
        period = f"{year}-{month:02d}"
        period_start = date(year, month, 1)
        
        # Check for cached report
        cached = await self.report_repo.get_cached(
            ReportType.MONTHLY_ABSENCE,
            period_start,
            department_id,
        )
        if cached and cached.status == ReportStatus.COMPLETED:
            return self._report_from_cache(cached)
        
        # Generate fresh report
        employees_data = await self._aggregator.get_all_employees_monthly_data(
            year, month, department_id
        )
        
        employees = []
        for emp_data in employees_data:
            employees.append(EmployeeMonthlyReport(
                employee_id=UUID(emp_data["employee_id"]),
                fiscal_code=emp_data.get("fiscal_code"),
                full_name=emp_data["full_name"],
                department=emp_data.get("department"),
                absences=emp_data["absences"],
                balances=emp_data["balances"],
                trips=emp_data["trips"],
                payroll_codes=emp_data["payroll_codes"],
            ))
        
        # Calculate summary
        summary = self._calculate_monthly_summary(employees)
        
        # Create report record
        report = GeneratedReport(
            report_type=ReportType.MONTHLY_ABSENCE,
            period_start=period_start,
            period_end=self._get_month_end(year, month),
            department_id=department_id,
            status=ReportStatus.COMPLETED,
            report_data={"employees": [e.model_dump() for e in employees]},
            summary=summary,
            generated_by=generated_by,
            generated_at=datetime.utcnow(),
        )
        
        await self.report_repo.create(report)
        await self._session.commit()
        
        # Audit
        await self._audit.log_action(
            user_id=generated_by,
            action="GENERATE_REPORT",
            resource_type="MONTHLY_REPORT",
            resource_id=str(report.id),
            description=f"Generated monthly report for {period}",
        )
        
        return MonthlyReportResponse(
            period=period,
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            employee_count=len(employees),
            employees=employees,
            summary=summary,
        )
    
    async def generate_lul_export(
        self,
        year: int,
        month: int,
    ) -> str:
        """
        Generate LUL export (CSV format) for Labor Consultant.
        
        Format (Zucchetti-like simulation):
        COD_AZIENDA;MATRICOLA;ANNO;MESE;COD_VOCE;ORE;GIORNI
        """
        employees_data = await self._aggregator.get_all_employees_monthly_data(year, month)
        
        lines = ["COD_AZIENDA;MATRICOLA;ANNO;MESE;COD_VOCE;ORE;GIORNI"]
        
        for emp in employees_data:
            emp_id = emp.get("employee_id") # Use specific ID mapping if available
            codes = emp.get("payroll_codes", {})
            
            # Base info
            base = f"KRONOS;{str(emp_id)[:8]};{year};{month}"
            
            # 1. Ordinary Hours (Worked)
            # This is not in payroll_codes, usually calculated as expected - absences
            # For simplicity we export absences which is what consultants primarily need
            
            # Absences
            for code, hours in codes.items():
                if hours > 0:
                    days = hours / 8.0 # Approx
                    lines.append(f"{base};{code};{hours:.2f};{days:.2f}")
                    
        return "\n".join(lines)
    # ═══════════════════════════════════════════════════════════
    
    async def generate_compliance_report(
        self,
        generated_by: Optional[UUID] = None,
    ) -> ComplianceReportResponse:
        """Generate compliance status report."""
        today = date.today()
        period = f"{today.year}-{today.month:02d}"
        
        # Get compliance data (issues and checks)
        comp_data = await self._aggregator.get_compliance_data()
        issues_data = comp_data.get("issues", [])
        checks_data = comp_data.get("checks", [])
        
        issues = [
            ComplianceIssue(
                employee_id=UUID(i["employee_id"]),
                employee_name=i["employee_name"],
                type=i["type"],
                description=i["description"],
                deadline=date.fromisoformat(i["deadline"]) if i.get("deadline") else None,
                days_missing=i.get("days_missing"),
                severity=i.get("severity", "warning"),
            )
            for i in issues_data
        ]
        
        from .schemas import ComplianceCheck
        checks = [ComplianceCheck(**c) for c in checks_data]
        
        # Calculate statistics
        critical_count = len([i for i in issues if i.severity == "critical"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        
        # Get total employee count for compliance rate
        workforce = await self._aggregator.get_workforce_status()
        total = workforce.get("total_employees", 1)
        
        at_risk = len(set(i.employee_id for i in issues))
        compliant = total - at_risk
        
        statistics = ComplianceStatistics(
            employees_compliant=compliant,
            employees_at_risk=warning_count,
            employees_critical=critical_count,
            compliance_rate=round(compliant / total * 100, 1) if total > 0 else 100,
        )
        
        # Determine overall status
        if critical_count > 0:
            status = "CRITICAL"
        elif warning_count > 0:
            status = "WARNING"
        else:
            status = "OK"
        
        return ComplianceReportResponse(
            period=period,
            compliance_status=status,
            issues=issues,
            checks=checks,
            statistics=statistics,
        )
    
    # ═══════════════════════════════════════════════════════════
    # Budget Report Operations
    # ═══════════════════════════════════════════════════════════
    
    async def generate_budget_report(
        self,
        year: int,
        month: Optional[int] = None,
        generated_by: Optional[UUID] = None,
    ) -> BudgetReportResponse:
        """Generate expense budget report."""
        if month:
            period = f"{year}-{month:02d}"
        else:
            period = str(year)
        
        budget_data = await self._aggregator.get_budget_summary(year, month)
        
        # Structure response
        from .schemas import ExpenseBudgetSummary, LeaveCostSummary
        
        expenses = ExpenseBudgetSummary(
            trips_budget=budget_data.get("trips_budget", 0),
            trips_spent=budget_data.get("trips_spent", 0),
            trips_utilization=budget_data.get("trips_utilization", 0),
            by_department=[],  # Would populate from data
        )
        
        leave_cost = LeaveCostSummary(
            vacation_days_taken=0,
            estimated_vacation_cost=0,
            sick_leave_days=0,
            sick_leave_cost=0,
            total_absence_cost=0,
        )
        
        return BudgetReportResponse(
            period=period,
            expenses=expenses,
            leave_cost=leave_cost,
            total_hr_cost=0,
        )
    
    # ═══════════════════════════════════════════════════════════
    # Alert Management
    # ═══════════════════════════════════════════════════════════
    
    async def get_active_alerts(self, limit: int = 50) -> List[AlertItem]:
        """Get active HR alerts."""
        alerts = await self.alert_repo.get_active(limit=limit)
        
        return [
            AlertItem(
                id=a.id,
                type=a.alert_type,
                title=a.title,
                description=a.description,
                severity=a.severity,
                employee_id=a.employee_id,
                action_required=a.action_required,
                action_deadline=a.action_deadline,
                created_at=a.created_at,
            )
            for a in alerts
        ]
    
    async def create_alert(
        self,
        alert_type: str,
        title: str,
        description: str = None,
        severity: str = "info",
        employee_id: UUID = None,
        department_id: UUID = None,
        action_required: bool = False,
        action_deadline: date = None,
        metadata: dict = None,
    ) -> HRAlert:
        """Create new HR alert."""
        alert = HRAlert(
            alert_type=alert_type,
            title=title,
            description=description,
            severity=severity,
            employee_id=employee_id,
            department_id=department_id,
            action_required=action_required,
            action_deadline=action_deadline,
            extra_data=metadata,
        )
        await self.alert_repo.create(alert)
        await self._session.commit()
        return alert
    
    async def acknowledge_alert(
        self,
        alert_id: UUID,
        acknowledged_by: UUID,
    ) -> HRAlert:
        """Acknowledge an alert."""
        alert = await self.alert_repo.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found", entity_type="HRAlert", entity_id=str(alert_id))
        
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        await self.alert_repo.update(alert)
        await self._session.commit()
        
        return alert
    
    async def resolve_alert(self, alert_id: UUID) -> HRAlert:
        """Mark alert as resolved."""
        alert = await self.alert_repo.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found", entity_type="HRAlert", entity_id=str(alert_id))
        
        alert.is_active = False
        alert.resolved_at = datetime.utcnow()
        
        await self.alert_repo.update(alert)
        await self._session.commit()
        
        return alert
    
    # ═══════════════════════════════════════════════════════════
    # Daily Snapshot Operations
    # ═══════════════════════════════════════════════════════════
    
    async def create_daily_snapshot(self) -> DailySnapshot:
        """Create daily workforce snapshot."""
        today = date.today()
        
        # Check if already exists
        existing = await self.snapshot_repo.get_by_date(today)
        
        if existing:
            snapshot = existing
        else:
            snapshot = DailySnapshot(snapshot_date=today)
        
        # Fetch current data
        workforce = await self._aggregator.get_workforce_status(today)
        approvals = await self._aggregator.get_pending_approvals()
        
        # Update snapshot
        snapshot.total_employees = workforce.get("total_employees", 0)
        snapshot.employees_on_leave = workforce.get("on_leave", 0)
        snapshot.employees_on_trip = workforce.get("on_trip", 0)
        snapshot.employees_sick = workforce.get("sick_leave", 0)
        snapshot.absence_rate = Decimal(str(workforce.get("absence_rate", 0)))
        snapshot.pending_leave_requests = approvals.get("leave_requests", 0)
        snapshot.pending_expense_reports = approvals.get("expense_reports", 0)
        
        if existing:
             await self.snapshot_repo.update(snapshot)
        else:
             await self.snapshot_repo.create(snapshot)
             
        await self._session.commit()
        
        logger.info(f"Created daily snapshot for {today}")
        return snapshot
    
    # ═══════════════════════════════════════════════════════════
    # Private Helper Methods
    # ═══════════════════════════════════════════════════════════
    
    async def _get_quick_stats(self, target_date: date) -> Dict[str, Any]:
        """Get quick statistics for dashboard."""
        # Calculate month-to-date metrics
        month_start = target_date.replace(day=1)
        
        return {
            "mtd_leave_requests": 0,
            "mtd_expense_reports": 0,
            "ytd_vacation_days_used": 0,
            "ytd_sick_days": 0,
        }
    
    def _report_from_cache(self, cached: GeneratedReport) -> MonthlyReportResponse:
        """Reconstruct report from cache."""
        employees = [
            EmployeeMonthlyReport(**emp)
            for emp in cached.report_data.get("employees", [])
        ]
        
        return MonthlyReportResponse(
            period=f"{cached.period_start.year}-{cached.period_start.month:02d}",
            generated_at=cached.generated_at,
            generated_by=cached.generated_by,
            employee_count=len(employees),
            employees=employees,
            summary=cached.summary or {},
        )
    
    def _calculate_monthly_summary(self, employees: List[EmployeeMonthlyReport]) -> Dict[str, Any]:
        """Calculate summary statistics from employee reports."""
        total_vacation_days = sum(e.absences.vacation.get("days", 0) for e in employees)
        total_sick_days = sum(e.absences.sick_leave.get("days", 0) for e in employees)
        total_trips = sum(e.trips.count for e in employees)
        total_expenses = sum(e.trips.total_expenses for e in employees)
        
        return {
            "total_employees": len(employees),
            "total_vacation_days": total_vacation_days,
            "total_sick_days": total_sick_days,
            "total_trips": total_trips,
            "total_expenses": total_expenses,
            "avg_vacation_days": total_vacation_days / len(employees) if employees else 0,
            "avg_sick_days": total_sick_days / len(employees) if employees else 0,
        }
    
    def _get_month_end(self, year: int, month: int) -> date:
        """Get last day of month."""
        if month == 12:
            return date(year + 1, 1, 1) - timedelta(days=1)
        return date(year, month + 1, 1) - timedelta(days=1)
