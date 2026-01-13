"""KRONOS Auth Service - Users Router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_permission, TokenPayload
from src.core.exceptions import NotFoundError
from src.shared.schemas import MessageResponse, DataTableRequest

from src.services.auth.service import UserService, RBACService
from src.services.auth.schemas import (
    UserResponse,
    UserListItem,
    UserUpdate,
    UserDataTableResponse,
    KeycloakSyncRequest,
    KeycloakSyncResponse,
)

router = APIRouter()

# Dependencies
async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)

async def get_rbac_service(session: AsyncSession = Depends(get_db)) -> RBACService:
    return RBACService(session)

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


@router.get("/users/internal/by-role/{role_id}", response_model=list[UserListItem])
async def get_users_by_role(
    role_id: UUID,
    service: UserService = Depends(get_user_service),
):
    """Get users by role ID (internal use)."""
    users = await service.get_users_by_role(role_id)
    return [UserListItem.model_validate(u) for u in users]


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
        user = await service.get_user(id)
        # Compute roles from boolean flags
        roles = []
        if user.is_admin:
            roles.append("admin")
        if user.is_manager:
            roles.append("manager")
        if user.is_approver:
            roles.append("approver")
        if user.is_hr:
            roles.append("hr")
        if user.is_employee:
            roles.append("employee")
        
        # Convert to dict and add roles
        user_dict = {
            "id": user.id,
            "keycloak_id": user.keycloak_id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}",
            "badge_number": user.badge_number,
            "fiscal_code": user.fiscal_code,
            "hire_date": user.hire_date,
            "termination_date": user.termination_date,
            "is_admin": user.is_admin,
            "is_manager": user.is_manager,
            "is_approver": user.is_approver,
            "is_hr": user.is_hr,
            "is_employee": user.is_employee,
            "is_active": user.is_active,
            "mfa_enabled": user.mfa_enabled,
            "contract_type_id": user.contract_type_id,
            "work_schedule_id": user.work_schedule_id,
            "location_id": user.location_id,
            "manager_id": user.manager_id,
            "last_sync_at": user.last_sync_at,
            "profile": user.profile,
            "permissions": [],
            "roles": roles,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "department_id": user.department_id,
            "service_id": user.service_id,
            "executive_level_id": user.executive_level_id,
        }
        return user_dict
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
