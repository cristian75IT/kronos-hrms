"""
KRONOS - Calendar Events Service

Handles calendar events CRUD operations.
"""
from datetime import date, datetime, time, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import (
    Calendar, CalendarEvent, CalendarShare, CalendarType, EventParticipant
)
from src.services.calendar import schemas
from src.services.calendar.services.base import BaseCalendarService
from src.services.calendar.exceptions import EventNotFound, EventAccessDenied, CalendarAccessDenied


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
        own_calendars = await self._repo.get_owned_calendars(user_id)
        own_ids = [c.id for c in own_calendars]
        
        shared_calendars = await self._repo.get_shared_with_user(user_id)
        shared_ids = [c.id for c in shared_calendars]
        
        # Get public calendars
        public_calendars = await self._repo.get_public_calendars()
        public_ids = [c.id for c in public_calendars]
        
        all_calendar_ids = list(set(own_ids + shared_ids + public_ids))
        
        if not all_calendar_ids:
            return []
        
        # Build query via repo
        return await self._event_repo.get_visible_events(
            calendar_ids=all_calendar_ids,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type
        )
    
    async def get_event(self, event_id: UUID) -> Optional[CalendarEvent]:
        """Get event by ID."""
        return await self._event_repo.get(event_id)
    
    async def create_event(self, user_id: UUID, data: schemas.EventCreate) -> CalendarEvent:
        """Create a new calendar event."""
        # Get or create default calendar for user
        calendar_id = data.calendar_id
        if not calendar_id:
            logger.info(f"No calendar_id provided, resolving default for user {user_id}")
            calendar_id = await self._get_or_create_default_calendar(user_id)
            logger.info(f"Resolved default calendar_id: {calendar_id}")
        
        # Validate calendar access
        calendar = await self._get_calendar_with_access(calendar_id, user_id, require_write=True)
        if not calendar:
            logger.warning(f"User {user_id} denied write access to calendar {calendar_id}")
            raise CalendarAccessDenied(calendar_id, user_id, "write")
        
        # Create event
        event_dict = data.model_dump(exclude={"calendar_id", "participant_ids"})
        event = CalendarEvent(
            id=uuid4(),
            calendar_id=calendar_id,
            created_by=user_id,
            **event_dict
        )
        
        event = await self._event_repo.create(event)
        
        # Add participants
        if data.participant_ids:
            for p_user_id in data.participant_ids:
                participant = EventParticipant(
                    id=uuid4(),
                    event_id=event.id,
                    user_id=p_user_id,
                    is_organizer=(p_user_id == user_id)
                )
                # assuming the session is managed by the service
                event.participants.append(participant)
            
        
        logger.info("Committing event to DB")
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
        
        # Reload event to ensure relationships are loaded (e.g. participants)
        # This prevents MissingGreenlet error in response model validation
        loaded_event = await self.get_event(event.id)
        if loaded_event:
            event = loaded_event
        
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
            raise EventNotFound(event_id)
        
        # Check write access
        calendar = await self._get_calendar_with_access(event.calendar_id, user_id, require_write=True)
        if not calendar:
            raise EventAccessDenied(event_id, user_id, "delete")
        
        update_dict = data.model_dump(exclude_unset=True, exclude={"participant_ids"})
        for key, value in update_dict.items():
            setattr(event, key, value)
        
        # Handle participants update if provided
        if data.participant_ids is not None:
            # Clear existing participants
            event.participants = []
            # Add new participants
            for p_user_id in data.participant_ids:
                participant = EventParticipant(
                    id=uuid4(),
                    event_id=event.id,
                    user_id=p_user_id,
                    is_organizer=(p_user_id == user_id)
                )
                event.participants.append(participant)

        await self._event_repo.update(event)
        await self.db.commit()

        # Reload event properly to load relationships
        loaded_event = await self.get_event(event.id)
        if loaded_event:
            event = loaded_event
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="CALENDAR_EVENT",
            resource_id=str(event_id),
            description=f"Updated event: {event.title}",
            request_data=update_dict
        )
        
        return event
    
    async def delete_event(self, event_id: UUID, user_id: UUID) -> bool:
        """Delete a calendar event."""
        event = await self.get_event(event_id)
        if not event:
            raise EventNotFound(event_id)
        
        # Check write access
        calendar = await self._get_calendar_with_access(event.calendar_id, user_id, require_write=True)
        if not calendar:
            raise EventAccessDenied(event_id, user_id, "write")
        
        event_title = event.title
        await self._event_repo.delete(event)
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
        calendar = await self._repo.get_personal_calendar(user_id)
        
        if calendar:
            return calendar.id
        
        # Create default calendar
        calendar = Calendar(
            id=uuid4(),
            owner_id=user_id,
            name="Il mio calendario",
            type=CalendarType.PERSONAL,
            visibility="private",
            color="#3B82F6",
        )
        await self._repo.create(calendar)
        await self.db.commit()
        return calendar.id
    
    async def _get_calendar_with_access(
        self, 
        calendar_id: UUID, 
        user_id: UUID, 
        require_write: bool = False
    ) -> Optional[Calendar]:
        """Get calendar if user has access."""
        calendar = await self._repo.get(calendar_id)
        
        if not calendar:
            return None
        
        # Owner has full access
        if calendar.owner_id == user_id:
            return calendar
        
        # Check shares
        for share in calendar.shares:
            if share.user_id == user_id:
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
