"""KRONOS HR Reporting - Base Aggregator."""
import logging
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.shared.clients import (
    AuthClient,
    LeavesClient,
    ExpenseClient,
    CalendarClient,
)

logger = logging.getLogger(__name__)

class BaseAggregator:
    def __init__(
        self, 
        auth_client: AuthClient, 
        leaves_client: LeavesClient, 
        expense_client: ExpenseClient, 
        calendar_client: CalendarClient
    ):
        self._auth_client = auth_client
        self._leaves_client = leaves_client
        self._expense_client = expense_client
        self._calendar_client = calendar_client

    async def _get_employee_leave_data(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Get leave data for employee in date range."""
        result = {
            "vacation": {"days": 0, "hours": 0},
            "rol": {"days": 0, "hours": 0},
            "permits": {"days": 0, "hours": 0},
            "sick_leave": {"days": 0, "hours": 0},
            "other": {"days": 0, "hours": 0},
        }
        
        try:
            leaves = await self._leaves_client.get_leaves_in_period(
                start_date=start_date,
                end_date=end_date,
                user_id=employee_id,
                status="approved,approved_conditional"
            )
            
            for l in leaves:
                try:
                    req_start = date.fromisoformat(l["start_date"])
                    req_end = date.fromisoformat(l["end_date"])
                except ValueError:
                    continue
                
                # Intersection
                p_start = max(start_date, req_start)
                p_end = min(end_date, req_end)
                
                if p_start > p_end:
                    continue
                    
                days = 0
                if req_start >= start_date and req_end <= end_date:
                    days = float(l.get("days_requested", 0))
                else:
                    wd = await self._calendar_client.calculate_working_days(
                        p_start, p_end
                    )
                    days = float(wd.get("days", 0) if wd else 0)
                
                hours = days * 8.0
                
                code = l.get("leave_type_code", "").upper()
                cat = "other"
                if any(x in code for x in ["FER", "VAC"]): cat = "vacation"
                elif "ROL" in code: cat = "rol"
                elif any(x in code for x in ["PER", "PM"]): cat = "permits"
                elif "MAL" in code: cat = "sick_leave"
                
                result[cat]["days"] += days
                result[cat]["hours"] += hours
                
        except Exception as e:
            logger.error(f"Error fetching employee leave data: {e}")
            
        return result

    async def _get_employee_balance(self, employee_id: UUID) -> Dict[str, Any]:
        """Get current leave balance for employee."""
        try:
            balance = await self._leaves_client.get_balance_summary(employee_id)
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
        return {
            "count": 0,
            "total_days": 0,
            "total_expenses": 0.0,
            "total_allowances": 0.0,
        }
