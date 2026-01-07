from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.security import get_current_user, TokenPayload
from src.services.leaves.calendar_service import LeaveCalendarService
from src.services.leaves.schemas import (
    CalendarRequest,
    CalendarResponse,
    DaysCalculationRequest,
    DaysCalculationResponse,
)
from src.services.leaves.deps import get_calendar_service

router = APIRouter()

# ═══════════════════════════════════════════════════════════
# Calendar Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/leaves/excluded-days")
async def get_excluded_days(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    user_id: Optional[str] = Query(None, description="User ID for contract rules (optional)"),
    token: TokenPayload = Depends(get_current_user),
    service: LeaveCalendarService = Depends(get_calendar_service),
):
    """Get list of excluded days (weekends, holidays, closures) in a date range."""
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # Use passed user_id or current user
    target_user_id = token.user_id
    if user_id and token.is_manager: # Only managers should be able to check others? Or simple mismatch check
         # For simplicity, if user_id passed, use it (filtering/security handled elsewhere ideally, 
         # but this is just calendar calculation)
         try:
             import uuid
             target_user_id = uuid.UUID(user_id)
         except:
             pass

    return await service.get_excluded_days(start, end, user_id=target_user_id)


@router.post("/leaves/calendar", response_model=CalendarResponse)
async def get_calendar(
    request: CalendarRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveCalendarService = Depends(get_calendar_service),
):
    """Get calendar events for FullCalendar."""
    user_id = token.user_id
    is_manager = token.is_manager
    
    return await service.get_calendar(request, user_id, is_manager)


@router.post("/leaves/calculate-days", response_model=DaysCalculationResponse)
async def calculate_days(
    request: DaysCalculationRequest,
    token: TokenPayload = Depends(get_current_user),
    service: LeaveCalendarService = Depends(get_calendar_service),
):
    """Calculate working days for preview."""
    # Pass user_id from token to service
    return await service.calculate_preview(request, user_id=token.user_id)
