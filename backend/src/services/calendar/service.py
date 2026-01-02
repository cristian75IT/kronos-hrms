"""KRONOS Calendar Service - Business Logic."""
from datetime import date, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, extract, text
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CalendarHoliday,
    CalendarClosure,
    CalendarEvent,
    EventParticipant,
    WorkingDayException,
    UserCalendar,
    CalendarShare,
)
from .schemas import (
    HolidayCreate,
    HolidayUpdate,
    ClosureCreate,
    ClosureUpdate,
    EventCreate,
    EventUpdate,
    UserCalendarCreate,
    UserCalendarUpdate,
    WorkingDayExceptionCreate,
    CalendarDayItem,
    CalendarDayView,
    CalendarRangeView,
    WorkingDaysResponse,
)
from src.shared.audit_client import get_audit_logger


class CalendarService:
    """Service for managing calendar operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = get_audit_logger("calendar-service")
    
    # ═══════════════════════════════════════════════════════════
    # USER CALENDARS CRUD
    # ═══════════════════════════════════════════════════════════
    
    async def get_user_calendars(self, user_id: UUID) -> List[UserCalendar]:
        """Get all custom calendars for a user (owned and shared)."""
        # Owned calendars
        query_owned = (
            select(UserCalendar)
            .options(joinedload(UserCalendar.shared_with))
            .where(UserCalendar.user_id == user_id)
        )
        
        # Shared with me calendars
        query_shared = (
            select(UserCalendar)
            .join(CalendarShare)
            .options(joinedload(UserCalendar.shared_with))
            .where(CalendarShare.shared_with_user_id == user_id)
        )
        
        result_owned = await self.db.execute(query_owned)
        owned = result_owned.scalars().unique().all()
        
        result_shared = await self.db.execute(query_shared)
        shared = result_shared.scalars().unique().all()
        
        # Tag owned vs shared for the service return if needed
        # But we'll handle the 'is_owner' flag in the response schema logic
        return list(owned) + list(shared)

    async def share_calendar(self, calendar_id: UUID, user_id: UUID, shared_with_user_id: UUID, can_edit: bool = False) -> Optional[CalendarShare]:
        """Share a calendar with another user."""
        # Verify ownership
        calendar = await self.get_user_calendar(calendar_id, user_id)
        if not calendar:
            return None
            
        share = CalendarShare(
            calendar_id=calendar_id,
            shared_with_user_id=shared_with_user_id,
            can_edit=can_edit
        )
        self.db.add(share)
        await self.db.commit()
        await self.db.refresh(share)
        return share

    async def unshare_calendar(self, calendar_id: UUID, user_id: UUID, shared_with_user_id: UUID) -> bool:
        """Remove a calendar share."""
        # Verify ownership
        calendar = await self.get_user_calendar(calendar_id, user_id)
        if not calendar:
            return False
            
        query = select(CalendarShare).where(
            and_(CalendarShare.calendar_id == calendar_id, CalendarShare.shared_with_user_id == shared_with_user_id)
        )
        result = await self.db.execute(query)
        share = result.scalar_one_or_none()
        
        if share:
            await self.db.delete(share)
            await self.db.commit()
            return True
        return False

    async def get_user_calendar(self, calendar_id: UUID, user_id: UUID) -> Optional[UserCalendar]:
        """Get a single custom calendar with shares."""
        query = (
            select(UserCalendar)
            .options(joinedload(UserCalendar.shared_with))
            .where(and_(UserCalendar.id == calendar_id, UserCalendar.user_id == user_id))
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def create_user_calendar(self, user_id: UUID, data: UserCalendarCreate) -> UserCalendar:
        """Create a new custom calendar."""
        calendar = UserCalendar(user_id=user_id, **data.model_dump())
        self.db.add(calendar)
        await self.db.commit()
        return await self.get_user_calendar(calendar.id, user_id)

    async def update_user_calendar(
        self, calendar_id: UUID, user_id: UUID, data: UserCalendarUpdate
    ) -> Optional[UserCalendar]:
        """Update a custom calendar."""
        calendar = await self.get_user_calendar(calendar_id, user_id)
        if not calendar:
            return None
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(calendar, field, value)
            
        await self.db.commit()
        return await self.get_user_calendar(calendar_id, user_id)

    async def delete_user_calendar(self, calendar_id: UUID, user_id: UUID) -> bool:
        """Delete a custom calendar."""
        calendar = await self.get_user_calendar(calendar_id, user_id)
        if not calendar:
            return False
        
        await self.db.delete(calendar)
        await self.db.commit()
        return True

    # ═══════════════════════════════════════════════════════════
    # HOLIDAYS CRUD
    # ═══════════════════════════════════════════════════════════
    
    async def get_holidays(
        self,
        year: Optional[int] = None,
        scope: Optional[str] = None,
        location_id: Optional[UUID] = None,
        include_inactive: bool = False,
    ) -> List[CalendarHoliday]:
        """Get holidays with optional filters."""
        query = select(CalendarHoliday)
        
        if year:
            query = query.where(CalendarHoliday.year == year)
        if scope:
            query = query.where(CalendarHoliday.scope == scope)
        if location_id:
            query = query.where(
                or_(
                    CalendarHoliday.location_id == location_id,
                    CalendarHoliday.location_id.is_(None)
                )
            )
        if not include_inactive:
            query = query.where(CalendarHoliday.is_active == True)
        
        query = query.order_by(CalendarHoliday.date)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_holiday(self, holiday_id: UUID) -> Optional[CalendarHoliday]:
        """Get a single holiday by ID."""
        result = await self.db.execute(
            select(CalendarHoliday).where(CalendarHoliday.id == holiday_id)
        )
        return result.scalar_one_or_none()
    
    async def create_holiday(
        self,
        data: HolidayCreate,
        created_by: Optional[UUID] = None,
    ) -> CalendarHoliday:
        """Create a new holiday."""
        holiday = CalendarHoliday(
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(holiday)
        await self.db.commit()
        await self.db.refresh(holiday)
        return holiday
    
    async def update_holiday(
        self,
        holiday_id: UUID,
        data: HolidayUpdate,
    ) -> Optional[CalendarHoliday]:
        """Update an existing holiday."""
        holiday = await self.get_holiday(holiday_id)
        if not holiday:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(holiday, key, value)
        
        await self.db.commit()
        await self.db.refresh(holiday)
        return holiday
    
    async def delete_holiday(self, holiday_id: UUID) -> bool:
        """Delete a holiday."""
        holiday = await self.get_holiday(holiday_id)
        if not holiday:
            return False
        
        await self.db.delete(holiday)
        await self.db.commit()
        return True
    
    # ═══════════════════════════════════════════════════════════
    # CLOSURES CRUD
    # ═══════════════════════════════════════════════════════════
    
    async def get_closures(
        self,
        year: Optional[int] = None,
        location_id: Optional[UUID] = None,
        include_inactive: bool = False,
    ) -> List[CalendarClosure]:
        """Get company closures with optional filters."""
        query = select(CalendarClosure)
        
        if year:
            query = query.where(CalendarClosure.year == year)
        if not include_inactive:
            query = query.where(CalendarClosure.is_active == True)
        
        if location_id:
            # Filter closures where location_id is in affected_locations OR affected_locations is empty/null
            query = query.where(
                or_(
                    CalendarClosure.affected_locations.is_(None),
                    CalendarClosure.affected_locations == text("'null'::jsonb"),  # Handle string null in JSONB
                    CalendarClosure.affected_locations == text("'[]'::jsonb"),    # Handle empty list
                    CalendarClosure.affected_locations.contains([str(location_id)])
                )
            )
        
        query = query.order_by(CalendarClosure.start_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_closure(self, closure_id: UUID) -> Optional[CalendarClosure]:
        """Get a single closure by ID."""
        result = await self.db.execute(
            select(CalendarClosure).where(CalendarClosure.id == closure_id)
        )
        return result.scalar_one_or_none()
    
    async def create_closure(
        self,
        data: ClosureCreate,
        created_by: Optional[UUID] = None,
    ) -> CalendarClosure:
        """Create a new company closure."""
        closure = CalendarClosure(
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(closure)
        await self.db.commit()
        await self.db.refresh(closure)
        return closure
    
    async def update_closure(
        self,
        closure_id: UUID,
        data: ClosureUpdate,
    ) -> Optional[CalendarClosure]:
        """Update an existing closure."""
        closure = await self.get_closure(closure_id)
        if not closure:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(closure, key, value)
        
        await self.db.commit()
        await self.db.refresh(closure)
        return closure
    
    async def delete_closure(self, closure_id: UUID) -> bool:
        """Delete a closure."""
        closure = await self.get_closure(closure_id)
        if not closure:
            return False
        
        await self.db.delete(closure)
        await self.db.commit()
        return True
    
    # ═══════════════════════════════════════════════════════════
    # EVENTS CRUD
    # ═══════════════════════════════════════════════════════════
    
    async def get_events(
        self,
        user_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        event_type: Optional[str] = None,
        include_public: bool = True,
    ) -> List[CalendarEvent]:
        """Get events with optional filters."""
        query = select(CalendarEvent).options(joinedload(CalendarEvent.participants))
        
        conditions = []
        
        if user_id:
            # Subquery for shared calendar IDs
            shared_calendar_ids = select(CalendarShare.calendar_id).where(
                CalendarShare.shared_with_user_id == user_id
            )
            
            if include_public:
                conditions.append(or_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.visibility == "public",
                    CalendarEvent.calendar_id.in_(shared_calendar_ids),
                ))
            else:
                conditions.append(or_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.calendar_id.in_(shared_calendar_ids),
                ))
        
        if start_date:
            conditions.append(CalendarEvent.end_date >= start_date)
        if end_date:
            conditions.append(CalendarEvent.start_date <= end_date)
        if event_type:
            conditions.append(CalendarEvent.event_type == event_type)
        
        conditions.append(CalendarEvent.status != "cancelled")
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(CalendarEvent.start_date, CalendarEvent.start_time)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_event(self, event_id: UUID) -> Optional[CalendarEvent]:
        """Get a single event by ID with participants."""
        result = await self.db.execute(
            select(CalendarEvent)
            .options(joinedload(CalendarEvent.participants))
            .where(CalendarEvent.id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def create_event(
        self,
        data: EventCreate,
        user_id: UUID,
    ) -> CalendarEvent:
        """Create a new event."""
        event_data = data.model_dump(exclude={"participant_ids"})
        event = CalendarEvent(
            **event_data,
            user_id=user_id,
            created_by=user_id,
        )
        self.db.add(event)
        await self.db.flush()
        
        # Add organizer as participant
        organizer = EventParticipant(
            event_id=event.id,
            user_id=user_id,
            is_organizer=True,
            response_status="accepted",
        )
        self.db.add(organizer)
        
        # Add other participants
        if data.participant_ids:
            for pid in data.participant_ids:
                if pid != user_id:
                    participant = EventParticipant(
                        event_id=event.id,
                        user_id=pid,
                        response_status="pending",
                    )
                    self.db.add(participant)
        
        await self.db.commit()
        # Return fully loaded event
        return await self.get_event(event.id)
    
    async def update_event(
        self,
        event_id: UUID,
        data: EventUpdate,
    ) -> Optional[CalendarEvent]:
        """Update an existing event."""
        event = await self.get_event(event_id)
        if not event:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        
        await self.db.commit()
        # Return fully loaded event
        return await self.get_event(event.id)
    
    async def delete_event(self, event_id: UUID) -> bool:
        """Delete an event (soft delete by setting status to cancelled)."""
        event = await self.get_event(event_id)
        if not event:
            return False
        
        event.status = "cancelled"
        await self.db.commit()
        
        await self._audit.log_action(
            action="DELETE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(event_id),
            description=f"Deleted event {event.title}",
        )
        
        return True
    
    # ═══════════════════════════════════════════════════════════
    # WORKING DAYS CALCULATION
    # ═══════════════════════════════════════════════════════════
    
    async def get_working_day_exceptions(
        self,
        year: int,
        location_id: Optional[UUID] = None,
    ) -> List[WorkingDayException]:
        """Get working day exceptions for a year."""
        query = select(WorkingDayException).where(WorkingDayException.year == year)
        
        if location_id:
            query = query.where(
                or_(
                    WorkingDayException.location_id == location_id,
                    WorkingDayException.location_id.is_(None)
                )
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_working_day_exception(
        self,
        data: WorkingDayExceptionCreate,
        created_by: Optional[UUID] = None,
    ) -> WorkingDayException:
        """Create a working day exception."""
        exception = WorkingDayException(
            **data.model_dump(),
            created_by=created_by,
        )
        self.db.add(exception)
        await self.db.commit()
        await self.db.refresh(exception)
        return exception

    async def delete_working_day_exception(self, exception_id: UUID) -> bool:
        """Delete a working day exception."""
        query = select(WorkingDayException).where(WorkingDayException.id == exception_id)
        result = await self.db.execute(query)
        exception = result.scalar_one_or_none()
        
        if not exception:
            return False
        
        await self.db.delete(exception)
        await self.db.commit()
        return True

    
    async def calculate_working_days(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        exclude_closures: bool = True,
        exclude_holidays: bool = True,
        working_days_per_week: int = 5,
    ) -> WorkingDaysResponse:
        """Calculate working days between two dates."""
        # Get holidays
        holidays_list = []
        if exclude_holidays:
            holidays = await self.get_holidays(
                year=start_date.year,
                location_id=location_id,
            )
            # Handle year boundary
            if end_date.year != start_date.year:
                holidays += await self.get_holidays(
                    year=end_date.year,
                    location_id=location_id,
                )
            holidays_list = [h.date for h in holidays if start_date <= h.date <= end_date]
        
        # Get closures
        closure_days = []
        if exclude_closures:
            closures = await self.get_closures(year=start_date.year, location_id=location_id)
            if end_date.year != start_date.year:
                closures += await self.get_closures(year=end_date.year, location_id=location_id)
            
            for closure in closures:
                current = max(closure.start_date, start_date)
                while current <= min(closure.end_date, end_date):
                    if current not in closure_days:
                        closure_days.append(current)
                    current += timedelta(days=1)
        
        # Get exceptions
        exceptions = await self.get_working_day_exceptions(start_date.year, location_id)
        if end_date.year != start_date.year:
            exceptions += await self.get_working_day_exceptions(end_date.year, location_id)
        
        working_exceptions = {e.date for e in exceptions if e.exception_type == "working"}
        non_working_exceptions = {e.date for e in exceptions if e.exception_type == "non_working"}
        
        # Calculate
        working_days = 0
        weekend_days = []
        current = start_date
        total_days = 0
        
        while current <= end_date:
            total_days += 1
            is_weekend = current.weekday() >= (7 - working_days_per_week) if working_days_per_week < 7 else False
            
            # Standard weekend check (Mon=0, Sun=6)
            if working_days_per_week == 5:
                is_weekend = current.weekday() >= 5  # Sat, Sun
            elif working_days_per_week == 6:
                is_weekend = current.weekday() >= 6  # Sun only
            
            if is_weekend:
                weekend_days.append(current)
            
            # Check if it's a working day
            is_working = not is_weekend
            
            # Apply exceptions
            if current in working_exceptions:
                is_working = True
            if current in non_working_exceptions:
                is_working = False
            
            # Exclude holidays and closures
            if is_working:
                if current in holidays_list or current in closure_days:
                    is_working = False
            
            if is_working:
                working_days += 1
            
            current += timedelta(days=1)
        
        return WorkingDaysResponse(
            start_date=start_date,
            end_date=end_date,
            total_calendar_days=total_days,
            working_days=working_days,
            holidays=holidays_list,
            closure_days=closure_days,
            weekend_days=weekend_days,
        )
    
    # ═══════════════════════════════════════════════════════════
    # AGGREGATED CALENDAR VIEW
    # ═══════════════════════════════════════════════════════════
    
    async def get_calendar_absences(self, start_date: date, end_date: date, user_id: Optional[UUID] = None) -> List[any]:
        """Fetch approved absences from leave service tables."""
        # Query directly from leaves.leave_requests joined with auth.users
        # This is a cross-schema query allowed in our shared-DB architecture
        sql = """
            SELECT 
                lr.id,
                lr.start_date,
                lr.end_date,
                lr.leave_type_code,
                u.first_name,
                u.last_name
            FROM leaves.leave_requests lr
            JOIN auth.users u ON lr.user_id = u.id
            WHERE lr.status = 'approved'
              AND lr.end_date >= :start_date
              AND lr.start_date <= :end_date
        """
        params = {"start_date": start_date, "end_date": end_date}
        
        if user_id:
            sql += " AND lr.user_id = :user_id"
            params["user_id"] = user_id
            
        result = await self.db.execute(text(sql), params)
        return list(result.mappings().all())

    async def get_calendar_range(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        working_days_per_week: int = 5,
    ) -> CalendarRangeView:
        """Get aggregated calendar view for a date range."""
        # Fetch all data
        holidays = await self.get_holidays(year=start_date.year, location_id=location_id)
        if end_date.year != start_date.year:
            holidays += await self.get_holidays(year=end_date.year, location_id=location_id)
        
        closures = await self.get_closures(year=start_date.year, location_id=location_id)
        if end_date.year != start_date.year:
            closures += await self.get_closures(year=end_date.year, location_id=location_id)
        
        exceptions = await self.get_working_day_exceptions(start_date.year, location_id)
        if end_date.year != start_date.year:
            exceptions += await self.get_working_day_exceptions(end_date.year, location_id)
        
        working_exceptions = {e.date for e in exceptions if e.exception_type == "working"}
        non_working_exceptions = {e.date for e in exceptions if e.exception_type == "non_working"}

        events = await self.get_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # NEW: Fetch absences (restore global visibility for team)
        absences = await self.get_calendar_absences(start_date, end_date)
        
        working_days_result = await self.calculate_working_days(
            start_date, end_date, location_id, working_days_per_week=working_days_per_week
        )
        
        # Build day views
        days = []
        current = start_date
        
        while current <= end_date:
            is_holiday = any(h.date == current for h in holidays)
            
            # Weekend logic matching calculate_working_days
            is_weekend = current.weekday() >= (7 - working_days_per_week) if working_days_per_week < 7 else False
            if working_days_per_week == 5:
                is_weekend = current.weekday() >= 5
            elif working_days_per_week == 6:
                is_weekend = current.weekday() >= 6
                
            is_closure = any(c.start_date <= current <= c.end_date for c in closures)
            
            items = []
            
            # Add holidays
            for h in holidays:
                if h.date == current:
                    items.append(CalendarDayItem(
                        id=h.id,
                        title=h.name,
                        item_type="holiday",
                        start_date=h.date,
                        end_date=h.date,
                        color="#EF4444",
                    ))
            
            # Add closures
            for c in closures:
                if c.start_date <= current <= c.end_date:
                    items.append(CalendarDayItem(
                        id=c.id,
                        title=c.name,
                        item_type="closure",
                        start_date=c.start_date,
                        end_date=c.end_date,
                        color="#F59E0B",
                    ))
            
            # Add absences
            for a in absences:
                if a["start_date"] <= current <= a["end_date"]:
                    items.append(CalendarDayItem(
                        id=a["id"],
                        title=f"{a['leave_type_code']}: {a['first_name']} {a['last_name']}",
                        item_type="leave",
                        start_date=a["start_date"],
                        end_date=a["end_date"],
                        color="#8B5CF6",
                        metadata={"leave_type": a["leave_type_code"]},
                    ))

            # Add events
            for e in events:
                if e.start_date <= current <= e.end_date:
                    items.append(CalendarDayItem(
                        id=e.id,
                        title=e.title,
                        item_type="event",
                        start_date=e.start_date,
                        end_date=e.end_date,
                        color=e.color,
                        metadata={"event_type": e.event_type, "calendar_id": str(e.calendar_id) if e.calendar_id else None},
                    ))
            
            # Determine if it's a working day (consistent with calculate_working_days)
            is_working = not is_weekend
            if current in working_exceptions:
                is_working = True
            if current in non_working_exceptions:
                is_working = False
            if is_working and (is_holiday or is_closure):
                is_working = False
            
            days.append(CalendarDayView(
                date=current,
                is_working_day=is_working,
                is_holiday=is_holiday,
                items=items,
            ))
            
            current += timedelta(days=1)
        
        return CalendarRangeView(
            start_date=start_date,
            end_date=end_date,
            days=days,
            working_days_count=working_days_result.working_days,
        )

    async def is_working_day(
        self,
        check_date: date,
        location_id: Optional[UUID] = None,
        working_days_per_week: int = 5,
    ) -> bool:
        """Check if a specific date is a working day."""
        result = await self.calculate_working_days(
            check_date, check_date, location_id, working_days_per_week=working_days_per_week
        )
        return result.working_days == 1
