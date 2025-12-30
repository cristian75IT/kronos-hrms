"""KRONOS Auth Service - Repository Layer."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import (
    User,
    Area,
    Location,
    ContractType,
    WorkSchedule,
)
from src.shared.schemas import DataTableRequest


class UserRepository:
    """Repository for users."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self._session.execute(
            select(User)
            .options(
                selectinload(User.contract_type),
                selectinload(User.work_schedule),
                selectinload(User.location),
                selectinload(User.manager),
                selectinload(User.areas),
            )
            .where(User.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Get user by Keycloak ID."""
        result = await self._session.execute(
            select(User).where(User.keycloak_id == keycloak_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Get all users."""
        query = select(User).order_by(User.last_name, User.first_name)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_datatable(
        self,
        request: DataTableRequest,
        active_only: bool = True,
    ) -> tuple[list[User], int, int]:
        """Get users for DataTable with server-side processing."""
        # Base query
        query = select(User)
        count_query = select(func.count(User.id))
        
        if active_only:
            query = query.where(User.is_active == True)
            count_query = count_query.where(User.is_active == True)
        
        # Total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply search filter
        if request.search_value:
            search = f"%{request.search_value}%"
            query = query.where(
                or_(
                    User.email.ilike(search),
                    User.first_name.ilike(search),
                    User.last_name.ilike(search),
                    User.badge_number.ilike(search),
                )
            )
            filtered_count = await self._session.execute(
                select(func.count(User.id)).where(
                    or_(
                        User.email.ilike(search),
                        User.first_name.ilike(search),
                        User.last_name.ilike(search),
                        User.badge_number.ilike(search),
                    )
                ).where(User.is_active == True if active_only else True)
            )
            filtered = filtered_count.scalar() or 0
        else:
            filtered = total
        
        # Apply ordering
        order_by = request.get_order_by()
        for col_name, direction in order_by:
            if hasattr(User, col_name):
                col = getattr(User, col_name)
                query = query.order_by(col.desc() if direction == "desc" else col.asc())
        
        # Default order
        if not order_by:
            query = query.order_by(User.last_name, User.first_name)
        
        # Pagination
        query = query.offset(request.start).limit(request.length)
        
        result = await self._session.execute(query)
        return list(result.scalars().all()), total, filtered

    async def get_subordinates(self, manager_id: UUID) -> list[User]:
        """Get direct reports of a manager."""
        result = await self._session.execute(
            select(User)
            .where(User.manager_id == manager_id)
            .where(User.is_active == True)
            .order_by(User.last_name, User.first_name)
        )
        return list(result.scalars().all())

    async def get_approvers(self) -> list[User]:
        """Get all users with approver capability."""
        result = await self._session.execute(
            select(User)
            .where(User.is_approver == True)
            .where(User.is_active == True)
            .order_by(User.last_name, User.first_name)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> User:
        """Create new user."""
        user = User(**kwargs)
        self._session.add(user)
        await self._session.flush()
        return user

    async def update(self, id: UUID, **kwargs: Any) -> Optional[User]:
        """Update user."""
        user = await self.get(id)
        if not user:
            return None
        
        for field, value in kwargs.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        await self._session.flush()
        return user

    async def deactivate(self, id: UUID) -> bool:
        """Deactivate user."""
        user = await self.get(id)
        if not user:
            return False
        
        user.is_active = False
        await self._session.flush()
        return True


class AreaRepository:
    """Repository for areas."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Area]:
        """Get area by ID."""
        result = await self._session.execute(
            select(Area)
            .options(selectinload(Area.users))
            .where(Area.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Area]:
        """Get area by code."""
        result = await self._session.execute(
            select(Area).where(Area.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[Area]:
        """Get all areas."""
        query = select(Area).order_by(Area.name)
        
        if active_only:
            query = query.where(Area.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Area:
        """Create new area."""
        area = Area(**kwargs)
        self._session.add(area)
        await self._session.flush()
        return area

    async def update(self, id: UUID, **kwargs: Any) -> Optional[Area]:
        """Update area."""
        area = await self.get(id)
        if not area:
            return None
        
        for field, value in kwargs.items():
            if hasattr(area, field) and value is not None:
                setattr(area, field, value)
        
        await self._session.flush()
        return area


class LocationRepository:
    """Repository for locations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Location]:
        """Get location by ID."""
        result = await self._session.execute(
            select(Location).where(Location.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Location]:
        """Get location by code."""
        result = await self._session.execute(
            select(Location).where(Location.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[Location]:
        """Get all locations."""
        query = select(Location).order_by(Location.name)
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Location:
        """Create new location."""
        location = Location(**kwargs)
        self._session.add(location)
        await self._session.flush()
        return location


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
