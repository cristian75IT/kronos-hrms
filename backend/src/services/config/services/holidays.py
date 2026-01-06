"""
KRONOS - Holidays & Closures Service

Handles holidays and company closures management.
"""
import json
from typing import Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from workalendar.europe import Italy

from src.core.exceptions import NotFoundError, ConflictError
from src.shared.audit_client import get_audit_logger
from src.shared.clients import LeaveClient
from src.services.config.repository import HolidayRepository, CompanyClosureRepository
from src.services.config.schemas import (
    HolidayCreate,
    GenerateHolidaysRequest,
    CompanyClosureCreate,
    CompanyClosureUpdate,
)
import logging


class HolidayService:
    """
    Service for holidays and company closures management.
    
    Handles:
    - Get/create/delete holidays
    - Generate national holidays
    - Company closures CRUD
    - Trigger leave recalculation on changes
    """
    
    CACHE_PREFIX = "config:"
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(
        self,
        session: AsyncSession,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        self._session = session
        self._holiday_repo = HolidayRepository(session)
        self._closure_repo = CompanyClosureRepository(session)
        self._redis = redis_client
        self._audit = get_audit_logger("config-service")
        self._logger = logging.getLogger(__name__)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holidays
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_holidays(
        self,
        year: int,
        location_id: Optional[UUID] = None,
    ) -> list:
        """Get holidays for a year."""
        cache_key = f"{self.CACHE_PREFIX}holidays:{year}:{location_id or 'all'}"
        
        if self._redis:
            cached = await self._redis.get(cache_key)
            if cached:
                return json.loads(cached)
        
        holidays = await self._holiday_repo.get_by_year(year, location_id)
        
        if self._redis:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps([self._holiday_to_dict(h) for h in holidays]),
            )
        
        return holidays
    
    async def create_holiday(self, data: HolidayCreate, user_id: Optional[UUID] = None):
        """Create new holiday."""
        existing = await self._holiday_repo.get_by_date(data.date)
        if existing:
            raise ConflictError(f"Holiday already exists for date: {data.date}")
        
        holiday = await self._holiday_repo.create(**data.model_dump())
        await self._invalidate_cache(f"holidays:{data.date.year}")
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="HOLIDAY",
            resource_id=str(holiday.id),
            description=f"Created holiday: {holiday.name} on {holiday.date}",
            request_data=data.model_dump(mode="json")
        )
        
        await self._trigger_leave_recalculation(data.date, data.date)
        
        return holiday
    
    async def delete_holiday(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete holiday."""
        holiday = await self._holiday_repo.get(id)
        if not holiday:
            raise NotFoundError("Holiday not found")
        
        year = holiday.year
        holiday_name = holiday.name
        holiday_date = holiday.date
        result = await self._holiday_repo.delete(id)
        await self._invalidate_cache(f"holidays:{year}")
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="HOLIDAY",
            resource_id=str(id),
            description=f"Deleted holiday: {holiday_name} on {holiday_date}"
        )
        
        await self._trigger_leave_recalculation(holiday_date, holiday_date)
        
        return result
    
    async def update_holiday(self, id: UUID, data, user_id: Optional[UUID] = None):
        """Update holiday - supports confirmation and other fields."""
        holiday = await self._holiday_repo.get(id)
        if not holiday:
            raise NotFoundError("Holiday not found")
        
        old_date = holiday.date
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(holiday, key, value)
        
        await self._session.commit()
        await self._session.refresh(holiday)
        await self._invalidate_cache(f"holidays:{holiday.year}")
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="HOLIDAY",
            resource_id=str(id),
            description=f"Updated holiday: {holiday.name}",
            request_data=update_data
        )
        
        await self._trigger_leave_recalculation(old_date, old_date)
        if holiday.date != old_date:
            await self._trigger_leave_recalculation(holiday.date, holiday.date)
        
        return holiday
    
    async def generate_holidays(self, data: GenerateHolidaysRequest, user_id: Optional[UUID] = None) -> list:
        """Generate Italian national holidays for a year using workalendar."""
        # Delete existing NATIONAL holidays for this year (preserve manual/local ones)
        await self._holiday_repo.delete_national_by_year(data.year)
        
        # Generate using workalendar
        cal = Italy()
        holidays_data = cal.holidays(data.year)
        
        created = []
        for holiday_date, name in holidays_data:
            holiday = await self._holiday_repo.create(
                date=holiday_date,
                name=name,
                year=data.year,
                is_national=True,
                location_id=None,
            )
            created.append(holiday)
        
        await self._invalidate_cache(f"holidays:{data.year}")
        
        await self._audit.log_action(
            user_id=user_id,
            action="GENERATE",
            resource_type="HOLIDAY",
            description=f"Generated national holidays for year {data.year}",
            request_data=data.model_dump(mode="json")
        )
        return created
    
    def _holiday_to_dict(self, holiday) -> dict:
        """Convert holiday to dict for caching."""
        return {
            "id": str(holiday.id),
            "date": holiday.date.isoformat(),
            "name": holiday.name,
            "is_national": holiday.is_national,
            "year": holiday.year,
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # Company Closures
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_closures(
        self,
        year: int,
        include_inactive: bool = False,
    ) -> list:
        """Get company closures for a year."""
        return await self._closure_repo.get_by_year(year, include_inactive)
    
    async def get_closure(self, id: UUID):
        """Get closure by ID."""
        return await self._closure_repo.get(id)
    
    async def create_closure(self, data: CompanyClosureCreate, created_by: UUID = None):
        """Create new company closure."""
        closure = await self._closure_repo.create(
            **data.model_dump(),
            created_by=created_by,
        )
        
        await self._audit.log_action(
            user_id=created_by,
            action="CREATE",
            resource_type="COMPANY_CLOSURE",
            resource_id=str(closure.id),
            description=f"Created company closure: {closure.name}",
            request_data=data.model_dump(mode="json")
        )
        
        await self._trigger_leave_recalculation(data.start_date, data.end_date)
        
        return closure
    
    async def update_closure(self, id: UUID, data: CompanyClosureUpdate, user_id: Optional[UUID] = None):
        """Update company closure."""
        closure = await self._closure_repo.update(id, **data.model_dump(exclude_unset=True))
        if not closure:
            raise NotFoundError("Company closure not found", entity_type="CompanyClosure", entity_id=str(id))
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="COMPANY_CLOSURE",
            resource_id=str(id),
            description=f"Updated company closure: {closure.name}",
            request_data=data.model_dump(mode="json")
        )
        
        await self._trigger_leave_recalculation(closure.start_date, closure.end_date)
        
        return closure
    
    async def delete_closure(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete company closure."""
        closure = await self.get_closure(id)
        result = await self._closure_repo.delete(id)
        if not result:
            raise NotFoundError("Company closure not found", entity_type="CompanyClosure", entity_id=str(id))
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="COMPANY_CLOSURE",
            resource_id=str(id),
            description=f"Deleted company closure: {closure.name}"
        )
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _trigger_leave_recalculation(self, start_date, end_date) -> None:
        """Trigger leave recalculation for approved requests overlapping with dates."""
        try:
            leave_client = LeaveClient()
            await leave_client.recalculate_for_closure(start_date, end_date)
        except Exception as e:
            self._logger.error(f"Failed to trigger leave recalculation: {e}")
    
    async def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache for a specific key."""
        if not self._redis or not key:
            return
        await self._redis.delete(f"{self.CACHE_PREFIX}{key}")
