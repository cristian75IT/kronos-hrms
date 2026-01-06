"""
KRONOS - Calendar Service Client

Client for calendar operations, holidays, and working day calculations.
"""
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class CalendarClient(BaseClient):
    """Client for Calendar Service interactions."""
    
    def __init__(self):
        super().__init__(
            base_url=settings.calendar_service_url,
            service_name="calendar",
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holiday Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_holidays(
        self,
        year: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """Get holidays from calendar service."""
        params = {"year": year}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        return await self.get_safe(
            "/api/v1/calendar/holidays-list",
            default=[],
            params=params,
        )
    
    async def get_closures(
        self,
        year: int,
        location_id: Optional[UUID] = None,
    ) -> list[dict]:
        """Get company closures from calendar service."""
        params = {"year": year}
        if location_id:
            params["location_id"] = str(location_id)
        
        return await self.get_safe(
            "/api/v1/calendar/closures-list",
            default=[],
            params=params,
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Calendar Range & Aggregation
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_calendar_range(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
    ) -> Optional[dict]:
        """Get aggregated calendar view for a date range."""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if location_id:
            params["location_id"] = str(location_id)
        
        return await self.get_safe("/api/v1/calendar/range", params=params)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Working Day Calculations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def calculate_working_days(
        self,
        start_date: date,
        end_date: date,
        location_id: Optional[UUID] = None,
        exclude_closures: bool = True,
        exclude_holidays: bool = True,
    ) -> Optional[dict]:
        """Calculate working days between two dates."""
        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "exclude_closures": exclude_closures,
            "exclude_holidays": exclude_holidays,
        }
        if location_id:
            payload["location_id"] = str(location_id)
        
        return await self.post_safe("/api/v1/calendar/working-days", json=payload)
    
    async def is_working_day(
        self,
        check_date: date,
        location_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a specific date is a working day."""
        params = {}
        if location_id:
            params["location_id"] = str(location_id)
        
        data = await self.get_safe(
            f"/api/v1/calendar/working-days/check/{check_date.isoformat()}",
            default={"is_working_day": True},
            params=params if params else None,
        )
        return data.get("is_working_day", True) if data else True
    
    async def get_working_days_count(self, start_date: date, end_date: date) -> int:
        """Wrapper for calculating working days count used by aggregator."""
        res = await self.calculate_working_days(start_date, end_date)
        if res:
            return int(res.get("working_days", 0))
        return 0
