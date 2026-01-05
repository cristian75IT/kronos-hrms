"""KRONOS Auth Service - API Router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, ConflictError
from src.shared.schemas import MessageResponse, DataTableRequest
from src.services.auth.service import UserService, RBACService
from src.services.auth.schemas import (
    UserResponse,
    UserListItem,
    UserUpdate,
    UserDataTableResponse,
    CurrentUserResponse,
    AreaResponse,
    AreaCreate,
    AreaUpdate,
    AreaWithUsersResponse,
    LocationResponse,
    LocationCreate,
    ContractTypeResponse,
    ContractTypeCreate,
    ContractTypeUpdate,
    WorkScheduleResponse,
    WorkScheduleCreate,
    EmployeeContractCreate,
    EmployeeContractResponse,
    EmployeeTrainingCreate,
    EmployeeTrainingUpdate,
    EmployeeTrainingResponse,
    KeycloakSyncRequest,
    KeycloakSyncResponse,
    PermissionRead,
    RoleRead,
    RolePermissionUpdate,
)


import logging
router = APIRouter()
logger = logging.getLogger(__name__)


async def get_user_service(
    session: AsyncSession = Depends(get_db),
) -> UserService:
    """Dependency for UserService."""
    return UserService(session)


async def get_rbac_service(
    session: AsyncSession = Depends(get_db),
) -> RBACService:
    """Dependency for RBACService."""
    return RBACService(session)


# ═══════════════════════════════════════════════════════════
# Auth Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/auth/me", response_model=CurrentUserResponse)
async def read_current_user(
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Get current authenticated user with profile."""
    # Ensure user exists in local DB (creates on first login)
    # Robust name parsing
    name_parts = token.name.split() if token.name else []
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    user = await service.get_or_create_from_token(
        keycloak_id=token.keycloak_id,
        email=token.email or "",
        username=token.preferred_username or token.email or "",
        first_name=first_name,
        last_name=last_name,
        roles=token.roles,
    )
    
    # Get permissions
    permissions = await rbac_service.get_permissions_for_roles(token.roles)
    
    return CurrentUserResponse(
        id=user.id,
        keycloak_id=user.keycloak_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        roles=token.roles,
        permissions=permissions,
        is_admin=user.is_admin,
        is_manager=user.is_manager,
        is_approver=user.is_approver,
        is_hr=user.is_hr,
        is_employee=user.is_employee,
        location=user.location.name if user.location else None,
        manager=user.manager.full_name if user.manager else None,
    )


# ═══════════════════════════════════════════════════════════
# User Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/users", response_model=list[UserListItem])
async def list_users(
    active_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    token: TokenPayload = Depends(require_permission("users:view")),
    service: UserService = Depends(get_user_service),
):
    """List all users. Manager or Admin only."""
    users = await service.get_users(active_only, limit, offset)
    return [UserListItem.model_validate(u) for u in users]


@router.post("/users/datatable", response_model=UserDataTableResponse)
async def users_datatable(
    request: DataTableRequest,
    active_only: bool = True,
    token: TokenPayload = Depends(require_permission("users:view")),
    service: UserService = Depends(get_user_service),
):
    """Get users for DataTable with server-side processing."""
    users, total, filtered = await service.get_users_datatable(request, active_only)
    
    return UserDataTableResponse(
        draw=request.draw,
        recordsTotal=total,
        recordsFiltered=filtered,
        data=[UserListItem.model_validate(u) for u in users],
    )


@router.get("/users/subordinates", response_model=list[UserListItem])
async def get_subordinates(
    token: TokenPayload = Depends(require_permission("users:view")),
    service: UserService = Depends(get_user_service),
):
    """Get direct reports of current manager."""
    user = await service.get_user_by_keycloak_id(token.keycloak_id)
    subordinates = await service.get_subordinates(user.id)
    return [UserListItem.model_validate(u) for u in subordinates]


