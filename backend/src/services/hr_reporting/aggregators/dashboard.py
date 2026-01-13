"""KRONOS HR Reporting - Dashboard Aggregator."""
import logging
from datetime import date
from typing import Dict, Any

from .base import BaseAggregator

logger = logging.getLogger(__name__)

class DashboardAggregator(BaseAggregator):
    """Aggregates data for the main dashboard."""

    async def get_workforce_status(self, target_date: date = None) -> Dict[str, Any]:
        """Get current workforce status."""
        target_date = target_date or date.today()
        
        try:
            # Get all active users
            users = await self._auth_client.get_users()
            total_employees = len([u for u in users if u.get("is_active", True)])
            
            # Get leave requests for today
            leave_summary = await self._get_leave_summary_for_date(target_date)
            on_leave = leave_summary.get("on_leave", 0)
            on_sick = leave_summary.get("on_sick", 0)
            
            # Get active trips
            trips_on_date = await self._expense_client.get_trips_for_date(target_date)
            on_trip = len(trips_on_date)
            
            # Calculate absence rate
            total_absent = on_leave + on_sick + on_trip
            absence_rate = (total_absent / total_employees * 100) if total_employees > 0 else 0
            
            # Calculate active workforce
            active_now = total_employees - total_absent
            if active_now < 0:
                active_now = 0

            return {
                "total_employees": total_employees,
                "active_now": active_now,
                "on_leave": on_leave,
                "on_trip": on_trip,
                "remote_working": 0,  # TODO: Integrate with attendance
                "sick_leave": on_sick,
                "absence_rate": round(absence_rate, 2),
            }
        except Exception as e:
            logger.error(f"Error fetching workforce status: {e}")
            return {
                "total_employees": 0,
                "active_now": 0,
                "on_leave": 0,
                "on_trip": 0,
                "remote_working": 0,
                "sick_leave": 0,
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

    async def _get_leave_summary_for_date(self, target_date: date) -> Dict[str, Any]:
        """Get leave summary for a specific date."""
        try:
            leaves = await self._leaves_client.get_leaves_for_date(target_date)
            on_leave = 0
            on_sick = 0
            for l in leaves:
                code = l.get("leave_type_code", "").upper()
                if "MAL" in code:
                    on_sick += 1
                else:
                    on_leave += 1
            return {"on_leave": on_leave, "on_sick": on_sick}
        except Exception as e:
            logger.error(f"Error getting summary for date: {e}")
            return {"on_leave": 0, "on_sick": 0}
