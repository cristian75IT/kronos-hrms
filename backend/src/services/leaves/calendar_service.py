from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from src.services.leaves.schemas import (
    CalendarRequest,
    CalendarResponse,
    CalendarEvent,
    DaysCalculationRequest,
    DaysCalculationResponse,
)
from src.services.leaves.models import LeaveRequestStatus
from src.services.leaves.repository import LeaveRequestRepository
from src.services.leaves.calendar_utils import CalendarUtils
from src.shared.clients import AuthClient
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

class LeaveCalendarService:
    """Service for calendar views and day calculations."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._auth_client = AuthClient()
        # Initializes CalendarUtils internally or injected?
        # Better to have it injected, but for simplicity consistent with LeaveService:
        from src.shared.clients import ConfigClient
        self._calendar_utils = CalendarUtils(ConfigClient())

    async def get_calendar(
        self,
        request: CalendarRequest,
        user_id: UUID,
        is_manager: bool = False,
    ) -> CalendarResponse:
        """Get calendar events for FullCalendar."""
        events = []
        
        # Determine which users to include
        user_ids = [user_id]
        if request.include_team and is_manager:
            # Get subordinates from auth service
            subordinates = await self._auth_client.get_subordinates(user_id)
            user_ids.extend(subordinates)
        
        # Get requests
        requests = await self._request_repo.get_by_date_range(
            start_date=request.start_date,
            end_date=request.end_date,
            user_ids=user_ids,
            status=[
                LeaveRequestStatus.APPROVED,
                LeaveRequestStatus.PENDING,
                LeaveRequestStatus.APPROVED_CONDITIONAL,
            ],
        )
        
        for req in requests:
            color = self._get_event_color(req.status, req.leave_type_code)
            events.append(CalendarEvent(
                id=str(req.id),
                title=f"{req.leave_type_code}",
                start=req.start_date,
                end=req.end_date,
                color=color,
                extendedProps={
                    "status": req.status.value,
                    "days": float(req.days_requested),
                    "user_id": str(req.user_id),
                },
            ))
        
        # Get holidays
        holidays = []
        if request.include_holidays:
            years = {request.start_date.year, request.end_date.year}
            raw_holidays = []
            for y in years:
                y_holidays = await self._calendar_utils.get_holidays(
                    y,
                    request.start_date,
                    request.end_date,
                )
                raw_holidays.extend(y_holidays)
            
            # Deduplicate by ID
            seen_ids = set()
            unique_raw_holidays = []
            for h in raw_holidays:
                if isinstance(h, dict) and h.get('id') and h.get('id') not in seen_ids:
                    seen_ids.add(h['id'])
                    unique_raw_holidays.append(h)

            holidays = [
                CalendarEvent(
                    id=f"hol_{h['id']}",
                    title=h['name'],
                    start=h['date'],
                    end=h['date'] + timedelta(days=1) if isinstance(h['date'], date) else (date.fromisoformat(h['date']) + timedelta(days=1)).isoformat() if isinstance(h['date'], str) else h['date'],
                    allDay=True,
                    color="#EF4444" if h.get('is_national') else "#3B82F6" if h.get('is_regional') else "#F59E0B",
                    extendedProps={
                        "type": "holiday",
                        "is_national": h.get('is_national', False),
                        "is_regional": h.get('is_regional', False),
                    }
                )
                for h in unique_raw_holidays
                if isinstance(h, dict) and 'id' in h and 'name' in h and 'date' in h
            ]
        
        # Get company closures
        closures = []
        raw_closures = await self._calendar_utils.get_company_closures(request.start_date, request.end_date)
        for closure in raw_closures:
            closure_start = closure.get("start_date")
            closure_end = closure.get("end_date")
            if closure_start and closure_end:
                # Convert to date objects to add 1 day to end (since FullCalendar end is exclusive)
                try:
                    c_start = date.fromisoformat(closure_start) if isinstance(closure_start, str) else closure_start
                    c_end = date.fromisoformat(closure_end) if isinstance(closure_end, str) else closure_end
                    c_end_exclusive = c_end + timedelta(days=1)
                except (ValueError, TypeError):
                    c_start = closure_start
                    c_end_exclusive = closure_end

                closures.append(CalendarEvent(
                    id=f"closure_{closure.get('id', 'unknown')}",
                    title=closure.get('name', 'Chiusura'),
                    start=c_start,
                    end=c_end_exclusive,
                    allDay=True,
                    color="#9333EA",  # Purple for closures
                    extendedProps={
                        "type": "closure",
                        "closure_type": closure.get('closure_type', 'total'),
                        "is_paid": closure.get('is_paid', True),
                        "consumes_leave_balance": closure.get('consumes_leave_balance', False),
                        "description": closure.get('description', ''),
                    }
                ))
            
        return CalendarResponse(events=events, holidays=holidays, closures=closures)

    async def get_excluded_days(self, start_date: date, end_date: date) -> dict:
        """Get detailed list of excluded days (weekends, holidays, closures) in a date range."""
        return await self._calendar_utils.get_excluded_list(start_date, end_date)

    async def calculate_preview(self, request: DaysCalculationRequest) -> DaysCalculationResponse:
        """Preview working days calculation."""
        days = await self._calendar_utils.calculate_working_days(
            request.start_date,
            request.end_date,
            request.start_half_day,
            request.end_half_day,
        )
        
        return DaysCalculationResponse(
            days=days,
            hours=days * Decimal("8"), # Approximation
            message=f"Calcolati {days} giorni lavorativi escludendo festività e chiusure."
        )

    def _get_event_color(self, status: LeaveRequestStatus, leave_type: str) -> str:
        """Get color for calendar event."""
        status_colors = {
            LeaveRequestStatus.APPROVED: "#22C55E",       # Green
            LeaveRequestStatus.PENDING: "#F59E0B",        # Orange
            LeaveRequestStatus.APPROVED_CONDITIONAL: "#EAB308",  # Yellow
        }
        return status_colors.get(status, "#3B82F6")
