"""KRONOS Calendar Service - Holidays Router."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_hr, TokenPayload
from ..schemas import HolidayCreate, HolidayUpdate, HolidayResponse
from ..service import CalendarService

router = APIRouter()


@router.get("", response_model=List[HolidayResponse])
async def list_holidays(
    year: Optional[int] = Query(None, description="Filter by year"),
    scope: Optional[str] = Query(None, description="Filter by scope (national, regional, local, company)"),
    location_id: Optional[UUID] = Query(None, description="Filter by location"),
    include_inactive: bool = Query(False, description="Include inactive holidays"),
    db: AsyncSession = Depends(get_db),
    # No auth required for read - allows service-to-service calls
):
    """Get all holidays with optional filters."""
    service = CalendarService(db)
    holidays = await service.get_holidays(
        year=year,
        scope=scope,
        location_id=location_id,
        include_inactive=include_inactive,
    )
    return holidays


@router.get("/{holiday_id}", response_model=HolidayResponse)
async def get_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db),
    # No auth required for read - allows service-to-service calls
):
    """Get a specific holiday by ID."""
    service = CalendarService(db)
    holiday = await service.get_holiday(holiday_id)
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found",
        )
    return holiday


@router.post("", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    data: HolidayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Create a new holiday. Requires HR or Admin privileges."""
    service = CalendarService(db)
    holiday = await service.create_holiday(
        data=data,
        created_by=current_user.user_id
    )
    return holiday


@router.put("/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    holiday_id: UUID,
    data: HolidayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Update an existing holiday. Requires HR or Admin privileges."""
    service = CalendarService(db)
    holiday = await service.update_holiday(holiday_id, data)
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found",
        )
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_hr),
):
    """Delete a holiday. Requires HR or Admin privileges."""
    service = CalendarService(db)
    success = await service.delete_holiday(holiday_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holiday not found",
        )
    return None
