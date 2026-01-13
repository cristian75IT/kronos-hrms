"""KRONOS Auth - RBAC Repository."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import Role, Permission, RolePermission


class RoleRepository:
    """Repository for RBAC Roles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Role]:
        """Get all roles with permissions."""
        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.name)
        )
        return list(result.scalars().all())

    async def get(self, id: UUID) -> Optional[Role]:
        """Get role by ID."""
        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        result = await self._session.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def get_permissions_for_roles(self, role_names: list[str]) -> list[str]:
        """Get all permission codes for roles and their ancestors."""
        if not role_names:
            return []
            
        # Recursive CTE to find all role IDs in the hierarchy
        initial_roles = (
            select(Role.id, Role.parent_id)
            .where(Role.name.in_(role_names))
            .cte(name="role_hierarchy", recursive=True)
        )
        
        parent_roles = (
            select(Role.id, Role.parent_id)
            .join(initial_roles, Role.id == initial_roles.c.parent_id)
        )
        
        role_hierarchy = initial_roles.union_all(parent_roles)
        
        # Join with permissions and include scope
        stmt = (
            select(
                func.concat(Permission.code, ':', RolePermission.scope)
            )
            .distinct()
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(role_hierarchy, RolePermission.role_id == role_hierarchy.c.id)
        )
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        """Update permissions for a role."""
        # Clear existing
        await self._session.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        # Add new
        if permission_ids:
            values = [{"role_id": role_id, "permission_id": pid} for pid in permission_ids]
            await self._session.execute(insert(RolePermission), values)
        
        await self._session.flush()


class PermissionRepository:
    """Repository for RBAC Permissions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Permission]:
        """Get all permissions."""
        result = await self._session.execute(
            select(Permission).order_by(Permission.resource, Permission.action)
        )
        return list(result.scalars().all())
