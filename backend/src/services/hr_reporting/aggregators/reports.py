"""KRONOS HR Reporting - Reports Aggregator (Monthly)."""
import logging
from datetime import date, timedelta
from typing import List, Dict, Any
from uuid import UUID

from .base import BaseAggregator

logger = logging.getLogger(__name__)

class ReportAggregator(BaseAggregator):
    """Aggregates data for monthly reports."""

    async def get_all_employees_monthly_data(
        self, 
        year: int, 
        month: int,
        department_id: UUID = None
    ) -> List[Dict[str, Any]]:
        """Get monthly data for all employees."""
        try:
            # 1. Get employees (filtered by dept if needed)
            if department_id:
                # TODO: Implement get_by_department in client
                users = await self._auth_client.get_users()
                # filter manually for now or assume client supports it
                users = [u for u in users if u.get("department_id") == str(department_id)]
            else:
                users = await self._auth_client.get_users()

            users = [u for u in users if u.get("is_active", True)]
            
            reports = []
            for user in users:
                data = await self.get_employee_monthly_data(
                    UUID(user["id"]), year, month
                )
                data["fiscal_code"] = user.get("fiscal_code")
                data["full_name"] = f"{user.get('first_name')} {user.get('last_name')}"
                data["department"] = user.get("department_name", "")
                reports.append(data)
                
            return reports
            
        except Exception as e:
            logger.error(f"Error generating all employees report: {e}")
            return []

    async def get_employee_monthly_data(
        self,
        employee_id: UUID, 
        year: int, 
        month: int
    ) -> Dict[str, Any]:
        """Get single employee monthly data."""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        # Parallel fetch could be better here
        leaves = await self._get_employee_leave_data(employee_id, start_date, end_date)
        balance = await self._get_employee_balance(employee_id)
        expenses = await self._get_employee_expense_data(employee_id, start_date, end_date)
        
        # Payroll codes calculation
        codes = self._calculate_payroll_codes(leaves)
        
        return {
            "employee_id": str(employee_id),
            "period": f"{year}-{month:02d}",
            "absences": leaves,
            "balances": balance,
            "trips": expenses,
            "payroll_codes": codes,
        }

    def _calculate_payroll_codes(self, leave_data: Dict[str, Any]) -> Dict[str, float]:
        """Map leave categories to mock payroll codes."""
        codes = {}
        if leave_data["vacation"]["hours"] > 0:
            codes["FERIE"] = leave_data["vacation"]["hours"]
        if leave_data["rol"]["hours"] > 0:
            codes["ROL"] = leave_data["rol"]["hours"]
        if leave_data["sick_leave"]["hours"] > 0:
            codes["MALATTIA"] = leave_data["sick_leave"]["hours"]
        if leave_data["permits"]["hours"] > 0:
            codes["PERMESSO"] = leave_data["permits"]["hours"]
            
        return codes
