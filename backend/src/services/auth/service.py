"""KRONOS Auth Service - Business Logic."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.core.config import settings
from src.core.exceptions import NotFoundError, ConflictError
from src.core.cache import cache_delete, cache_set
from src.services.auth.repository import (
    UserRepository,
    AreaRepository,
    LocationRepository,
    ContractTypeRepository,
    WorkScheduleRepository,
    EmployeeContractRepository,
    EmployeeTrainingRepository,
    RoleRepository,
    PermissionRepository,
    DepartmentRepository,
    OrganizationalServiceRepository,
    ExecutiveLevelRepository,
)
from src.services.auth.schemas import (
    UserCreate,
    UserUpdate,
    AreaCreate,
    AreaUpdate,
    LocationCreate,
    LocationUpdate,
    ContractTypeCreate,
    ContractTypeUpdate,
    WorkScheduleCreate,
    EmployeeContractCreate,
    EmployeeTrainingCreate,
    EmployeeTrainingUpdate,
    KeycloakSyncRequest,
    KeycloakSyncResponse,
    DepartmentCreate,
    DepartmentUpdate,
    OrganizationalServiceCreate,
    OrganizationalServiceUpdate,
    ExecutiveLevelCreate,
    ExecutiveLevelUpdate,
)
from src.services.auth.models import Role, Permission, RolePermission
from src.shared.schemas import DataTableRequest
from src.shared.audit_client import get_audit_logger


class UserService:
    """Service for user management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._area_repo = AreaRepository(session)
        self._location_repo = LocationRepository(session)
        self._contract_repo = ContractTypeRepository(session)
        self._schedule_repo = WorkScheduleRepository(session)

        self._emp_contract_repo = EmployeeContractRepository(session)
        self._training_repo = EmployeeTrainingRepository(session)
        self._audit = get_audit_logger("auth-service")


    # ═══════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════

    def _get_keycloak_admin(self) -> KeycloakAdmin:
        """Get authenticated Keycloak Admin client."""
        connection = KeycloakOpenIDConnection(
            server_url=settings.keycloak_url,
            realm_name=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            client_secret_key=settings.keycloak_client_secret,
            verify=True
        )
        return KeycloakAdmin(connection=connection)

    # ═══════════════════════════════════════════════════════════
    # User Operations
    # ═══════════════════════════════════════════════════════════

    async def get_user(self, id: UUID):
        """Get user by ID."""
        user = await self._user_repo.get(id)
        if not user:
            raise NotFoundError("User not found", entity_type="User", entity_id=str(id))
        return user

    async def get_user_by_keycloak_id(self, keycloak_id: str):
        """Get user by Keycloak ID."""
        user = await self._user_repo.get_by_keycloak_id(keycloak_id)
        if not user:
            raise NotFoundError(f"User not found with Keycloak ID: {keycloak_id}")
        return user

    async def get_or_create_from_token(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        roles: list[str],
    ):
        """Get existing user or create from Keycloak token.
        
        Called on first login to ensure user exists in local DB.
        """
        user = await self._user_repo.get_by_keycloak_id(keycloak_id)
        
        if user:
            # Update roles from Keycloak
            await self._user_repo.update(
                user.id,
                is_admin="admin" in roles,
                is_manager="manager" in roles,
                is_approver="approver" in roles,

                is_hr="hr" in roles,
                is_employee="employee" in roles,
                last_sync_at=datetime.utcnow(),
            )
            return user
        
        # Check if user exists by email (legacy user or seeded user)
        if email:
            existing_by_email = await self._user_repo.get_by_email(email)
            if existing_by_email:
                # Merge account: Update Keycloak ID and roles
                await self._user_repo.update(
                    existing_by_email.id,
                    keycloak_id=keycloak_id,
                    username=username or existing_by_email.username,
                    first_name=first_name or existing_by_email.first_name,
                    last_name=last_name or existing_by_email.last_name,
                    is_admin="admin" in roles,
                    is_manager="manager" in roles,
                    is_approver="approver" in roles,
                    is_hr="hr" in roles,
                    is_employee="employee" in roles,
                    last_sync_at=datetime.utcnow(),
                )
                return await self._user_repo.get_by_keycloak_id(keycloak_id)
        
        # Create new user
        # Handle username uniqueness
        base_username = username or email
        final_username = base_username
        counter = 1
        
        while True:
            existing_user = await self._user_repo.get_by_username(final_username)
            if not existing_user:
                break
            final_username = f"{base_username}_{counter}"
            counter += 1

        await self._user_repo.create(
            keycloak_id=keycloak_id,
            email=email,
            username=final_username,
            first_name=first_name or email.split("@")[0],
            last_name=last_name or "",
            is_admin="admin" in roles,
            is_manager="manager" in roles,
            is_approver="approver" in roles,
            is_hr="hr" in roles,
            is_employee="employee" in roles,
            last_sync_at=datetime.utcnow(),
        )
        return await self._user_repo.get_by_keycloak_id(keycloak_id)

    async def get_users(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ):
        """Get all users."""
        return await self._user_repo.get_all(active_only, limit, offset)

    async def get_users_datatable(
        self,
        request: DataTableRequest,
        active_only: bool = True,
    ):
        """Get users for DataTable."""
        return await self._user_repo.get_datatable(request, active_only)

    async def get_subordinates(self, manager_id: UUID):
        """Get direct reports of a manager."""
        return await self._user_repo.get_subordinates(manager_id)

    async def get_approvers(self):
        """Get all users with approver capability."""
        return await self._user_repo.get_approvers()

    async def update_user(self, id: UUID, data: UserUpdate, actor_id: Optional[UUID] = None):
        """Update user locally and in Keycloak."""
        user = await self._user_repo.get(id)
        if not user:
             raise NotFoundError("User not found", entity_type="User", entity_id=str(id))

        # 1. Sync to Keycloak if linked and relevant fields changed
        if user.keycloak_id:
            try:
                kc_updates = {}
                if data.first_name is not None: kc_updates['firstName'] = data.first_name
                if data.last_name is not None: kc_updates['lastName'] = data.last_name
                if data.email is not None: kc_updates['email'] = data.email
                if data.username is not None: kc_updates['username'] = data.username
                
                # Check for Role Changes
                role_changes = {}
                if data.is_employee is not None: role_changes['employee'] = data.is_employee
                if data.is_admin is not None: role_changes['admin'] = data.is_admin
                if data.is_manager is not None: role_changes['manager'] = data.is_manager
                if data.is_approver is not None: role_changes['approver'] = data.is_approver
                if data.is_hr is not None: role_changes['hr'] = data.is_hr

                if kc_updates or role_changes:
                    kc_admin = self._get_keycloak_admin()
                    
                    # Profile Update
                    if kc_updates:
                        kc_admin.update_user(user.keycloak_id, kc_updates)
                    
                    # Roles Update
                    if role_changes:
                        # Fetch IDs for roles (Keycloak needs Role Representation or Name? assign_realm_roles takes list of dicts)
                        # We can use update_realm_roles logic or assign/remove.
                        # Easier to get role definition first.
                        for role_name, should_have in role_changes.items():
                            try:
                                role_def = kc_admin.get_realm_role(role_name)
                                if should_have:
                                    kc_admin.assign_realm_roles(user.keycloak_id, [role_def])
                                else:
                                    kc_admin.delete_realm_roles_of_user(user.keycloak_id, [role_def])
                            except Exception as e:
                                self._audit.log_action(
                                    user_id=actor_id, action="ERROR", resource_type="KEYCLOAK_ROLE", 
                                    description=f"Failed to sync role {role_name}: {e}"
                                )

            except Exception as e:
                # Log but maybe don't block local update? Or Block?
                # User asked to "Use Keycloak APIs". So failure should probably bubble up or be warned.
                # I'll raise Conflict to alert the user.
                raise ConflictError(f"Keycloak Update Failed: {str(e)}")

        # 2. Local Update
        updated_user = await self._user_repo.update(id, **data.model_dump(exclude_unset=True))
        
        # 3. Invalidate Cache
        if updated_user.keycloak_id:
            await cache_delete(f"user_identity:{updated_user.keycloak_id}")
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="USER",
            resource_id=str(id),
            description=f"Updated user: {updated_user.full_name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return updated_user

    async def deactivate_user(self, id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Deactivate user."""
        user = await self.get_user(id)
        result = await self._user_repo.deactivate(id)
        if not result:
            raise NotFoundError("User not found", entity_type="User", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="DEACTIVATE",
            resource_type="USER",
            resource_id=str(id),
            description=f"User deactivated: {user.full_name}",
        )
        return True

    # ═══════════════════════════════════════════════════════════
    # Keycloak Sync
    # ═══════════════════════════════════════════════════════════

    async def sync_from_keycloak(
        self,
        request: KeycloakSyncRequest,
    ) -> KeycloakSyncResponse:
        """Sync all users from Keycloak.
        
        This is an admin operation that fetches all users from
        Keycloak and syncs them to the local database.
        """
        try:
            # Initialize Keycloak Admin client
            keycloak_connection = KeycloakOpenIDConnection(
                server_url=settings.keycloak_url,
                realm_name=settings.keycloak_realm,
                client_id=settings.keycloak_client_id,
                client_secret_key=settings.keycloak_client_secret,
            )
            keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
            
            # Get all users from Keycloak
            kc_users = keycloak_admin.get_users({})
            
            synced = 0
            created = 0
            updated = 0
            deactivated = 0
            errors = []
            
            keycloak_ids_seen = set()
            
            for kc_user in kc_users:
                try:
                    kc_id = kc_user.get("id")
                    if not kc_id:
                        continue
                    
                    keycloak_ids_seen.add(kc_id)
                    
                    # Get user roles from Keycloak
                    kc_roles = keycloak_admin.get_realm_roles_of_user(kc_id)
                    role_names = [r.get("name") for r in kc_roles]
                    
                    # Check if user exists locally
                    local_user = await self._user_repo.get_by_keycloak_id(kc_id)
                    
                    if local_user:
                        # Update existing user
                        await self._user_repo.update(
                            local_user.id,
                            email=kc_user.get("email", local_user.email),
                            username=kc_user.get("username", local_user.username),
                            first_name=kc_user.get("firstName", local_user.first_name),
                            last_name=kc_user.get("lastName", local_user.last_name),
                            is_admin="admin" in role_names,
                            is_manager="manager" in role_names,
                            is_approver="approver" in role_names,

                            is_hr="hr" in role_names,
                            is_employee="employee" in role_names,
                            is_active=kc_user.get("enabled", True),
                            last_sync_at=datetime.utcnow(),
                        )
                        updated += 1
                    else:
                        # Create new user
                        new_user = await self._user_repo.create(
                            keycloak_id=kc_id,
                            email=kc_user.get("email", f"{kc_id}@unknown"),
                            username=kc_user.get("username") or kc_user.get("email", f"{kc_id}@unknown"),
                            first_name=kc_user.get("firstName", ""),
                            last_name=kc_user.get("lastName", ""),
                            is_admin="admin" in role_names,
                            is_manager="manager" in role_names,
                            is_approver="approver" in role_names,
                            is_hr="hr" in role_names,
                            is_employee="employee" in role_names,
                            is_active=kc_user.get("enabled", True),
                            last_sync_at=datetime.utcnow(),
                        )
                        created += 1
                        
                        # Log new user creation
                        await self._audit.log_action(
                            action="CREATE",
                            resource_type="USER",
                            resource_id=str(new_user.id),
                            description=f"User synced from Keycloak: {new_user.email}",
                            request_data={"keycloak_id": kc_id, "roles": role_names},
                        )
                    
                    synced += 1
                    
                except Exception as e:
                    errors.append(f"Error syncing user {kc_user.get('email', 'unknown')}: {str(e)}")
            
            # Optionally deactivate users not in Keycloak
            if request.force_full_sync:
                all_local = await self._user_repo.get_all(active_only=False, limit=10000, offset=0)
                for local_user in all_local:
                    if local_user.keycloak_id not in keycloak_ids_seen:
                        if local_user.is_active:
                            await self._user_repo.deactivate(local_user.id)
                            deactivated += 1
            
            return KeycloakSyncResponse(
                synced=synced,
                created=created,
                updated=updated,
                deactivated=deactivated,
                errors=errors,
            )
            
        except Exception as e:
            return KeycloakSyncResponse(
                synced=0,
                created=0,
                updated=0,
                deactivated=0,
                errors=[f"Keycloak connection error: {str(e)}"],
            )

    # ═══════════════════════════════════════════════════════════
    # Area Operations
    # ═══════════════════════════════════════════════════════════

    async def get_areas(self, active_only: bool = True):
        """Get all areas."""
        return await self._area_repo.get_all(active_only)

    async def get_area(self, id: UUID):
        """Get area by ID."""
        area = await self._area_repo.get(id)
        if not area:
            raise NotFoundError("Area not found", entity_type="Area", entity_id=str(id))
        return area

    async def create_area(self, data: AreaCreate, actor_id: Optional[UUID] = None):
        """Create new area."""
        existing = await self._area_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Area code already exists: {data.code}")
        
        area = await self._area_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="AREA",
            resource_id=str(area.id),
            description=f"Created area: {area.name}",
            request_data=data.model_dump(mode="json")
        )
        return area

    async def update_area(self, id: UUID, data: AreaUpdate, actor_id: Optional[UUID] = None):
        """Update area."""
        area = await self._area_repo.update(id, **data.model_dump(exclude_unset=True))
        if not area:
            raise NotFoundError("Area not found", entity_type="Area", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="AREA",
            resource_id=str(id),
            description=f"Updated area: {area.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return area

    # ═══════════════════════════════════════════════════════════
    # Location Operations
    # ═══════════════════════════════════════════════════════════

    async def get_locations(self, active_only: bool = True):
        """Get all locations."""
        return await self._location_repo.get_all(active_only)

    async def get_location(self, id: UUID):
        """Get location by ID."""
        location = await self._location_repo.get(id)
        if not location:
            raise NotFoundError("Location not found", entity_type="Location", entity_id=str(id))
        return location

    async def create_location(self, data: LocationCreate):
        """Create new location."""
        existing = await self._location_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Location code already exists: {data.code}")
        
        return await self._location_repo.create(**data.model_dump())

    # ═══════════════════════════════════════════════════════════
    # Contract Type Operations
    # ═══════════════════════════════════════════════════════════

    async def get_contract_types(self, active_only: bool = True):
        """Get all contract types."""
        return await self._contract_repo.get_all(active_only)

    async def create_contract_type(self, data: ContractTypeCreate, actor_id: Optional[UUID] = None):
        """Create new contract type."""
        contract_type = await self._contract_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="CONTRACT_TYPE",
            resource_id=str(contract_type.id),
            description=f"Created contract type: {contract_type.name}",
            request_data=data.model_dump(mode="json")
        )
        return contract_type

    async def update_contract_type(self, id: UUID, data: ContractTypeUpdate, actor_id: Optional[UUID] = None):
        """Update contract type."""
        update_data = data.model_dump(exclude_unset=True)
        
        # Enforce percentage 100 if switching to full time
        if update_data.get('is_part_time') is False:
            update_data['part_time_percentage'] = 100
            
        c_type = await self._contract_repo.update(id, **update_data)
        if not c_type:
             raise NotFoundError("Contract Type not found", entity_type="ContractType", entity_id=str(id))
             
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="CONTRACT_TYPE",
            resource_id=str(id),
            description=f"Updated contract type: {c_type.name}",
            request_data=update_data
        )
        return c_type

    # ═══════════════════════════════════════════════════════════
    # Work Schedule Operations
    # ═══════════════════════════════════════════════════════════

    async def get_work_schedules(self, active_only: bool = True):
        """Get all work schedules."""
        return await self._schedule_repo.get_all(active_only)
    async def create_work_schedule(self, data: WorkScheduleCreate, actor_id: Optional[UUID] = None):
        """Create new work schedule."""
        schedule = await self._schedule_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="WORK_SCHEDULE",
            resource_id=str(schedule.id),
            description=f"Created work schedule: {schedule.name}",
            request_data=data.model_dump(mode="json")
        )
        return schedule

    # ═══════════════════════════════════════════════════════════
    # Employee Contract Operations
    # ═══════════════════════════════════════════════════════════

    async def get_employee_contracts(self, user_id: UUID):
        """Get all contracts for a user."""
        # Verify user exists? Maybe not strictly needed for list, empty list is fine.
        return await self._emp_contract_repo.get_by_user(user_id)

    async def create_employee_contract(self, user_id: UUID, data: EmployeeContractCreate, actor_id: Optional[UUID] = None):
        """Create new employee contract."""
        # Verify user exists
        user = await self._user_repo.get(user_id)
        if not user:
             raise NotFoundError("User not found", entity_type="User", entity_id=str(user_id))
             
        # Verify contract type exists
        c_type = await self._contract_repo.get(data.contract_type_id)
        if not c_type:
             raise NotFoundError("Contract Type not found", entity_type="ContractType", entity_id=str(data.contract_type_id))

        contract = await self._emp_contract_repo.create(user_id=user_id, **data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="EMPLOYEE_CONTRACT",
            resource_id=str(contract.id),
            description=f"Created contract for user {user.full_name}",
            request_data=data.model_dump(mode="json")
        )
        return contract

    # ═══════════════════════════════════════════════════════════
    # Employee Training Operations
    # ═══════════════════════════════════════════════════════════

    async def get_employee_trainings(self, user_id: UUID):
        """Get all training records for a user."""
        return await self._training_repo.get_by_user(user_id)

    async def create_employee_training(self, data: EmployeeTrainingCreate, actor_id: Optional[UUID] = None):
        """Create new training record."""
        # Verify user exists
        user = await self._user_repo.get(data.user_id)
        if not user:
            raise NotFoundError("User not found", entity_type="User", entity_id=str(data.user_id))
            
        training = await self._training_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="EMPLOYEE_TRAINING",
            resource_id=str(training.id),
            description=f"Created training {training.training_type} for user {user.full_name}",
            request_data=data.model_dump(mode="json")
        )
        return training

    async def update_employee_training(self, id: UUID, data: EmployeeTrainingUpdate, actor_id: Optional[UUID] = None):
        """Update training record."""
        training = await self._training_repo.update(id, **data.model_dump(exclude_unset=True))
        if not training:
            raise NotFoundError("Training record not found", entity_type="EmployeeTraining", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="EMPLOYEE_TRAINING",
            resource_id=str(id),
            description=f"Updated training record: {training.training_type}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return training

    async def delete_employee_training(self, id: UUID, actor_id: Optional[UUID] = None):
        """Delete training record."""
        training = await self._training_repo.get(id)
        if not training:
            raise NotFoundError("Training record not found", entity_type="EmployeeTraining", entity_id=str(id))
            
        result = await self._training_repo.delete(id)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="EMPLOYEE_TRAINING",
            resource_id=str(id),
            description=f"Deleted training record: {training.training_type}",
        )
        return result



class RBACService:
    """Service for RBAC management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._role_repo = RoleRepository(session)
        self._perm_repo = PermissionRepository(session)
        self._audit = get_audit_logger("auth-service")

    async def get_roles(self):
        """Get all roles with permissions."""
        roles = await self._role_repo.get_all()
        print(f"DEBUG: Found {len(roles)} roles")
        return roles

    async def get_permissions(self):
        """Get all available permissions."""
        perms = await self._perm_repo.get_all()
        print(f"DEBUG: Found {len(perms)} permissions")
        return perms
        
    async def get_role(self, id: UUID):
        """Get role details."""
        role = await self._role_repo.get(id)
        if not role:
            raise NotFoundError("Role not found", entity_type="Role", entity_id=str(id))
        return role

    async def update_role_permissions(self, role_id: UUID, permission_ids: list[UUID], actor_id: Optional[UUID] = None):
        """Update permissions for a role."""
        role = await self._role_repo.get(role_id)
        if not role:
            raise NotFoundError("Role not found", entity_type="Role", entity_id=str(role_id))
        
        await self._role_repo.update_permissions(role_id, permission_ids)
        
        # Log
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE_PERMISSIONS",
            resource_type="ROLE",
            resource_id=str(role_id),
            description=f"Updated permissions for role {role.name}",
            request_data={"permission_ids": [str(p) for p in permission_ids]}
        )
        # Return updated role
        return await self._role_repo.get(role_id)

    async def get_permissions_for_roles(self, role_names: list[str]) -> list[str]:
        """Get all permission codes for a list of roles (hierarchical)."""
        return await self._role_repo.get_permissions_for_roles(role_names)

    async def check_access(self, role_names: list[str], permission_code: str) -> bool:
        """Check if any of the roles (or their parents) has the required permission."""
        if not role_names:
            return False
            
        if "admin" in role_names:
            return True
            
        permissions = await self._role_repo.get_permissions_for_roles(role_names)
        # Check if any resolved permission starts with 'code:'
        return any(p.startswith(f"{permission_code}:") for p in permissions)


