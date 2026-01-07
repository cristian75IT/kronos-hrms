"""
KRONOS - Calendar Management Service

Handles personal calendars CRUD and sharing.
"""
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from src.services.calendar.models import (
    Calendar, CalendarShare, CalendarType, CalendarPermission
)
from src.services.calendar import schemas
from src.services.calendar.services.base import BaseCalendarService
from src.services.calendar.exceptions import CalendarNotFound, CalendarAccessDenied


class CalendarManagementService(BaseCalendarService):
    """
    Service for personal calendar management.
    
    Handles:
    - Get/create/update/delete calendars
    - Share/unshare calendars
    """
    
    async def get_calendars(self, user_id: UUID) -> List[Calendar]:
        """Get all calendars accessible by user (Personal + Shared + Public)."""
        # Own calendars
        own_calendars = await self._repo.get_owned_calendars(user_id)
        
        # Shared with me
        shared_calendars = await self._repo.get_shared_with_user(user_id)
        
        # Combine and deduplicate
        combined = list(own_calendars)
        calendar_ids = {c.id for c in combined}
        for cal in shared_calendars:
            if cal.id not in calendar_ids:
                combined.append(cal)
                calendar_ids.add(cal.id)
        
        return combined
    
    async def create_calendar(self, user_id: UUID, data: schemas.CalendarCreate) -> Calendar:
        """Create a new calendar."""
        calendar = Calendar(
            id=uuid4(),
            owner_id=user_id,
            name=data.name,
            description=data.description,
            color=data.color or "#3B82F6",
            type=data.type or CalendarType.PERSONAL,
            visibility=data.visibility or "private",
        )
        
        await self._repo.create(calendar)
        await self.db.commit()
        await self.db.refresh(calendar)
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="CALENDAR",
            resource_id=str(calendar.id),
            description=f"Created calendar: {calendar.name}",
            request_data=data.model_dump(mode="json")
        )
        
        return calendar
    
    async def update_calendar(
        self, 
        user_id: UUID, 
        calendar_id: UUID, 
        data: schemas.CalendarUpdate
    ) -> Calendar:
        """Update a calendar."""
        calendar = await self._repo.get(calendar_id)
        
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        if calendar.owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not owner of calendar")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(calendar, key, value)
        
        await self.db.commit()
        await self.db.refresh(calendar)
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="CALENDAR",
            resource_id=str(calendar_id),
            description=f"Updated calendar: {calendar.name}",
            request_data=update_data
        )
        
        return calendar
    
    async def delete_calendar(self, user_id: UUID, calendar_id: UUID) -> bool:
        """Delete a calendar."""
        calendar = await self._repo.get(calendar_id)
        
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        if calendar.owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not owner of calendar")
        
        calendar_name = calendar.name
        await self._repo.delete(calendar)
        await self.db.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="CALENDAR",
            resource_id=str(calendar_id),
            description=f"Deleted calendar: {calendar_name}"
        )
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Sharing
    # ═══════════════════════════════════════════════════════════════════════
    
    async def share_calendar(
        self, 
        calendar_id: UUID, 
        user_id: UUID, 
        shared_with_user_id: UUID, 
        permission: CalendarPermission
    ) -> CalendarShare:
        """Share a calendar with another user."""
        calendar = await self._repo.get(calendar_id)
        
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        if calendar.owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not owner of calendar")
        
        # Check if already shared
        share = await self._share_repo.get_by_calendar_and_user(calendar_id, shared_with_user_id)
        
        if share:
            share.permission = permission
        else:
            share = CalendarShare(
                id=uuid4(),
                calendar_id=calendar_id,
                user_id=shared_with_user_id,
                permission=permission,
            )
            await self._share_repo.create(share)
        
        await self.db.commit()
        await self.db.refresh(share)
        
        await self._audit.log_action(
            user_id=user_id,
            action="SHARE",
            resource_type="CALENDAR",
            resource_id=str(calendar_id),
            description=f"Shared calendar with user {shared_with_user_id}",
            request_data={"shared_with": str(shared_with_user_id), "permission": permission.value}
        )
        
        return share
    
    async def unshare_calendar(
        self, 
        calendar_id: UUID, 
        user_id: UUID, 
        shared_with_user_id: UUID
    ) -> bool:
        """Remove calendar sharing."""
        calendar = await self._repo.get(calendar_id)
        
        if not calendar:
            raise CalendarNotFound(calendar_id)
        
        if calendar.owner_id != user_id:
            raise CalendarAccessDenied(calendar_id, user_id, "unshare")
        
        share = await self._share_repo.get_by_calendar_and_user(calendar_id, shared_with_user_id)
        
        if share:
            await self._share_repo.delete(share)
            await self.db.commit()
            
            await self._audit.log_action(
                user_id=user_id,
                action="UNSHARE",
                resource_type="CALENDAR",
                resource_id=str(calendar_id),
                description=f"Removed sharing with user {shared_with_user_id}"
            )
        
        return True
