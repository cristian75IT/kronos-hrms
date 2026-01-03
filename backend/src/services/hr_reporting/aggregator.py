"""
KRONOS HR Reporting Service - Data Aggregator.

Aggregates data from multiple KRONOS microservices for reporting.
Uses service clients for inter-service communication.
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.core.config import settings
from src.shared.clients import (
    AuthClient,
    LeavesClient,
    LeavesWalletClient,
    ExpenseClient,
    ExpensiveWalletClient,
    CalendarClient,
)

logger = logging.getLogger(__name__)


class HRDataAggregator:
    """
    Aggregates workforce data from all KRONOS services.
    
    This class is responsible for:
    - Fetching data from individual services
    - Combining and transforming data for reports
    - Calculating derived metrics
    """
    
    def __init__(self):
        self._auth_client = AuthClient()
        self._leaves_client = LeavesClient()
        self._leaves_wallet_client = LeavesWalletClient()
        self._expense_client = ExpenseClient()
        self._expense_wallet_client = ExpensiveWalletClient()
        self._calendar_client = CalendarClient()
    
    # ═══════════════════════════════════════════════════════════
    # Dashboard Data
    # ═══════════════════════════════════════════════════════════
    
    async def get_workforce_status(self, target_date: date = None) -> Dict[str, Any]:
        """Get current workforce status."""
        target_date = target_date or date.today()
        
        try:
            # Get all active users
            users = await self._auth_client.get_users()
            total_employees = len([u for u in users if u.get("is_active", True)])
            
            # Get leave requests for today
            on_leave = 0
            on_sick = 0
            
            # This would be optimized with a dedicated endpoint
            # For now we simulate the aggregation logic
            leave_summary = await self._get_leave_summary_for_date(target_date)
            on_leave = leave_summary.get("on_leave", 0)
            on_sick = leave_summary.get("on_sick", 0)
            
            # Get active trips
            on_trip = await self._get_active_trips_count(target_date)
            
            # Calculate absence rate
            total_absent = on_leave + on_sick + on_trip
            absence_rate = (total_absent / total_employees * 100) if total_employees > 0 else 0
            
            return {
                "total_employees": total_employees,
                "on_leave_today": on_leave,
                "on_trip_today": on_trip,
                "working_remotely": 0,  # TODO: Integrate with attendance
                "sick_today": on_sick,
                "absence_rate": round(absence_rate, 2),
            }
        except Exception as e:
            logger.error(f"Error fetching workforce status: {e}")
            return {
                "total_employees": 0,
                "on_leave_today": 0,
                "on_trip_today": 0,
                "working_remotely": 0,
                "sick_today": 0,
                "absence_rate": 0,
            }
    
    async def get_pending_approvals(self) -> Dict[str, Any]:
        """Get pending approval counts."""
        try:
            leave_requests = await self._leaves_client.get_pending_requests_count()
            expense_reports = await self._expense_client.get_pending_reports_count()
            trip_requests = await self._expense_client.get_pending_trips_count()
            
            return {
                "leave_requests": leave_requests,
                "expense_reports": expense_reports,
                "trip_requests": trip_requests,
                "total": leave_requests + expense_reports + trip_requests,
            }
        except Exception as e:
            logger.error(f"Error fetching pending approvals: {e}")
            return {
                "leave_requests": 0,
                "expense_reports": 0,
                "trip_requests": 0,
                "total": 0,
            }
    
    # ═══════════════════════════════════════════════════════════
    # Monthly Report Data
    # ═══════════════════════════════════════════════════════════
    
    async def get_employee_monthly_data(
        self,
        employee_id: UUID,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Get comprehensive monthly data for an employee."""
        try:
            # Date range for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Get employee info
            user_info = await self._auth_client.get_user(employee_id)
            
            # Get leave data
            leave_data = await self._get_employee_leave_data(
                employee_id, start_date, end_date
            )
            
            # Get balance data
            balance_data = await self._get_employee_balance(employee_id)
            
            # Get expense/trip data
            expense_data = await self._get_employee_expense_data(
                employee_id, start_date, end_date
            )
            
            # Calculate payroll codes
            payroll_codes = self._calculate_payroll_codes(leave_data)
            
            return {
                "employee_id": str(employee_id),
                "fiscal_code": user_info.get("fiscal_code") if user_info else None,
                "full_name": f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}" if user_info else "Unknown",
                "department": user_info.get("department") if user_info else None,
                "absences": leave_data,
                "balances": balance_data,
                "trips": expense_data,
                "payroll_codes": payroll_codes,
            }
        except Exception as e:
            logger.error(f"Error fetching monthly data for {employee_id}: {e}")
            return None
    
    async def get_all_employees_monthly_data(
        self,
        year: int,
        month: int,
        department_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Get monthly data for all employees."""
        try:
            users = await self._auth_client.get_users()
            
            # Filter by department if specified
            if department_id:
                users = [u for u in users if u.get("department_id") == str(department_id)]
            
            # Filter active only
            users = [u for u in users if u.get("is_active", True)]
            
            results = []
            for user in users:
                user_id = UUID(user.get("id"))
                data = await self.get_employee_monthly_data(user_id, year, month)
                if data:
                    results.append(data)
            
            return results
        except Exception as e:
            logger.error(f"Error fetching all employees monthly data: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════
    # Compliance Data
    # ═══════════════════════════════════════════════════════════
    
    async def get_compliance_issues(self) -> List[Dict[str, Any]]:
        """Get current compliance issues."""
        issues = []
        
        try:
            users = await self._auth_client.get_users()
            active_users = [u for u in users if u.get("is_active", True)]
            
            today = date.today()
            current_year = today.year
            
            for user in active_users:
                user_id = UUID(user.get("id"))
                user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
                
                # Check vacation balance for previous year (AP)
                balance = await self._get_employee_balance(user_id)
                ap_balance = balance.get("vacation_remaining", {}).get("ap", 0)
                
                # Check if approaching June 30 deadline with remaining AP
                if ap_balance > 0 and today.month >= 1:  # Alert starts from January
                    deadline = date(current_year, 6, 30)
                    if today <= deadline:
                        issues.append({
                            "employee_id": str(user_id),
                            "employee_name": user_name,
                            "type": "VACATION_AP_EXPIRING",
                            "description": f"Residuo ferie anno precedente: {ap_balance} giorni. Scadenza 30/06/{current_year}",
                            "deadline": str(deadline),
                            "days_missing": ap_balance,
                            "severity": "warning" if today.month < 5 else "critical",
                        })
                
                # Check legal minimum vacation taken
                # (2 consecutive weeks must be taken each year)
                # This would require more detailed leave tracking
                
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
        
        return issues
    
    # ═══════════════════════════════════════════════════════════
    # Budget Data
    # ═══════════════════════════════════════════════════════════
    
    async def get_budget_summary(
        self,
        year: int,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get expense budget summary."""
        try:
            # This would integrate with config service for budget settings
            # and expense service for actual spending
            
            # For now, return structure with placeholder data
            return {
                "trips_budget": 50000.00,
                "trips_spent": 0.0,
                "trips_utilization": 0.0,
                "by_department": [],
            }
        except Exception as e:
            logger.error(f"Error fetching budget summary: {e}")
            return {}
    
    # ═══════════════════════════════════════════════════════════
    # Private Helper Methods
    # ═══════════════════════════════════════════════════════════
    
    async def _get_leave_summary_for_date(self, target_date: date) -> Dict[str, Any]:
        """Get leave summary for a specific date."""
        # This would call leaves service with appropriate filters
        # For now returns placeholder
        return {"on_leave": 0, "on_sick": 0}
    
    async def _get_active_trips_count(self, target_date: date) -> int:
        """Get count of active trips for a date."""
        # This would call expense service
        return 0
    
    async def _get_employee_leave_data(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Get leave data for employee in date range."""
        # This would call leaves service for approved requests
        return {
            "vacation": {"days": 0, "hours": 0},
            "rol": {"days": 0, "hours": 0},
            "permits": {"days": 0, "hours": 0},
            "sick_leave": {"days": 0, "hours": 0},
            "other": {"days": 0, "hours": 0},
        }
    
    async def _get_employee_balance(self, employee_id: UUID) -> Dict[str, Any]:
        """Get current leave balance for employee."""
        try:
            balance = await self._leaves_wallet_client.get_balance_summary(employee_id)
            if balance:
                return {
                    "vacation_remaining": {
                        "ap": balance.get("vacation_ap", 0),
                        "ac": balance.get("vacation_ac", 0),
                    },
                    "rol_remaining": balance.get("rol", 0),
                    "permits_remaining": balance.get("permits", 0),
                }
        except Exception as e:
            logger.error(f"Error fetching balance for {employee_id}: {e}")
        
        return {
            "vacation_remaining": {"ap": 0, "ac": 0},
            "rol_remaining": 0,
            "permits_remaining": 0,
        }
    
    async def _get_employee_expense_data(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Get expense/trip data for employee in date range."""
        # This would call expense service
        return {
            "count": 0,
            "total_days": 0,
            "total_expenses": 0.0,
            "total_allowances": 0.0,
        }
    
    def _calculate_payroll_codes(self, leave_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate payroll codes from leave data."""
        return {
            "FERIE": leave_data.get("vacation", {}).get("hours", 0),
            "ROL": leave_data.get("rol", {}).get("hours", 0),
            "PERM": leave_data.get("permits", {}).get("hours", 0),
            "MALATTIA": leave_data.get("sick_leave", {}).get("hours", 0),
            "ALTRO": leave_data.get("other", {}).get("hours", 0),
        }
