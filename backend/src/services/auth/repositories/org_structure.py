"""KRONOS Auth - Organization Structure Repository."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import (
    ExecutiveLevel,
    Department,
    OrganizationalService,
)


class ExecutiveLevelRepository:
    """Repository for executive levels."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[ExecutiveLevel]:
        """Get executive level by ID."""
        result = await self._session.execute(
            select(ExecutiveLevel)
            .where(ExecutiveLevel.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ExecutiveLevel]:
        """Get executive level by code."""
        result = await self._session.execute(
            select(ExecutiveLevel).where(ExecutiveLevel.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[ExecutiveLevel]:
        """Get all executive levels."""
        query = select(ExecutiveLevel).order_by(ExecutiveLevel.hierarchy_level, ExecutiveLevel.title)
        
        if active_only:
            query = query.where(ExecutiveLevel.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ExecutiveLevel:
        """Create new executive level."""
        level = ExecutiveLevel(**kwargs)
        self._session.add(level)
        await self._session.flush()
        return level

    async def update(self, id: UUID, **kwargs: Any) -> Optional[ExecutiveLevel]:
        """Update executive level."""
        level = await self.get(id)
        if not level:
            return None
        
        for field, value in kwargs.items():
            if hasattr(level, field) and value is not None:
                setattr(level, field, value)
        
        await self._session.flush()
        return level


class DepartmentRepository:
    """Repository for departments."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Department]:
        """Get department by ID."""
        result = await self._session.execute(
            select(Department)
            .options(
                selectinload(Department.manager),
                selectinload(Department.deputy_manager),
                selectinload(Department.parent),
                selectinload(Department.children),
                selectinload(Department.services),
            )
            .where(Department.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Department]:
        """Get department by code."""
        result = await self._session.execute(
            select(Department)
            .options(
                selectinload(Department.manager),
                selectinload(Department.deputy_manager),
            )
            .where(Department.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[Department]:
        """Get all departments."""
        query = select(Department).order_by(Department.name)
        
        if active_only:
            query = query.where(Department.is_active == True)
        
        # Eager load manager for list view
        query = query.options(
            selectinload(Department.manager),
            selectinload(Department.deputy_manager),
        )
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def get_tree(self, active_only: bool = True) -> list[Department]:
        """Get root departments with children loaded."""
        query = select(Department).where(Department.parent_id == None).order_by(Department.name)
        
        if active_only:
            query = query.where(Department.is_active == True)
            
        # We assume recursive loading is handled by strategy or manual recursion in app logic if needed
        # Or simplistic eager load of children
        query = query.options(
            selectinload(Department.children)
            .selectinload(Department.children), # Level 2
            selectinload(Department.manager)
        )
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Department:
        """Create new department."""
        department = Department(**kwargs)
        self._session.add(department)
        await self._session.flush()
        return department

    async def update(self, id: UUID, **kwargs: Any) -> Optional[Department]:
        """Update department."""
        department = await self.get(id)
        if not department:
            return None
        
        for field, value in kwargs.items():
            if hasattr(department, field) and value is not None:
                setattr(department, field, value)
        
        await self._session.flush()
        return department


class OrganizationalServiceRepository:
    """Repository for organizational services."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[OrganizationalService]:
        """Get service by ID."""
        result = await self._session.execute(
            select(OrganizationalService)
            .options(
                selectinload(OrganizationalService.coordinator),
                selectinload(OrganizationalService.deputy_coordinator),
                selectinload(OrganizationalService.department),
            )
            .where(OrganizationalService.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_department(self, department_id: UUID) -> list[OrganizationalService]:
        """Get services by department."""
        result = await self._session.execute(
            select(OrganizationalService)
            .options(
                selectinload(OrganizationalService.coordinator),
            )
            .where(OrganizationalService.department_id == department_id)
            .order_by(OrganizationalService.name)
        )
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Optional[OrganizationalService]:
        """Get service by code."""
        result = await self._session.execute(
            select(OrganizationalService).where(OrganizationalService.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[OrganizationalService]:
        """Get all services."""
        query = select(OrganizationalService).order_by(OrganizationalService.name)
        
        if active_only:
            query = query.where(OrganizationalService.is_active == True)
            
        query = query.options(
            selectinload(OrganizationalService.department),
            selectinload(OrganizationalService.coordinator),
        )
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> OrganizationalService:
        """Create new service."""
        service = OrganizationalService(**kwargs)
        self._session.add(service)
        await self._session.flush()
        return service

    async def update(self, id: UUID, **kwargs: Any) -> Optional[OrganizationalService]:
        """Update service."""
        service = await self.get(id)
        if not service:
            return None
        
        for field, value in kwargs.items():
            if hasattr(service, field) and value is not None:
                setattr(service, field, value)
        
        await self._session.flush()
        return service
