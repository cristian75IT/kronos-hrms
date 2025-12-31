"""KRONOS Config Service - Business Logic."""
import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from workalendar.europe import Italy

from src.core.config import settings
from src.core.exceptions import NotFoundError, ValidationError, ConflictError
from src.services.config.repository import (
    SystemConfigRepository,
    LeaveTypeRepository,
    HolidayRepository,
    CompanyClosureRepository,
    ExpenseTypeRepository,
    DailyAllowanceRuleRepository,
)
from src.services.config.schemas import (
    SystemConfigCreate,
    SystemConfigUpdate,
    LeaveTypeCreate,
    LeaveTypeUpdate,
    HolidayCreate,
    GenerateHolidaysRequest,
    CompanyClosureCreate,
    CompanyClosureUpdate,
    ExpenseTypeCreate,
    DailyAllowanceRuleCreate,
)


class ConfigService:
    """Service for dynamic configuration with Redis cache."""

    CACHE_PREFIX = "config:"
    CACHE_TTL = 300  # 5 minutes

    def __init__(
        self,
        session: AsyncSession,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        self._session = session
        self._config_repo = SystemConfigRepository(session)
        self._leave_type_repo = LeaveTypeRepository(session)
        self._holiday_repo = HolidayRepository(session)
        self._closure_repo = CompanyClosureRepository(session)
        self._expense_type_repo = ExpenseTypeRepository(session)
        self._allowance_repo = DailyAllowanceRuleRepository(session)
        self._redis = redis_client

    # ═══════════════════════════════════════════════════════════
    # System Config
    # ═══════════════════════════════════════════════════════════

    async def get(self, key: str, default: Any = None) -> Any:
        """Get config value with cache.

        Args:
            key: Config key (e.g., 'leave.min_notice_days.rol')
            default: Fallback value if not found

        Returns:
            Config value (automatically typed based on value_type)
        """
        # Try cache first
        if self._redis:
            cache_key = f"{self.CACHE_PREFIX}{key}"
            cached = await self._redis.get(cache_key)
            if cached is not None:
                return json.loads(cached)

        # Query database
        config = await self._config_repo.get_by_key(key)
        if config is None:
            return default

        # Parse value
        value = self._parse_value(config.value, config.value_type)

        # Cache result
        if self._redis:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(value),
            )

        return value

    async def set(self, key: str, value: Any) -> None:
        """Update config value and invalidate cache."""
        config = await self._config_repo.get_by_key(key)
        if not config:
            raise NotFoundError(f"Config key not found: {key}")

        await self._config_repo.update(key, value=value)
        await self._invalidate_cache(key)

    async def get_by_category(self, category: str) -> dict[str, Any]:
        """Get all configs in a category."""
        configs = await self._config_repo.get_by_category(category)
        return {
            c.key: self._parse_value(c.value, c.value_type)
            for c in configs
        }

    async def get_all(self) -> list:
        """Get all configs."""
        return await self._config_repo.get_all()

    async def create_config(self, data: SystemConfigCreate):
        """Create new config entry."""
        existing = await self._config_repo.get_by_key(data.key)
        if existing:
            raise ConflictError(f"Config key already exists: {data.key}")

        return await self._config_repo.create(
            key=data.key,
            value=data.value,
            value_type=data.value_type,
            category=data.category,
            description=data.description,
            is_sensitive=data.is_sensitive,
        )

    def _parse_value(self, value: Any, value_type: str) -> Any:
        """Convert JSONB value to Python type."""
        if value_type == "integer":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "boolean":
            return bool(value)
        elif value_type == "json":
            return value
        else:
            return str(value)

    async def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache for a specific key or all config."""
        if not self._redis:
            return

        if key:
            await self._redis.delete(f"{self.CACHE_PREFIX}{key}")
        else:
            # Use SCAN to find all config keys (safer than KEYS)
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=f"{self.CACHE_PREFIX}*",
                    count=100,
                )
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break

    async def clear_cache(self) -> None:
        """Clear the entire Redis cache for this service."""
        if not self._redis:
            return
            
        await self._redis.flushdb()

    # ═══════════════════════════════════════════════════════════
    # Leave Types
    # ═══════════════════════════════════════════════════════════

    async def get_leave_types(self, active_only: bool = True) -> list:
        """Get all leave types."""
        # Try cache
        if self._redis and active_only:
            cache_key = f"{self.CACHE_PREFIX}leave_types"
            cached = await self._redis.get(cache_key)
            if cached:
                return json.loads(cached)

        types = await self._leave_type_repo.get_all(active_only)

        # Cache if active only
        if self._redis and active_only:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps([self._leave_type_to_dict(t) for t in types]),
            )

        return types

    async def get_leave_type(self, id: UUID):
        """Get leave type by ID."""
        leave_type = await self._leave_type_repo.get(id)
        if not leave_type:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))
        return leave_type

    async def get_leave_type_by_code(self, code: str):
        """Get leave type by code."""
        leave_type = await self._leave_type_repo.get_by_code(code)
        if not leave_type:
            raise NotFoundError(f"Leave type not found: {code}")
        return leave_type

    async def create_leave_type(self, data: LeaveTypeCreate):
        """Create new leave type."""
        existing = await self._leave_type_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Leave type code already exists: {data.code}")

        leave_type = await self._leave_type_repo.create(**data.model_dump())
        await self._invalidate_cache("leave_types")
        return leave_type

    async def update_leave_type(self, id: UUID, data: LeaveTypeUpdate):
        """Update leave type."""
        leave_type = await self._leave_type_repo.update(id, **data.model_dump(exclude_unset=True))
        if not leave_type:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))

        await self._invalidate_cache("leave_types")
        return leave_type

    async def delete_leave_type(self, id: UUID) -> bool:
        """Deactivate leave type."""
        result = await self._leave_type_repo.deactivate(id)
        if not result:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))

        await self._invalidate_cache("leave_types")
        return True

    def _leave_type_to_dict(self, leave_type) -> dict:
        """Convert leave type to dict for caching."""
        return {
            "id": str(leave_type.id),
            "code": leave_type.code,
            "name": leave_type.name,
            "description": leave_type.description,
            "color": leave_type.color,
            "icon": leave_type.icon,
            "sort_order": leave_type.sort_order,
            "scales_balance": leave_type.scales_balance,
            "balance_type": leave_type.balance_type,
            "requires_approval": leave_type.requires_approval,
            "requires_attachment": leave_type.requires_attachment,
            "requires_protocol": leave_type.requires_protocol,
            "min_notice_days": leave_type.min_notice_days,
            "max_consecutive_days": leave_type.max_consecutive_days,
            "max_per_month": leave_type.max_per_month,
            "allow_past_dates": leave_type.allow_past_dates,
            "allow_half_day": leave_type.allow_half_day,
            "allow_negative_balance": leave_type.allow_negative_balance,
            "is_active": leave_type.is_active,
            "created_at": leave_type.created_at.isoformat() if leave_type.created_at else None,
            "updated_at": leave_type.updated_at.isoformat() if leave_type.updated_at else None,
        }

    # ═══════════════════════════════════════════════════════════
    # Holidays
    # ═══════════════════════════════════════════════════════════

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

    async def create_holiday(self, data: HolidayCreate):
        """Create new holiday."""
        existing = await self._holiday_repo.get_by_date(data.date)
        if existing:
            raise ConflictError(f"Holiday already exists for date: {data.date}")

        holiday = await self._holiday_repo.create(**data.model_dump())
        await self._invalidate_cache(f"holidays:{data.date.year}")
        return holiday

    async def delete_holiday(self, id: UUID) -> bool:
        """Delete holiday."""
        holiday = await self._holiday_repo.get(id)
        if not holiday:
            raise NotFoundError("Holiday not found")

        year = holiday.year
        result = await self._holiday_repo.delete(id)
        await self._invalidate_cache(f"holidays:{year}")
        return result

    async def generate_holidays(self, data: GenerateHolidaysRequest) -> list:
        """Generate Italian national holidays for a year using workalendar."""
        # Delete existing for this year
        await self._holiday_repo.delete_by_year(data.year)

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

    # ═══════════════════════════════════════════════════════════
    # Expense Types
    # ═══════════════════════════════════════════════════════════

    async def get_expense_types(self, active_only: bool = True) -> list:
        """Get all expense types."""
        return await self._expense_type_repo.get_all(active_only)

    async def get_expense_type_by_code(self, code: str):
        """Get expense type by code."""
        expense_type = await self._expense_type_repo.get_by_code(code)
        if not expense_type:
            raise NotFoundError(f"Expense type not found: {code}")
        return expense_type

    async def create_expense_type(self, data: ExpenseTypeCreate):
        """Create new expense type."""
        existing = await self._expense_type_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Expense type code already exists: {data.code}")

        return await self._expense_type_repo.create(**data.model_dump())

    # ═══════════════════════════════════════════════════════════
    # Daily Allowance Rules
    # ═══════════════════════════════════════════════════════════

    async def get_allowance_rules(self) -> list:
        """Get all daily allowance rules."""
        return await self._allowance_repo.get_all()

    async def get_allowance_rule(self, destination_type: str):
        """Get allowance rule by destination type."""
        rule = await self._allowance_repo.get_by_destination_type(destination_type)
        if not rule:
            raise NotFoundError(f"Allowance rule not found: {destination_type}")
        return rule

    async def create_allowance_rule(self, data: DailyAllowanceRuleCreate):
        """Create new allowance rule."""
        existing = await self._allowance_repo.get_by_destination_type(data.destination_type)
        if existing:
            raise ConflictError(f"Rule already exists for: {data.destination_type}")

        return await self._allowance_repo.create(**data.model_dump())

    # ═══════════════════════════════════════════════════════════
    # Company Closures
    # ═══════════════════════════════════════════════════════════

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
        return closure

    async def update_closure(self, id: UUID, data: CompanyClosureUpdate):
        """Update company closure."""
        closure = await self._closure_repo.update(id, **data.model_dump(exclude_unset=True))
        if not closure:
            raise NotFoundError("Company closure not found", entity_type="CompanyClosure", entity_id=str(id))
        return closure

    async def delete_closure(self, id: UUID) -> bool:
        """Delete company closure."""
        result = await self._closure_repo.delete(id)
        if not result:
            raise NotFoundError("Company closure not found", entity_type="CompanyClosure", entity_id=str(id))
        return True
