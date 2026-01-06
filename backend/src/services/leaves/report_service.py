from datetime import date, timedelta
from decimal import Decimal

from src.services.leaves.repository import LeaveRequestRepository
from src.services.leaves.calendar_utils import CalendarUtils

class LeaveReportService:
    """Service for leave attendance reports."""
    
    def __init__(self, session: AsyncSession, calendar_utils: CalendarUtils):
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._calendar = calendar_utils

    async def get_daily_attendance(self, request: DailyAttendanceRequest) -> DailyAttendanceResponse:
        """Get daily attendance report for HR."""
        # 1. Fetch users and leaves for the date
        users, leaves = await self._request_repo.get_attendance_data(request.date, request.department)
        leave_map = {l.user_id: l for l in leaves}
        
        # 3. Build response
        items = []
        total_present = 0
        total_absent = 0
        
        for user in users:
             leave = leave_map.get(user.id)
             if leave:
                 status = f"Assente ({leave.leave_type_code})"
                 # Determine hours
                 hours = Decimal(0)
                 if leave.start_date == request.date and leave.start_half_day:
                     hours = Decimal(4)
                 elif leave.end_date == request.date and leave.end_half_day:
                     hours = Decimal(4)
                     
                 total_absent += 1
                 item = DailyAttendanceItem(
                     user_id=user.id,
                     full_name=f"{user.first_name} {user.last_name}",
                     status=status,
                     hours_worked=hours,
                     leave_request_id=leave.id,
                     leave_type_code=leave.leave_type_code
                 )
             else:
                 status = "Presente"
                 hours = Decimal(8) 
                 total_present += 1
                 item = DailyAttendanceItem(
                     user_id=user.id,
                     full_name=f"{user.first_name} {user.last_name}",
                     status=status,
                     hours_worked=hours
                 )
             items.append(item)
             
        return DailyAttendanceResponse(
            date=request.date,
            items=items,
            total_present=total_present,
            total_absent=total_absent
        )

    async def get_aggregate_report(self, request: AggregateReportRequest) -> AggregateReportResponse:
        """Get aggregated attendance report for HR."""
        # 1. Fetch users and leaves
        users, all_leaves = await self._request_repo.get_aggregate_attendance_data(
            request.start_date, request.end_date, request.department
        )
        
        if not users:
            return AggregateReportResponse(start_date=request.start_date, end_date=request.end_date, items=[])
        
        # 3. Pre-calculate excluded days for the entire range
        period_days_data = await self._calendar.get_excluded_list(request.start_date, request.end_date)
        total_potential_days = period_days_data["working_days"]
        excluded_info = {d["date"]: d for d in period_days_data["excluded_days"]}
        excluded_dates = {d["date"] for d in period_days_data["excluded_days"]}
        
        items = []
        for user in users:
            user_leaves = [l for l in all_leaves if l.user_id == user.id]
            
            vacation_days = Decimal(0)
            holiday_days = Decimal(0)
            rol_hours = Decimal(0)
            permit_hours = Decimal(0)
            sick_days = Decimal(0)
            other_absences = Decimal(0)
            
            # Count holidays/closures in period
            user_dept = user.profile.department if user.profile else None
            for d_date, info in excluded_info.items():
                if request.start_date <= d_date <= request.end_date:
                    reason = info["reason"]
                    if reason == "holiday":
                        holiday_days += Decimal("1.0")
                    elif reason == "closure":
                        # Check department overlap
                        affected_depts = info.get("affected_departments")
                        if affected_depts and user_dept and user_dept not in affected_depts:
                            continue
                        
                        holiday_days += Decimal("1.0")
                        if info.get("consumes_balance"):
                            vacation_days += Decimal("1.0")

            for leave in user_leaves:
                # Calculate overlap days
                effective_start = max(leave.start_date, request.start_date)
                effective_end = min(leave.end_date, request.end_date)
                
                if effective_start <= effective_end:
                    # Count working days in overlap
                    overlap_working_days = Decimal(0)
                    curr = effective_start
                    while curr <= effective_end:
                        if curr not in excluded_dates:
                            overlap_working_days += Decimal("1.0")
                        curr += timedelta(days=1)
                    
                    # Adjust for half days
                    if effective_start == leave.start_date and leave.start_half_day:
                         if effective_start not in excluded_dates:
                            overlap_working_days -= Decimal("0.5")
                    if effective_end == leave.end_date and leave.end_half_day:
                         if effective_end not in excluded_dates:
                            overlap_working_days -= Decimal("0.5")
                        
                    # Map to categories
                    code = leave.leave_type_code
                    if code == "FER":
                        vacation_days += overlap_working_days
                    elif code == "ROL":
                        rol_hours += overlap_working_days * Decimal("8.0")
                    elif code in ["PAR", "PER"]:
                        permit_hours += overlap_working_days * Decimal("8.0") 
                    elif code == "MAL":
                        sick_days += overlap_working_days
                    else:
                        other_absences += overlap_working_days
            
            # 4. Calculate effectively worked days
            today = date.today()
            effective_end_for_worked = min(request.end_date, today)
            
            worked_days_count = Decimal(0)
            if request.start_date <= effective_end_for_worked:
                curr = request.start_date
                while curr <= effective_end_for_worked:
                    if curr not in excluded_dates:
                        # Check if user had an absence
                        has_absence = False
                        for leave in user_leaves:
                            if leave.start_date <= curr <= leave.end_date:
                                if leave.start_date == curr and leave.start_half_day:
                                    worked_days_count += Decimal("0.5")
                                    has_absence = True
                                elif leave.end_date == curr and leave.end_half_day:
                                    worked_days_count += Decimal("0.5")
                                    has_absence = True
                                else:
                                    has_absence = True
                                break
                        
                        if not has_absence:
                            worked_days_count += Decimal("1.0")
                    curr += timedelta(days=1)

            worked_days = float(worked_days_count)
            
            items.append(AggregateReportItem(
                user_id=user.id,
                full_name=f"{user.first_name} {user.last_name}",
                total_days=total_potential_days,
                worked_days=worked_days,
                vacation_days=vacation_days,
                holiday_days=holiday_days,
                rol_hours=rol_hours,
                permit_hours=permit_hours,
                sick_days=sick_days,
                other_absences=other_absences
            ))
            
        return AggregateReportResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            items=items
        )
