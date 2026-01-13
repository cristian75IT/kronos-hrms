"""KRONOS Auth - Contracts and Schedules Repository."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import (
    ContractType,
    WorkSchedule,
    EmployeeContract,
)


class ContractTypeRepository:
    """Repository for contract types."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[ContractType]:
        """Get contract type by ID."""
        result = await self._session.execute(
            select(ContractType).where(ContractType.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[ContractType]:
        """Get all contract types."""
        query = select(ContractType).order_by(ContractType.name)
        
        if active_only:
            query = query.where(ContractType.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ContractType:
        """Create new contract type."""
        contract = ContractType(**kwargs)
        self._session.add(contract)
        await self._session.flush()
        return contract


class WorkScheduleRepository:
    """Repository for work schedules."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[WorkSchedule]:
        """Get work schedule by ID."""
        result = await self._session.execute(
            select(WorkSchedule).where(WorkSchedule.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[WorkSchedule]:
        """Get all work schedules."""
        query = select(WorkSchedule).order_by(WorkSchedule.name)
        
        if active_only:
            query = query.where(WorkSchedule.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> WorkSchedule:
        """Create new work schedule."""
        schedule = WorkSchedule(**kwargs)
        self._session.add(schedule)
        await self._session.flush()
        return schedule


class EmployeeContractRepository:
    """Repository for employee contracts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: UUID) -> list[EmployeeContract]:
        """Get all contracts for a user."""
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.user_id == user_id)
            .order_by(EmployeeContract.start_date.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> EmployeeContract:
        """Create new contract."""
        contract = EmployeeContract(**kwargs)
        self._session.add(contract)
        await self._session.flush()
        
        # Reload with relationships to avoid MissingGreenlet error in Pydantic serialization
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.id == contract.id)
        )
        result = await self._session.execute(query)
        return result.scalar_one()
