"""KRONOS Calendar Service - Events Router."""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user
from ..schemas import EventCreate, EventUpdate, EventResponse
from ..service import CalendarService

router = APIRouter()


@router.get("", response_model=List[EventResponse])
async def list_events(
    start_date: Optional[date] = Query(None, description="Start date for range filter"),
    end_date: Optional[date] = Query(None, description="End date for range filter"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    include_public: bool = Query(True, description="Include public events"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get calendar events for the current user."""
    service = CalendarService(db)
    events = await service.get_events(
        user_id=current_user.get("id"),
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        include_public=include_public,
    )
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific event by ID."""
    service = CalendarService(db)
    event = await service.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    # Check visibility
    user_id = current_user.get("id")
    if event.visibility == "private" and str(event.user_id) != str(user_id):
        # Check if user is a participant
        participant_ids = [str(p.user_id) for p in event.participants]
        if str(user_id) not in participant_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this event",
            )
    
    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new calendar event."""
    service = CalendarService(db)
    event = await service.create_event(
        data=data,
        user_id=current_user.get("id"),
    )
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing event. Only the owner can update."""
    service = CalendarService(db)
    event = await service.get_event(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    # Only owner or organizer can update
    user_id = current_user.get("id")
    is_organizer = any(p.user_id == user_id and p.is_organizer for p in event.participants)
    
    if str(event.user_id) != str(user_id) and not is_organizer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event owner can update it",
        )
    
    updated = await service.update_event(event_id, data)
    return updated


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete (cancel) an event. Only the owner can delete."""
    service = CalendarService(db)
    event = await service.get_event(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    # Only owner can delete
    if str(event.user_id) != str(current_user.get("id")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event owner can delete it",
        )
    
    await service.delete_event(event_id)
    return None


@router.post("/{event_id}/respond")
async def respond_to_event(
    event_id: UUID,
    response: str = Query(..., pattern="^(accepted|declined|tentative)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Respond to an event invitation."""
    from datetime import datetime
    from sqlalchemy import select, update
    from ..models import EventParticipant
    
    user_id = current_user.get("id")
    
    # Find participation
    result = await db.execute(
        select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
        )
    )
    participant = result.scalar_one_or_none()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not invited to this event",
        )
    
    participant.response_status = response
    participant.responded_at = datetime.utcnow()
    await db.commit()
    
    return {"message": f"Response '{response}' recorded"}
