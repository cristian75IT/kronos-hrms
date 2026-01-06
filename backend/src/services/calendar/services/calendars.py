"""
KRONOS - Calendar Management Service

Handles personal calendars CRUD and sharing.
"""
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import (
    Calendar, CalendarShare, CalendarType, CalendarPermission
)
from src.services.calendar import schemas
from src.services.calendar.services.base import BaseCalendarService


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
        own_stmt = select(Calendar).options(
            selectinload(Calendar.shares)
        ).where(Calendar.owner_id == user_id)
        
        own_result = await self.db.execute(own_stmt)
        own_calendars = list(own_result.scalars().all())
        
        # Shared with me
        shared_stmt = (
            select(Calendar)
            .options(selectinload(Calendar.shares))
            .join(CalendarShare, Calendar.id == CalendarShare.calendar_id)
            .where(CalendarShare.shared_with_id == user_id)
        )
        shared_result = await self.db.execute(shared_stmt)
        shared_calendars = list(shared_result.scalars().all())
        
        # Combine and deduplicate
        calendar_ids = {c.id for c in own_calendars}
        for cal in shared_calendars:
            if cal.id not in calendar_ids:
                own_calendars.append(cal)
                calendar_ids.add(cal.id)
        
        return own_calendars
    
    async def create_calendar(self, user_id: UUID, data: schemas.CalendarCreate) -> Calendar:
        """Create a new calendar."""
        calendar = Calendar(
            id=uuid4(),
            owner_id=user_id,
            name=data.name,
            description=data.description,
            color=data.color or "#3B82F6",
            calendar_type=data.calendar_type or CalendarType.PERSONAL,
            visibility=data.visibility or "private",
        )
        
        self.db.add(calendar)
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
        stmt = select(Calendar).where(Calendar.id == calendar_id)
        result = await self.db.execute(stmt)
        calendar = result.scalar_one_or_none()
        
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
        stmt = select(Calendar).where(Calendar.id == calendar_id)
        result = await self.db.execute(stmt)
        calendar = result.scalar_one_or_none()
        
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        if calendar.owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not owner of calendar")
        
        calendar_name = calendar.name
        await self.db.delete(calendar)
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
        stmt = select(Calendar).where(Calendar.id == calendar_id)
        result = await self.db.execute(stmt)
        calendar = result.scalar_one_or_none()
        
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        if calendar.owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not owner of calendar")
        
        # Check if already shared
        existing = await self.db.execute(
            select(CalendarShare).where(
                and_(
                    CalendarShare.calendar_id == calendar_id,
                    CalendarShare.shared_with_id == shared_with_user_id
                )
            )
        )
        share = existing.scalar_one_or_none()
        
        if share:
            share.permission = permission
        else:
            share = CalendarShare(
                id=uuid4(),
                calendar_id=calendar_id,
                shared_with_id=shared_with_user_id,
                permission=permission,
            )
            self.db.add(share)
        
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
        stmt = select(Calendar).where(Calendar.id == calendar_id)
        result = await self.db.execute(stmt)
        calendar = result.scalar_one_or_none()
        
        if not calendar:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Calendar not found")
        
        if calendar.owner_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not owner of calendar")
        
        share_result = await self.db.execute(
            select(CalendarShare).where(
                and_(
                    CalendarShare.calendar_id == calendar_id,
                    CalendarShare.shared_with_id == shared_with_user_id
                )
            )
        )
        share = share_result.scalar_one_or_none()
        
        if share:
            await self.db.delete(share)
            await self.db.commit()
            
            await self._audit.log_action(
                user_id=user_id,
                action="UNSHARE",
                resource_type="CALENDAR",
                resource_id=str(calendar_id),
                description=f"Removed sharing with user {shared_with_user_id}"
            )
        
        return True
