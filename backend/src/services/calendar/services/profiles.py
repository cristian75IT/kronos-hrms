"""
KRONOS - Calendar Profiles Service

Handles work week profiles and holiday profiles management.
"""
from typing import Optional, List
import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import (
    WorkWeekProfile, HolidayProfile, CalendarHoliday, LocationCalendar
)
from src.services.calendar import schemas
from src.services.calendar.services.base import BaseCalendarService
from src.services.calendar.exceptions import (
    WorkWeekProfileNotFound,
    HolidayProfileNotFound,
    HolidayNotFound
)


class CalendarProfileService(BaseCalendarService):
    """
    Service for calendar profiles management.
    
    Handles:
    - Work week profiles (Mon-Fri, Sat-Sun, etc.)
    - Holiday profiles with recurrence rules
    - Location calendar configurations
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # Work Week Profiles
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_work_week_profiles(self) -> List[WorkWeekProfile]:
        """Get all work week profiles."""
        return await self._profile_repo.get_all()
    
    async def get_work_week_profile(self, id: UUID) -> Optional[WorkWeekProfile]:
        """Get work week profile by ID."""
        return await self._profile_repo.get(id)
    
    async def create_work_week_profile(self, data: schemas.WorkWeekProfileCreate) -> WorkWeekProfile:
        """Create a new work week profile."""
        profile = WorkWeekProfile(
            id=uuid4(),
            **data.model_dump()
        )
        await self._profile_repo.create(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        
        await self._audit.log_action(
            action="CREATE",
            resource_type="WORK_WEEK_PROFILE",
            resource_id=str(profile.id),
            description=f"Created work week profile: {profile.name}",
            request_data=data.model_dump(mode="json")
        )
        
        return profile
    
    async def update_work_week_profile(
        self, 
        id: UUID, 
        data: schemas.WorkWeekProfileUpdate
    ) -> WorkWeekProfile:
        """Update a work week profile."""
        profile = await self.get_work_week_profile(id)
        if not profile:
            raise WorkWeekProfileNotFound(id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        
        await self._profile_repo.update(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        
        await self._audit.log_action(
            action="UPDATE",
            resource_type="WORK_WEEK_PROFILE",
            resource_id=str(id),
            description=f"Updated work week profile: {profile.name}",
            request_data=update_data
        )
        
        return profile
    
    async def delete_work_week_profile(self, id: UUID) -> bool:
        """Delete a work week profile."""
        profile = await self.get_work_week_profile(id)
        if not profile:
            raise WorkWeekProfileNotFound(id)
        
        profile_name = profile.name
        await self._profile_repo.delete(profile)
        await self.db.commit()
        
        await self._audit.log_action(
            action="DELETE",
            resource_type="WORK_WEEK_PROFILE",
            resource_id=str(id),
            description=f"Deleted work week profile: {profile_name}"
        )
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holiday Profiles
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_holiday_profiles(self) -> List[HolidayProfile]:
        """Get all holiday profiles."""
        return await self._holiday_repo.get_all()
    
    async def get_holiday_profile(self, id: UUID) -> Optional[HolidayProfile]:
        """Get holiday profile by ID."""
        return await self._holiday_repo.get(id)
    
    async def create_holiday_profile(self, data: schemas.HolidayProfileCreate) -> HolidayProfile:
        """Create a new holiday profile."""
        profile = HolidayProfile(
            id=uuid4(),
            **data.model_dump()
        )
        await self._holiday_repo.create(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        
        await self._audit.log_action(
            action="CREATE",
            resource_type="HOLIDAY_PROFILE",
            resource_id=str(profile.id),
            description=f"Created holiday profile: {profile.name}",
            request_data=data.model_dump(mode="json")
        )
        
        return profile
    
    async def update_holiday_profile(
        self, 
        id: UUID, 
        data: schemas.HolidayProfileUpdate
    ) -> HolidayProfile:
        """Update a holiday profile."""
        profile = await self.get_holiday_profile(id)
        if not profile:
            raise HolidayProfileNotFound(id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        
        await self._holiday_repo.update(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        
        await self._audit.log_action(
            action="UPDATE",
            resource_type="HOLIDAY_PROFILE",
            resource_id=str(id),
            description=f"Updated holiday profile: {profile.name}",
            request_data=update_data
        )
        
        return profile
    
    async def delete_holiday_profile(self, id: UUID) -> bool:
        """Delete a holiday profile."""
        profile = await self.get_holiday_profile(id)
        if not profile:
            raise HolidayProfileNotFound(id)
        
        profile_name = profile.name
        await self._holiday_repo.delete(profile)
        await self.db.commit()
        
        await self._audit.log_action(
            action="DELETE",
            resource_type="HOLIDAY_PROFILE",
            resource_id=str(id),
            description=f"Deleted holiday profile: {profile_name}"
        )
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holidays in Profile (CalendarHoliday model)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_holidays_in_profile(self, profile_id: UUID) -> List[CalendarHoliday]:
        """Get all holidays in a profile."""
        return await self._cal_holiday_repo.get_by_profile(profile_id)
    
    async def create_holiday(self, profile_id: UUID, data: schemas.HolidayCreate) -> CalendarHoliday:
        """Create a holiday in a profile."""
        holiday = CalendarHoliday(
            id=uuid4(),
            profile_id=profile_id,
            **data.model_dump()
        )
        await self._cal_holiday_repo.create(holiday)
        await self.db.commit()
        await self.db.refresh(holiday)
        
        await self._audit.log_action(
            action="CREATE",
            resource_type="HOLIDAY",
            resource_id=str(holiday.id),
            description=f"Created holiday: {holiday.name}",
            request_data=data.model_dump(mode="json")
        )
        
        return holiday
    
    async def update_holiday(self, id: UUID, data: schemas.HolidayUpdate) -> CalendarHoliday:
        """Update a holiday."""
        holiday = await self._cal_holiday_repo.get(id)
        
        if not holiday:
            raise HolidayNotFound(id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(holiday, key, value)
        
        await self._cal_holiday_repo.update(holiday)
        await self.db.commit()
        await self.db.refresh(holiday)
        
        await self._audit.log_action(
            action="UPDATE",
            resource_type="HOLIDAY",
            resource_id=str(id),
            description=f"Updated holiday: {holiday.name}",
            request_data=update_data
        )
        
        return holiday
    
    async def delete_holiday(self, id: UUID) -> bool:
        """Delete a holiday."""
        holiday = await self._cal_holiday_repo.get(id)
        
        if not holiday:
            raise HolidayNotFound(id)
        
        holiday_name = holiday.name
        await self._cal_holiday_repo.delete(holiday)
        await self.db.commit()
        
        await self._audit.log_action(
            action="DELETE",
            resource_type="HOLIDAY",
            resource_id=str(id),
            description=f"Deleted holiday: {holiday_name}"
        )
        
        return True

    async def generate_default_holidays(self, profile_id: UUID, year: int) -> int:
        """Generate default (Italian) holidays for a given year in a profile."""
        profile = await self.get_holiday_profile(profile_id)
        if not profile:
            raise HolidayProfileNotFound(profile_id)

        # Italian holidays list
        italian_holidays = [
            {"date": f"{year}-01-01", "name": "Capodanno"},
            {"date": f"{year}-01-06", "name": "Epifania"},
            {"date": f"{year}-04-25", "name": "Festa della Liberazione"},
            {"date": f"{year}-05-01", "name": "Festa del Lavoro"},
            {"date": f"{year}-06-02", "name": "Festa della Repubblica"},
            {"date": f"{year}-08-15", "name": "Ferragosto"},
            {"date": f"{year}-11-01", "name": "Ognissanti"},
            {"date": f"{year}-12-08", "name": "Immacolata Concezione"},
            {"date": f"{year}-12-25", "name": "Natale"},
            {"date": f"{year}-12-26", "name": "Santo Stefano"},
        ]
        
        # Easter Calculation (Simple Gauss algorithm for Western Easter)
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
        
        easter_date = f"{year}-{month:02d}-{day:02d}"
        italian_holidays.append({"date": easter_date, "name": "Pasqua"})
        
        # Pasquetta (Easter Monday)
        dt_easter = datetime.date(year, month, day)
        dt_pasquetta = dt_easter + datetime.timedelta(days=1)
        italian_holidays.append({"date": str(dt_pasquetta), "name": "Lunedì dell'Angelo"})

        # Get existing holidays to avoid duplicates
        existing_models = await self.get_holidays_in_profile(profile_id)
        existing_dates = {h.date for h in existing_models}

        count = 0
        for h in italian_holidays:
            if h["date"] not in existing_dates:
                try:
                    await self.create_holiday(profile_id, schemas.HolidayCreate(
                        name=h["name"],
                        date=h["date"],
                        year=year,
                        scope="national",
                        is_recurring=False
                    ))
                    count += 1
                except Exception:
                    pass 
        
        return count

    
    # ═══════════════════════════════════════════════════════════════════════
    # Location Calendars
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_location_calendars(self) -> List[LocationCalendar]:
        """Get all location calendars."""
        return await self._loc_repo.get_all()
    
    async def create_location_calendar(self, data: schemas.LocationCalendarCreate) -> LocationCalendar:
        """Create a location calendar."""
        loc_cal = LocationCalendar(
            id=uuid4(),
            **data.model_dump(exclude={"holiday_profile_ids"})
        )
        await self._loc_repo.create(loc_cal)
        await self.db.commit()
        await self.db.refresh(loc_cal)
        
        await self._audit.log_action(
            action="CREATE",
            resource_type="LOCATION_CALENDAR",
            resource_id=str(loc_cal.id),
            description=f"Created location calendar",
            request_data=data.model_dump(mode="json")
        )
        
        return loc_cal
