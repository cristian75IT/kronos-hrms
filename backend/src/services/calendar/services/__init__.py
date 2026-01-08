"""
KRONOS - Calendar Services Package

Modular calendar service architecture for enterprise maintainability.

This package splits the monolithic CalendarService (~1110 lines) into focused modules:
- base.py: Shared utilities, location config, holiday calculations (~165 lines)
- calendars.py: Personal calendars CRUD and sharing (~245 lines)
- events.py: Calendar events CRUD (~230 lines)
- profiles.py: Work week and holiday profiles (~305 lines)

Usage:
    from src.services.calendar.services import CalendarService
    
    service = CalendarService(db)
    events = await service.get_visible_events(user_id)
"""
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import (
    Calendar, CalendarEvent, CalendarClosure, WorkingDayException,
    LocationCalendar, HolidayProfile
)
from src.services.calendar import schemas
from src.shared.audit_client import get_audit_logger
from src.shared.clients import LeavesClient

# Import sub-services
from src.services.calendar.services.base import BaseCalendarService
from src.services.calendar.services.calendars import CalendarManagementService
from src.services.calendar.services.events import CalendarEventService
from src.services.calendar.services.profiles import CalendarProfileService

import logging

logger = logging.getLogger(__name__)


class CalendarService(BaseCalendarService):
    """
    Unified Calendar Service façade.
    
    Delegates to specialized sub-services while maintaining backward compatibility.
    
    Sub-services:
    - _calendars: Personal calendar management
    - _events: Calendar events CRUD
    - _profiles: Work week and holiday profiles
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        
        # Initialize sub-services
        self._calendars = CalendarManagementService(db)
        self._events = CalendarEventService(db)
        self._profiles = CalendarProfileService(db)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Calendar Management (delegated to CalendarManagementService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_calendars(self, user_id: UUID) -> List[Calendar]:
        return await self._calendars.get_calendars(user_id)
    
    async def create_calendar(self, user_id: UUID, data: schemas.CalendarCreate) -> Calendar:
        return await self._calendars.create_calendar(user_id, data)
    
    async def update_calendar(self, user_id: UUID, calendar_id: UUID, data: schemas.CalendarUpdate) -> Calendar:
        return await self._calendars.update_calendar(user_id, calendar_id, data)
    
    async def delete_calendar(self, user_id: UUID, calendar_id: UUID) -> bool:
        return await self._calendars.delete_calendar(user_id, calendar_id)
    
    async def share_calendar(self, calendar_id: UUID, user_id: UUID, shared_with_user_id: UUID, permission):
        return await self._calendars.share_calendar(calendar_id, user_id, shared_with_user_id, permission)
    
    async def unshare_calendar(self, calendar_id: UUID, user_id: UUID, shared_with_user_id: UUID) -> bool:
        return await self._calendars.unshare_calendar(calendar_id, user_id, shared_with_user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Events (delegated to CalendarEventService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_visible_events(
        self, 
        user_id: UUID, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        event_type: Optional[str] = None
    ) -> List[CalendarEvent]:
        return await self._events.get_visible_events(user_id, start_date, end_date, event_type)
    
    async def get_event(self, event_id: UUID) -> Optional[CalendarEvent]:
        return await self._events.get_event(event_id)
    
    async def create_event(self, user_id: UUID, data: schemas.EventCreate) -> CalendarEvent:
        return await self._events.create_event(user_id, data)
    
    async def update_event(self, event_id: UUID, data: schemas.EventUpdate, user_id: UUID) -> CalendarEvent:
        return await self._events.update_event(event_id, data, user_id)
    
    async def delete_event(self, event_id: UUID, user_id: UUID) -> bool:
        return await self._events.delete_event(event_id, user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Profiles (delegated to CalendarProfileService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_work_week_profiles(self):
        return await self._profiles.get_work_week_profiles()
    
    async def get_work_week_profile(self, id: UUID):
        return await self._profiles.get_work_week_profile(id)
    
    async def create_work_week_profile(self, data: schemas.WorkWeekProfileCreate):
        return await self._profiles.create_work_week_profile(data)
    
    async def update_work_week_profile(self, id: UUID, data: schemas.WorkWeekProfileUpdate):
        return await self._profiles.update_work_week_profile(id, data)
    
    async def delete_work_week_profile(self, id: UUID) -> bool:
        return await self._profiles.delete_work_week_profile(id)
    
    async def get_holiday_profiles(self):
        return await self._profiles.get_holiday_profiles()
    
    async def get_holiday_profile(self, id: UUID):
        return await self._profiles.get_holiday_profile(id)
    
    async def create_holiday_profile(self, data: schemas.HolidayProfileCreate):
        return await self._profiles.create_holiday_profile(data)
    
    async def update_holiday_profile(self, id: UUID, data: schemas.HolidayProfileUpdate):
        return await self._profiles.update_holiday_profile(id, data)
    
    async def delete_holiday_profile(self, id: UUID) -> bool:
        return await self._profiles.delete_holiday_profile(id)
    
    async def get_holidays_in_profile(self, profile_id: UUID):
        return await self._profiles.get_holidays_in_profile(profile_id)
    
    async def create_holiday(self, profile_id: UUID, data: schemas.HolidayCreate):
        return await self._profiles.create_holiday(profile_id, data)
    
    async def update_holiday(self, id: UUID, data: schemas.HolidayUpdate):
        return await self._profiles.update_holiday(id, data)
    
    async def delete_holiday(self, id: UUID) -> bool:
        return await self._profiles.delete_holiday(id)
    
    async def get_location_calendars(self):
        return await self._profiles.get_location_calendars()
    
    async def create_location_calendar(self, data: schemas.LocationCalendarCreate):
        return await self._profiles.create_location_calendar(data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Working Days Calculation (in main service - core logic)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def calculate_working_days(
        self, 
        start_date: date, 
        end_date: date, 
        location_id: Optional[UUID] = None,
        exclude_holidays: bool = True,
        exclude_closures: bool = True
    ) -> schemas.WorkingDaysResponse:
        """Calculate working days between two dates based on location profile."""
        config = await self._get_location_config(location_id)
        work_days_mask = self._get_working_days_mask(config)
        
        holidays_set = set()
        if exclude_holidays:
            holidays_set = await self._get_location_holidays(config, start_date.year, end_date.year)
        
        working_days_count = 0
        total_days = (end_date - start_date).days + 1
        holiday_list = []
        weekend_list = []
        
        current_date = start_date
        while current_date <= end_date:
            weekday_idx = current_date.weekday()  # 0=Mon, 6=Sun
            is_working = work_days_mask[weekday_idx]
            is_holiday = current_date in holidays_set
            
            if not is_working:
                weekend_list.append(current_date)
            
            if is_holiday:
                holiday_list.append(current_date)
            
            if is_working and not is_holiday:
                working_days_count += 1
            
            current_date += timedelta(days=1)
        
        return schemas.WorkingDaysResponse(
            start_date=start_date,
            end_date=end_date,
            total_calendar_days=total_days,
            working_days=working_days_count,
            holidays=sorted(list(holidays_set)),
            closure_days=[],
            weekend_days=weekend_list
        )
    
    async def is_working_day(self, check_date: date, location_id: Optional[UUID] = None) -> bool:
        """Check if a specific date is a working day."""
        res = await self.calculate_working_days(check_date, check_date, location_id)
        return res.working_days > 0
    
    # ═══════════════════════════════════════════════════════════════════════
    # System Holidays & Closures (remain in main service)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_system_holidays(self, year: int) -> List[Dict[str, Any]]:
        """Get all holidays from System calendars for a given year."""
        profiles = await self._holiday_repo.get_all()
        
        holidays_list = []
        for profile in profiles:
            for hol in (profile.holidays or []):
                if hol.is_recurring and hol.recurrence_rule:
                    calc_date = self._calculate_recurrence(hol.recurrence_rule, year)
                    if calc_date:
                        holidays_list.append({
                            "id": str(hol.id),
                            "date": calc_date.isoformat(),
                            "name": hol.name,
                            "type": "holiday",
                            "is_confirmed": True,
                        })
                elif hol.date and hol.date.year == year:
                    holidays_list.append({
                        "id": str(hol.id),
                        "date": hol.date.isoformat(),
                        "name": hol.name,
                        "type": "holiday",
                        "is_confirmed": True,
                    })
        
        return sorted(holidays_list, key=lambda x: x["date"])
    
    async def get_location_closures(self, year: int, location_id: Optional[UUID]) -> List[Dict[str, Any]]:
        """Get closures for a location."""
        closures = await self._closure_repo.get_by_year(year, location_id)
        
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
                "type": "closure",
                "location_id": str(c.location_id) if c.location_id else None,
            }
            for c in closures
        ]
    
    async def create_closure(self, data: schemas.ClosureCreate) -> CalendarClosure:
        """Create a company closure."""
        from uuid import uuid4
        closure = CalendarClosure(
            id=uuid4(),
            **data.model_dump()
        )
        await self._closure_repo.create(closure)
        await self.db.commit()
        await self.db.refresh(closure)
        
        await self._audit.log_action(
            action="CREATE",
            resource_type="CLOSURE",
            resource_id=str(closure.id),
            description=f"Created closure: {closure.name}",
            request_data=data.model_dump(mode="json")
        )
        
        return closure
    
    async def update_closure(self, id: UUID, data: schemas.ClosureUpdate) -> CalendarClosure:
        """Update a closure."""
        from src.services.calendar.exceptions import ClosureNotFound
        
        closure = await self._closure_repo.get(id)
        
        if not closure:
            raise ClosureNotFound(id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(closure, key, value)
        
        await self._closure_repo.update(closure)
        await self.db.commit()
        await self.db.refresh(closure)
        
        await self._audit.log_action(
            action="UPDATE",
            resource_type="CLOSURE",
            resource_id=str(id),
            description=f"Updated closure: {closure.name}",
            request_data=update_data
        )
        
        return closure
    
    async def delete_closure(self, id: UUID) -> bool:
        """Delete a closure."""
        closure = await self._closure_repo.get(id)
        
        if closure:
            await self._closure_repo.delete(closure)
            await self.db.commit()
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Calendar Range Aggregator
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_calendar_range(
        self, 
        user_id: UUID, 
        start_date: date, 
        end_date: date,
        location_id: Optional[UUID] = None
    ) -> schemas.CalendarRangeView:
        """Produce an aggregated range view by day."""
        
        # 1. Fetch all raw data first
        
        # Holidays
        raw_holidays = []
        for year in range(start_date.year, end_date.year + 1):
            raw_holidays.extend(await self.get_system_holidays(year))
            
        # Closures
        raw_closures = []
        for year in range(start_date.year, end_date.year + 1):
            raw_closures.extend(await self.get_location_closures(year, location_id))
            
        # Events (User Visible)
        events = await self.get_visible_events(user_id, start_date, end_date)
        
        # Leaves
        leaves = []
        try:
            leaves_client = LeavesClient()
            leaves_data = await leaves_client.get_leaves_in_period(
                start_date=start_date, 
                end_date=end_date, 
                user_id=user_id
            )
            # Normalize leaves data
            for lv in leaves_data:
                l_start = date.fromisoformat(lv["start_date"]) if isinstance(lv["start_date"], str) else lv["start_date"]
                l_end = date.fromisoformat(lv["end_date"]) if isinstance(lv["end_date"], str) else lv["end_date"]
                leaves.append({
                    **lv,
                    "start_date": l_start,
                    "end_date": l_end
                })
        except Exception as e:
            logger.warning(f"Failed to fetch leaves: {e}")

        # 2. Prepare Working Day Utils
        config = await self._get_location_config(location_id)
        work_days_mask = self._get_working_days_mask(config)
        
        # We need a set of holiday dates for rapid lookup during the loop
        holiday_dates = {date.fromisoformat(h["date"]) for h in raw_holidays}

        # 3. Iterate Day by Day
        days_views = []
        working_days_count = 0
        
        current = start_date
        while current <= end_date:
            day_items = []
            
            # -- Check Holiday --
            is_holiday_today = current in holiday_dates
            holiday_today = next((h for h in raw_holidays if date.fromisoformat(h["date"]) == current), None)
            
            if holiday_today:
                day_items.append(schemas.CalendarDayItem(
                    id=UUID(holiday_today["id"]) if holiday_today.get("id") else None,
                    title=holiday_today["name"],
                    item_type="holiday",
                    date=current,
                    is_all_day=True,
                    metadata={"scope": "national"} 
                ))

            # -- Check Work Day --
            weekday_idx = current.weekday()
            is_working_schedule = work_days_mask[weekday_idx]
            is_working_day = is_working_schedule and not is_holiday_today
            
            if is_working_day:
                working_days_count += 1
                
            # -- Check Closures --
            for c in raw_closures:
                c_start = date.fromisoformat(c["start_date"])
                c_end = date.fromisoformat(c["end_date"])
                if c_start <= current <= c_end:
                    day_items.append(schemas.CalendarDayItem(
                        id=UUID(c["id"]) if c.get("id") else None,
                        title=c["name"],
                        item_type="closure",
                        date=current,
                        is_all_day=True,
                        metadata={
                            "closure_id": c["id"],
                            "location_id": c.get("location_id")
                        }
                    ))
            
            # -- Check Events --
            for e in events:
                if e.start_date <= current <= e.end_date:
                    day_items.append(schemas.CalendarDayItem(
                        id=e.id,
                        title=e.title,
                        item_type=e.event_type or "event",
                        date=current,
                        start_date=e.start_date,
                        start_time=e.start_time,
                        end_time=e.end_time,
                        is_all_day=e.is_all_day,
                        color=e.color, 
                        metadata={
                            "calendar_id": str(e.calendar_id) if e.calendar_id else None,
                            "location": e.location,
                            "visibility": e.visibility,
                            "status": e.status,
                            "is_virtual": e.is_virtual,
                            "meeting_url": e.meeting_url
                        }
                    ))
                    
            # -- Check Leaves --
            for lv in leaves:
                if lv["start_date"] <= current <= lv["end_date"]:
                     day_items.append(schemas.CalendarDayItem(
                        id=UUID(lv["id"]) if "id" in lv else None,
                        title=lv.get("leave_type_code", "Ferie"),
                        item_type="leave",
                        date=current,
                        is_all_day=True,
                        metadata={
                            "leave_type_code": lv.get("leave_type_code"),
                            "status": lv.get("status")
                        }
                    ))

            days_views.append(schemas.CalendarDayView(
                date=current,
                is_working_day=is_working_day,
                is_holiday=is_holiday_today,
                holiday_name=holiday_today["name"] if holiday_today else None,
                items=day_items
            ))
            
            current += timedelta(days=1)
            
        return schemas.CalendarRangeView(
            start_date=start_date,
            end_date=end_date,
            days=days_views,
            working_days_count=working_days_count
        )

    # ═══════════════════════════════════════════════════════════════════════
    # Working Day Exceptions
    # ═══════════════════════════════════════════════════════════════════════

    async def get_working_day_exceptions(self, year: int, location_id: Optional[UUID] = None) -> List[WorkingDayException]:
        """Get all working day exceptions for a year."""
        return await self._ex_repo.get_by_year(year, location_id)

    async def create_working_day_exception(self, data: schemas.WorkingDayExceptionCreate) -> WorkingDayException:
        """Create a new working day exception."""
        exception = WorkingDayException(
            id=uuid4(),
            **data.model_dump()
        )
        await self._ex_repo.create(exception)
        await self.db.commit()
        await self.db.refresh(exception)

        await self._audit.log_action(
            action="CREATE",
            resource_type="WORKING_DAY_EXCEPTION",
            resource_id=str(exception.id),
            description=f"Created working day exception for {exception.date}",
            request_data=data.model_dump(mode="json")
        )

        return exception

    async def delete_working_day_exception(self, exception_id: UUID) -> bool:
        """Delete a working day exception."""
        exception = await self._ex_repo.get(exception_id)
        if exception:
            await self._ex_repo.delete(exception)
            await self.db.commit()
            
            await self._audit.log_action(
                action="DELETE",
                resource_type="WORKING_DAY_EXCEPTION",
                resource_id=str(exception_id),
                description=f"Deleted working day exception for {exception.date}"
            )
            return True
        return False


# Export for backward compatibility
__all__ = [
    "CalendarService",
    "CalendarManagementService",
    "CalendarEventService",
    "CalendarProfileService",
]
