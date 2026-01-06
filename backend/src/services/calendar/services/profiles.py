"""
KRONOS - Calendar Profiles Service

Handles work week profiles and holiday profiles management.
"""
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import (
    WorkWeekProfile, HolidayProfile, CalendarHoliday, LocationCalendar
)
from src.services.calendar import schemas
from src.services.calendar.services.base import BaseCalendarService


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
        stmt = select(WorkWeekProfile)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_work_week_profile(self, id: UUID) -> Optional[WorkWeekProfile]:
        """Get work week profile by ID."""
        stmt = select(WorkWeekProfile).where(WorkWeekProfile.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_work_week_profile(self, data: schemas.WorkWeekProfileCreate) -> WorkWeekProfile:
        """Create a new work week profile."""
        profile = WorkWeekProfile(
            id=uuid4(),
            **data.model_dump()
        )
        self.db.add(profile)
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
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Work week profile not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        
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
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Work week profile not found")
        
        profile_name = profile.name
        await self.db.delete(profile)
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
        stmt = select(HolidayProfile).options(selectinload(HolidayProfile.holidays))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_holiday_profile(self, id: UUID) -> Optional[HolidayProfile]:
        """Get holiday profile by ID."""
        stmt = select(HolidayProfile).options(
            selectinload(HolidayProfile.holidays)
        ).where(HolidayProfile.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_holiday_profile(self, data: schemas.HolidayProfileCreate) -> HolidayProfile:
        """Create a new holiday profile."""
        profile = HolidayProfile(
            id=uuid4(),
            **data.model_dump()
        )
        self.db.add(profile)
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
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Holiday profile not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        
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
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Holiday profile not found")
        
        profile_name = profile.name
        await self.db.delete(profile)
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
        stmt = select(CalendarHoliday).where(CalendarHoliday.profile_id == profile_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_holiday(self, profile_id: UUID, data: schemas.HolidayCreate) -> CalendarHoliday:
        """Create a holiday in a profile."""
        holiday = CalendarHoliday(
            id=uuid4(),
            profile_id=profile_id,
            **data.model_dump()
        )
        self.db.add(holiday)
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
        stmt = select(CalendarHoliday).where(CalendarHoliday.id == id)
        result = await self.db.execute(stmt)
        holiday = result.scalar_one_or_none()
        
        if not holiday:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Holiday not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(holiday, key, value)
        
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
        stmt = select(CalendarHoliday).where(CalendarHoliday.id == id)
        result = await self.db.execute(stmt)
        holiday = result.scalar_one_or_none()
        
        if not holiday:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Holiday not found")
        
        holiday_name = holiday.name
        await self.db.delete(holiday)
        await self.db.commit()
        
        await self._audit.log_action(
            action="DELETE",
            resource_type="HOLIDAY",
            resource_id=str(id),
            description=f"Deleted holiday: {holiday_name}"
        )
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Location Calendars
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_location_calendars(self) -> List[LocationCalendar]:
        """Get all location calendars."""
        stmt = select(LocationCalendar).options(
            selectinload(LocationCalendar.work_week_profile),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_location_calendar(self, data: schemas.LocationCalendarCreate) -> LocationCalendar:
        """Create a location calendar."""
        loc_cal = LocationCalendar(
            id=uuid4(),
            **data.model_dump(exclude={"holiday_profile_ids"})
        )
        self.db.add(loc_cal)
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
