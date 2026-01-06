"""KRONOS Calendar Service - Enterprise Implementation."""
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Calendar, 
    HolidayProfile, 
    CalendarHoliday, 
    LocationCalendar, 
    WorkWeekProfile, 
    LocationSubscription, 
    CalendarType,
    CalendarShare,
    CalendarPermission,
    CalendarClosure,
    WorkingDayException,
    CalendarEvent, 
    EventParticipant
)
from src.services.calendar import schemas
from src.services.calendar.repository import (
    CalendarRepository,
    CalendarShareRepository,
    CalendarEventRepository,
    WorkWeekProfileRepository,
    HolidayProfileRepository,
    CalendarHolidayRepository,
    LocationCalendarRepository,
    CalendarClosureRepository,
    WorkingDayExceptionRepository
)
from src.shared.audit_client import get_audit_logger
from src.shared.clients import LeavesClient

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db # Kept for transaction management (commit) if needed, though repos handle flush. 
        # Ideally service manages unit of work (commit).
        
        self.calendar_repo = CalendarRepository(db)
        self.share_repo = CalendarShareRepository(db)
        self.event_repo = CalendarEventRepository(db)
        self.work_week_repo = WorkWeekProfileRepository(db)
        self.holiday_profile_repo = HolidayProfileRepository(db)
        self.holiday_repo = CalendarHolidayRepository(db)
        self.location_repo = LocationCalendarRepository(db)
        self.closure_repo = CalendarClosureRepository(db)
        self.exception_repo = WorkingDayExceptionRepository(db)
        
        self._audit = get_audit_logger("calendar-service")

    # ════════════════════════════════════════════════
    # CORE CALCULATION ENGINE
    # ════════════════════════════════════════════════

    async def calculate_working_days(
        self, 
        start_date: date, 
        end_date: date, 
        location_id: Optional[UUID] = None,
        exclude_holidays: bool = True,
        exclude_closures: bool = True
    ) -> schemas.WorkingDaysResponse:
        """
        Calculate working days between two dates based on location profile.
        """
        # 1. Load Configuration
        config = await self._get_location_config(location_id)
        work_week = config.work_week_profile.weekly_config
        
        # 2. Load Holidays and Closures if requested
        holidays_set = set()
        
        if exclude_holidays:
             holidays = await self._get_location_holidays(config, start_date.year, end_date.year)
             holidays_set = {h.date for h in holidays if start_date <= h.date <= end_date}
             
        # TODO: Implement closure events fetching from subscribed calendars properly
        # For now, we rely on the implementation in get_location_closures if called separately
        
        # 3. Iterate and Count
        working_days_count = 0
        total_days = (end_date - start_date).days + 1
        
        current_date = start_date
        holiday_list = []
        weekend_list = []
        
        WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        while current_date <= end_date:
            # Use weekday() (0-6) to ensure locale independence
            weekday_idx = current_date.weekday()
            weekday_name = WEEKDAYS[weekday_idx]
            
            day_config = work_week.get(weekday_name, {"is_working": False})
            
            is_weekend = not day_config.get("is_working", False)
            is_holiday = current_date in holidays_set
            
            if is_weekend:
                weekend_list.append(current_date)
            
            if is_holiday:
                holiday_list.append(current_date)
            
            if not is_weekend and not is_holiday:
                working_days_count += 1
            
            current_date += timedelta(days=1)

        return schemas.WorkingDaysResponse(
            start_date=start_date,
            end_date=end_date,
            total_calendar_days=total_days,
            working_days=working_days_count,
            holidays=sorted(list(holidays_set)),
            closure_days=[], # TODO
            weekend_days=weekend_list
        )
    
    async def is_working_day(self, check_date: date, location_id: Optional[UUID] = None) -> bool:
        """Check if a specific date is a working day."""
        res = await self.calculate_working_days(check_date, check_date, location_id)
        return res.working_days > 0

    # ════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════

    async def _get_location_config(self, location_id: Optional[UUID]) -> LocationCalendar:
        """Fetch LocationCalendar. If not found or None, return a DEFAULT."""
        if location_id:
            loc_cal = await self.location_repo.get_by_location(location_id)
            if loc_cal:
                return loc_cal
        
        # Fallback to default logic
        default_wp = await self.work_week_repo.get_default()
        
        if not default_wp:
            # Extreme fallback: Standard 5-day work week
            default_wp = WorkWeekProfile(
                weekly_config={
                    "monday": {"is_working": True},
                    "tuesday": {"is_working": True},
                    "wednesday": {"is_working": True},
                    "thursday": {"is_working": True},
                    "friday": {"is_working": True},
                    "saturday": {"is_working": False},
                    "sunday": {"is_working": False}
                },
                total_weekly_hours=40
            )
        
        # Mock wrapper
        return LocationCalendar(
            work_week_profile=default_wp,
            subscriptions=[] # No subscriptions by default if not configured
        )

    async def _get_location_holidays(self, config: LocationCalendar, start_year: int, end_year: int) -> List[schemas.HolidayBase]:
        """Flatten holidays from all subscribed profiles for the given years."""
        # 1. Get subscribed calendar IDs
        calendar_ids = [sub.calendar_id for sub in config.subscriptions]
        
        if not calendar_ids:
            # Migration/Fallback: Fetch "SYSTEM" type calendars by default.
            system_calendars = await self.calendar_repo.get_system_calendars()
            calendar_ids = [c.id for c in system_calendars]
        
        if not calendar_ids:
            return []

        # 2. Fetch HolidayProfiles linked to these calendars
        profiles = await self.holiday_profile_repo.get_by_calendar_ids(calendar_ids)
        profile_ids = [p.id for p in profiles]
        
        if not profile_ids:
            return []

        # 3. Fetch Holiday Definitions
        holiday_defs = await self.holiday_repo.get_by_profiles(profile_ids)
        
        # 4. Expand Recurrences
        expanded_holidays = []
        for h_def in holiday_defs:
            if h_def.is_recurring and h_def.recurrence_rule:
                # Expand for requested years
                for year in range(start_year, end_year + 1):
                    date_instance = self._calculate_recurrence(h_def.recurrence_rule, year)
                    if date_instance:
                        expanded_holidays.append(schemas.HolidayBase(
                            name=h_def.name,
                            date=date_instance,
                            is_recurring=True,
                            is_confirmed=h_def.is_confirmed
                        ))
            elif h_def.date:
                 # Fixed date
                 if start_year <= h_def.date.year <= end_year:
                     expanded_holidays.append(schemas.HolidayBase(
                         name=h_def.name,
                         date=h_def.date,
                         is_recurring=False,
                         is_confirmed=h_def.is_confirmed
                     ))
        
        return expanded_holidays

    def _calculate_recurrence(self, rule: dict, year: int) -> Optional[date]:
        """Calculate specific date from rule for a given year."""
        rtype = rule.get("type")
        
        if rtype == "yearly":
            try:
                return date(year, rule["month"], rule["day"])
            except ValueError:
                return None # e.g. Feb 29 on non-leap year
                
        elif rtype == "easter_relative":
            offset = rule.get("offset", 0) # 0 = Easter Sunday, 1 = Monday
            easter_d = self._get_easter_date(year)
            return easter_d + timedelta(days=offset)
            
        return None

    def _get_easter_date(self, year: int) -> date:
        """Calculate Western Easter date."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    # ════════════════════════════════════════════════
    # CRUD & MANAGEMENT
    # ════════════════════════════════════════════════
    
    async def get_calendars(self, user_id: UUID) -> List[Calendar]:
        """Get all calendars accessible by user (Personal + Shared + System/Location public?)"""
        return await self.calendar_repo.get_accessible_calendars(user_id)
    
    async def create_calendar(self, user_id: UUID, data: schemas.CalendarCreate) -> Calendar:
        cal = Calendar(
            owner_id=user_id,
            type=data.type,
            name=data.name,
            description=data.description,
            color=data.color,
            is_active=data.is_active
        )
        await self.calendar_repo.create(cal)
        await self.db.commit()
        
        # Reload to get shares (initially empty but good for consistency)
        cal = await self.calendar_repo.get(cal.id)
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="CALENDAR",
            resource_id=str(cal.id),
            description=f"Created calendar: {cal.name}",
            request_data=data.model_dump(mode="json")
        )
        return cal

    async def update_calendar(self, user_id: UUID, calendar_id: UUID, data: schemas.CalendarUpdate) -> Optional[Calendar]:
        cal = await self.calendar_repo.get(calendar_id)
        if not cal or cal.owner_id != user_id:
            return None
            
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(cal, key, value)
            
        await self.calendar_repo.update(cal)
        await self.db.commit()
        
        # Reload
        cal = await self.calendar_repo.get(cal.id)
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="CALENDAR",
            resource_id=str(cal.id),
            description=f"Updated calendar: {cal.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return cal

    async def delete_calendar(self, user_id: UUID, calendar_id: UUID) -> bool:
        cal = await self.calendar_repo.get(calendar_id)
        if not cal or cal.owner_id != user_id:
            # TODO: also allow admin
            return False
            
        await self.calendar_repo.delete(cal)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="CALENDAR",
            resource_id=str(calendar_id),
            description=f"Deleted calendar: {cal.name}"
        )
        return True

    async def share_calendar(self, calendar_id: UUID, user_id: UUID, shared_with_user_id: UUID, permission: CalendarPermission) -> Optional[CalendarShare]:
        # Check ownership
        cal = await self.calendar_repo.get(calendar_id)
        if not cal or cal.owner_id != user_id:
            return None
        
        # Check existing
        existing = await self.share_repo.get(calendar_id, shared_with_user_id)
        if existing:
            existing.permission = permission
            await self.db.commit()
            return existing
        
        share = CalendarShare(
            calendar_id=calendar_id,
            user_id=shared_with_user_id,
            permission=permission
        )
        await self.share_repo.create(share)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="SHARE",
            resource_type="CALENDAR",
            resource_id=str(calendar_id),
            description=f"Shared calendar {cal.name} with user {shared_with_user_id}",
            request_data={"permission": permission}
        )
        return share

    async def unshare_calendar(self, calendar_id: UUID, user_id: UUID, shared_with_user_id: UUID) -> bool:
        # Check ownership
        cal = await self.calendar_repo.get(calendar_id)
        if not cal or cal.owner_id != user_id:
            return False
            
        share = await self.share_repo.get(calendar_id, shared_with_user_id)
        if share:
             await self.share_repo.delete(share)
             await self.db.commit()
             
             await self._audit.log_action(
                user_id=user_id,
                action="UNSHARE",
                resource_type="CALENDAR",
                resource_id=str(calendar_id),
                description=f"Unshared calendar {cal.name} with user {shared_with_user_id}"
            )
             return True
        return False

    # ════════════════════════════════════════════════
    # PROFILES MANAGEMENT (ADMIN)
    # ════════════════════════════════════════════════

    async def get_work_week_profiles(self) -> List[WorkWeekProfile]:
        return await self.work_week_repo.get_all()

    async def get_work_week_profile(self, id: UUID) -> Optional[WorkWeekProfile]:
        return await self.work_week_repo.get(id)

    async def create_work_week_profile(self, data: schemas.WorkWeekProfileCreate) -> WorkWeekProfile:
        obj = WorkWeekProfile(**data.model_dump())
        await self.work_week_repo.create(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="CREATE",
            resource_type="WORK_WEEK_PROFILE",
            resource_id=str(obj.id),
            description=f"Created work week profile: {obj.name}",
            request_data=data.model_dump(mode="json")
        )
        return obj
    
    async def update_work_week_profile(self, id: UUID, data: schemas.WorkWeekProfileUpdate) -> Optional[WorkWeekProfile]:
        obj = await self.work_week_repo.get(id)
        if not obj: return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.work_week_repo.update(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="UPDATE",
            resource_type="WORK_WEEK_PROFILE",
            resource_id=str(obj.id),
            description=f"Updated work week profile: {obj.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return obj

    async def delete_work_week_profile(self, id: UUID) -> bool:
        obj = await self.work_week_repo.get(id)
        if not obj: return False
        await self.work_week_repo.delete(obj)
        await self.db.commit()
        return True

    async def get_holiday_profiles(self) -> List[HolidayProfile]:
        return await self.holiday_profile_repo.get_all()

    async def get_holiday_profile(self, id: UUID) -> Optional[HolidayProfile]:
        return await self.holiday_profile_repo.get(id)

    async def create_holiday_profile(self, data: schemas.HolidayProfileCreate) -> HolidayProfile:
        obj = HolidayProfile(**data.model_dump())
        await self.holiday_profile_repo.create(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="CREATE",
            resource_type="HOLIDAY_PROFILE",
            resource_id=str(obj.id),
            description=f"Created holiday profile: {obj.name}",
            request_data=data.model_dump(mode="json")
        )
        return obj

    async def update_holiday_profile(self, id: UUID, data: schemas.HolidayProfileUpdate) -> Optional[HolidayProfile]:
        obj = await self.holiday_profile_repo.get(id)
        if not obj: return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.holiday_profile_repo.update(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="UPDATE",
            resource_type="HOLIDAY_PROFILE",
            resource_id=str(obj.id),
            description=f"Updated holiday profile: {obj.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return obj

    async def delete_holiday_profile(self, id: UUID) -> bool:
        obj = await self.holiday_profile_repo.get(id)
        if not obj: return False
        await self.holiday_profile_repo.delete(obj)
        await self.db.commit()
        return True

    # Holidays Management within Profile
    async def get_holidays_in_profile(self, profile_id: UUID) -> List[CalendarHoliday]:
        return await self.holiday_repo.get_by_profile(profile_id)

    async def create_holiday(self, profile_id: UUID, data: schemas.HolidayCreate) -> CalendarHoliday:
        dump = data.model_dump(exclude={"profile_id"})
        obj = CalendarHoliday(profile_id=profile_id, **dump)
        await self.holiday_repo.create(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="CREATE",
            resource_type="CALENDAR_HOLIDAY",
            resource_id=str(obj.id),
            description=f"Created holiday: {obj.name} in profile {profile_id}",
            request_data=data.model_dump(mode="json")
        )
        return obj

    async def update_holiday(self, id: UUID, data: schemas.HolidayUpdate) -> Optional[CalendarHoliday]:
        obj = await self.holiday_repo.get(id)
        if not obj: return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.holiday_repo.update(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="UPDATE",
            resource_type="CALENDAR_HOLIDAY",
            resource_id=str(obj.id),
            description=f"Updated holiday: {obj.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return obj

    async def delete_holiday(self, id: UUID) -> bool:
        obj = await self.holiday_repo.get(id)
        if not obj: return False
        await self.holiday_repo.delete(obj)
        await self.db.commit()
        return True

    # Location Calendars
    async def get_location_calendars(self) -> List[LocationCalendar]:
        return await self.location_repo.get_all()
    
    async def create_location_calendar(self, data: schemas.LocationCalendarCreate) -> LocationCalendar:
        obj = LocationCalendar(**data.model_dump())
        await self.location_repo.create(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="CREATE",
            resource_type="LOCATION_CALENDAR",
            resource_id=str(obj.id),
            description=f"Created location calendar for location {obj.location_id}",
            request_data=data.model_dump(mode="json")
        )
        return obj

    async def get_system_holidays(self, year: int) -> List[dict]:
        """Get all holidays from System calendars for a given year."""
        # 1. Get System Calendars
        calendars = await self.calendar_repo.get_system_calendars()
        cal_ids = [c.id for c in calendars]
        
        if not cal_ids:
            return []
            
        # 2. Get Profiles
        profiles = await self.holiday_profile_repo.get_by_calendar_ids(cal_ids)
        profile_ids = [p.id for p in profiles]
        
        if not profile_ids:
            return []
            
        # 3. Fetch Definitions
        holiday_defs = await self.holiday_repo.get_by_profiles(profile_ids)
        
        # 4. Expand
        expanded_holidays = []
        for h_def in holiday_defs:
            if h_def.is_recurring and h_def.recurrence_rule:
                date_instance = self._calculate_recurrence(h_def.recurrence_rule, year)
                if date_instance:
                    expanded_holidays.append({
                        "id": h_def.id,
                        "date": date_instance,
                        "name": h_def.name,
                        "is_recurring": True,
                        "is_confirmed": h_def.is_confirmed
                    })
            elif h_def.date:
                if h_def.date.year == year:
                    expanded_holidays.append({
                        "id": h_def.id,
                        "date": h_def.date,
                        "name": h_def.name,
                        "is_recurring": False,
                        "is_confirmed": h_def.is_confirmed
                    })
        
        expanded_holidays.sort(key=lambda x: x["date"])
        return expanded_holidays

    async def get_location_closures(self, year: int, location_id: Optional[UUID]) -> List[dict]:
        """Get closures for a location."""
        # 1. Get Location Config to find subscriptions
        config = await self._get_location_config(location_id)
        calendar_ids = [sub.calendar_id for sub in config.subscriptions]
        
        # Also include SYSTEM calendars by default if we want
        sys_cals = await self.calendar_repo.get_system_calendars()
        calendar_ids.extend([c.id for c in sys_cals])
        
        if not calendar_ids:
            return []
            
        # 2. Fetch Events (type=closure) via Event Repo
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        closures = await self.event_repo.get_closures(calendar_ids, start_date, end_date)
        
        return [{
            "date": c.start_date, # Approximation for list view, usually range
            "start_date": c.start_date,
            "end_date": c.end_date,
            "name": c.title,
            "type": "closure",
            "id": c.id
        } for c in closures]

    async def create_closure(self, data: schemas.ClosureCreate) -> CalendarClosure:
        obj = CalendarClosure(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date
        )
        await self.closure_repo.create(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="CREATE",
            resource_type="CALENDAR_CLOSURE",
            resource_id=str(obj.id),
            description=f"Created closure: {obj.name}",
            request_data=data.model_dump(mode="json")
        )
        return obj

    async def update_closure(self, id: UUID, data: schemas.ClosureUpdate) -> Optional[CalendarClosure]:
         obj = await self.closure_repo.get(id)
         if not obj: return None
         for k, v in data.model_dump(exclude_unset=True).items():
             setattr(obj, k, v)
         await self.closure_repo.update(obj)
         await self.db.commit()
         
         await self._audit.log_action(
            user_id=None, # Admin
            action="UPDATE",
            resource_type="CALENDAR_CLOSURE",
            resource_id=str(obj.id),
            description=f"Updated closure: {obj.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
         )
         return obj

    async def delete_closure(self, id: UUID) -> bool:
         obj = await self.closure_repo.get(id)
         if not obj: return False
         await self.closure_repo.delete(obj)
         await self.db.commit()
         return True

    # ════════════════════════════════════════════════
    # WORKING DAY EXCEPTIONS (ADMIN)
    # ════════════════════════════════════════════════

    async def get_working_day_exceptions(self, year: int, location_id: Optional[UUID] = None) -> List[WorkingDayException]:
        return await self.exception_repo.get_by_year(year, location_id)

    async def create_working_day_exception(self, data: schemas.WorkingDayExceptionCreate) -> WorkingDayException:
        obj = WorkingDayException(**data.model_dump())
        await self.exception_repo.create(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=None, # Admin
            action="CREATE",
            resource_type="WORKING_DAY_EXCEPTION",
            resource_id=str(obj.id),
            description=f"Created working day exception on {obj.date}",
            request_data=data.model_dump(mode="json")
        )
        return obj

    async def delete_working_day_exception(self, id: UUID) -> bool:
        obj = await self.exception_repo.get(id)
        if not obj: return False
        await self.exception_repo.delete(obj)
        await self.db.commit()
        return True

    # ════════════════════════════════════════════════
    # EVENTS MANAGEMENT
    # ════════════════════════════════════════════════

    async def get_visible_events(
        self, 
        user_id: UUID, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        event_type: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Get events from all calendars visible to the user."""
        
        # 1. Get visible calendars
        calendars = await self.calendar_repo.get_accessible_calendars(user_id)
        cal_ids = [c.id for c in calendars]
        
        return await self.event_repo.get_visible_events(cal_ids, start_date, end_date, event_type)

    async def get_event(self, event_id: UUID) -> Optional[CalendarEvent]:
        return await self.event_repo.get(event_id)
        
    async def create_event(self, user_id: UUID, data: schemas.EventCreate) -> CalendarEvent:
        # If no calendar_id provided, use or create user's default personal calendar
        calendar_id = data.calendar_id
        if not calendar_id:
            # Find user's personal calendar
            cal = await self.calendar_repo.get_personal_calendar(user_id)
            
            if not cal:
                # Create a default personal calendar for the user
                cal = Calendar(
                    name="Il mio calendario",
                    type=CalendarType.PERSONAL,
                    owner_id=user_id,
                    is_active=True
                )
                await self.calendar_repo.create(cal)
                await self.db.commit()
            
            calendar_id = cal.id
        else:
            # Check write permission on calendar
            cal = await self.calendar_repo.get(calendar_id)
            if not cal:
                raise ValueError("Calendar not found")
                
            # Permission check: owner or shared with write?
            can_write = False
            if cal.owner_id == user_id:
                can_write = True
            else:
                # Check share (using permissive check logic or specific query)
                share = await self.share_repo.get_with_permission(
                     cal.id, user_id, [schemas.CalendarPermission.WRITE, schemas.CalendarPermission.ADMIN]
                )
                if share:
                    can_write = True
                    
            # System calendars? Only Admin can write (assuming calling service handles admin check or we add it)
            # The current logic just "pass"es in the original code, implying no check or implicit trust if can_write is set.
            # Assuming simplified logic here to match original flow where `pass` effectively did nothing
            # prompting later code to check `can_write`.
                 
            if not can_write and cal.type != CalendarType.SYSTEM:
                 # TODO: Raise proper permission error. Original code had `pass`? 
                 # Original code had `pass` then seemingly continued? 
                 # Logic seems to imply we should raise if not can_write.
                 # Let's enforce it.
                 raise ValueError("No write permission on this calendar")
             
        # Create
        dump = data.model_dump(exclude={"participants", "participant_ids", "calendar_id"})
        obj = CalendarEvent(**dump, calendar_id=calendar_id, created_by=user_id)
        await self.event_repo.create(obj)
        await self.db.commit()
        
        # Add participants if any
        if data.participant_ids:
             for pid in data.participant_ids:
                 part = EventParticipant(event_id=obj.id, user_id=pid)
                 self.db.add(part) # We can add these to session directly or via repo. Direct is fine for simple associators.
             await self.db.commit()
             
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(obj.id),
            description=f"Created event: {obj.title}",
            request_data=data.model_dump(mode="json")
        )
        
        # Reload with eager loading
        return await self.get_event(obj.id)

    async def update_event(self, event_id: UUID, data: schemas.EventUpdate, user_id: UUID) -> Optional[CalendarEvent]:
        obj = await self.get_event(event_id)
        if not obj: return None
        
        # Permission check (simplified: owner or creator)
        # TODO: Check calendar permission too
        
        for k, v in data.model_dump(exclude_unset=True).items():
             if k != "participants":
                setattr(obj, k, v)
        
        await self.event_repo.update(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(obj.id),
            description=f"Updated event: {obj.title}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return obj

    async def delete_event(self, event_id: UUID, user_id: UUID) -> bool:
        obj = await self.get_event(event_id)
        if not obj: return False
        
        # Permission check
        
        await self.event_repo.delete(obj)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(event_id),
            description=f"Deleted event: {obj.title}"
        )
        return True
    
    async def get_calendar_range(
        self, 
        user_id: UUID, 
        start_date: date, 
        end_date: date,
        location_id: Optional[UUID] = None
    ) -> schemas.CalendarRangeView:
        """
        Produce an aggregated range view including holidays, closures, and user events.
        """
        # 1. Get holidays and working days info
        calc_res = await self.calculate_working_days(
            start_date=start_date,
            end_date=end_date,
            location_id=location_id
        )
        
        # 2. Get visible events
        events = await self.get_visible_events(user_id, start_date, end_date)
        
        # 3. Get system holidays names mapped by date
        # We need holidays with names for the range
        config = await self._get_location_config(location_id)
        holidays = await self._get_location_holidays(config, start_date.year, end_date.year)
        holiday_map = {h.date: h.name for h in holidays if start_date <= h.date <= end_date}
        
        # 4. Get closures
        # Closures are usually in specific calendars, get_location_closures returns them as dicts
        closures = await self.get_location_closures(start_date.year, location_id)
        if end_date.year > start_date.year:
            closures.extend(await self.get_location_closures(end_date.year, location_id))
        
        closure_map = {}
        for c in closures:
            # Simple simulation of date mapping if it's a multi-day closure
            curr = c["start_date"]
            while curr <= c["end_date"]:
                if start_date <= curr <= end_date:
                    closure_map[curr] = c["name"]
                curr += timedelta(days=1)

        # 5. Get Leaves (Approved)
        leaves_client = LeavesClient()
        # Fetch leaves including "approved" and "approved_conditional"
        leaves_data = await leaves_client.get_leaves_in_period(
            start_date=start_date,
            end_date=end_date,
            status="approved,approved_conditional"
        )
        
        # Build leaves map: date -> list of leaves
        leaves_map: Dict[date, List[dict]] = {}
        for leave in leaves_data:
            l_start = date.fromisoformat(leave["start_date"]) if isinstance(leave["start_date"], str) else leave["start_date"]
            l_end = date.fromisoformat(leave["end_date"]) if isinstance(leave["end_date"], str) else leave["end_date"]
            
            # Map full name
            user_name = leave.get("user_name", "Dipendente")
            leave_code = leave.get("leave_type_code", "ASSENZA")
            
            # Format title as requested: "Name Surname - FERIE/ROL/PERMESSO"
            title = f"{user_name} - {leave_code}"
            
            # Iterate days of the leave
            curr = l_start
            while curr <= l_end:
                if start_date <= curr <= end_date:
                    if curr not in leaves_map:
                        leaves_map[curr] = []
                    leaves_map[curr].append({
                        "id": leave["id"],
                        "title": title,
                        "start_date": l_start,
                        "end_date": l_end,
                        "leave_type_code": leave_code,
                        "status": leave.get("status")
                    })
                curr += timedelta(days=1)

        # 6. Build days list
        days = []
        current_date = start_date
        while current_date <= end_date:
            day_items = []
            
            # Add Holiday if exists
            h_name = holiday_map.get(current_date)
            if h_name:
                day_items.append(schemas.CalendarDayItem(
                    id=uuid4(), # Virtual ID
                    title=h_name,
                    item_type=schemas.CalendarItemType.HOLIDAY,
                    start_date=current_date,
                    end_date=current_date,
                    color="#EF4444",
                    is_all_day=True
                ))
            
            # Add Closure if exists
            c_name = closure_map.get(current_date)
            if c_name:
                day_items.append(schemas.CalendarDayItem(
                    id=uuid4(), # Virtual ID
                    title=c_name,
                    item_type=schemas.CalendarItemType.CLOSURE,
                    start_date=current_date,
                    end_date=current_date,
                    color="#F59E0B",
                    is_all_day=True
                ))
            
            # Add Leaves
            if current_date in leaves_map:
                for l_data in leaves_map[current_date]:
                     # Determine color based on status
                     status = l_data.get("status")
                     color = "#10B981" if status in ["approved", "approved_conditional"] else "#F59E0B" if status == "pending" else "#3B82F6"
                     
                     day_items.append(schemas.CalendarDayItem(
                        id=UUID(l_data["id"]) if isinstance(l_data["id"], str) else l_data["id"],
                        title=l_data["title"],
                        item_type=schemas.CalendarItemType.LEAVE,
                        start_date=l_data["start_date"],
                        end_date=l_data["end_date"],
                        color=color,
                        is_all_day=True,
                        metadata={
                            "leave_type": l_data["leave_type_code"],
                            "status": status
                        }
                    ))

            # Add User Events
            for e in events:
                if e.start_date <= current_date <= e.end_date:
                    day_items.append(schemas.CalendarDayItem(
                        id=e.id,
                        title=e.title,
                        item_type=schemas.CalendarItemType.EVENT,
                        start_date=e.start_date,
                        end_date=e.end_date,
                        color=e.calendar.color if e.calendar else "#4F46E5",
                        is_all_day=e.is_all_day,
                        start_time=e.start_time,
                        end_time=e.end_time,
                        metadata={"calendar_id": str(e.calendar_id)} if e.calendar_id else None
                    ))
            
            is_working = await self.is_working_day(current_date, location_id)
            
            days.append(schemas.CalendarDayView(
                date=current_date,
                is_working_day=is_working,
                is_holiday=current_date in holiday_map or current_date in closure_map,
                holiday_name=h_name or c_name,
                items=day_items
            ))
            
            current_date += timedelta(days=1)

        return schemas.CalendarRangeView(
            start_date=start_date,
            end_date=end_date,
            days=days,
            working_days_count=calc_res.working_days
        )
