"""KRONOS Auth Service - Repository Layer."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, or_, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import (
    User,
    Area,
    Location,
    ContractType,
    WorkSchedule,
    EmployeeContract,
    UserProfile,
    EmployeeTraining,
    Role,
    Permission,
    RolePermission,
    Department,
    OrganizationalService,
    ExecutiveLevel,
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


class EmployeeTrainingRepository:
    """Repository for employee training records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[EmployeeTraining]:
        """Get training record by ID."""
        result = await self._session.execute(
            select(EmployeeTraining).where(EmployeeTraining.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[EmployeeTraining]:
        """Get all training records for a user."""
        result = await self._session.execute(
            select(EmployeeTraining)
            .where(EmployeeTraining.user_id == user_id)
            .order_by(EmployeeTraining.issue_date.desc())
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> EmployeeTraining:
        """Create new training record."""
        training = EmployeeTraining(**kwargs)
        self._session.add(training)
        await self._session.flush()
        return training

    async def update(self, id: UUID, **kwargs: Any) -> Optional[EmployeeTraining]:
        """Update training record."""
        training = await self.get(id)
        if not training:
            return None
        
        for field, value in kwargs.items():
            if hasattr(training, field) and value is not None:
                setattr(training, field, value)
        
        await self._session.flush()
        return training

    async def delete(self, id: UUID) -> bool:
        """Delete training record."""
        training = await self.get(id)
        if not training:
            return False
        
        await self._session.delete(training)
        await self._session.flush()
        await self._session.delete(training)
        await self._session.flush()
        return True


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
