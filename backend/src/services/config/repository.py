"""KRONOS Config Service - Repository Layer."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.config.models import (
    SystemConfig,
    LeaveType,
    Holiday,
    CompanyClosure,
    ExpenseType,
    DailyAllowanceRule,
    PolicyRule,
)


class SystemConfigRepository:
    """Repository for system configuration."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key(self, key: str) -> Optional[SystemConfig]:
        """Get config by key."""
        result = await self._session.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> list[SystemConfig]:
        """Get all configs in a category."""
        result = await self._session.execute(
            select(SystemConfig)
            .where(SystemConfig.category == category)
            .order_by(SystemConfig.key)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[SystemConfig]:
        """Get all configs."""
        result = await self._session.execute(
            select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> SystemConfig:
        """Create new config."""
        config = SystemConfig(**kwargs)
        self._session.add(config)
        await self._session.flush()
        return config

    async def update(self, key: str, **kwargs: Any) -> Optional[SystemConfig]:
        """Update config by key."""
        config = await self.get_by_key(key)
        if not config:
            return None
        
        for field, value in kwargs.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        await self._session.flush()
        return config

    async def delete(self, key: str) -> bool:
        """Delete config by key."""
        config = await self.get_by_key(key)
        if not config:
            return False
        
        await self._session.delete(config)
        await self._session.flush()
        return True


class LeaveTypeRepository:
    """Repository for leave types."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[LeaveType]:
        """Get leave type by ID."""
        result = await self._session.execute(
            select(LeaveType).where(LeaveType.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[LeaveType]:
        """Get leave type by code."""
        result = await self._session.execute(
            select(LeaveType).where(LeaveType.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[LeaveType]:
        """Get all leave types."""
        query = select(LeaveType).order_by(LeaveType.sort_order, LeaveType.name)
        
        if active_only:
            query = query.where(LeaveType.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> LeaveType:
        """Create new leave type."""
        leave_type = LeaveType(**kwargs)
        self._session.add(leave_type)
        await self._session.flush()
        return leave_type

    async def update(self, id: UUID, **kwargs: Any) -> Optional[LeaveType]:
        """Update leave type."""
        leave_type = await self.get(id)
        if not leave_type:
            return None
        
        for field, value in kwargs.items():
            if hasattr(leave_type, field) and value is not None:
                setattr(leave_type, field, value)
        
        await self._session.flush()
        return leave_type

    async def deactivate(self, id: UUID) -> bool:
        """Deactivate leave type (soft delete)."""
        leave_type = await self.get(id)
        if not leave_type:
            return False
        
        leave_type.is_active = False
        await self._session.flush()
        return True


class HolidayRepository:
    """Repository for holidays."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Holiday]:
        """Get holiday by ID."""
        result = await self._session.execute(
            select(Holiday).where(Holiday.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_year(
        self,
        year: int,
        location_id: Optional[UUID] = None,
    ) -> list[Holiday]:
        """Get holidays for a year."""
        query = select(Holiday).where(Holiday.year == year)
        
        if location_id:
            # Get national + location-specific
            query = query.where(
                (Holiday.location_id == None) | (Holiday.location_id == location_id)
            )
        
        query = query.order_by(Holiday.date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_date(self, date) -> Optional[Holiday]:
        """Get holiday by date."""
        result = await self._session.execute(
            select(Holiday).where(Holiday.date == date)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> Holiday:
        """Create new holiday."""
        # Extract year from date
        if "year" not in kwargs and "date" in kwargs:
            kwargs["year"] = kwargs["date"].year
        
        holiday = Holiday(**kwargs)
        self._session.add(holiday)
        await self._session.flush()
        return holiday

    async def delete(self, id: UUID) -> bool:
        """Delete holiday."""
        holiday = await self.get(id)
        if not holiday:
            return False
        
        await self._session.delete(holiday)
        await self._session.flush()
        return True

    async def delete_by_year(self, year: int) -> int:
        """Delete all holidays for a year. Returns count deleted."""
        result = await self._session.execute(
            select(Holiday).where(Holiday.year == year)
        )
        holidays = result.scalars().all()
        count = len(holidays)
        
        for holiday in holidays:
            await self._session.delete(holiday)
        
        await self._session.flush()
        return count

    async def delete_national_by_year(self, year: int) -> int:
        """Delete only national holidays for a year."""
        result = await self._session.execute(
            select(Holiday).where(Holiday.year == year, Holiday.is_national == True)
        )
        holidays = result.scalars().all()
        count = len(holidays)
        
        for holiday in holidays:
            await self._session.delete(holiday)
        
        await self._session.flush()
        return count


class CompanyClosureRepository:
    """Repository for company closures."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[CompanyClosure]:
        """Get closure by ID."""
        result = await self._session.execute(
            select(CompanyClosure).where(CompanyClosure.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_year(
        self,
        year: int,
        include_inactive: bool = False,
    ) -> list[CompanyClosure]:
        """Get all closures for a year."""
        query = select(CompanyClosure).where(CompanyClosure.year == year)
        
        if not include_inactive:
            query = query.where(CompanyClosure.is_active == True)
        
        query = query.order_by(CompanyClosure.start_date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date,
        end_date,
        include_inactive: bool = False,
    ) -> list[CompanyClosure]:
        """Get closures that overlap with a date range."""
        query = select(CompanyClosure).where(
            CompanyClosure.start_date <= end_date,
            CompanyClosure.end_date >= start_date,
        )
        
        if not include_inactive:
            query = query.where(CompanyClosure.is_active == True)
        
        query = query.order_by(CompanyClosure.start_date)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> CompanyClosure:
        """Create company closure."""
        # Auto-set year from start_date
        if "year" not in kwargs and "start_date" in kwargs:
            kwargs["year"] = kwargs["start_date"].year
        
        closure = CompanyClosure(**kwargs)
        self._session.add(closure)
        await self._session.flush()
        return closure

    async def update(self, id: UUID, **kwargs: Any) -> Optional[CompanyClosure]:
        """Update company closure."""
        closure = await self.get(id)
        if not closure:
            return None
        
        for key, value in kwargs.items():
            if hasattr(closure, key) and value is not None:
                setattr(closure, key, value)
        
        await self._session.flush()
        return closure

    async def delete(self, id: UUID) -> bool:
        """Delete company closure."""
        closure = await self.get(id)
        if not closure:
            return False
        
        await self._session.delete(closure)
        await self._session.flush()
        return True


class ExpenseTypeRepository:
    """Repository for expense types."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[ExpenseType]:
        """Get expense type by ID."""
        result = await self._session.execute(
            select(ExpenseType).where(ExpenseType.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ExpenseType]:
        """Get expense type by code."""
        result = await self._session.execute(
            select(ExpenseType).where(ExpenseType.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[ExpenseType]:
        """Get all expense types."""
        query = select(ExpenseType).order_by(ExpenseType.category, ExpenseType.name)
        
        if active_only:
            query = query.where(ExpenseType.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ExpenseType:
        """Create new expense type."""
        expense_type = ExpenseType(**kwargs)
        self._session.add(expense_type)
        await self._session.flush()
        return expense_type


class DailyAllowanceRuleRepository:
    """Repository for daily allowance rules."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_destination_type(
        self,
        destination_type: str,
    ) -> Optional[DailyAllowanceRule]:
        """Get rule by destination type."""
        result = await self._session.execute(
            select(DailyAllowanceRule)
            .where(DailyAllowanceRule.destination_type == destination_type)
            .where(DailyAllowanceRule.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[DailyAllowanceRule]:
        """Get all rules."""
        query = select(DailyAllowanceRule).order_by(DailyAllowanceRule.name)
        
        if active_only:
            query = query.where(DailyAllowanceRule.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> DailyAllowanceRule:
        """Create new rule."""
        rule = DailyAllowanceRule(**kwargs)
        self._session.add(rule)
        await self._session.flush()
        return rule