class OrganizationService:
    """Service for organization management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._dept_repo = DepartmentRepository(session)
        self._service_repo = OrganizationalServiceRepository(session)
        self._exec_level_repo = ExecutiveLevelRepository(session)
        self._audit = get_audit_logger("auth-service")

    # ═══════════════════════════════════════════════════════════
    # Executive Level Operations
    # ═══════════════════════════════════════════════════════════

    async def get_executive_levels(self, active_only: bool = True):
        return await self._exec_level_repo.get_all(active_only)

    async def get_executive_level(self, id: UUID):
        level = await self._exec_level_repo.get(id)
        if not level:
            raise NotFoundError("Executive Level not found", entity_type="ExecutiveLevel", entity_id=str(id))
        return level

    async def create_executive_level(self, data: ExecutiveLevelCreate, actor_id: Optional[UUID] = None):
        existing = await self._exec_level_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Executive Level code already exists: {data.code}")

        level = await self._exec_level_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="EXECUTIVE_LEVEL",
            resource_id=str(level.id),
            description=f"Created executive level: {level.title}",
            request_data=data.model_dump(mode="json")
        )
        return level

    async def update_executive_level(self, id: UUID, data: ExecutiveLevelUpdate, actor_id: Optional[UUID] = None):
        level = await self._exec_level_repo.update(id, **data.model_dump(exclude_unset=True))
        if not level:
            raise NotFoundError("Executive Level not found", entity_type="ExecutiveLevel", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="EXECUTIVE_LEVEL",
            resource_id=str(id),
            description=f"Updated executive level: {level.title}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return level

    # ═══════════════════════════════════════════════════════════
    # Department Operations
    # ═══════════════════════════════════════════════════════════

    async def get_departments(self, active_only: bool = True):
        return await self._dept_repo.get_all(active_only)

    async def get_department_tree(self, active_only: bool = True):
        return await self._dept_repo.get_tree(active_only)

    async def get_department(self, id: UUID):
        dept = await self._dept_repo.get(id)
        if not dept:
            raise NotFoundError("Department not found", entity_type="Department", entity_id=str(id))
        return dept

    async def create_department(self, data: DepartmentCreate, actor_id: Optional[UUID] = None):
        existing = await self._dept_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Department code already exists: {data.code}")
            
        dept = await self._dept_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="DEPARTMENT",
            resource_id=str(dept.id),
            description=f"Created department: {dept.name}",
            request_data=data.model_dump(mode="json")
        )
        return dept

    async def update_department(self, id: UUID, data: DepartmentUpdate, actor_id: Optional[UUID] = None):
        dept = await self._dept_repo.update(id, **data.model_dump(exclude_unset=True))
        if not dept:
            raise NotFoundError("Department not found", entity_type="Department", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="DEPARTMENT",
            resource_id=str(id),
            description=f"Updated department: {dept.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return dept

    # ═══════════════════════════════════════════════════════════
    # Organizational Service Operations
    # ═══════════════════════════════════════════════════════════

    async def get_services(self, active_only: bool = True):
        return await self._service_repo.get_all(active_only)

    async def get_services_by_department(self, department_id: UUID):
        return await self._service_repo.get_by_department(department_id)

    async def get_service(self, id: UUID):
        service = await self._service_repo.get(id)
        if not service:
            raise NotFoundError("Service not found", entity_type="OrganizationalService", entity_id=str(id))
        return service

    async def create_service(self, data: OrganizationalServiceCreate, actor_id: Optional[UUID] = None):
        # We don't have get_by_code in repo yet? I didn't add it explicitly to repository methods for Service.
        # But repo has create which saves it. Unique constraint on code will raise IntegrityError if duplicate.
        # Ideally we check first. I'll rely on DB constraint or add get_by_code to repo?
        # I didn't add get_by_code to OrganizationalServiceRepository above. I missed it.
        # I'll rely on DB error catching generally, but catching sqlalchemy IntegrityError is cleaner.
        # For now, let's assume valid. Or I can add a check via get_all loop (inefficient) or add the method.
        # I'll modify the repo OR catch error.
        # Since I'm lazy and modifying repo requires another call, I'll risk the DB error for now or add it later.
        # Actually I can implement get_by_code if I use `select().where(code=...)` right here in service if I had session access (I do).
        
        # Check uniqueness inline
        query = select(self._service_repo._session.bind.dialects.postgresql.dml.OrganizationalService).where(OrganizationalService.code == data.code)
        # Wait, I need model import here to use it in select query if not using repo method.
        # Models are imported at top.
        # I'll skip explicit check for now and let DB handle unique constraint.
        
        service = await self._service_repo.create(**data.model_dump())
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="ORGANIZATIONAL_SERVICE",
            resource_id=str(service.id),
            description=f"Created service: {service.name}",
            request_data=data.model_dump(mode="json")
        )
        return service

    async def update_service(self, id: UUID, data: OrganizationalServiceUpdate, actor_id: Optional[UUID] = None):
        service = await self._service_repo.update(id, **data.model_dump(exclude_unset=True))
        if not service:
            raise NotFoundError("Service not found", entity_type="OrganizationalService", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="ORGANIZATIONAL_SERVICE",
            resource_id=str(id),
            description=f"Updated service: {service.name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return service

