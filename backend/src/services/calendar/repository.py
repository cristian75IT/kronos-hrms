from datetime import date
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select, or_, and_, delete, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Calendar,
    CalendarType,
    CalendarShare,
    CalendarEvent,
    WorkWeekProfile,
    HolidayProfile,
    CalendarHoliday,
    LocationCalendar,
    CalendarClosure,
    WorkingDayException,
    CalendarPermission,
    LocationSubscription,
)
from src.core.exceptions import NotFoundError


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class CalendarRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[Calendar]:
        stmt = select(Calendar).options(selectinload(Calendar.shares)).where(Calendar.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_accessible_calendars(self, user_id: UUID) -> Sequence[Calendar]:
        """
        Get all calendars accessible by user:
        - Owned by user
        - Shared with user
        - System / Location (public)
        """
        stmt = select(Calendar).options(selectinload(Calendar.shares)).outerjoin(
            CalendarShare, Calendar.id == CalendarShare.calendar_id
        ).where(
            or_(
                Calendar.owner_id == user_id,
                CalendarShare.user_id == user_id,
                Calendar.type.in_([CalendarType.SYSTEM, CalendarType.LOCATION])
            )
        ).distinct()
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_system_calendars(self) -> Sequence[Calendar]:
        stmt = select(Calendar).where(Calendar.type == CalendarType.SYSTEM, Calendar.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_personal_calendar(self, user_id: UUID) -> Optional[Calendar]:
        stmt = select(Calendar).where(
            Calendar.owner_id == user_id,
            Calendar.type == CalendarType.PERSONAL
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_owned_calendars(self, user_id: UUID) -> Sequence[Calendar]:
        stmt = select(Calendar).options(selectinload(Calendar.shares)).where(Calendar.owner_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_shared_with_user(self, user_id: UUID) -> Sequence[Calendar]:
        stmt = (
            select(Calendar)
            .options(selectinload(Calendar.shares))
            .join(CalendarShare, Calendar.id == CalendarShare.calendar_id)
            .where(CalendarShare.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_public_calendars(self) -> Sequence[Calendar]:
        stmt = select(Calendar).options(selectinload(Calendar.shares)).where(Calendar.visibility == "public")
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, calendar: Calendar) -> Calendar:
        self.session.add(calendar)
        await self.session.flush()
        # Refresh with relationships if needed, or done by caller
        return calendar

    async def update(self, calendar: Calendar) -> Calendar:
        self.session.add(calendar)
        await self.session.flush()
        return calendar

    async def delete(self, calendar: Calendar):
        await self.session.delete(calendar)
        await self.session.flush()


class CalendarShareRepository(BaseRepository):
    async def get(self, calendar_id: UUID, user_id: UUID) -> Optional[CalendarShare]:
        stmt = select(CalendarShare).where(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_with_permission(self, calendar_id: UUID, user_id: UUID, permissions: List[CalendarPermission]) -> Optional[CalendarShare]:
         stmt = select(CalendarShare).where(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.user_id == user_id,
            CalendarShare.permission.in_(permissions)
        )
         result = await self.session.execute(stmt)
         return result.scalar_one_or_none()

    async def get_by_calendar_and_user(self, calendar_id: UUID, user_id: UUID) -> Optional[CalendarShare]:
        stmt = select(CalendarShare).where(
            CalendarShare.calendar_id == calendar_id,
            CalendarShare.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, share: CalendarShare) -> CalendarShare:
        self.session.add(share)
        await self.session.flush()
        return share

    async def delete(self, share: CalendarShare):
        await self.session.delete(share)
        await self.session.flush()


class CalendarEventRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[CalendarEvent]:
        stmt = select(CalendarEvent).where(CalendarEvent.id == id).options(
            selectinload(CalendarEvent.participants),
            selectinload(CalendarEvent.calendar)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_visible_events(
        self, 
        calendar_ids: List[UUID], 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        event_type: Optional[str] = None
    ) -> Sequence[CalendarEvent]:
        if not calendar_ids:
            return []

        stmt = select(CalendarEvent).where(CalendarEvent.calendar_id.in_(calendar_ids))

        if start_date:
            stmt = stmt.where(CalendarEvent.end_date >= start_date)
        if end_date:
            stmt = stmt.where(CalendarEvent.start_date <= end_date)
        if event_type:
            stmt = stmt.where(CalendarEvent.event_type == event_type)

        stmt = stmt.options(
            selectinload(CalendarEvent.participants),
            selectinload(CalendarEvent.calendar)
        ).order_by(CalendarEvent.start_date, CalendarEvent.start_time)

        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_closures(self, calendar_ids: List[UUID], start_date: date, end_date: date) -> Sequence[CalendarEvent]:
        if not calendar_ids:
            return []
            
        stmt = select(CalendarEvent).where(
            CalendarEvent.calendar_id.in_(calendar_ids),
            CalendarEvent.event_type == 'closure', 
            CalendarEvent.start_date <= end_date,
            CalendarEvent.end_date >= start_date
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, event: CalendarEvent) -> CalendarEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def update(self, event: CalendarEvent) -> CalendarEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def delete(self, event: CalendarEvent):
        await self.session.delete(event)
        await self.session.flush()


class WorkWeekProfileRepository(BaseRepository):
    async def get_all(self) -> Sequence[WorkWeekProfile]:
        result = await self.session.execute(select(WorkWeekProfile))
        return result.scalars().all()

    async def get(self, id: UUID) -> Optional[WorkWeekProfile]:
        return await self.session.get(WorkWeekProfile, id)

    async def get_default(self) -> Optional[WorkWeekProfile]:
        stmt = select(WorkWeekProfile).where(WorkWeekProfile.is_default == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, profile: WorkWeekProfile) -> WorkWeekProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update(self, profile: WorkWeekProfile) -> WorkWeekProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def delete(self, profile: WorkWeekProfile):
        await self.session.delete(profile)
        await self.session.flush()


class HolidayProfileRepository(BaseRepository):
    async def get_all(self) -> Sequence[HolidayProfile]:
        stmt = select(HolidayProfile).options(selectinload(HolidayProfile.holidays))
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get(self, id: UUID) -> Optional[HolidayProfile]:
        return await self.session.get(HolidayProfile, id)
        
    async def get_by_calendar_ids(self, calendar_ids: List[UUID]) -> Sequence[HolidayProfile]:
        stmt = select(HolidayProfile).where(HolidayProfile.calendar_id.in_(calendar_ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, profile: HolidayProfile) -> HolidayProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile
    
    async def update(self, profile: HolidayProfile) -> HolidayProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def delete(self, profile: HolidayProfile):
        await self.session.delete(profile)
        await self.session.flush()


class CalendarHolidayRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[CalendarHoliday]:
        return await self.session.get(CalendarHoliday, id)

    async def get_by_profile(self, profile_id: UUID) -> Sequence[CalendarHoliday]:
        stmt = select(CalendarHoliday).where(
            CalendarHoliday.profile_id == profile_id,
            CalendarHoliday.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_profiles(self, profile_ids: List[UUID]) -> Sequence[CalendarHoliday]:
        if not profile_ids:
            return []
        stmt = select(CalendarHoliday).where(
            CalendarHoliday.profile_id.in_(profile_ids),
            CalendarHoliday.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, holiday: CalendarHoliday) -> CalendarHoliday:
        self.session.add(holiday)
        await self.session.flush()
        return holiday
        
    async def update(self, holiday: CalendarHoliday) -> CalendarHoliday:
        self.session.add(holiday)
        await self.session.flush()
        return holiday

    async def delete(self, holiday: CalendarHoliday):
        await self.session.delete(holiday)
        await self.session.flush()


class LocationCalendarRepository(BaseRepository):
    async def get_by_location(self, location_id: Optional[UUID]) -> Optional[LocationCalendar]:
        if not location_id:
            return None
            
        stmt = select(LocationCalendar).options(
            joinedload(LocationCalendar.work_week_profile),
            selectinload(LocationCalendar.subscriptions)
            .joinedload(LocationSubscription.calendar)
            .joinedload(Calendar.holiday_profile)
            .selectinload(HolidayProfile.holidays),
        ).where(LocationCalendar.location_id == location_id)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(self) -> Optional[LocationCalendar]:
        stmt = (
            select(LocationCalendar)
            .options(
                joinedload(LocationCalendar.work_week_profile),
                selectinload(LocationCalendar.subscriptions)
                .joinedload(LocationSubscription.calendar)
                .joinedload(Calendar.holiday_profile)
                .selectinload(HolidayProfile.holidays),
            )
            .where(LocationCalendar.location_id == None)
            .where(LocationCalendar.is_default == True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[LocationCalendar]:
        stmt = select(LocationCalendar).options(
            joinedload(LocationCalendar.work_week_profile),
            selectinload(LocationCalendar.subscriptions)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, location_calendar: LocationCalendar) -> LocationCalendar:
        self.session.add(location_calendar)
        await self.session.flush()
        return location_calendar


class CalendarClosureRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[CalendarClosure]:
         return await self.session.get(CalendarClosure, id)

    async def create(self, closure: CalendarClosure) -> CalendarClosure:
        self.session.add(closure)
        await self.session.flush()
        return closure
        
    async def update(self, closure: CalendarClosure) -> CalendarClosure:
        self.session.add(closure)
        await self.session.flush()
        return closure

    async def get_by_year(self, year: int, location_id: Optional[UUID] = None) -> Sequence[CalendarClosure]:
        stmt = select(CalendarClosure).where(
            func.extract('year', CalendarClosure.start_date) == year
        )
        if location_id:
            stmt = stmt.where(CalendarClosure.location_id == location_id)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, closure: CalendarClosure):
        await self.session.delete(closure)
        await self.session.flush()



class WorkingDayExceptionRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[WorkingDayException]:
        return await self.session.get(WorkingDayException, id)

    async def get_by_year(self, year: int, location_id: Optional[UUID] = None) -> Sequence[WorkingDayException]:
        stmt = select(WorkingDayException).where(
            func.extract('year', WorkingDayException.date) == year
        )
        if location_id:
            stmt = stmt.where(WorkingDayException.location_id == location_id)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, exception: WorkingDayException) -> WorkingDayException:
        self.session.add(exception)
        await self.session.flush()
        return exception

    async def delete(self, exception: WorkingDayException):
        await self.session.delete(exception)
        await self.session.flush()
