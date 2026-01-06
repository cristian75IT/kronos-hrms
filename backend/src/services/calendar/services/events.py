"""
KRONOS - Calendar Events Service

Handles calendar events CRUD operations.
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import (
    Calendar, CalendarEvent, CalendarShare, CalendarType
)
from src.services.calendar import schemas
from src.services.calendar.services.base import BaseCalendarService


class CalendarEventService(BaseCalendarService):
    """
    Service for calendar events management.
    
    Handles:
    - Get visible events
    - Create/update/delete events
    - Event visibility/permissions
    """
    
    async def get_visible_events(
        self, 
        user_id: UUID, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None,
        event_type: Optional[str] = None
    ) -> List[CalendarEvent]:
        """Get events from all calendars visible to the user."""
        # Get calendar IDs the user can see
        own_calendars = await self.db.execute(
            select(Calendar.id).where(Calendar.owner_id == user_id)
        )
        own_ids = [r[0] for r in own_calendars.fetchall()]
        
        shared_calendars = await self.db.execute(
            select(CalendarShare.calendar_id).where(CalendarShare.shared_with_id == user_id)
        )
        shared_ids = [r[0] for r in shared_calendars.fetchall()]
        
        # Get public calendars
        public_calendars = await self.db.execute(
            select(Calendar.id).where(Calendar.visibility == "public")
        )
        public_ids = [r[0] for r in public_calendars.fetchall()]
        
        all_calendar_ids = list(set(own_ids + shared_ids + public_ids))
        
        if not all_calendar_ids:
            return []
        
        # Build query
        stmt = select(CalendarEvent).where(CalendarEvent.calendar_id.in_(all_calendar_ids))
        
        if start_date:
            stmt = stmt.where(CalendarEvent.end_date >= start_date)
        if end_date:
            stmt = stmt.where(CalendarEvent.start_date <= end_date)
        if event_type:
            stmt = stmt.where(CalendarEvent.event_type == event_type)
        
        stmt = stmt.order_by(CalendarEvent.start_date)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_event(self, event_id: UUID) -> Optional[CalendarEvent]:
        """Get event by ID."""
        stmt = select(CalendarEvent).where(CalendarEvent.id == event_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_event(self, user_id: UUID, data: schemas.EventCreate) -> CalendarEvent:
        """Create a new calendar event."""
        # Get or create default calendar for user
        calendar_id = data.calendar_id
        if not calendar_id:
            calendar_id = await self._get_or_create_default_calendar(user_id)
        
        # Validate calendar access
        calendar = await self._get_calendar_with_access(calendar_id, user_id, require_write=True)
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="No write access to calendar")
        
        # Create event
        event_data = data.model_dump(exclude={"calendar_id"})
        event = CalendarEvent(
            id=uuid4(),
            calendar_id=calendar_id,
            created_by=user_id,
            **event_data
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(event.id),
            description=f"Created event: {event.title}",
            request_data=data.model_dump(mode="json")
        )
        
        return event
    
    async def update_event(
        self, 
        event_id: UUID, 
        data: schemas.EventUpdate, 
        user_id: UUID
    ) -> CalendarEvent:
        """Update a calendar event."""
        event = await self.get_event(event_id)
        if not event:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check write access
        calendar = await self._get_calendar_with_access(event.calendar_id, user_id, require_write=True)
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="No write access to this event")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        
        await self.db.commit()
        await self.db.refresh(event)
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(event_id),
            description=f"Updated event: {event.title}",
            request_data=update_data
        )
        
        return event
    
    async def delete_event(self, event_id: UUID, user_id: UUID) -> bool:
        """Delete a calendar event."""
        event = await self.get_event(event_id)
        if not event:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check write access
        calendar = await self._get_calendar_with_access(event.calendar_id, user_id, require_write=True)
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="No write access to this event")
        
        event_title = event.title
        await self.db.delete(event)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(event_id),
            description=f"Deleted event: {event_title}"
        )
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_or_create_default_calendar(self, user_id: UUID) -> UUID:
        """Get or create user's default personal calendar."""
        stmt = select(Calendar).where(
            and_(
                Calendar.owner_id == user_id,
                Calendar.calendar_type == CalendarType.PERSONAL
            )
        ).limit(1)
        result = await self.db.execute(stmt)
        calendar = result.scalar_one_or_none()
        
        if calendar:
            return calendar.id
        
        # Create default calendar
        calendar = Calendar(
            id=uuid4(),
            owner_id=user_id,
            name="Il mio calendario",
            calendar_type=CalendarType.PERSONAL,
            visibility="private",
            color="#3B82F6",
        )
        self.db.add(calendar)
        await self.db.commit()
        return calendar.id
    
    async def _get_calendar_with_access(
        self, 
        calendar_id: UUID, 
        user_id: UUID, 
        require_write: bool = False
    ) -> Optional[Calendar]:
        """Get calendar if user has access."""
        stmt = select(Calendar).options(
            selectinload(Calendar.shares)
        ).where(Calendar.id == calendar_id)
        result = await self.db.execute(stmt)
        calendar = result.scalar_one_or_none()
        
        if not calendar:
            return None
        
        # Owner has full access
        if calendar.owner_id == user_id:
            return calendar
        
        # Check shares
        for share in calendar.shares:
            if share.shared_with_id == user_id:
                if require_write:
                    from src.services.calendar.models import CalendarPermission
                    if share.permission in [CalendarPermission.WRITE, CalendarPermission.ADMIN]:
                        return calendar
                else:
                    return calendar
        
        # Public calendar (read-only)
        if not require_write and calendar.visibility == "public":
            return calendar
        
        return None
