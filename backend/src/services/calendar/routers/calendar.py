"""KRONOS Calendar Service - Calendar View Router."""
from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload
from ..schemas import (
    CalendarRangeView,
    WorkingDayExceptionCreate,
    WorkingDayExceptionResponse,
    UserCalendarCreate,
    UserCalendarUpdate,
    UserCalendarResponse,
    CalendarShareCreate,
    CalendarShareResponse,
    WorkingDaysRequest,
    WorkingDaysResponse,
)
from ..service import CalendarService

router = APIRouter()


@router.get("/range", response_model=CalendarRangeView)
async def get_calendar_range(
    start_date: date = Query(..., description="Start date of the range"),
    end_date: date = Query(..., description="End date of the range"),
    location_id: Optional[UUID] = Query(None, description="Location filter"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get aggregated calendar view for a date range.
    
    Returns all holidays, closures, and events within the specified range,
    along with working day information.
    """
    service = CalendarService(db)
    result = await service.get_calendar_range(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.user_id,
        location_id=location_id,
    )
    return result


@router.get("/date/{check_date}")
async def get_calendar_date(
    check_date: date,
    location_id: Optional[UUID] = Query(None, description="Location filter"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get calendar information for a specific date.
    
    Returns whether it's a working day and all items scheduled.
    """
    service = CalendarService(db)
    result = await service.get_calendar_range(
        start_date=check_date,
        end_date=check_date,
        user_id=current_user.user_id,
        location_id=location_id,
    )
    
    if result.days:
        return result.days[0]
    
    return {
        "date": check_date,
        "is_working_day": True,
        "is_holiday": False,
        "items": [],
    }


@router.post("/working-days", response_model=WorkingDaysResponse)
async def calculate_working_days(
    request: WorkingDaysRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Calculate the number of working days between two dates.
    
    Takes into account:
    - Weekends (based on configured working week)
    - National and regional holidays
    - Company closures
    - Working day exceptions
    """
    service = CalendarService(db)
    result = await service.calculate_working_days(
        start_date=request.start_date,
        end_date=request.end_date,
        location_id=request.location_id,
        exclude_closures=request.exclude_closures,
        exclude_holidays=request.exclude_holidays,
    )
    return result


@router.get("/working-days/check/{check_date}")
async def is_working_day(
    check_date: date,
    location_id: Optional[UUID] = Query(None, description="Location filter"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Check if a specific date is a working day."""
    service = CalendarService(db)
    is_working = await service.is_working_day(check_date, location_id)
    
    return {
        "date": check_date,
        "is_working_day": is_working,
    }


@router.get("/exceptions", response_model=list[WorkingDayExceptionResponse])
async def list_working_day_exceptions(
    year: int = Query(..., description="Year to filter"),
    location_id: Optional[UUID] = Query(None, description="Location filter"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get all working day exceptions for a year."""
    service = CalendarService(db)
    exceptions = await service.get_working_day_exceptions(year, location_id)
    return exceptions


@router.post("/exceptions", response_model=WorkingDayExceptionResponse, status_code=201)
async def create_working_day_exception(
    data: WorkingDayExceptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create a working day exception.
    
    Use this to mark a normally non-working day as working (e.g., Saturday work recovery)
    or vice versa.
    """
    from src.core.security import require_admin
    # Note: In production, this would require admin check
    
    service = CalendarService(db)
    exception = await service.create_working_day_exception(
        data=data,
        created_by=current_user.user_id,
    )
    return exception


@router.delete("/exceptions/{exception_id}", status_code=204)
async def delete_working_day_exception(
    exception_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Delete a working day exception."""
    from src.core.security import require_hr
    # This requires HR or Admin
    
    service = CalendarService(db)
    success = await service.delete_working_day_exception(exception_id)
    
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Exception not found")
    
    return None


@router.get("/user-calendars", response_model=list[UserCalendarResponse])
async def list_user_calendars(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """List all custom calendars for the current user."""
    service = CalendarService(db)
    calendars = await service.get_user_calendars(current_user.user_id)
    
    results = []
    for cal in calendars:
        res = UserCalendarResponse.model_validate(cal)
        res.is_owner = cal.user_id == current_user.user_id
        results.append(res)
    return results


@router.post("/user-calendars", response_model=UserCalendarResponse)
async def create_user_calendar(
    data: UserCalendarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create a new custom calendar."""
    service = CalendarService(db)
    return await service.create_user_calendar(current_user.user_id, data)


@router.put("/user-calendars/{calendar_id}", response_model=UserCalendarResponse)
async def update_user_calendar(
    calendar_id: UUID,
    data: UserCalendarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Update a custom calendar."""
    service = CalendarService(db)
    calendar = await service.update_user_calendar(calendar_id, current_user.user_id, data)
    if not calendar:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Calendar not found")
    return calendar


@router.delete("/user-calendars/{calendar_id}", status_code=204)
async def delete_user_calendar(
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Delete a custom calendar."""
    service = CalendarService(db)
    success = await service.delete_user_calendar(calendar_id, current_user.user_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Calendar not found")
    return None

@router.post("/user-calendars/{calendar_id}/share", response_model=CalendarShareResponse)
async def share_calendar(
    calendar_id: UUID,
    data: CalendarShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Share a calendar with another user."""
    service = CalendarService(db)
    share = await service.share_calendar(
        calendar_id=calendar_id,
        user_id=current_user.user_id,
        shared_with_user_id=data.shared_with_user_id,
        can_edit=data.can_edit
    )
    if not share:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Calendar not found or you are not the owner")
    return share


@router.delete("/user-calendars/{calendar_id}/share/{shared_user_id}", status_code=204)
async def unshare_calendar(
    calendar_id: UUID,
    shared_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Remove a calendar share."""
    service = CalendarService(db)
    success = await service.unshare_calendar(
        calendar_id=calendar_id,
        user_id=current_user.user_id,
        shared_with_user_id=shared_user_id
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Share not found or you are not the owner")
    return None
