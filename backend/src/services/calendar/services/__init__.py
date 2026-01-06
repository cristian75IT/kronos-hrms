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
from uuid import UUID

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
        stmt = select(HolidayProfile).options(
            selectinload(HolidayProfile.holidays)
        )
        result = await self.db.execute(stmt)
        profiles = result.scalars().all()
        
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
        stmt = select(CalendarClosure).where(
            and_(
                or_(
                    CalendarClosure.location_id == location_id,
                    CalendarClosure.location_id == None  # Company-wide closures
                ),
                CalendarClosure.start_date >= date(year, 1, 1),
                CalendarClosure.end_date <= date(year, 12, 31),
            )
        )
        result = await self.db.execute(stmt)
        closures = result.scalars().all()
        
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
        self.db.add(closure)
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
        stmt = select(CalendarClosure).where(CalendarClosure.id == id)
        result = await self.db.execute(stmt)
        closure = result.scalar_one_or_none()
        
        if not closure:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Closure not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(closure, key, value)
        
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
        stmt = select(CalendarClosure).where(CalendarClosure.id == id)
        result = await self.db.execute(stmt)
        closure = result.scalar_one_or_none()
        
        if closure:
            await self.db.delete(closure)
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
    ) -> schemas.CalendarRangeResponse:
        """Produce an aggregated range view including holidays, closures, and user events."""
        
        # Get holidays
        holidays = []
        for year in range(start_date.year, end_date.year + 1):
            year_holidays = await self.get_system_holidays(year)
            for h in year_holidays:
                hdate = date.fromisoformat(h["date"])
                if start_date <= hdate <= end_date:
                    holidays.append(schemas.CalendarDayItem(
                        date=hdate,
                        type="holiday",
                        title=h["name"],
                    ))
        
        # Get closures
        closures = []
        for year in range(start_date.year, end_date.year + 1):
            year_closures = await self.get_location_closures(year, location_id)
            for c in year_closures:
                cstart = date.fromisoformat(c["start_date"])
                cend = date.fromisoformat(c["end_date"])
                if cstart <= end_date and cend >= start_date:
                    closures.append(schemas.CalendarDayItem(
                        date=cstart,
                        end_date=cend,
                        type="closure",
                        title=c["name"],
                    ))
        
        # Get user events
        events = await self.get_visible_events(user_id, start_date, end_date)
        event_items = [
            schemas.CalendarDayItem(
                date=e.start_date,
                end_date=e.end_date,
                type=e.event_type or "event",
                title=e.title,
                event_id=e.id,
            )
            for e in events
        ]
        
        # Get leaves (from leave service)
        leaves = []
        try:
            leaves_client = LeavesClient()
            leaves_data = await leaves_client.get_user_leaves(user_id, start_date, end_date)
            for lv in leaves_data:
                leaves.append(schemas.CalendarDayItem(
                    date=date.fromisoformat(lv["start_date"]) if isinstance(lv["start_date"], str) else lv["start_date"],
                    end_date=date.fromisoformat(lv["end_date"]) if isinstance(lv["end_date"], str) else lv["end_date"],
                    type="leave",
                    title=lv.get("leave_type_code", "Ferie"),
                    leave_type_code=lv.get("leave_type_code"),
                    status=lv.get("status"),
                ))
        except Exception as e:
            logger.warning(f"Failed to fetch leaves: {e}")
        
        return schemas.CalendarRangeResponse(
            start_date=start_date,
            end_date=end_date,
            holidays=holidays,
            closures=closures,
            events=event_items,
            leaves=leaves,
        )


# Export for backward compatibility
__all__ = [
    "CalendarService",
    "CalendarManagementService",
    "CalendarEventService",
    "CalendarProfileService",
]
