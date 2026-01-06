"""KRONOS Calendar Service - Calendar Enterprise Router."""
from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload
from ..schemas import (
    WorkingDaysRequest,
    WorkingDaysResponse,
    CalendarCreate,
    CalendarUpdate,
    CalendarResponse,
    CalendarShareCreate,
    CalendarShareResponse,
    EventCreate,
    EventUpdate,
    EventResponse,
    WorkingDayExceptionCreate,
    WorkingDayExceptionResponse,
    ClosureCreate,
    ClosureUpdate,
    ClosureResponse,
    CalendarRangeView,
)
from ..services import CalendarService

router = APIRouter()

# ════════════════════════════════════════════════
# WORKING DAYS CALCULATIONS
# ════════════════════════════════════════════════

@router.post(
    "/working-days",
    response_model=WorkingDaysResponse,
    tags=["Calendar"],
    summary="Calculate working days between two dates"
)
async def calculate_working_days(
    request: WorkingDaysRequest,
    db: AsyncSession = Depends(get_db),
):
    """Calculate the number of working days between two dates."""
    service = CalendarService(db)
    result = await service.calculate_working_days(
        start_date=request.start_date,
        end_date=request.end_date,
        location_id=request.location_id,
        exclude_closures=request.exclude_closures,
        exclude_holidays=request.exclude_holidays,
    )
    return result

@router.get(
    "/holidays-list",
    response_model=List[dict],
    tags=["Calendar"],
    summary="List all holidays for a range"
)
async def list_holidays(
    year: int = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List expanded system holidays for a specific year/range."""
    service = CalendarService(db)
    holidays = await service.get_system_holidays(year)
    # Filter by date range if provided
    if start_date:
        holidays = [h for h in holidays if h['date'] >= start_date]
    if end_date:
        holidays = [h for h in holidays if h['date'] <= end_date]
    return holidays

@router.get("/closures-list", response_model=List[dict])
async def list_closures(
    year: int = Query(...),
    location_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List closures for a location in a specific year."""
    service = CalendarService(db)
    closures = await service.get_location_closures(year, location_id)
    return closures

@router.get(
    "/working-days/check/{check_date}",
    tags=["Calendar"],
    summary="Check if a date is a working day"
)
async def is_working_day(
    check_date: date,
    location_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Check if a specific date is a working day."""
    service = CalendarService(db)
    is_working = await service.is_working_day(check_date, location_id)
    return {
        "date": check_date,
        "is_working_day": is_working,
    }

# ════════════════════════════════════════════════
# UNIFIED CALENDARS CRUD
# ════════════════════════════════════════════════

@router.get(
    "/calendars",
    response_model=List[CalendarResponse],
    tags=["Calendar"],
    summary="Get user's calendars (owned and shared)"
)
async def get_calendars(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """List all calendars visible to the user."""
    service = CalendarService(db)
    calendars = await service.get_calendars(current_user.user_id)
    
    # Map to response and set is_owner
    results = []
    for c in calendars:
        # Pydantic's from_attributes handles the ORM->Pydantic conversion of base fields
        # But we need to manually set is_owner because it's not on the model
        # We can construct the dict first or validate then update
        
        # Validating from ORM object directly might skip is_owner if it's not on ORM
        # So we validate, then update. But Pydantic models are immutable if frozen?
        # Default is mutable.
        cal_resp = CalendarResponse.model_validate(c)
        cal_resp.is_owner = (c.owner_id == current_user.user_id)
        results.append(cal_resp)
        
    return results

@router.get("/range", response_model=CalendarRangeView)
async def get_calendar_range(
    start_date: date = Query(...),
    end_date: date = Query(...),
    location_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get aggregated calendar view for a date range."""
    service = CalendarService(db)
    return await service.get_calendar_range(
        user_id=current_user.user_id,
        start_date=start_date,
        end_date=end_date,
        location_id=location_id
    )

@router.post("/calendars", response_model=CalendarResponse, status_code=201)
async def create_calendar(
    data: CalendarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create a new calendar."""
    service = CalendarService(db)
    return await service.create_calendar(current_user.user_id, data)

@router.put("/calendars/{calendar_id}", response_model=CalendarResponse)
async def update_calendar(
    calendar_id: UUID,
    data: CalendarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Update a calendar."""
    service = CalendarService(db)
    updated = await service.update_calendar(current_user.user_id, calendar_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return updated

@router.delete("/calendars/{calendar_id}", status_code=204)
async def delete_calendar(
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Delete a calendar."""
    service = CalendarService(db)
    success = await service.delete_calendar(current_user.user_id, calendar_id)
    if not success:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return None

@router.post("/calendars/{calendar_id}/share", response_model=CalendarShareResponse)
async def share_calendar(
    calendar_id: UUID,
    data: CalendarShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Share a calendar with another user."""
    service = CalendarService(db)
    shared = await service.share_calendar(
        calendar_id=calendar_id, 
        user_id=current_user.user_id, 
        shared_with_user_id=data.user_id, 
        permission=data.permission
    )
    if not shared:
        raise HTTPException(status_code=404, detail="Calendar not found or error")
    return shared

@router.delete("/calendars/{calendar_id}/share/{shared_user_id}", status_code=204)
async def unshare_calendar(
    calendar_id: UUID,
    shared_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Unshare a calendar."""
    service = CalendarService(db)
    success = await service.unshare_calendar(
        calendar_id=calendar_id,
        user_id=current_user.user_id,
        shared_with_user_id=shared_user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Share not found or error")
    return None

# ════════════════════════════════════════════════
# EVENTS
# ════════════════════════════════════════════════

@router.get("/events", response_model=List[EventResponse])
async def list_events(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    event_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get all events visible to the user."""
    service = CalendarService(db)
    return await service.get_visible_events(
        user_id=current_user.user_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type
    )

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    event = await service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    # TODO: Add visibility check here if not already handled or needed
    return event

@router.post("/events", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    try:
        return await service.create_event(current_user.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    updated = await service.update_event(event_id, data, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found or permission denied")
    return updated

@router.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    success = await service.delete_event(event_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found or permission denied")
    return None

# ════════════════════════════════════════════════
# WORKING DAY EXCEPTIONS
# ════════════════════════════════════════════════

@router.get("/exceptions", response_model=List[WorkingDayExceptionResponse])
async def list_exceptions(
    year: int = Query(...),
    location_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.get_working_day_exceptions(year, location_id)

@router.post("/exceptions", response_model=WorkingDayExceptionResponse, status_code=201)
async def create_exception(
    data: WorkingDayExceptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.create_working_day_exception(data)

@router.delete("/exceptions/{exception_id}", status_code=204)
async def delete_exception(
    exception_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    success = await service.delete_working_day_exception(exception_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exception not found")
    return None

# ════════════════════════════════════════════════
# CLOSURES CRUD
# ════════════════════════════════════════════════

@router.post("/closures", response_model=ClosureResponse, status_code=201)
async def create_closure(
    data: ClosureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.create_closure(data)

@router.put("/closures/{closure_id}", response_model=ClosureResponse)
async def update_closure(
    closure_id: UUID,
    data: ClosureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    updated = await service.update_closure(closure_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Closure not found")
    return updated

@router.delete("/closures/{closure_id}", status_code=204)
async def delete_closure(
    closure_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    success = await service.delete_closure(closure_id)
    if not success:
        raise HTTPException(status_code=404, detail="Closure not found")
    return None
