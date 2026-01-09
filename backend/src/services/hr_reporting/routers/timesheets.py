"""
Timesheet Router.
"""
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.core.database import get_db
from src.core.security import get_current_user, TokenPayload, require_permission

from ..models import MonthlyTimesheet
from ..services.timesheet import TimesheetService
from ..schemas import MonthlyTimesheetResponse, TimesheetConfirmation

router = APIRouter(prefix="/timesheets", tags=["Monthly Timesheets"])

def get_service(session: AsyncSession = Depends(get_db)) -> TimesheetService:
    return TimesheetService(session)

@router.get("/me", response_model=List[MonthlyTimesheetResponse])
async def list_my_timesheets(
    current_user: TokenPayload = Depends(get_current_user),
    service: TimesheetService = Depends(get_service),
    session: AsyncSession = Depends(get_db),
):
    """List recent timesheets (last 12 months)."""
    # Simple query
    stmt = select(MonthlyTimesheet).where(
        MonthlyTimesheet.employee_id == current_user.user_id
    ).order_by(desc(MonthlyTimesheet.year), desc(MonthlyTimesheet.month)).limit(12)
    
    result = await session.execute(stmt)
    items = result.scalars().all()
    
    # We assume list view doesn't need detailed days or checking confirmation window for all
    # But response model requires it.
    # Default values will be used (can_confirm=False).
    # If the user needs to know actionable items, we iterate.
    
    # Optimization: Check confirmation window requires settings.
    # We can do it in loop or just return basic info.
    return items

@router.get("/me/{year}/{month}", response_model=MonthlyTimesheetResponse)
async def get_my_timesheet(
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    current_user: TokenPayload = Depends(get_current_user),
    service: TimesheetService = Depends(get_service),
):
    """
    Get (or generate) monthly timesheet for current user.
    """
    return await service.get_timesheet_for_user(current_user.user_id, year, month)

@router.post("/me/{year}/{month}/confirm", response_model=MonthlyTimesheetResponse)
async def confirm_my_timesheet(
    data: TimesheetConfirmation,
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    current_user: TokenPayload = Depends(get_current_user),
    service: TimesheetService = Depends(get_service),
):
    """
    Confirm monthly timesheet.
    """
    await service.confirm_timesheet(
        current_user.user_id, year, month, data
    )
    # Return updated state
    return await service.get_timesheet_for_user(current_user.user_id, year, month)
