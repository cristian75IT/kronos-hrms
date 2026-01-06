"""KRONOS Calendar Service - Admin Management Router."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload

from ..schemas import (
    WorkWeekProfileCreate, WorkWeekProfileUpdate, WorkWeekProfileResponse,
    HolidayProfileCreate, HolidayProfileUpdate, HolidayProfileResponse,
    HolidayCreate, HolidayUpdate, HolidayResponse,
    LocationCalendarCreate, LocationCalendarUpdate, LocationCalendarResponse
)
from ..services import CalendarService

router = APIRouter()

# TODO: Add proper Admin dependency
# async def require_admin(user: TokenPayload = Depends(get_current_user)):
#     if not user.is_admin:
#         raise HTTPException(status_code=403, detail="Admin privileges required")

# ════════════════════════════════════════════════
# WORK WEEK PROFILES
# ════════════════════════════════════════════════

@router.get(
    "/work-week-profiles",
    response_model=List[WorkWeekProfileResponse],
    tags=["Calendar Admin"],
    summary="List all work week profiles",
    description="Retrieve a list of all defined work week profiles (e.g., Standard 5-day, 6-day)."
)
async def list_work_week_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.get_work_week_profiles()

@router.post(
    "/work-week-profiles",
    response_model=WorkWeekProfileResponse,
    status_code=201,
    tags=["Calendar Admin"],
    summary="Create a new work week profile"
)
async def create_work_week_profile(
    data: WorkWeekProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    return await service.create_work_week_profile(data)

@router.get(
    "/work-week-profiles/{profile_id}",
    response_model=WorkWeekProfileResponse,
    tags=["Calendar Admin"],
    summary="Get a specific work week profile"
)
async def get_work_week_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    obj = await service.get_work_week_profile(profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.put(
    "/work-week-profiles/{profile_id}",
    response_model=WorkWeekProfileResponse,
    tags=["Calendar Admin"],
    summary="Update a work week profile"
)
async def update_work_week_profile(
    profile_id: UUID,
    data: WorkWeekProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    obj = await service.update_work_week_profile(profile_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.delete(
    "/work-week-profiles/{profile_id}",
    status_code=204,
    tags=["Calendar Admin"],
    summary="Delete a work week profile"
)
async def delete_work_week_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    success = await service.delete_work_week_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return None

# ════════════════════════════════════════════════
# HOLIDAY PROFILES
# ════════════════════════════════════════════════

@router.get(
    "/holiday-profiles",
    response_model=List[HolidayProfileResponse],
    tags=["Calendar Admin"],
    summary="List all holiday profiles"
)
async def list_holiday_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.get_holiday_profiles()

@router.post(
    "/holiday-profiles",
    response_model=HolidayProfileResponse,
    status_code=201,
    tags=["Calendar Admin"],
    summary="Create a new holiday profile"
)
async def create_holiday_profile(
    data: HolidayProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    return await service.create_holiday_profile(data)

@router.get(
    "/holiday-profiles/{profile_id}",
    response_model=HolidayProfileResponse,
    tags=["Calendar Admin"],
    summary="Get a specific holiday profile"
)
async def get_holiday_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    obj = await service.get_holiday_profile(profile_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.put("/holiday-profiles/{profile_id}", response_model=HolidayProfileResponse)
async def update_holiday_profile(
    profile_id: UUID,
    data: HolidayProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    obj = await service.update_holiday_profile(profile_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Profile not found")
    return obj

@router.delete("/holiday-profiles/{profile_id}", status_code=204)
async def delete_holiday_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    success = await service.delete_holiday_profile(profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return None

# ════════════════════════════════════════════════
# HOLIDAYS (Nested in Profile)
# ════════════════════════════════════════════════

@router.get(
    "/holiday-profiles/{profile_id}/holidays",
    response_model=List[HolidayResponse],
    tags=["Calendar Admin"],
    summary="List all holidays within a profile"
)
async def list_holidays_in_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.get_holidays_in_profile(profile_id)

@router.post("/holiday-profiles/{profile_id}/holidays", response_model=HolidayResponse, status_code=201)
async def create_holiday(
    profile_id: UUID,
    data: HolidayCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    # Ensure profile exists? Service could check but we trust create_holiday fails on FK constraint if not
    return await service.create_holiday(profile_id, data)

@router.put("/holidays/{holiday_id}", response_model=HolidayResponse)
async def update_holiday(
    holiday_id: UUID,
    data: HolidayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    obj = await service.update_holiday(holiday_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return obj

@router.delete("/holidays/{holiday_id}", status_code=204)
async def delete_holiday(
    holiday_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    success = await service.delete_holiday(holiday_id)
    if not success:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return None

# ════════════════════════════════════════════════
# LOCATION CALENDARS
# ════════════════════════════════════════════════

@router.get(
    "/location-calendars",
    response_model=List[LocationCalendarResponse],
    tags=["Calendar Admin"],
    summary="List all location calendar configurations"
)
async def list_location_calendars(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.get_location_calendars()

@router.post("/location-calendars", response_model=LocationCalendarResponse, status_code=201)
async def create_location_calendar(
    data: LocationCalendarCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    return await service.create_location_calendar(data)

@router.put("/location-calendars/{id}", response_model=LocationCalendarResponse)
async def update_location_calendar(
    id: UUID,
    data: LocationCalendarUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    obj = await service.update_location_calendar(id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return obj

@router.post("/location-calendars/{location_id}/subscriptions/{calendar_id}", status_code=201)
async def add_location_subscription(
    location_id: UUID,
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    # Check if location calendar exists for this location, if not create default?
    # Our service method expects location_id and calendar_id
    sub = await service.add_location_subscription(location_id, calendar_id)
    if not sub:
         raise HTTPException(status_code=400, detail="Could not add subscription (maybe duplicates or missing base config)")
    return {"status": "subscribed", "calendar_id": calendar_id}

@router.delete("/location-calendars/{location_id}/subscriptions/{calendar_id}", status_code=204)
async def remove_location_subscription(
    location_id: UUID,
    calendar_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_permission("settings:edit")),
):
    service = CalendarService(db)
    success = await service.remove_location_subscription(location_id, calendar_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return None