@router.get("/users/approvers", response_model=list[UserListItem])
async def get_approvers(
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """Get all users with approver capability."""
    approvers = await service.get_approvers()
    return [UserListItem.model_validate(u) for u in approvers]


@router.get("/users/by-keycloak/{keycloak_id}", response_model=UserResponse)
async def get_user_by_keycloak_id(
    keycloak_id: str,
    service: UserService = Depends(get_user_service),
    rbac_service: RBACService = Depends(get_rbac_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get user by Keycloak ID (internal use for identity resolution)."""
    try:
        user = await service.get_user_by_keycloak_id(keycloak_id)
        # Fetch permissions for roles in the token
        permissions = await rbac_service.get_permissions_for_roles(token.roles)
        
        # Hydrate response
        response = UserResponse.model_validate(user)
        response.permissions = permissions
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/internal/approvers", response_model=list[UserListItem])
async def get_internal_approvers(
    service: UserService = Depends(get_user_service),
):
    """Get all users with approver capability (internal use).
    
    This endpoint is for service-to-service calls and doesn't require authentication.
    Only accessible within the internal Docker network.
    """
    approvers = await service.get_approvers()
    return [UserListItem.model_validate(u) for u in approvers]


@router.get("/users/internal/all", response_model=list[UserListItem])
async def get_internal_users(
    active_only: bool = True,
    service: UserService = Depends(get_user_service),
):
    """Get all users (internal use).
    
    This endpoint is for service-to-service calls and doesn't require authentication.
    Only accessible within the internal Docker network.
    """
    users = await service.get_users(active_only, limit=1000, offset=0)
    return [UserListItem.model_validate(u) for u in users]


@router.get("/users/{id}", response_model=UserResponse)
async def get_user(
    id: UUID,
    service: UserService = Depends(get_user_service),
):
    """Get user by ID. Manager or Admin only."""
    try:
        return await service.get_user(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/users/{id}", response_model=UserResponse)
async def update_user(
    id: UUID,
    data: UserUpdate,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Update user. Admin only."""
    try:
        return await service.update_user(id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{id}", response_model=MessageResponse)
async def deactivate_user(
    id: UUID,
    token: TokenPayload = Depends(require_permission("users:delete")),
    service: UserService = Depends(get_user_service),
):
    """Deactivate user. Admin only."""
    try:
        await service.deactivate_user(id, actor_id=token.user_id)
        return MessageResponse(message="User deactivated")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/sync", response_model=KeycloakSyncResponse)
async def sync_users_from_keycloak(
    request: KeycloakSyncRequest = KeycloakSyncRequest(),
    token: TokenPayload = Depends(require_permission("users:manage")),
    service: UserService = Depends(get_user_service),
):
    """Sync all users from Keycloak. Admin only."""
    return await service.sync_from_keycloak(request)


# ═══════════════════════════════════════════════════════════
# Area Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/areas", response_model=list[AreaResponse])
async def list_areas(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """List all areas."""
    return await service.get_areas(active_only)


@router.get("/areas/{id}", response_model=AreaWithUsersResponse)
async def get_area(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """Get area by ID with users."""
    try:
        return await service.get_area(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/areas", response_model=AreaResponse, status_code=201)
async def create_area(
    data: AreaCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: UserService = Depends(get_user_service),
):
    """Create new area. Admin only."""
    try:
        return await service.create_area(data, actor_id=token.user_id)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/areas/{id}", response_model=AreaResponse)
async def update_area(
    id: UUID,
    data: AreaUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: UserService = Depends(get_user_service),
):
    """Update area. Admin only."""
    try:
        return await service.update_area(id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Location Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/locations", response_model=list[LocationResponse])
async def list_locations(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """List all locations."""
    return await service.get_locations(active_only)


@router.get("/locations/{id}", response_model=LocationResponse)
async def get_location(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """Get location by ID."""
    try:
        return await service.get_location(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/locations", response_model=LocationResponse, status_code=201)
async def create_location(
    data: LocationCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: UserService = Depends(get_user_service),
):
    """Create new location. Admin only."""
    try:
        return await service.create_location(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Employee Contract Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/users/{user_id}/contracts", response_model=list[EmployeeContractResponse])
async def get_user_contracts(
    user_id: UUID,
    token: TokenPayload = Depends(require_permission("users:view")),
    service: UserService = Depends(get_user_service),
):
    """Get all contracts for a user."""
    return await service.get_employee_contracts(user_id)


@router.post("/users/{user_id}/contracts", response_model=EmployeeContractResponse, status_code=201)
async def create_user_contract(
    user_id: UUID,
    data: EmployeeContractCreate,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Add a new contract to user history. Admin only."""
    try:
        return await service.create_employee_contract(user_id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Contract Type Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/contract-types", response_model=list[ContractTypeResponse])
async def list_contract_types(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """List all contract types."""
    return await service.get_contract_types(active_only)


@router.post("/contract-types", response_model=ContractTypeResponse, status_code=201)
async def create_contract_type(
    data: ContractTypeCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: UserService = Depends(get_user_service),
):
    """Create new contract type. Admin only."""
    return await service.create_contract_type(data, actor_id=token.user_id)


@router.put("/contract-types/{id}", response_model=ContractTypeResponse)
async def update_contract_type(
    id: UUID,
    data: ContractTypeUpdate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: UserService = Depends(get_user_service),
):
    """Update contract type. Admin only."""
    return await service.update_contract_type(id, data, actor_id=token.user_id)


# ═══════════════════════════════════════════════════════════
# Work Schedule Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/work-schedules", response_model=list[WorkScheduleResponse])
async def list_work_schedules(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """List all work schedules."""
    return await service.get_work_schedules(active_only)


@router.post("/work-schedules", response_model=WorkScheduleResponse, status_code=201)
async def create_work_schedule(
    data: WorkScheduleCreate,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: UserService = Depends(get_user_service),
):
    """Create new work schedule. Admin only."""
    return await service.create_work_schedule(data, actor_id=token.user_id)


# ═══════════════════════════════════════════════════════════
# Employee Training Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/users/{user_id}/trainings", response_model=list[EmployeeTrainingResponse])
async def get_user_trainings(
    user_id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Get all training records for a user."""
    # Check if current user is HR/Admin or the user themselves
    if not (token.user_id == user_id or token.is_admin or "users:view" in token.permissions):
         raise HTTPException(status_code=403, detail="Not authorized to view these training records")
         
    return await service.get_employee_trainings(user_id)


@router.post("/trainings", response_model=EmployeeTrainingResponse, status_code=201)
async def create_training(
    data: EmployeeTrainingCreate,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Create new training record. HR or Admin only."""
             
    return await service.create_employee_training(data, actor_id=token.user_id)


@router.put("/trainings/{id}", response_model=EmployeeTrainingResponse)
async def update_training(
    id: UUID,
    data: EmployeeTrainingUpdate,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Update training record. HR or Admin only."""
        
    try:
        return await service.update_employee_training(id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/trainings/{id}", status_code=204)
async def delete_training(
    id: UUID,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Delete training record. HR or Admin only."""
        
    try:
        await service.delete_employee_training(id, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# RBAC Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/roles", response_model=list[RoleRead])
async def list_roles(
    token: TokenPayload = Depends(require_permission("roles:view")),
    service: RBACService = Depends(get_rbac_service),
):
    """List all RBAC roles with permissions. Requires roles:view permission."""
    logger.info("Entering list_roles endpoint")
    try:
        logger.info("Calling service.get_roles()")
        roles = await service.get_roles()
        logger.info(f"Got {len(roles)} roles. Validating...")
        
        # Force serialization to catch errors here
        serialized = [RoleRead.model_validate(r) for r in roles]
        logger.info("Validation successful")
        return serialized
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"CRASH in list_roles: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(
    token: TokenPayload = Depends(require_permission("roles:view")),
    service: RBACService = Depends(get_rbac_service),
):
    """List all available permissions. Admin only."""
    logger.info("Entering list_permissions endpoint")
    try:
        logger.info("Calling service.get_permissions()")
        perms = await service.get_permissions()
        logger.info(f"Got {len(perms)} permissions. Validating...")
        
        # Force serialization to catch errors here
        serialized = [PermissionRead.model_validate(p) for p in perms]
        logger.info("Validation successful")
        return serialized
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"CRASH in list_permissions: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


@router.put("/roles/{id}/permissions", response_model=RoleRead)
async def update_role_permissions(
    id: UUID,
    data: RolePermissionUpdate,
    token: TokenPayload = Depends(require_permission("roles:edit")),
    service: RBACService = Depends(get_rbac_service),
):
    """Update permissions for a role. Requires roles:edit permission."""
    try:
        return await service.update_role_permissions(id, data.permission_ids, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

