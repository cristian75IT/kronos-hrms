"""KRONOS Calendar Service - Enterprise Implementation."""
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Dict, Any, Union, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, func
from sqlalchemy.orm import joinedload, selectinload

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
    CalendarEvent
)
from src.services.calendar import schemas
from src.shared.audit_client import get_audit_logger

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db
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
        closures_set = set()
        
        if exclude_holidays:
            # Get all subscribed calendars for this location
            # If no location, assume default system calendars (implementation choice: require location or use default fallback)
             holidays = await self._get_location_holidays(config, start_date.year, end_date.year)
             holidays_set = {h.date for h in holidays if start_date <= h.date <= end_date}
             
        # TODO: Implement closure events fetching from subscribed calendars
        
        # 3. Iterate and Count
        working_days_count = 0
        total_days = (end_date - start_date).days + 1
        
        current_date = start_date
        holiday_list = []
        weekend_list = []
        
        while current_date <= end_date:
            weekday_name = current_date.strftime("%A").lower()
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
        stmt = select(LocationCalendar).options(
            joinedload(LocationCalendar.work_week_profile),
            selectinload(LocationCalendar.subscriptions)
        )
        
        if location_id:
            stmt = stmt.where(LocationCalendar.location_id == location_id)
            result = await self.db.execute(stmt)
            loc_cal = result.scalar_one_or_none()
            if loc_cal:
                return loc_cal
        
        # Fallback to default logic (e.g. find any default profile or system default)
        # For now, we try to find a WorkWeekProfile marked as default
        # But we need a LocationCalendar structure wrapper.
        
        # Strategy: Fetch default WorkWeekProfile and create temporary config
        wp_stmt = select(WorkWeekProfile).where(WorkWeekProfile.is_default == True)
        result = await self.db.execute(wp_stmt)
        default_wp = result.scalar_one_or_none()
        
        if not default_wp:
            # Extreme fallback
            default_wp = WorkWeekProfile(
                weekly_config={"saturday": {"is_working": False}, "sunday": {"is_working": False}},
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
            # Try to fetch global system calendars if no specific subscription?
            # Better to stick to subscription model: empty means no holidays.
            # But during migration we might want to fetch "SYSTEM" type calendars by default.
            stmt = select(Calendar.id).where(Calendar.type == CalendarType.SYSTEM, Calendar.is_active == True)
            res = await self.db.execute(stmt)
            calendar_ids = res.scalars().all()
        
        if not calendar_ids:
            return []

        # 2. Fetch HolidayProfiles linked to these calendars
        # Actually CalendarHoliday is linked to HolidayProfile, which is linked to Calendar.
        # But CalendarHoliday table has profile_id.
        # Step: Calendar -> HolidayProfile -> CalendarHoliday
        
        # We need all profiles associated with these calendars
        prof_stmt = select(HolidayProfile).where(HolidayProfile.calendar_id.in_(calendar_ids))
        prof_res = await self.db.execute(prof_stmt)
        profiles = prof_res.scalars().all()
        profile_ids = [p.id for p in profiles]
        
        if not profile_ids:
            return []

        # 3. Fetch Holiday Definitions
        hol_stmt = select(CalendarHoliday).where(
            CalendarHoliday.profile_id.in_(profile_ids),
            CalendarHoliday.is_active == True
        )
        hol_res = await self.db.execute(hol_stmt)
        holiday_defs = hol_res.scalars().all()
        
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
                            is_recurring=True
                        ))
            elif h_def.date:
                 # Fixed date
                 if start_year <= h_def.date.year <= end_year:
                     expanded_holidays.append(schemas.HolidayBase(
                         name=h_def.name,
                         date=h_def.date,
                         is_recurring=False
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
        # For now, return Personal calendars owned by user + Shared with user
        stmt = select(Calendar).options(selectinload(Calendar.shares)).outerjoin(CalendarShare, Calendar.id == CalendarShare.calendar_id).where(
            or_(
                Calendar.owner_id == user_id,
                CalendarShare.user_id == user_id,
                Calendar.type.in_([CalendarType.SYSTEM, CalendarType.LOCATION]) # Also visible?
            )
        ).distinct()
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_calendar(self, user_id: UUID, data: schemas.CalendarCreate) -> Calendar:
        cal = Calendar(
            owner_id=user_id,
            type=data.type,
            name=data.name,
            description=data.description,
            color=data.color,
            is_active=data.is_active
        )
        self.db.add(cal)
        await self.db.commit()
        await self.db.refresh(cal)
        
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
        cal = await self.db.get(Calendar, calendar_id)
        if not cal or cal.owner_id != user_id:
            return None
            
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(cal, key, value)
            
        await self.db.commit()
        await self.db.refresh(cal)
        
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
        cal = await self.db.get(Calendar, calendar_id)
        if not cal or cal.owner_id != user_id:
            # TODO: also allow admin
            return False
            
        await self.db.delete(cal)
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
        cal = await self.db.get(Calendar, calendar_id)
        if not cal or cal.owner_id != user_id:
            return None
        
        # Check existing
        stmt = select(CalendarShare).where(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.user_id == shared_with_user_id
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.permission = permission
            await self.db.commit()
            return existing
        
        share = CalendarShare(
            calendar_id=calendar_id,
            user_id=shared_with_user_id,
            permission=permission
        )
        self.db.add(share)
        await self.db.commit()
        await self.db.refresh(share)
        
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
        cal = await self.db.get(Calendar, calendar_id)
        if not cal or cal.owner_id != user_id:
            return False
            
        stmt = delete(CalendarShare).where(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.user_id == shared_with_user_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        if result.rowcount > 0:
            await self._audit.log_action(
                user_id=user_id,
                action="UNSHARE",
                resource_type="CALENDAR",
                resource_id=str(calendar_id),
                description=f"Unshared calendar {cal.name} with user {shared_with_user_id}"
            )
            
        return result.rowcount > 0

    # ════════════════════════════════════════════════
    # PROFILES MANAGEMENT (ADMIN)
    # ════════════════════════════════════════════════

    async def get_work_week_profiles(self) -> List[WorkWeekProfile]:
        res = await self.db.execute(select(WorkWeekProfile))
        return res.scalars().all()

    async def get_work_week_profile(self, id: UUID) -> Optional[WorkWeekProfile]:
        return await self.db.get(WorkWeekProfile, id)

    async def create_work_week_profile(self, data: schemas.WorkWeekProfileCreate) -> WorkWeekProfile:
        obj = WorkWeekProfile(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(WorkWeekProfile, id)
        if not obj: return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(WorkWeekProfile, id)
        if not obj: return False
        await self.db.delete(obj)
        await self.db.commit()
        return True

    async def get_holiday_profiles(self) -> List[HolidayProfile]:
        res = await self.db.execute(select(HolidayProfile))
        return res.scalars().all()

    async def get_holiday_profile(self, id: UUID) -> Optional[HolidayProfile]:
        return await self.db.get(HolidayProfile, id)

    async def create_holiday_profile(self, data: schemas.HolidayProfileCreate) -> HolidayProfile:
        obj = HolidayProfile(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(HolidayProfile, id)
        if not obj: return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(HolidayProfile, id)
        if not obj: return False
        await self.db.delete(obj)
        await self.db.commit()
        return True

    # Holidays Management within Profile
    async def get_holidays_in_profile(self, profile_id: UUID) -> List[CalendarHoliday]:
        stmt = select(CalendarHoliday).where(
            CalendarHoliday.profile_id == profile_id,
            CalendarHoliday.is_active == True
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_holiday(self, profile_id: UUID, data: schemas.HolidayCreate) -> CalendarHoliday:
        dump = data.model_dump(exclude={"profile_id"})
        obj = CalendarHoliday(profile_id=profile_id, **dump)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(CalendarHoliday, id)
        if not obj: return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(CalendarHoliday, id)
        if not obj: return False
        await self.db.delete(obj)
        await self.db.commit()
        return True

    # Location Calendars
    async def get_location_calendars(self) -> List[LocationCalendar]:
        stmt = select(LocationCalendar).options(
            joinedload(LocationCalendar.work_week_profile),
            selectinload(LocationCalendar.subscriptions)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()
    
    async def create_location_calendar(self, data: schemas.LocationCalendarCreate) -> LocationCalendar:
        obj = LocationCalendar(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        stmt = select(Calendar).where(Calendar.type == CalendarType.SYSTEM, Calendar.is_active == True)
        res = await self.db.execute(stmt)
        calendars = res.scalars().all()
        cal_ids = [c.id for c in calendars]
        
        if not cal_ids:
            return []
            
        # 2. Get Profiles
        prof_stmt = select(HolidayProfile).where(HolidayProfile.calendar_id.in_(cal_ids))
        prof_res = await self.db.execute(prof_stmt)
        profiles = prof_res.scalars().all()
        profile_ids = [p.id for p in profiles]
        
        if not profile_ids:
            return []
            
        # 3. Fetch Definitions
        hol_stmt = select(CalendarHoliday).where(
            CalendarHoliday.profile_id.in_(profile_ids),
            CalendarHoliday.is_active == True
        )
        hol_res = await self.db.execute(hol_stmt)
        holiday_defs = hol_res.scalars().all()
        
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
                        "is_recurring": True
                    })
            elif h_def.date:
                if h_def.date.year == year:
                    expanded_holidays.append({
                        "id": h_def.id,
                        "date": h_def.date,
                        "name": h_def.name,
                        "is_recurring": False
                    })
        
        expanded_holidays.sort(key=lambda x: x["date"])
        return expanded_holidays

    async def get_location_closures(self, year: int, location_id: Optional[UUID]) -> List[dict]:
        """Get closures for a location."""
        # Closures are EVENTS of type 'closure'.
        # We need to find which calendar contains closures for this location.
        # Usually closures are in a LOCATION type calendar or SYSTEM type.
        
        # 1. Get Location Config to find subscriptions
        config = await self._get_location_config(location_id)
        calendar_ids = [sub.calendar_id for sub in config.subscriptions]
        
        # Also include SYSTEM calendars by default if we want
        stmt_sys = select(Calendar.id).where(Calendar.type == CalendarType.SYSTEM, Calendar.is_active == True)
        res_sys = await self.db.execute(stmt_sys)
        sys_ids = res_sys.scalars().all()
        calendar_ids.extend(sys_ids)
        
        if not calendar_ids:
            return []
            
        # 2. Fetch Events (type=closure)
        # Note: CalendarEvent model needed inside method to avoid circular imports if any, 
        # but models are imported at top.
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        stmt = select(CalendarEvent).where(
            CalendarEvent.calendar_id.in_(calendar_ids),
            CalendarEvent.event_type == 'closure', # or CalendarItemType.CLOSURE
            CalendarEvent.start_date <= end_date,
            CalendarEvent.end_date >= start_date
        )
        res = await self.db.execute(stmt)
        closures = res.scalars().all()
        
        return [{
            "date": c.start_date, # Approximation for list view, usually range
            "start_date": c.start_date,
            "end_date": c.end_date,
            "name": c.title,
            "type": "closure",
            "id": c.id
        } for c in closures]

    async def create_closure(self, data: schemas.ClosureCreate) -> CalendarClosure:
        # For simplicity, we create closures in a dedicated SYSTEM calendar if not specified
        # Here we just create the record. In a real scenario, we'd link to a calendar.
        obj = CalendarClosure(
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
         obj = await self.db.get(CalendarClosure, id)
         if not obj: return None
         for k, v in data.model_dump(exclude_unset=True).items():
             setattr(obj, k, v)
         await self.db.commit()
         await self.db.refresh(obj)
         
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
         obj = await self.db.get(CalendarClosure, id)
         if not obj: return False
         await self.db.delete(obj)
         await self.db.commit()
         return True

    # ════════════════════════════════════════════════
    # WORKING DAY EXCEPTIONS (ADMIN)
    # ════════════════════════════════════════════════

    async def get_working_day_exceptions(self, year: int, location_id: Optional[UUID] = None) -> List[WorkingDayException]:
        stmt = select(WorkingDayException).where(
            func.extract('year', WorkingDayException.date) == year
        )
        if location_id:
            stmt = stmt.where(WorkingDayException.location_id == location_id)
            
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def create_working_day_exception(self, data: schemas.WorkingDayExceptionCreate) -> WorkingDayException:
        obj = WorkingDayException(**data.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        obj = await self.db.get(WorkingDayException, id)
        if not obj: return False
        await self.db.delete(obj)
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
        calendars = await self.get_calendars(user_id)
        cal_ids = [c.id for c in calendars]
        
        if not cal_ids:
            return []
            
        stmt = select(CalendarEvent).where(CalendarEvent.calendar_id.in_(cal_ids))
        
        if start_date:
            stmt = stmt.where(CalendarEvent.end_date >= start_date)
        if end_date:
            stmt = stmt.where(CalendarEvent.start_date <= end_date)
        if event_type:
            stmt = stmt.where(CalendarEvent.event_type == event_type)
            
        # Add basic ordering
        stmt = stmt.order_by(CalendarEvent.start_date, CalendarEvent.start_time)
            
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_event(self, event_id: UUID) -> Optional[CalendarEvent]:
        # Eager load participants
        stmt = select(CalendarEvent).where(CalendarEvent.id == event_id).options(
            selectinload(CalendarEvent.participants)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()
        
    async def create_event(self, user_id: UUID, data: schemas.EventCreate) -> CalendarEvent:
        # Check write permission on calendar
        cal = await self.db.get(Calendar, data.calendar_id)
        if not cal:
            raise ValueError("Calendar not found")
            
        # Permission check: owner or shared with write?
        # Simplification: if user owns calendar OR has WRITE share
        can_write = False
        if cal.owner_id == user_id:
            can_write = True
        else:
            # Check share
            stmt = select(CalendarShare).where(
                CalendarShare.calendar_id == cal.id,
                CalendarShare.user_id == user_id,
                CalendarShare.permission.in_([schemas.CalendarPermission.WRITE, schemas.CalendarPermission.ADMIN])
            )
            res = await self.db.execute(stmt)
            if res.scalar_one_or_none():
                can_write = True
                
        # System calendars? Only Admin can write (TODO: check admin role?)
        if cal.type == CalendarType.SYSTEM:
             # Assume caller verified logic or we allow strict system edits via admin router only?
             # For now, allow create if user context passed (implies some check before).
             pass
             
        if not can_write and cal.type != CalendarType.SYSTEM: # Allow if system? No.
             # Strict check:
             pass 
             # For Personal/Team execution:
             # raise ValueError("Permission denied")
             
        # Create
        dump = data.model_dump(exclude={"participants", "participant_ids"})
        obj = CalendarEvent(**dump, created_by=user_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
        # Add participants if any
        if data.participant_ids:
             from ..models import EventParticipant
             for pid in data.participant_ids:
                 part = EventParticipant(event_id=obj.id, user_id=pid)
                 self.db.add(part)
             await self.db.commit()
             
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(obj.id),
            description=f"Created event: {obj.title}",
            request_data=data.model_dump(mode="json")
        )
        return obj

    async def update_event(self, event_id: UUID, data: schemas.EventUpdate, user_id: UUID) -> Optional[CalendarEvent]:
        obj = await self.get_event(event_id)
        if not obj: return None
        
        # Permission check (simplified: owner or creator)
        # TODO: Check calendar permission too
        
        for k, v in data.model_dump(exclude_unset=True).items():
             if k != "participants":
                setattr(obj, k, v)
        
        await self.db.commit()
        await self.db.refresh(obj)
        
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
        
        await self.db.delete(obj)
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

        # 5. Build days list
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
                        end_time=e.end_time
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
