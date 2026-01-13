"""KRONOS Auth - User Repository."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import User, Role
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
                selectinload(User.profile),
            )
            .where(User.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Get user by Keycloak ID with eagerly loaded relationships."""
        result = await self._session.execute(
            select(User)
            .options(
                selectinload(User.contract_type),
                selectinload(User.work_schedule),
                selectinload(User.location),
                selectinload(User.manager),
                selectinload(User.areas),
                selectinload(User.profile),
            )
            .where(User.keycloak_id == keycloak_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self._session.execute(
            select(User).where(User.username == username)
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

    async def get_by_role_id(self, role_id: UUID) -> list[User]:
        """Get users by role ID."""
        # 1. Get role name
        role_result = await self._session.execute(
            select(Role.name).where(Role.id == role_id)
        )
        role_name = role_result.scalar_one_or_none()
        
        if not role_name:
            return []
            
        # 2. Get users with this role name from user_roles table
        # Using text() here because user_roles is a join table potentially not mapped fully or logic is specific
        stmt = select(User).from_statement(
            text("""
                SELECT users.*
                FROM auth.users users
                JOIN auth.user_roles ur ON users.id = ur.user_id
                WHERE ur.role_name = :role_name
            """)
        ).params(role_name=role_name)
        
        result = await self._session.execute(stmt)
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
