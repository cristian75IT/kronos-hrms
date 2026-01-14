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

    async def get_employee_daily_attendance_range(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Get daily attendance data for a specific employee over a date range.
        
        Returns a list of daily attendance records with status, hours, etc.
        Used primarily for generating monthly timesheets.
        """
        try:
            from datetime import timedelta
            
            # Get employee info
            user = await self._auth_client.get_user(str(employee_id))
            if not user:
                logger.warning(f"User {employee_id} not found")
                return []
            
            # Get all leaves for this employee in the period
            leaves = await self._leaves_client.get_leaves_in_period(
                start_date=start_date,
                end_date=end_date,
                user_id=employee_id,
                status="APPROVED"  # Only approved leaves count
            )
            
            # Try to get trips - the endpoint might not exist
            trips = []
            try:
                trips_response = await self._expense_client.get_safe(
                    "/api/v1/trips/internal/in-period",
                    default=[],
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "user_id": str(employee_id),
                    }
                )
                trips = trips_response if trips_response else []
            except Exception as e:
                logger.debug(f"Could not fetch trips for employee {employee_id}: {e}")
            
            # Build a dictionary of leaves by date
            leaves_by_date = {}
            for leave in leaves:
                leave_start = leave.get("start_date")
                leave_end = leave.get("end_date")
                
                # Handle date parsing if needed
                if isinstance(leave_start, str):
                    from datetime import datetime
                    leave_start = datetime.fromisoformat(leave_start.replace('Z', '+00:00')).date()
                if isinstance(leave_end, str):
                    from datetime import datetime
                    leave_end = datetime.fromisoformat(leave_end.replace('Z', '+00:00')).date()
                
                # Add this leave to each day it covers
                current = leave_start
                while current <= leave_end:
                    if start_date <= current <= end_date:
                        leaves_by_date[current] = leave
                    current += timedelta(days=1)
            
            # Build a dictionary of trips by date
            trips_by_date = {}
            for trip in trips:
                trip_start = trip.get("start_date")
                trip_end = trip.get("end_date")
                
                # Handle date parsing if needed
                if isinstance(trip_start, str):
                    from datetime import datetime
                    trip_start = datetime.fromisoformat(trip_start.replace('Z', '+00:00')).date()
                if isinstance(trip_end, str):
                    from datetime import datetime
                    trip_end = datetime.fromisoformat(trip_end.replace('Z', '+00:00')).date()
                
                # Add this trip to each day it covers
                current = trip_start
                while current <= trip_end:
                    if start_date <= current <= end_date:
                        trips_by_date[current] = trip
                    current += timedelta(days=1)
            
            # Get holidays for the period
            holidays = []
            try:
                holidays = await self._calendar_client.get_holidays(
                    year=start_date.year,
                    start_date=start_date,
                    end_date=end_date
                )
            except Exception as e:
                logger.warning(f"Could not fetch holidays: {e}")

            holiday_dates = set()
            for h in holidays:
                try:
                    h_date = h.get("date")
                    if isinstance(h_date, str):
                        from datetime import datetime
                        h_date = datetime.fromisoformat(h_date).date()
                    holiday_dates.add(h_date)
                except:
                    pass

            # Build daily records
            results = []
            current_date = start_date
            
            while current_date <= end_date:
                # Determine status for this day
                status = "Presente"
                leave_type = None
                hours_worked = 8.0
                hours_expected = 8.0
                notes = None
                
                # Check if on leave
                if current_date in leaves_by_date:
                    leave = leaves_by_date[current_date]
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
                    
                    hours_worked = 0.0
                    notes = leave.get("notes")
                
                # Check if on trip
                elif current_date in trips_by_date:
                    status = "Trasferta"
                    hours_worked = 8.0
                    trip = trips_by_date[current_date]
                    notes = trip.get("destination")
                
                # Check if weekend or holiday
                weekday = current_date.weekday()
                if weekday >= 5:  # Saturday or Sunday
                    status = "Weekend"
                    hours_worked = 0.0
                    hours_expected = 0.0
                elif current_date in holiday_dates:
                    status = "Festività"
                    hours_worked = 0.0
                    hours_expected = 0.0
                
                results.append({
                    "date": current_date,
                    "status": status,
                    "hours_worked": hours_worked,
                    "hours_expected": hours_expected,
                    "leave_type": leave_type,
                    "notes": notes,
                    "weekday": weekday,
                })
                
                current_date += timedelta(days=1)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching employee daily attendance: {e}", exc_info=True)
            return []
