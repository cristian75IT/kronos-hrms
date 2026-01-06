"""KRONOS Config Service - Repository Layer."""
from typing import Any, Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.config.models import (
    SystemConfig,
    LeaveType,
    Holiday,
    CompanyClosure,
    ExpenseType,
    DailyAllowanceRule,
    NationalContract,
    NationalContractVersion,
    NationalContractLevel,
    NationalContractTypeConfig,
    CalculationMode,
    ContractType,
)


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session


class SystemConfigRepository(BaseRepository):
    async def get_by_key(self, key: str) -> Optional[SystemConfig]:
        result = await self._session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> List[SystemConfig]:
        result = await self._session.execute(
            select(SystemConfig)
            .where(SystemConfig.category == category)
            .order_by(SystemConfig.key)
        )
        return list(result.scalars().all())

    async def get_all(self) -> List[SystemConfig]:
        result = await self._session.execute(
            select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> SystemConfig:
        config = SystemConfig(**kwargs)
        self._session.add(config)
        await self._session.flush()
        return config

    async def update(self, key: str, **kwargs: Any) -> Optional[SystemConfig]:
        config = await self.get_by_key(key)
        if not config:
            return None
        for field, value in kwargs.items():
            if hasattr(config, field):
                setattr(config, field, value)
        await self._session.flush()
        return config


class LeaveTypeRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[LeaveType]:
        result = await self._session.execute(select(LeaveType).where(LeaveType.id == id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[LeaveType]:
        result = await self._session.execute(select(LeaveType).where(LeaveType.code == code))
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> List[LeaveType]:
        query = select(LeaveType).order_by(LeaveType.sort_order, LeaveType.name)
        if active_only:
            query = query.where(LeaveType.is_active == True)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> LeaveType:
        leave_type = LeaveType(**kwargs)
        self._session.add(leave_type)
        await self._session.flush()
        return leave_type

    async def update(self, id: UUID, **kwargs: Any) -> Optional[LeaveType]:
        leave_type = await self.get(id)
        if not leave_type:
            return None
        for field, value in kwargs.items():
            if hasattr(leave_type, field) and value is not None:
                setattr(leave_type, field, value)
        await self._session.flush()
        return leave_type

    async def deactivate(self, id: UUID) -> bool:
        leave_type = await self.get(id)
        if not leave_type:
            return False
        leave_type.is_active = False
        await self._session.flush()
        return True


class HolidayRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[Holiday]:
        result = await self._session.execute(select(Holiday).where(Holiday.id == id))
        return result.scalar_one_or_none()

    async def get_by_year(self, year: int, location_id: Optional[UUID] = None) -> List[Holiday]:
        query = select(Holiday).where(Holiday.year == year)
        if location_id:
            query = query.where((Holiday.location_id == None) | (Holiday.location_id == location_id))
        query = query.order_by(Holiday.date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_date(self, date) -> Optional[Holiday]:
        result = await self._session.execute(select(Holiday).where(Holiday.date == date))
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> Holiday:
        if "year" not in kwargs and "date" in kwargs:
            kwargs["year"] = kwargs["date"].year
        holiday = Holiday(**kwargs)
        self._session.add(holiday)
        await self._session.flush()
        return holiday

    async def delete(self, id: UUID) -> bool:
        holiday = await self.get(id)
        if not holiday:
            return False
        await self._session.delete(holiday)
        await self._session.flush()
        return True

    async def delete_national_by_year(self, year: int) -> int:
        result = await self._session.execute(
            select(Holiday).where(Holiday.year == year, Holiday.is_national == True)
        )
        holidays = result.scalars().all()
        count = len(holidays)
        for holiday in holidays:
            await self._session.delete(holiday)
        await self._session.flush()
        return count


class CompanyClosureRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[CompanyClosure]:
        result = await self._session.execute(select(CompanyClosure).where(CompanyClosure.id == id))
        return result.scalar_one_or_none()

    async def get_by_year(self, year: int, include_inactive: bool = False) -> List[CompanyClosure]:
        query = select(CompanyClosure).where(CompanyClosure.year == year)
        if not include_inactive:
            query = query.where(CompanyClosure.is_active == True)
        query = query.order_by(CompanyClosure.start_date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> CompanyClosure:
        if "year" not in kwargs and "start_date" in kwargs:
            kwargs["year"] = kwargs["start_date"].year
        closure = CompanyClosure(**kwargs)
        self._session.add(closure)
        await self._session.flush()
        return closure

    async def update(self, id: UUID, **kwargs: Any) -> Optional[CompanyClosure]:
        closure = await self.get(id)
        if not closure:
            return None
        for key, value in kwargs.items():
            if hasattr(closure, key) and value is not None:
                setattr(closure, key, value)
        await self._session.flush()
        return closure

    async def delete(self, id: UUID) -> bool:
        closure = await self.get(id)
        if not closure:
            return False
        await self._session.delete(closure)
        await self._session.flush()
        return True


class ExpenseTypeRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[ExpenseType]:
        result = await self._session.execute(select(ExpenseType).where(ExpenseType.id == id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ExpenseType]:
        result = await self._session.execute(select(ExpenseType).where(ExpenseType.code == code))
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> List[ExpenseType]:
        query = select(ExpenseType).order_by(ExpenseType.category, ExpenseType.name)
        if active_only:
            query = query.where(ExpenseType.is_active == True)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ExpenseType:
        expense_type = ExpenseType(**kwargs)
        self._session.add(expense_type)
        await self._session.flush()
        return expense_type


class DailyAllowanceRuleRepository(BaseRepository):
    async def get_by_destination_type(self, destination_type: str) -> Optional[DailyAllowanceRule]:
        result = await self._session.execute(
            select(DailyAllowanceRule)
            .where(DailyAllowanceRule.destination_type == destination_type)
            .where(DailyAllowanceRule.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> List[DailyAllowanceRule]:
        query = select(DailyAllowanceRule).order_by(DailyAllowanceRule.name)
        if active_only:
            query = query.where(DailyAllowanceRule.is_active == True)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> DailyAllowanceRule:
        rule = DailyAllowanceRule(**kwargs)
        self._session.add(rule)
        await self._session.flush()
        return rule


class NationalContractRepository(BaseRepository):
    async def get_all(self, active_only: bool = True) -> List[NationalContract]:
        query = select(NationalContract).options(
            selectinload(NationalContract.versions),
            selectinload(NationalContract.levels)
        )
        if active_only:
            query = query.where(NationalContract.is_active == True)
        query = query.order_by(NationalContract.name)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get(self, id: UUID) -> Optional[NationalContract]:
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
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> Optional[NationalContract]:
        result = await self._session.execute(
            select(NationalContract).where(NationalContract.code == code)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> NationalContract:
        contract = NationalContract(**kwargs)
        self._session.add(contract)
        await self._session.flush()
        return contract

    async def update(self, id: UUID, **kwargs: Any) -> Optional[NationalContract]:
        contract = await self.get(id)
        if not contract:
            return None
        for key, value in kwargs.items():
            if hasattr(contract, key):
                setattr(contract, key, value)
        await self._session.flush()
        return contract


class NationalContractVersionRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[NationalContractVersion]:
        query = select(NationalContractVersion).options(
            selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContractVersion.rol_calc_mode)
        ).where(NationalContractVersion.id == id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_contract(self, contract_id: UUID) -> List[NationalContractVersion]:
        query = select(NationalContractVersion).options(
            selectinload(NationalContractVersion.contract_type_configs)
            .selectinload(NationalContractTypeConfig.contract_type),
            selectinload(NationalContractVersion.vacation_calc_mode),
            selectinload(NationalContractVersion.rol_calc_mode)
        ).where(
            NationalContractVersion.national_contract_id == contract_id
        ).order_by(NationalContractVersion.valid_from.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_valid_at_date(self, contract_id: UUID, reference_date) -> Optional[NationalContractVersion]:
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
        return result.scalar_one_or_none()

    async def get_previous_valid(self, contract_id: UUID, date_before) -> Optional[NationalContractVersion]:
        query = select(NationalContractVersion).where(
            and_(
                NationalContractVersion.national_contract_id == contract_id,
                NationalContractVersion.valid_to == None,
                NationalContractVersion.valid_from < date_before
            )
        ).order_by(NationalContractVersion.valid_from.desc()).limit(1)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> NationalContractVersion:
        version = NationalContractVersion(**kwargs)
        self._session.add(version)
        await self._session.flush()
        return version

    async def update(self, id: UUID, **kwargs: Any) -> Optional[NationalContractVersion]:
        version = await self.get(id)
        if not version:
            return None
        for key, value in kwargs.items():
            if hasattr(version, key):
                setattr(version, key, value)
        await self._session.flush()
        return version

    async def delete(self, id: UUID) -> bool:
        version = await self.get(id)
        if not version:
            return False
        await self._session.delete(version)
        await self._session.flush()
        return True


class NationalContractLevelRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[NationalContractLevel]:
        result = await self._session.execute(
            select(NationalContractLevel).where(NationalContractLevel.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> NationalContractLevel:
        level = NationalContractLevel(**kwargs)
        self._session.add(level)
        await self._session.flush()
        return level

    async def update(self, id: UUID, **kwargs: Any) -> Optional[NationalContractLevel]:
        level = await self.get(id)
        if not level:
            return None
        for key, value in kwargs.items():
            if hasattr(level, key):
                setattr(level, key, value)
        await self._session.flush()
        return level

    async def delete(self, id: UUID) -> bool:
        level = await self.get(id)
        if not level:
            return False
        await self._session.delete(level)
        await self._session.flush()
        return True


class NationalContractTypeConfigRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[NationalContractTypeConfig]:
        stmt = select(NationalContractTypeConfig).options(
            selectinload(NationalContractTypeConfig.contract_type)
        ).where(NationalContractTypeConfig.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> NationalContractTypeConfig:
        config = NationalContractTypeConfig(**kwargs)
        self._session.add(config)
        await self._session.flush()
        return config
    
    async def update(self, id: UUID, **kwargs: Any) -> Optional[NationalContractTypeConfig]:
        config = await self.get(id)
        if not config:
            return None
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        await self._session.flush()
        return config

    async def delete(self, id: UUID) -> bool:
        config = await self.get(id)
        if not config:
            return False
        await self._session.delete(config)
        await self._session.flush()
        return True
        

class CalculationModeRepository(BaseRepository):
    async def get(self, id: UUID) -> Optional[CalculationMode]:
        result = await self._session.execute(
            select(CalculationMode).where(CalculationMode.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[CalculationMode]:
        result = await self._session.execute(
            select(CalculationMode).where(CalculationMode.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[CalculationMode]:
        result = await self._session.execute(
            select(CalculationMode).where(CalculationMode.is_active == True)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs: Any) -> CalculationMode:
        mode = CalculationMode(**kwargs)
        self._session.add(mode)
        await self._session.flush()
        return mode
        
    async def update(self, id: UUID, **kwargs: Any) -> Optional[CalculationMode]:
        mode = await self.get(id)
        if not mode:
            return None
        for key, value in kwargs.items():
            if hasattr(mode, key):
                setattr(mode, key, value)
        await self._session.flush()
        return mode


class ContractTypeRepository(BaseRepository):
    async def get_all(self, active_only: bool = True) -> List[ContractType]:
        query = select(ContractType)
        if active_only:
            query = query.where(ContractType.is_active == True)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get(self, id: UUID) -> Optional[ContractType]:
         result = await self._session.execute(select(ContractType).where(ContractType.id == id))
         return result.scalar_one_or_none()
