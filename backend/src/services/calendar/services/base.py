"""
KRONOS - Calendar Service Base

Shared dependencies and utilities for calendar sub-services.
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.calendar.models import LocationCalendar, HolidayProfile, CalendarHoliday
from src.shared.audit_client import get_audit_logger
import logging

logger = logging.getLogger(__name__)


class BaseCalendarService:
    """
    Base class for calendar service modules.
    
    Provides:
    - Database session
    - Audit logger
    - Location config utilities
    - Easter date calculation
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = get_audit_logger("calendar-service")
    
    # ═══════════════════════════════════════════════════════════════════════
    # Location Configuration
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_location_config(self, location_id: Optional[UUID]) -> LocationCalendar:
        """Fetch LocationCalendar. If not found or None, return a DEFAULT."""
        if location_id:
            stmt = (
                select(LocationCalendar)
                .options(
                    selectinload(LocationCalendar.work_week_profile),
                    selectinload(LocationCalendar.holiday_profiles)
                    .selectinload(HolidayProfile.holidays),
                )
                .where(LocationCalendar.location_id == location_id)
            )
            result = await self.db.execute(stmt)
            loc_cal = result.scalar_one_or_none()
            if loc_cal:
                return loc_cal
        
        # Try default (where location_id IS NULL and is_default=True)
        stmt = (
            select(LocationCalendar)
            .options(
                selectinload(LocationCalendar.work_week_profile),
                selectinload(LocationCalendar.holiday_profiles)
                .selectinload(HolidayProfile.holidays),
            )
            .where(LocationCalendar.location_id == None)
            .where(LocationCalendar.is_default == True)
        )
        result = await self.db.execute(stmt)
        default_cal = result.scalar_one_or_none()
        
        if default_cal:
            return default_cal
        
        # Return a synthetic default with Mon-Fri working days
        return self._create_synthetic_default()
    
    def _create_synthetic_default(self) -> LocationCalendar:
        """Create a synthetic default LocationCalendar."""
        return LocationCalendar(
            id=None,
            location_id=None,
            is_default=True,
            work_week_profile=None,  # Will use Mon-Fri default
            holiday_profiles=[],
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holiday Calculations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_location_holidays(
        self, 
        config: LocationCalendar, 
        start_year: int, 
        end_year: int
    ) -> set[date]:
        """Flatten holidays from all subscribed profiles for the given years."""
        holidays_set: set[date] = set()
        
        profiles = config.holiday_profiles if config.holiday_profiles else []
        
        for profile in profiles:
            for holiday in (profile.holidays or []):
                if holiday.is_recurring and holiday.recurrence_rule:
                    # Calculate for each year in range
                    for year in range(start_year, end_year + 1):
                        calculated_date = self._calculate_recurrence(
                            holiday.recurrence_rule, year
                        )
                        if calculated_date:
                            holidays_set.add(calculated_date)
                elif holiday.date:
                    # Fixed date holiday
                    if start_year <= holiday.date.year <= end_year:
                        holidays_set.add(holiday.date)
        
        return holidays_set
    
    def _calculate_recurrence(self, rule: dict, year: int) -> Optional[date]:
        """Calculate specific date from rule for a given year."""
        rule_type = rule.get("type")
        
        if rule_type == "fixed":
            month = rule.get("month", 1)
            day = rule.get("day", 1)
            try:
                return date(year, month, day)
            except ValueError:
                return None
        
        elif rule_type == "easter_offset":
            offset = rule.get("days", 0)
            easter = self._get_easter_date(year)
            return easter + timedelta(days=offset)
        
        return None
    
    def _get_easter_date(self, year: int) -> date:
        """Calculate Western Easter date using Anonymous Gregorian algorithm."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Working Days Calculation
    # ═══════════════════════════════════════════════════════════════════════
    
    def _get_working_days_mask(self, config: LocationCalendar) -> list[bool]:
        """Get working days mask (Mon=0, Sun=6)."""
        if config.work_week_profile:
            profile = config.work_week_profile
            return [
                profile.monday,
                profile.tuesday,
                profile.wednesday,
                profile.thursday,
                profile.friday,
                profile.saturday,
                profile.sunday,
            ]
        # Default: Mon-Fri
        return [True, True, True, True, True, False, False]
