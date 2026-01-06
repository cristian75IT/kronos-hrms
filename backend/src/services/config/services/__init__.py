"""
KRONOS - Config Services Package

Modular config service architecture for enterprise maintainability.

This package splits the monolithic ConfigService (~1199 lines) into focused modules:
- system_config.py: System configuration (key-value settings) (~170 lines)
- leave_types.py: Leave type management (~160 lines)
- holidays.py: Holidays and company closures (~280 lines)
- contracts.py: National contracts (CCNL), versions, levels (~420 lines)

Usage:
    from src.services.config.services import ConfigService
    
    service = ConfigService(session, redis_client)
    leave_types = await service.get_leave_types()
"""
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.audit_client import get_audit_logger
from src.services.config.repository import ExpenseTypeRepository, DailyAllowanceRuleRepository
from src.services.config.schemas import ExpenseTypeCreate, DailyAllowanceRuleCreate
from src.core.exceptions import NotFoundError, ConflictError

# Import sub-services
from src.services.config.services.system_config import SystemConfigService
from src.services.config.services.leave_types import LeaveTypeService
from src.services.config.services.holidays import HolidayService
from src.services.config.services.contracts import NationalContractService


class ConfigService:
    """
    Unified Config Service façade.
    
    This class provides a single interface for all configuration operations
    while delegating to specialized sub-services for maintainability.
    
    Sub-services:
    - _system: System configuration (key-value settings)
    - _leave_types: Leave type management
    - _holidays: Holidays and company closures
    - _contracts: National contracts (CCNL)
    """
    
    def __init__(
        self,
        session: AsyncSession,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        self._session = session
        self._redis = redis_client
        
        # Initialize sub-services
        self._system = SystemConfigService(session, redis_client)
        self._leave_types = LeaveTypeService(session, redis_client)
        self._holidays = HolidayService(session, redis_client)
        self._contracts = NationalContractService(session)
        
        # Expense types and allowances (remain in main service for now)
        self._expense_type_repo = ExpenseTypeRepository(session)
        self._allowance_repo = DailyAllowanceRuleRepository(session)
        self._audit = get_audit_logger("config-service")
    
    # ═══════════════════════════════════════════════════════════════════════
    # System Config (delegated to SystemConfigService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get(self, key: str, default: Any = None) -> Any:
        return await self._system.get(key, default)
    
    async def set(self, key: str, value: Any, user_id: Optional[UUID] = None) -> None:
        return await self._system.set(key, value, user_id)
    
    async def get_by_category(self, category: str) -> dict[str, Any]:
        return await self._system.get_by_category(category)
    
    async def get_all(self) -> list:
        return await self._system.get_all()
    
    async def create_config(self, data, user_id: Optional[UUID] = None):
        return await self._system.create_config(data, user_id)
    
    async def clear_cache(self) -> None:
        return await self._system.clear_cache()
    
    # ═══════════════════════════════════════════════════════════════════════
    # Leave Types (delegated to LeaveTypeService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_leave_types(self, active_only: bool = True) -> list:
        return await self._leave_types.get_leave_types(active_only)
    
    async def get_leave_type(self, id: UUID):
        return await self._leave_types.get_leave_type(id)
    
    async def get_leave_type_by_code(self, code: str):
        return await self._leave_types.get_leave_type_by_code(code)
    
    async def create_leave_type(self, data, user_id: Optional[UUID] = None):
        return await self._leave_types.create_leave_type(data, user_id)
    
    async def update_leave_type(self, id: UUID, data, user_id: Optional[UUID] = None):
        return await self._leave_types.update_leave_type(id, data, user_id)
    
    async def delete_leave_type(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        return await self._leave_types.delete_leave_type(id, user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Holidays (delegated to HolidayService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_holidays(self, year: int, location_id: Optional[UUID] = None) -> list:
        return await self._holidays.get_holidays(year, location_id)
    
    async def create_holiday(self, data, user_id: Optional[UUID] = None):
        return await self._holidays.create_holiday(data, user_id)
    
    async def delete_holiday(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        return await self._holidays.delete_holiday(id, user_id)
    
    async def update_holiday(self, id: UUID, data, user_id: Optional[UUID] = None):
        return await self._holidays.update_holiday(id, data, user_id)
    
    async def generate_holidays(self, data, user_id: Optional[UUID] = None) -> list:
        return await self._holidays.generate_holidays(data, user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Company Closures (delegated to HolidayService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_closures(self, year: int, include_inactive: bool = False) -> list:
        return await self._holidays.get_closures(year, include_inactive)
    
    async def get_closure(self, id: UUID):
        return await self._holidays.get_closure(id)
    
    async def create_closure(self, data, created_by: UUID = None):
        return await self._holidays.create_closure(data, created_by)
    
    async def update_closure(self, id: UUID, data, user_id: Optional[UUID] = None):
        return await self._holidays.update_closure(id, data, user_id)
    
    async def delete_closure(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        return await self._holidays.delete_closure(id, user_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # National Contracts (delegated to NationalContractService)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_national_contracts(self, active_only: bool = True) -> list:
        return await self._contracts.get_national_contracts(active_only)
    
    async def get_national_contract(self, id: UUID):
        return await self._contracts.get_national_contract(id)
    
    async def create_national_contract(self, data, user_id: Optional[UUID] = None):
        return await self._contracts.create_national_contract(data, user_id)
    
    async def update_national_contract(self, id: UUID, data, user_id: Optional[UUID] = None):
        return await self._contracts.update_national_contract(id, data, user_id)
    
    async def delete_national_contract(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        return await self._contracts.delete_national_contract(id, user_id)
    
    # Contract Versions
    async def get_contract_versions(self, contract_id: UUID) -> list:
        return await self._contracts.get_contract_versions(contract_id)
    
    async def get_contract_version(self, version_id: UUID):
        return await self._contracts.get_contract_version(version_id)
    
    async def get_contract_version_at_date(self, contract_id: UUID, reference_date):
        return await self._contracts.get_contract_version_at_date(contract_id, reference_date)
    
    async def create_contract_version(self, data, created_by: UUID = None):
        return await self._contracts.create_contract_version(data, created_by)
    
    async def update_contract_version(self, version_id: UUID, data, user_id: Optional[UUID] = None):
        return await self._contracts.update_contract_version(version_id, data, user_id)
    
    async def delete_contract_version(self, version_id: UUID, user_id: Optional[UUID] = None) -> bool:
        return await self._contracts.delete_contract_version(version_id, user_id)
    
    # Contract Types
    async def get_contract_types(self):
        return await self._contracts.get_contract_types()
    
    async def create_contract_type_config(self, data, actor_id: Optional[UUID] = None):
        return await self._contracts.create_contract_type_config(data, actor_id)
    
    async def update_contract_type_config(self, config_id: UUID, data, actor_id: Optional[UUID] = None):
        return await self._contracts.update_contract_type_config(config_id, data, actor_id)
    
    async def delete_contract_type_config(self, config_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        return await self._contracts.delete_contract_type_config(config_id, actor_id)
    
    # Contract Levels
    async def create_national_contract_level(self, data, actor_id: Optional[UUID] = None):
        return await self._contracts.create_national_contract_level(data, actor_id)
    
    async def update_national_contract_level(self, level_id: UUID, data, actor_id: Optional[UUID] = None):
        return await self._contracts.update_national_contract_level(level_id, data, actor_id)
    
    async def delete_national_contract_level(self, level_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        return await self._contracts.delete_national_contract_level(level_id, actor_id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Expense Types & Allowances (remain in main service)
    # ═══════════════════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # Calculation Modes (remain in main service for now)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_calculation_modes(self):
        """Get all calculation modes."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        stmt = select(CalculationMode).where(CalculationMode.is_active == True)
        result = await self._session.execute(stmt)
        return result.scalars().all()
    
    async def get_calculation_mode(self, id: UUID):
        """Get calculation mode by ID."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        stmt = select(CalculationMode).where(CalculationMode.id == id)
        result = await self._session.execute(stmt)
        mode = result.scalar_one_or_none()
        
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
        return mode
    
    async def create_calculation_mode(self, data, actor_id: Optional[UUID] = None):
        """Create new calculation mode."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        # Check for duplicate code
        stmt = select(CalculationMode).where(CalculationMode.code == data.code)
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError(f"Calculation mode code already exists: {data.code}")
        
        mode = CalculationMode(**data.model_dump())
        self._session.add(mode)
        await self._session.commit()
        await self._session.refresh(mode)
        
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
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        stmt = select(CalculationMode).where(CalculationMode.id == id)
        result = await self._session.execute(stmt)
        mode = result.scalar_one_or_none()
        
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mode, key, value)
        
        await self._session.commit()
        await self._session.refresh(mode)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="CALCULATION_MODE",
            resource_id=str(id),
            description=f"Updated calculation mode: {mode.name}",
            request_data=update_data
        )
        return mode
    
    async def delete_calculation_mode(self, id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Deactivate calculation mode (soft delete)."""
        from src.services.config.models import CalculationMode
        from sqlalchemy import select
        
        stmt = select(CalculationMode).where(CalculationMode.id == id)
        result = await self._session.execute(stmt)
        mode = result.scalar_one_or_none()
        
        if not mode:
            raise NotFoundError("Calculation mode not found", entity_type="CalculationMode", entity_id=str(id))
        
        mode.is_active = False
        mode_name = mode.name
        await self._session.commit()
        
        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="CALCULATION_MODE",
            resource_id=str(id),
            description=f"Deactivated calculation mode: {mode_name}"
        )
        return True


# Export for backward compatibility
__all__ = [
    "ConfigService",
    "SystemConfigService",
    "LeaveTypeService",
    "HolidayService",
    "NationalContractService",
]
