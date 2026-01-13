"""
KRONOS HR Reporting Service - Data Aggregator FAÇADE.

This class delegates actual aggregation logic to specialized sub-aggregators.
"""
import logging
from datetime import date
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.shared.clients import (
    AuthClient,
    LeavesClient,
    ExpenseClient,
    CalendarClient,
)

from src.services.hr_reporting.aggregators.dashboard import DashboardAggregator
from src.services.hr_reporting.aggregators.attendance import AttendanceAggregator
from src.services.hr_reporting.aggregators.reports import ReportAggregator
from src.services.hr_reporting.aggregators.compliance import ComplianceAggregator
from src.services.hr_reporting.aggregators.budget import BudgetAggregator

logger = logging.getLogger(__name__)

class HRDataAggregator:
    """
    Facade for all aggregation operations.
    Maintains backward compatibility for consumers (Router/Service).
    """
    
    def __init__(self):
        # Clients are instantiated here and passed down
        # This keeps the DI logic centralized
        self._auth_client = AuthClient()
        self._leaves_client = LeavesClient()
        self._expense_client = ExpenseClient()
        self._calendar_client = CalendarClient()
        
        # Sub-aggregators
        self._dashboard = DashboardAggregator(self._auth_client, self._leaves_client, self._expense_client, self._calendar_client)
        self._attendance = AttendanceAggregator(self._auth_client, self._leaves_client, self._expense_client, self._calendar_client)
        self._report = ReportAggregator(self._auth_client, self._leaves_client, self._expense_client, self._calendar_client)
        self._compliance = ComplianceAggregator(self._auth_client, self._leaves_client, self._expense_client, self._calendar_client)
        self._budget = BudgetAggregator(self._auth_client, self._leaves_client, self._expense_client, self._calendar_client)

    # -------------------------------------------------------------------------
    # Delegations
    # -------------------------------------------------------------------------

    async def get_workforce_status(self, target_date: date = None) -> Dict[str, Any]:
        return await self._dashboard.get_workforce_status(target_date)
    
    async def get_pending_approvals(self) -> Dict[str, Any]:
        return await self._dashboard.get_pending_approvals()
    
    async def get_daily_attendance_details(self, target_date: date, department: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self._attendance.get_daily_attendance_details(target_date, department)
        
    async def get_aggregate_attendance_details(self, start_date: date, end_date: date, department: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self._attendance.get_aggregate_attendance_details(start_date, end_date, department)
        
    async def get_employee_daily_attendance_range(self, employee_id: UUID, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        return await self._attendance.get_employee_daily_attendance_range(employee_id, start_date, end_date)

    async def get_employee_monthly_data(self, employee_id: UUID, year: int, month: int) -> Dict[str, Any]:
        return await self._report.get_employee_monthly_data(employee_id, year, month)
        
    async def get_all_employees_monthly_data(self, year: int, month: int, department_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        return await self._report.get_all_employees_monthly_data(year, month, department_id)
        
    async def get_compliance_data(self) -> Dict[str, Any]:
        return await self._compliance.get_compliance_data()
        
    async def get_budget_summary(self, year: int, month: Optional[int] = None) -> Dict[str, Any]:
        return await self._budget.get_budget_summary(year, month)
