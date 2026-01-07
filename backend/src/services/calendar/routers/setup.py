from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import datetime as dt

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload
from src.services.calendar.services.profiles import CalendarProfileService
from src.services.calendar.schemas import (
    SetupHolidaysPayload,
    HolidayProfileCreate,
    HolidayCreate
)
from src.services.calendar.models import HolidayProfile

router = APIRouter()

async def get_profile_service(session: AsyncSession = Depends(get_db)):
    return CalendarProfileService(session)

@router.post("/setup/holidays", response_model=dict)
async def setup_holidays(
    payload: SetupHolidaysPayload,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: CalendarProfileService = Depends(get_profile_service)
):
    """Bulk setup holidays and holiday profiles."""
    results = {"profiles": 0, "holidays": 0}
    
    for profile_data in payload.profiles:
        # Check by code
        stmt = select(HolidayProfile).where(HolidayProfile.code == profile_data.code)
        res = await service.db.execute(stmt)
        existing_profile = res.scalar_one_or_none()
        
        profile_id = None
        if existing_profile:
            profile_id = existing_profile.id
        else:
            profile = await service.create_holiday_profile(
                HolidayProfileCreate(
                    code=profile_data.code,
                    name=profile_data.name,
                    country_code=profile_data.country_code,
                    region_code=profile_data.region_code
                )
            )
            profile_id = profile.id
            results["profiles"] += 1
            
        # Holidays: get current holidays for this profile to avoid duplicates
        existing_holidays = await service.get_holidays_in_profile(profile_id)
        existing_names = {h.name for h in existing_holidays}
        
        for holiday_data in profile_data.holidays:
            if holiday_data.name in existing_names:
                continue
                
            await service.create_holiday(
                profile_id,
                HolidayCreate(
                    name=holiday_data.name,
                    date=holiday_data.date,
                    is_recurring=holiday_data.is_recurring,
                    recurrence_rule=holiday_data.recurrence_rule,
                    is_confirmed=True
                )
            )
            results["holidays"] += 1
            
    return results
