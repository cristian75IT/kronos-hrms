"""KRONOS Auth Service - Business Logic."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import NotFoundError, ConflictError
from src.services.auth.repository import (
    UserRepository,
    AreaRepository,
    LocationRepository,
    ContractTypeRepository,
    WorkScheduleRepository,
    EmployeeContractRepository,
    EmployeeTrainingRepository,
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
)
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
        self._schedule_repo = WorkScheduleRepository(session)
        self._emp_contract_repo = EmployeeContractRepository(session)
        self._training_repo = EmployeeTrainingRepository(session)
        self._audit = get_audit_logger("auth-service")


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
                last_sync_at=datetime.utcnow(),
            )
            return user
        
        # Create new user
        return await self._user_repo.create(
            keycloak_id=keycloak_id,
            email=email,
            username=username or email,
            first_name=first_name or email.split("@")[0],
            last_name=last_name or "",
            is_admin="admin" in roles,
            is_manager="manager" in roles,
            is_approver="approver" in roles,
            is_hr="hr" in roles,
            last_sync_at=datetime.utcnow(),
        )

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
        """Update user."""
        user = await self._user_repo.update(id, **data.model_dump(exclude_unset=True))
        if not user:
            raise NotFoundError("User not found", entity_type="User", entity_id=str(id))
            
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="USER",
            resource_id=str(id),
            description=f"Updated user: {user.full_name}",
            request_data=data.model_dump(mode="json", exclude_unset=True)
        )
        return user

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
