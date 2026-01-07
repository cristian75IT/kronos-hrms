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
from sqlalchemy import select, and_, desc

from src.services.auth.models import EmployeeContract
from src.services.config.models import NationalContractVersion

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

    async def get_excluded_days(self, start_date: date, end_date: date, user_id: Optional[UUID] = None) -> dict:
        """Get detailed list of excluded days (weekends, holidays, closures) in a date range."""
        count_saturday = False
        if user_id:
            count_saturday = await self._get_saturday_rule(user_id, start_date)
            
        # We need to expose count_saturday to CalendarUtils.get_excluded_list/days_data
        # Note: CalendarUtils.get_excluded_list internally calls get_excluded_days_data which accepts count_saturday
        # But get_excluded_list signature doesn't expose it. We should call get_excluded_days_data directly and format here
        # OR assume get_excluded_list handles it?
        # looking at utils code, get_excluded_list DOES NOT accept count_saturday.
        # So we should call get_excluded_days_data manually.
        
        data = await self._calendar_utils.get_excluded_days_data(start_date, end_date, user_id, count_saturday=count_saturday)
        
        # Format for UI (same as get_excluded_list)
        details = data["details"]
        sorted_keys = sorted(details.keys())
        excluded_list = []
        for k in sorted_keys:
            val = details[k]
            item = {
                "date": val["date"],
                "reason": val["reason"],
                "name": val["name"]
            }
            if val["info"]:
                item.update(val["info"])
            excluded_list.append(item)
            
        return {
            "start_date": start_date,
            "end_date": end_date,
            "working_days": data["working_days_count"],
            "excluded_days": excluded_list
        }

    async def calculate_preview(self, request: DaysCalculationRequest, user_id: Optional[UUID] = None) -> DaysCalculationResponse:
        """Preview working days calculation."""
        count_saturday = False
        if user_id:
            count_saturday = await self._get_saturday_rule(user_id, request.start_date)

        days = await self._calendar_utils.calculate_working_days(
            request.start_date,
            request.end_date,
            request.start_half_day,
            request.end_half_day,
            user_id=user_id,
            count_saturday=count_saturday
        )
        
        return DaysCalculationResponse(
            days=days,
            hours=days * Decimal("8"), # Approximation
            message=f"Calcolati {days} giorni lavorativi escludendo festività e chiusure."
        )

    async def _get_saturday_rule(self, user_id: UUID, date_ref: date) -> bool:
        """Check if Saturday should be counted as leave for the user at given date."""
        try:
            # 1. Find active employee contract
            query = select(EmployeeContract).where(
                and_(
                    EmployeeContract.user_id == user_id,
                    EmployeeContract.start_date <= date_ref,
                    # Handle NULL end_date (active indefinitely)
                    # or end_date >= date_ref
                    (EmployeeContract.end_date.is_(None) | (EmployeeContract.end_date >= date_ref))
                )
            ).order_by(desc(EmployeeContract.start_date)).limit(1)
            
            contract = await self._session.scalar(query)
            if not contract or not contract.national_contract_id:
                return False
                
            # 2. Find active national contract version
            # We need the version valid at date_ref
            query_nc = select(NationalContractVersion).where(
                and_(
                    NationalContractVersion.national_contract_id == contract.national_contract_id,
                    NationalContractVersion.valid_from <= date_ref,
                    (NationalContractVersion.valid_to.is_(None) | (NationalContractVersion.valid_to >= date_ref))
                )
            ).order_by(desc(NationalContractVersion.valid_from)).limit(1)
            
            version = await self._session.scalar(query_nc)
            if version:
                return version.count_saturday_as_leave
                
            return False
        except Exception as e:
            print(f"Error fetching Saturday rule for user {user_id}: {e}")
            return False

    def _get_event_color(self, status: LeaveRequestStatus, leave_type: str) -> str:
        """Get color for calendar event."""
        status_colors = {
            LeaveRequestStatus.APPROVED: "#22C55E",       # Green
            LeaveRequestStatus.PENDING: "#F59E0B",        # Orange
            LeaveRequestStatus.APPROVED_CONDITIONAL: "#EAB308",  # Yellow
        }
        return status_colors.get(status, "#3B82F6")
