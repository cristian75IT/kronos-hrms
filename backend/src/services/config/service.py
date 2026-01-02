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
        """Get all configs with parsed values."""
        configs = await self._config_repo.get_all()
        for config in configs:
            config.value = self._parse_value(config.value, config.value_type)
        return configs

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
            if isinstance(value, str):
                return value.lower() == "true"
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

    async def update_holiday(self, id: UUID, data) -> Any:
        """Update holiday - supports confirmation and other fields."""
        holiday = await self._holiday_repo.get(id)
        if not holiday:
            raise NotFoundError("Holiday not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(holiday, key, value)
        
        await self._db.commit()
        await self._db.refresh(holiday)
        await self._invalidate_cache(f"holidays:{holiday.year}")
        return holiday


    async def generate_holidays(self, data: GenerateHolidaysRequest) -> list:
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

    # ═══════════════════════════════════════════════════════════
    # National Contracts (CCNL)
    # ═══════════════════════════════════════════════════════════

    async def get_national_contracts(self, active_only: bool = True) -> list:
        """Get all national contracts."""
        from src.services.config.models import NationalContract, NationalContractVersion, NationalContractTypeConfig
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(NationalContract).options(
            selectinload(NationalContract.versions)
            .selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContract.versions)
            .selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContract.versions)
            .selectinload(NationalContractVersion.rol_calc_mode),
            selectinload(NationalContract.levels)
        )
        if active_only:
            query = query.where(NationalContract.is_active == True)
        query = query.order_by(NationalContract.name)
        
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_national_contract(self, id: UUID):
        """Get national contract by ID."""
        from src.services.config.models import NationalContract, NationalContractVersion, NationalContractTypeConfig
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(NationalContract).options(
            selectinload(NationalContract.versions)
            .selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContract.versions)
            .selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContract.versions)
            .selectinload(NationalContractVersion.rol_calc_mode),
            selectinload(NationalContract.levels)
        ).where(NationalContract.id == id)
        
        result = await self._session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        return contract

    async def create_national_contract(self, data):
        """Create new national contract."""
        from src.services.config.models import NationalContract
        from sqlalchemy import select
        
        # Check if code exists
        query = select(NationalContract).where(NationalContract.code == data.code)
        result = await self._session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ConflictError(f"National contract code already exists: {data.code}")
        
        contract = NationalContract(**data.model_dump())
        self._session.add(contract)
        await self._session.commit()
        await self._session.refresh(contract)
        return contract

    async def update_national_contract(self, id: UUID, data):
        """Update national contract."""
        from src.services.config.models import NationalContract
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(NationalContract).options(
            selectinload(NationalContract.versions)
        ).where(NationalContract.id == id)
        result = await self._session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contract, key, value)
        
        await self._session.commit()
        await self._session.refresh(contract)
        return contract

    async def delete_national_contract(self, id: UUID) -> bool:
        """Deactivate national contract (soft delete)."""
        from src.services.config.models import NationalContract
        from sqlalchemy import select
        
        query = select(NationalContract).where(NationalContract.id == id)
        result = await self._session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        
        contract.is_active = False
        await self._session.commit()
        return True

    # ═══════════════════════════════════════════════════════════
    # National Contract Versions
    # ═══════════════════════════════════════════════════════════

    async def get_contract_versions(self, contract_id: UUID) -> list:
        """Get all versions for a national contract."""
        from src.services.config.models import NationalContractVersion, NationalContractTypeConfig
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(NationalContractVersion).options(
            selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContractVersion.rol_calc_mode)
        ).where(
            NationalContractVersion.national_contract_id == contract_id
        ).order_by(NationalContractVersion.valid_from.desc())
        
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_contract_version(self, version_id: UUID):
        """Get a specific version by ID."""
        from src.services.config.models import NationalContractVersion, NationalContractTypeConfig
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        query = select(NationalContractVersion).options(
            selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContractVersion.rol_calc_mode)
        ).where(NationalContractVersion.id == version_id)
        result = await self._session.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        return version

    async def get_contract_version_at_date(self, contract_id: UUID, reference_date):
        """Get the version valid at a specific date.
        
        This is the core method for historical calculations.
        Returns the version where valid_from <= reference_date AND (valid_to is NULL OR valid_to >= reference_date).
        """
        from src.services.config.models import NationalContractVersion, NationalContractTypeConfig
        from sqlalchemy import select, and_, or_
        from sqlalchemy.orm import selectinload
        
        query = select(NationalContractVersion).options(
            selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContractVersion.rol_calc_mode)
        ).where(
            and_(
                NationalContractVersion.national_contract_id == contract_id,
                NationalContractVersion.valid_from <= reference_date,
                or_(
                    NationalContractVersion.valid_to == None,
                    NationalContractVersion.valid_to >= reference_date
                )
            )
        ).order_by(NationalContractVersion.valid_from.desc()).limit(1)
        
        result = await self._session.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise NotFoundError(
                f"No contract version found for date {reference_date}", 
                entity_type="NationalContractVersion", 
                entity_id=str(contract_id)
            )
        return version

    async def create_contract_version(self, data, created_by: UUID = None):
        """Create new version for a national contract.
        
        Automatically updates the valid_to of the previous version.
        """
        from src.services.config.models import NationalContract, NationalContractVersion
        from sqlalchemy import select
        from datetime import timedelta
        
        # Verify contract exists
        query = select(NationalContract).where(NationalContract.id == data.national_contract_id)
        result = await self._session.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(data.national_contract_id))
        
        # Find the previous version that is still valid (valid_to is NULL)
        query = select(NationalContractVersion).where(
            and_(
                NationalContractVersion.national_contract_id == data.national_contract_id,
                NationalContractVersion.valid_to == None,
                NationalContractVersion.valid_from < data.valid_from
            )
        ).order_by(NationalContractVersion.valid_from.desc()).limit(1)
        
        result = await self._session.execute(query)
        previous_version = result.scalar_one_or_none()
        
        # Update the previous version's valid_to to day before new version starts
        if previous_version:
            previous_version.valid_to = data.valid_from - timedelta(days=1)
        
        # Create new version
        version_data = data.model_dump()
        version_data['created_by'] = created_by
        version = NationalContractVersion(**version_data)
        self._session.add(version)
        
        await self._session.commit()
        await self._session.refresh(version)
        return version

    async def update_contract_version(self, version_id: UUID, data):
        """Update a contract version."""
        from src.services.config.models import NationalContractVersion
        from sqlalchemy import select
        
        query = select(NationalContractVersion).where(NationalContractVersion.id == version_id)
        result = await self._session.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(version, key, value)
        
        await self._session.commit()
        await self._session.refresh(version)
        return version

    async def delete_contract_version(self, version_id: UUID) -> bool:
        """Delete a contract version (hard delete)."""
        from src.services.config.models import NationalContractVersion
        from sqlalchemy import select
        
        query = select(NationalContractVersion).where(NationalContractVersion.id == version_id)
        result = await self._session.execute(query)
        version = result.scalar_one_or_none()
        
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        
        await self._session.delete(version)
        await self._session.commit()
        return True


    async def get_contract_types(self):
        """Get all available contract types."""
        from src.services.config.models import ContractType
        from sqlalchemy import select
        
        stmt = select(ContractType).where(ContractType.is_active == True)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create_contract_type_config(self, data):
        """Create contract type parameter configuration."""
        from src.services.config.models import NationalContractTypeConfig
        
        config = NationalContractTypeConfig(**data.model_dump())
        self._session.add(config)
        await self._session.commit()
        await self._session.refresh(config)
        return config

    async def delete_contract_type_config(self, config_id: UUID) -> bool:
        """Delete contract type parameter configuration."""
        from src.services.config.models import NationalContractTypeConfig
        from sqlalchemy import select
        
        stmt = select(NationalContractTypeConfig).where(NationalContractTypeConfig.id == config_id)
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            raise NotFoundError("Config not found", entity_type="NationalContractTypeConfig", entity_id=str(config_id))
            
        await self._session.delete(config)
        await self._session.commit()
        return True

    async def update_contract_type_config(self, config_id: UUID, data):
        """Update contract type parameter configuration."""
        from src.services.config.models import NationalContractTypeConfig
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        stmt = select(NationalContractTypeConfig).options(
            selectinload(NationalContractTypeConfig.contract_type)
        ).where(NationalContractTypeConfig.id == config_id)
        
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            raise NotFoundError("Contract type configuration not found", entity_type="NationalContractTypeConfig", entity_id=str(config_id))
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
            
        await self._session.commit()
        await self._session.refresh(config)
        return config

    # ═══════════════════════════════════════════════════════════
    # National Contract Levels
    # ═══════════════════════════════════════════════════════════

    async def create_national_contract_level(self, data):
        """Create new level for a national contract."""
        from src.services.config.models import NationalContractLevel
        
        level = NationalContractLevel(**data.model_dump())
        self._session.add(level)
        await self._session.commit()
        await self._session.refresh(level)
        return level

    async def update_national_contract_level(self, level_id: UUID, data):
        """Update a contract level."""
        from src.services.config.models import NationalContractLevel
        from sqlalchemy import select
        
        query = select(NationalContractLevel).where(NationalContractLevel.id == level_id)
        result = await self._session.execute(query)
        level = result.scalar_one_or_none()
        
        if not level:
            raise NotFoundError("Contract level not found", entity_type="NationalContractLevel", entity_id=str(level_id))
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(level, key, value)
        
        await self._session.commit()
        await self._session.refresh(level)
        return level

    async def delete_national_contract_level(self, level_id: UUID) -> bool:
        """Delete a contract level."""
        from src.services.config.models import NationalContractLevel
        from sqlalchemy import select
        
        query = select(NationalContractLevel).where(NationalContractLevel.id == level_id)
        result = await self._session.execute(query)
        level = result.scalar_one_or_none()
        
        if not level:
            raise NotFoundError("Contract level not found", entity_type="NationalContractLevel", entity_id=str(level_id))
        
        await self._session.delete(level)
        await self._session.commit()
        return True

    # ═══════════════════════════════════════════════════════════
    # Calculation Modes
    # ═══════════════════════════════════════════════════════════

    async def get_calculation_modes(self) -> list:
        """Get all calculation modes."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        query = select(CalculationMode).where(CalculationMode.is_active == True)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_calculation_mode(self, id: UUID):
        """Get calculation mode by ID."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        query = select(CalculationMode).where(CalculationMode.id == id)
        result = await self._session.execute(query)
        mode = result.scalar_one_or_none()
        
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
        return mode

    async def create_calculation_mode(self, data):
        """Create new calculation mode."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        # Check code uniqueness
        query = select(CalculationMode).where(CalculationMode.code == data.code)
        result = await self._session.execute(query)
        existing = result.scalar_one_or_none()
        if existing:
            raise ConflictError(f"Calculation mode code already exists: {data.code}")
            
        mode = CalculationMode(**data.model_dump())
        self._session.add(mode)
        await self._session.commit()
        await self._session.refresh(mode)
        return mode

    async def update_calculation_mode(self, id: UUID, data):
        """Update calculation mode."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        query = select(CalculationMode).where(CalculationMode.id == id)
        result = await self._session.execute(query)
        mode = result.scalar_one_or_none()
        
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mode, key, value)
            
        await self._session.commit()
        await self._session.refresh(mode)
        return mode

    async def delete_calculation_mode(self, id: UUID) -> bool:
        """Deactivate calculation mode (soft delete)."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        query = select(CalculationMode).where(CalculationMode.id == id)
        result = await self._session.execute(query)
        mode = result.scalar_one_or_none()
        
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
            
        mode.is_active = False
        await self._session.commit()
        return True
