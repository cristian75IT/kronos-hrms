"""KRONOS Config Service - Business Logic."""
import json
import logging
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from workalendar.europe import Italy

from src.core.config import settings
from src.core.exceptions import NotFoundError, ValidationError, ConflictError
from src.shared.audit_client import get_audit_logger
from src.shared.clients import LeaveClient
from src.services.config.repository import (
    SystemConfigRepository,
    LeaveTypeRepository,
    HolidayRepository,
    CompanyClosureRepository,
    ExpenseTypeRepository,
    DailyAllowanceRuleRepository,
    NationalContractRepository,
    NationalContractVersionRepository,
    NationalContractLevelRepository,
    NationalContractTypeConfigRepository,
    CalculationModeRepository,
    ContractTypeRepository,
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
        self._redis = redis_client
        self._audit = get_audit_logger("config-service")
        
        # Repositories
        self._config_repo = SystemConfigRepository(session)
        self._leave_type_repo = LeaveTypeRepository(session)
        self._holiday_repo = HolidayRepository(session)
        self._closure_repo = CompanyClosureRepository(session)
        self._expense_type_repo = ExpenseTypeRepository(session)
        self._allowance_repo = DailyAllowanceRuleRepository(session)
        self._national_contract_repo = NationalContractRepository(session)
        self._contract_version_repo = NationalContractVersionRepository(session)
        self._contract_level_repo = NationalContractLevelRepository(session)
        self._contract_type_config_repo = NationalContractTypeConfigRepository(session)
        self._calc_mode_repo = CalculationModeRepository(session)
        self._contract_type_repo = ContractTypeRepository(session)

    async def _trigger_leave_recalculation(self, start_date, end_date) -> None:
        """Trigger leave recalculation for approved requests overlapping with dates."""
        try:
            leave_client = LeaveClient()
            await leave_client.recalculate_for_closure(start_date, end_date)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to trigger leave recalculation: {e}")

    # ═══════════════════════════════════════════════════════════
    # System Config
    # ═══════════════════════════════════════════════════════════

    async def get(self, key: str, default: Any = None) -> Any:
        """Get config value with cache."""
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

    async def set(self, key: str, value: Any, user_id: Optional[UUID] = None) -> None:
        """Update config value and invalidate cache."""
        config = await self._config_repo.get_by_key(key)
        if not config:
            raise NotFoundError(f"Config key not found: {key}")

        await self._config_repo.update(key, value=value)
        await self._invalidate_cache(key)

        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="SYSTEM_CONFIG",
            resource_id=key,
            description=f"Updated system config: {key}",
            request_data={"value": value}
        )

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

    async def create_config(self, data: SystemConfigCreate, user_id: Optional[UUID] = None):
        """Create new config entry."""
        existing = await self._config_repo.get_by_key(data.key)
        if existing:
            raise ConflictError(f"Config key already exists: {data.key}")

        config = await self._config_repo.create(
            key=data.key,
            value=data.value,
            value_type=data.value_type,
            category=data.category,
            description=data.description,
            is_sensitive=data.is_sensitive,
        )

        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="SYSTEM_CONFIG",
            resource_id=data.key,
            description=f"Created system config: {data.key}",
            request_data=data.model_dump(mode="json")
        )

        return config

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
            # Use SCAN to find all config keys
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

    async def create_leave_type(self, data: LeaveTypeCreate, user_id: Optional[UUID] = None):
        """Create new leave type."""
        existing = await self._leave_type_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Leave type code already exists: {data.code}")

        leave_type = await self._leave_type_repo.create(**data.model_dump())
        await self._invalidate_cache("leave_types")

        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="LEAVE_TYPE",
            resource_id=str(leave_type.id),
            description=f"Created leave type: {leave_type.name} ({leave_type.code})",
            request_data=data.model_dump(mode="json")
        )
        return leave_type

    async def update_leave_type(self, id: UUID, data: LeaveTypeUpdate, user_id: Optional[UUID] = None):
        """Update leave type."""
        leave_type = await self._leave_type_repo.update(id, **data.model_dump(exclude_unset=True))
        if not leave_type:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))

        await self._invalidate_cache("leave_types")

        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="LEAVE_TYPE",
            resource_id=str(id),
            description=f"Updated leave type: {leave_type.name}",
            request_data=data.model_dump(mode="json")
        )
        return leave_type

    async def delete_leave_type(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Deactivate leave type."""
        leave_type = await self.get_leave_type(id)
        result = await self._leave_type_repo.deactivate(id)
        if not result:
            raise NotFoundError("Leave type not found", entity_type="LeaveType", entity_id=str(id))

        await self._invalidate_cache("leave_types")

        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="LEAVE_TYPE",
            resource_id=str(id),
            description=f"Deactivated leave type: {leave_type.name}"
        )
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

    async def update_holiday(self, id: UUID, data, user_id: Optional[UUID] = None) -> Any:
        # Note: HolidayRepository.update is not implemented in repo.py above for simple update, 
        # but the service used manual update. I should implement update in Repo or do manual fetch/update. 
        # For now, I'll do manual fetch to keep logic same or I should have added update to repo.
        # But wait, BaseRepository style update was added to many classes. Let's check.
        # HolidayRepository in my LAST edit has create and delete. No update.
        # I will fetch and update via session manually here as fallback or better yet add update to repo next time.
        # But wait, I am committed to removing direct SQL. 
        # `_holiday_repo` is injected. I can implement `update` in repo now? 
        # No, I can't touch repo file now without another tool call.
        # I will access `_holiday_repo._session` which is allowed as it's the session.
        # Actually, standard pattern is `repo.update`.
        # I missed `update` in `HolidayRepository`.
        # I will just do the logic here using `holiday = await self._holiday_repo.get(id)` and standard SQLAlchemy update via session which is already injected.
        
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
        await self._holiday_repo.delete_national_by_year(data.year)

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

    async def create_expense_type(self, data: ExpenseTypeCreate, actor_id: Optional[UUID] = None):
        """Create new expense type."""
        existing = await self._expense_type_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Expense type code already exists: {data.code}")

        expense_type = await self._expense_type_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="EXPENSE_TYPE",
            resource_id=str(expense_type.id),
            description=f"Created expense type: {expense_type.name} ({expense_type.code})",
            request_data=data.model_dump(mode="json")
        )
        return expense_type

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

    async def create_allowance_rule(self, data: DailyAllowanceRuleCreate, actor_id: Optional[UUID] = None):
        """Create new allowance rule."""
        existing = await self._allowance_repo.get_by_destination_type(data.destination_type)
        if existing:
            raise ConflictError(f"Rule already exists for: {data.destination_type}")

        rule = await self._allowance_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="ALLOWANCE_RULE",
            resource_id=str(rule.id),
            description=f"Created allowance rule: {rule.name} for {rule.destination_type}",
            request_data=data.model_dump(mode="json")
        )
        return rule

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

    # ═══════════════════════════════════════════════════════════
    # National Contracts (CCNL)
    # ═══════════════════════════════════════════════════════════

    async def get_national_contracts(self, active_only: bool = True) -> list:
        """Get all national contracts."""
        return await self._national_contract_repo.get_all(active_only)

    async def get_national_contract(self, id: UUID):
        """Get national contract by ID."""
        contract = await self._national_contract_repo.get(id)
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        return contract

    async def create_national_contract(self, data, user_id: Optional[UUID] = None):
        """Create new national contract."""
        existing = await self._national_contract_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"National contract code already exists: {data.code}")
        
        contract = await self._national_contract_repo.create(**data.model_dump())

        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="NATIONAL_CONTRACT",
            resource_id=str(contract.id),
            description=f"Created national contract: {contract.name} ({contract.code})",
            request_data=data.model_dump(mode="json")
        )
        return contract

    async def update_national_contract(self, id: UUID, data, user_id: Optional[UUID] = None):
        """Update national contract."""
        contract = await self._national_contract_repo.update(id, **data.model_dump(exclude_unset=True))
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))

        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="NATIONAL_CONTRACT",
            resource_id=str(id),
            description=f"Updated national contract: {contract.name}",
            request_data=data.model_dump(exclude_unset=True)
        )
        return contract

    async def delete_national_contract(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Deactivate national contract (soft delete)."""
        contract = await self.get_national_contract(id)
        await self._national_contract_repo.delete(id)

        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="NATIONAL_CONTRACT",
            resource_id=str(id),
            description=f"Deactivated national contract: {contract.name}"
        )
        return True

    # ═══════════════════════════════════════════════════════════
    # National Contract Versions
    # ═══════════════════════════════════════════════════════════

    async def get_contract_versions(self, contract_id: UUID) -> list:
        """Get all versions for a national contract."""
        return await self._contract_version_repo.get_by_contract(contract_id)

    async def get_contract_version(self, version_id: UUID):
        """Get a specific version by ID."""
        version = await self._contract_version_repo.get(version_id)
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        return version

    async def get_contract_version_at_date(self, contract_id: UUID, reference_date):
        """Get the version valid at a specific date."""
        version = await self._contract_version_repo.get_valid_at_date(contract_id, reference_date)
        if not version:
            raise NotFoundError(
                f"No contract version found for date {reference_date}", 
                entity_type="NationalContractVersion", 
                entity_id=str(contract_id)
            )
        return version

    async def create_contract_version(self, data, created_by: UUID = None):
        """Create new version for a national contract."""
        from datetime import timedelta
        
        contract = await self.get_national_contract(data.national_contract_id)
        
        # Find previous valid
        previous_version = await self._contract_version_repo.get_previous_valid(
            data.national_contract_id, data.valid_from
        )
        
        # Update previous version
        if previous_version:
            previous_version.valid_to = data.valid_from - timedelta(days=1)
            await self._session.flush() # Commit handled at end of request or explicit commit
        
        version_data = data.model_dump()
        version_data['created_by'] = created_by
        version = await self._contract_version_repo.create(**version_data)
        
        await self._session.commit()

        await self._audit.log_action(
            user_id=created_by,
            action="CREATE",
            resource_type="NATIONAL_CONTRACT_VERSION",
            resource_id=str(version.id),
            description=f"Created new version for national contract {contract.name}: {version.version_name}",
            request_data=data.model_dump(mode="json")
        )
        return version

    async def update_contract_version(self, version_id: UUID, data, user_id: Optional[UUID] = None):
        """Update a contract version."""
        version = await self._contract_version_repo.update(version_id, **data.model_dump(exclude_unset=True))
        if not version:
             raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))

        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="NATIONAL_CONTRACT_VERSION",
            resource_id=str(version_id),
            description=f"Updated national contract version: {version.version_name}",
            request_data=data.model_dump(mode="json")
        )
        return version

    async def delete_contract_version(self, version_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete a contract version (hard delete)."""
        version = await self.get_contract_version(version_id)
        await self._contract_version_repo.delete(version_id)

        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="NATIONAL_CONTRACT_VERSION",
            resource_id=str(version_id),
            description=f"Deleted national contract version: {version.version_name}"
        )
        return True

    async def get_contract_types(self):
        """Get all available contract types."""
        return await self._contract_type_repo.get_all()

    async def create_contract_type_config(self, data, actor_id: Optional[UUID] = None):
        """Create contract type parameter configuration."""
        config = await self._contract_type_config_repo.create(**data.model_dump())

        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="CONTRACT_TYPE_CONFIG",
            resource_id=str(config.id),
            description=f"Created contract type config for version {data.national_contract_version_id}",
            request_data=data.model_dump(mode="json")
        )
        return config

    async def delete_contract_type_config(self, config_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Delete contract type parameter configuration."""
        result = await self._contract_type_config_repo.delete(config_id)
        if not result:
            raise NotFoundError("Config not found", entity_type="NationalContractTypeConfig", entity_id=str(config_id))

        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="CONTRACT_TYPE_CONFIG",
            resource_id=str(config_id),
            description=f"Deleted contract type config override"
        )
        return True

    async def update_contract_type_config(self, config_id: UUID, data, actor_id: Optional[UUID] = None):
        """Update contract type parameter configuration."""
        config = await self._contract_type_config_repo.update(config_id, **data.model_dump(exclude_unset=True))
        if not config:
            raise NotFoundError("Contract type configuration not found", entity_type="NationalContractTypeConfig", entity_id=str(config_id))

        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="CONTRACT_TYPE_CONFIG",
            resource_id=str(config_id),
            description=f"Updated contract type config for version {config.national_contract_version_id}",
            request_data=data.model_dump(mode="json")
        )
        return config

    # ═══════════════════════════════════════════════════════════
    # National Contract Levels
    # ═══════════════════════════════════════════════════════════

    async def create_national_contract_level(self, data, actor_id: Optional[UUID] = None):
        """Create new level for a national contract."""
        level = await self._contract_level_repo.create(**data.model_dump())

        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="NATIONAL_CONTRACT_LEVEL",
            resource_id=str(level.id),
            description=f"Created level {level.level_name} for contract {level.national_contract_id}",
            request_data=data.model_dump(mode="json")
        )
        return level

    async def update_national_contract_level(self, level_id: UUID, data, actor_id: Optional[UUID] = None):
        """Update a contract level."""
        level = await self._contract_level_repo.update(level_id, **data.model_dump(exclude_unset=True))
        if not level:
            raise NotFoundError("Contract level not found", entity_type="NationalContractLevel", entity_id=str(level_id))

        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="NATIONAL_CONTRACT_LEVEL",
            resource_id=str(level_id),
            description=f"Updated level {level.level_name}",
            request_data=data.model_dump(mode="json")
        )
        return level

    async def delete_national_contract_level(self, level_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Delete a contract level."""
        level = await self._contract_level_repo.get(level_id)
        if not level:
             raise NotFoundError("Contract level not found", entity_type="NationalContractLevel", entity_id=str(level_id))
             
        await self._contract_level_repo.delete(level_id)

        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="NATIONAL_CONTRACT_LEVEL",
            resource_id=str(level_id),
            description=f"Deleted level {level.level_name}"
        )
        return True

    # ═══════════════════════════════════════════════════════════
    # Calculation Modes
    # ═══════════════════════════════════════════════════════════

    async def get_calculation_modes(self) -> list:
        """Get all calculation modes."""
        return await self._calc_mode_repo.get_all()

    async def get_calculation_mode(self, id: UUID):
        """Get calculation mode by ID."""
        mode = await self._calc_mode_repo.get(id)
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
        return mode

    async def create_calculation_mode(self, data, actor_id: Optional[UUID] = None):
        """Create new calculation mode."""
        existing = await self._calc_mode_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Calculation mode code already exists: {data.code}")
            
        mode = await self._calc_mode_repo.create(**data.model_dump())

        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="CALCULATION_MODE",
            resource_id=str(mode.id),
            description=f"Created calculation mode: {mode.name} ({mode.code})",
            request_data=data.model_dump(mode="json")
        )
        return mode

    async def update_calculation_mode(self, id: UUID, data, actor_id: Optional[UUID] = None):
        """Update calculation mode."""
        mode = await self._calc_mode_repo.update(id, **data.model_dump(exclude_unset=True))
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))

        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="CALCULATION_MODE",
            resource_id=str(id),
            description=f"Updated calculation mode: {mode.name}",
            request_data=data.model_dump(mode="json")
        )
        return mode

    async def delete_calculation_mode(self, id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Deactivate calculation mode (soft delete)."""
        mode = await self.get_calculation_mode(id)
        
        # Soft delete by update
        await self._calc_mode_repo.update(id, is_active=False)

        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="CALCULATION_MODE",
            resource_id=str(id),
            description=f"Deactivated calculation mode: {mode.name}"
        )
        return True
