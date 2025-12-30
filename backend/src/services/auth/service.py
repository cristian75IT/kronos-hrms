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
)
from src.services.auth.schemas import (
    UserCreate,
    UserUpdate,
    AreaCreate,
    AreaUpdate,
    LocationCreate,
    LocationUpdate,
    ContractTypeCreate,
    WorkScheduleCreate,
    KeycloakSyncRequest,
    KeycloakSyncResponse,
)
from src.shared.schemas import DataTableRequest


class UserService:
    """Service for user management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._area_repo = AreaRepository(session)
        self._location_repo = LocationRepository(session)
        self._contract_repo = ContractTypeRepository(session)
        self._schedule_repo = WorkScheduleRepository(session)

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
                last_sync_at=datetime.utcnow(),
            )
            return user
        
        # Create new user
        return await self._user_repo.create(
            keycloak_id=keycloak_id,
            email=email,
            first_name=first_name or email.split("@")[0],
            last_name=last_name or "",
            is_admin="admin" in roles,
            is_manager="manager" in roles,
            is_approver="approver" in roles,
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

    async def update_user(self, id: UUID, data: UserUpdate):
        """Update user."""
        user = await self._user_repo.update(id, **data.model_dump(exclude_unset=True))
        if not user:
            raise NotFoundError("User not found", entity_type="User", entity_id=str(id))
        return user

    async def deactivate_user(self, id: UUID) -> bool:
        """Deactivate user."""
        result = await self._user_repo.deactivate(id)
        if not result:
            raise NotFoundError("User not found", entity_type="User", entity_id=str(id))
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
                            first_name=kc_user.get("firstName", local_user.first_name),
                            last_name=kc_user.get("lastName", local_user.last_name),
                            is_admin="admin" in role_names,
                            is_manager="manager" in role_names,
                            is_approver="approver" in role_names,
                            is_active=kc_user.get("enabled", True),
                            last_sync_at=datetime.utcnow(),
                        )
                        updated += 1
                    else:
                        # Create new user
                        await self._user_repo.create(
                            keycloak_id=kc_id,
                            email=kc_user.get("email", f"{kc_id}@unknown"),
                            first_name=kc_user.get("firstName", ""),
                            last_name=kc_user.get("lastName", ""),
                            is_admin="admin" in role_names,
                            is_manager="manager" in role_names,
                            is_approver="approver" in role_names,
                            is_active=kc_user.get("enabled", True),
                            last_sync_at=datetime.utcnow(),
                        )
                        created += 1
                    
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

    async def create_area(self, data: AreaCreate):
        """Create new area."""
        existing = await self._area_repo.get_by_code(data.code)
        if existing:
            raise ConflictError(f"Area code already exists: {data.code}")
        
        return await self._area_repo.create(**data.model_dump())

    async def update_area(self, id: UUID, data: AreaUpdate):
        """Update area."""
        area = await self._area_repo.update(id, **data.model_dump(exclude_unset=True))
        if not area:
            raise NotFoundError("Area not found", entity_type="Area", entity_id=str(id))
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

    async def create_contract_type(self, data: ContractTypeCreate):
        """Create new contract type."""
        return await self._contract_repo.create(**data.model_dump())

    # ═══════════════════════════════════════════════════════════
    # Work Schedule Operations
    # ═══════════════════════════════════════════════════════════

    async def get_work_schedules(self, active_only: bool = True):
        """Get all work schedules."""
        return await self._schedule_repo.get_all(active_only)

    async def create_work_schedule(self, data: WorkScheduleCreate):
        """Create new work schedule."""
        return await self._schedule_repo.create(**data.model_dump())
