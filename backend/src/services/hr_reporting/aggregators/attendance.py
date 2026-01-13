"""KRONOS HR Reporting - Attendance Aggregator."""
import logging
from datetime import date
from typing import Dict, Any, List, Optional
from uuid import UUID

from .base import BaseAggregator

logger = logging.getLogger(__name__)

class AttendanceAggregator(BaseAggregator):
    """Aggregates attendance data (daily details)."""

    async def get_daily_attendance_details(
        self,
        target_date: date,
        department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get detailed attendance status for all employees on a given date."""
        try:
            # Get all active users
            users = await self._auth_client.get_users()
            active_users = [u for u in users if u.get("is_active", True)]
            
            # Filter by department if specified
            if department:
                active_users = [
                    u for u in active_users 
                    if u.get("department", "").lower() == department.lower()
                ]
            
            # Get leave requests for the date
            leaves_on_date = await self._leaves_client.get_leaves_for_date(target_date)
            leave_by_user = {str(l.get("user_id")): l for l in leaves_on_date}
            
            # Get trips for the date  
            trips_on_date = await self._expense_client.get_trips_for_date(target_date)
            trip_by_user = {str(t.get("user_id")): t for t in trips_on_date}
            
            results = []
            for user in active_users:
                user_id = user.get("id")
                full_name = user.get("full_name") or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                
                # Determine status
                status = "Presente"
                leave_request_id = None
                leave_type = None
                hours_worked = 8.0  # Default full day
                notes = None
                
                # Check if on leave
                if user_id in leave_by_user:
                    leave = leave_by_user[user_id]
                    leave_type = leave.get("leave_type_code", "")
                    
                    if leave_type.startswith("MAL"):
                        status = "Malattia"
                    elif leave_type in ("FER", "FERIE"):
                        status = "Ferie"
                    elif leave_type == "ROL":
                        status = "ROL"
                    elif leave_type in ("PER", "PERM"):
                        status = "Permesso"
                    else:
                        status = f"Assente ({leave_type})"
                    
                    leave_request_id = leave.get("id")
                    hours_worked = 0.0
                    notes = leave.get("notes")
                
                # Check if on trip
                elif user_id in trip_by_user:
                    status = "Trasferta"
                    hours_worked = 8.0  # Working in travel
                    notes = trip_by_user[user_id].get("destination")
                
                results.append({
                    "user_id": user_id,
                    "full_name": full_name,
                    "department": user.get("department"),
                    "status": status,
                    "hours_worked": hours_worked,
                    "leave_request_id": leave_request_id,
                    "leave_type": leave_type,
                    "notes": notes,
                })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching daily attendance details: {e}")
            return []

    async def get_aggregate_attendance_details(
        self,
        start_date: date,
        end_date: date,
        department: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get aggregate attendance statistics for all employees in a date range.
        
        Returns per-employee totals for worked days, leave types, etc.
        """
        try:
            # Get all active users
            users = await self._auth_client.get_users()
            active_users = [u for u in users if u.get("is_active", True)]
            
            # Filter by department if specified
            if department:
                active_users = [
                    u for u in active_users 
                    if u.get("department", "").lower() == department.lower()
                ]
            
            # Calculate working days in period
            working_days = await self._calendar_client.get_working_days_count(
                start_date, end_date
            )
            
            # Get holiday count
            holidays = await self._calendar_client.get_holidays(start_date, end_date)
            holiday_count = len(holidays) if holidays else 0
            
            results = []
            for user in active_users:
                user_id = UUID(user.get("id"))
                full_name = user.get("full_name") or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                
                # Get leave data for the period
                leave_data = await self._get_employee_leave_data(
                    user_id, start_date, end_date
                )
                
                # Calculate worked days
                vacation_days = leave_data.get("vacation", {}).get("days", 0)
                sick_days = leave_data.get("sick_leave", {}).get("days", 0)
                other = leave_data.get("other", {}).get("days", 0)
                rol_hours = leave_data.get("rol", {}).get("hours", 0)
                permit_hours = leave_data.get("permits", {}).get("hours", 0)
                
                # Convert ROL/permits to days (assuming 8h day)
                rol_days = rol_hours / 8.0
                permit_days = permit_hours / 8.0
                
                total_absence_days = vacation_days + sick_days + other + rol_days + permit_days
                worked_days = max(0, working_days - int(total_absence_days))
                
                results.append({
                    "user_id": str(user_id),
                    "full_name": full_name,
                    "department": user.get("department"),
                    "worked_days": worked_days,
                    "total_days": working_days,
                    "vacation_days": vacation_days,
                    "holiday_days": holiday_count,
                    "rol_hours": rol_hours,
                    "permit_hours": permit_hours,
                    "sick_days": sick_days,
                    "other_absences": other,
                })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching aggregate attendance: {e}")
            return []
