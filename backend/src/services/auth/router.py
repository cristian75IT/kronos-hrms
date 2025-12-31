"""KRONOS Auth Service - API Router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_admin, require_manager, TokenPayload
from src.core.exceptions import NotFoundError, ConflictError
from src.shared.schemas import MessageResponse, DataTableRequest
from src.services.auth.service import UserService
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
    KeycloakSyncRequest,
    KeycloakSyncResponse,
)


router = APIRouter()


async def get_user_service(
    session: AsyncSession = Depends(get_db),
) -> UserService:
    """Dependency for UserService."""
    return UserService(session)


# ═══════════════════════════════════════════════════════════
# Auth Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/auth/me", response_model=CurrentUserResponse)
async def get_current_user(
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """Get current authenticated user with profile."""
    # Ensure user exists in local DB (creates on first login)
    user = await service.get_or_create_from_token(
        keycloak_id=token.keycloak_id,
        email=token.email or "",
        username=token.preferred_username or token.email or "",
        first_name=token.name.split()[0] if token.name else "",
        last_name=" ".join(token.name.split()[1:]) if token.name and len(token.name.split()) > 1 else "",
        roles=token.roles,
    )
    
    return CurrentUserResponse(
        id=user.id,
        keycloak_id=user.keycloak_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        roles=token.roles,
        is_admin=user.is_admin,
        is_manager=user.is_manager,
        is_approver=user.is_approver,
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
    token: TokenPayload = Depends(require_manager),
    service: UserService = Depends(get_user_service),
):
    """List all users. Manager or Admin only."""
    users = await service.get_users(active_only, limit, offset)
    return [UserListItem.model_validate(u) for u in users]


@router.post("/users/datatable", response_model=UserDataTableResponse)
async def users_datatable(
    request: DataTableRequest,
    active_only: bool = True,
    token: TokenPayload = Depends(require_manager),
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
    token: TokenPayload = Depends(require_manager),
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
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Update user. Admin only."""
    try:
        return await service.update_user(id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{id}", response_model=MessageResponse)
async def deactivate_user(
    id: UUID,
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Deactivate user. Admin only."""
    try:
        await service.deactivate_user(id)
        return MessageResponse(message="User deactivated")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/users/sync", response_model=KeycloakSyncResponse)
async def sync_users_from_keycloak(
    request: KeycloakSyncRequest = KeycloakSyncRequest(),
    token: TokenPayload = Depends(require_admin),
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
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Create new area. Admin only."""
    try:
        return await service.create_area(data)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/areas/{id}", response_model=AreaResponse)
async def update_area(
    id: UUID,
    data: AreaUpdate,
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Update area. Admin only."""
    try:
        return await service.update_area(id, data)
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
    token: TokenPayload = Depends(require_admin),
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
    token: TokenPayload = Depends(require_manager),
    service: UserService = Depends(get_user_service),
):
    """Get all contracts for a user."""
    return await service.get_employee_contracts(user_id)


@router.post("/users/{user_id}/contracts", response_model=EmployeeContractResponse, status_code=201)
async def create_user_contract(
    user_id: UUID,
    data: EmployeeContractCreate,
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Add a new contract to user history. Admin only."""
    try:
        return await service.create_employee_contract(user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Contract Type Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/contract-types", response_model=list[ContractTypeResponse])
async def list_contract_types(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """List all contract types."""
    return await service.get_contract_types(active_only)


@router.post("/contract-types", response_model=ContractTypeResponse, status_code=201)
async def create_contract_type(
    data: ContractTypeCreate,
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Create new contract type. Admin only."""
    return await service.create_contract_type(data)


@router.put("/contract-types/{id}", response_model=ContractTypeResponse)
async def update_contract_type(
    id: UUID,
    data: ContractTypeUpdate,
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Update contract type. Admin only."""
    return await service.update_contract_type(id, data)


# ═══════════════════════════════════════════════════════════
# Work Schedule Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/work-schedules", response_model=list[WorkScheduleResponse])
async def list_work_schedules(
    active_only: bool = True,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """List all work schedules."""
    return await service.get_work_schedules(active_only)


@router.post("/work-schedules", response_model=WorkScheduleResponse, status_code=201)
async def create_work_schedule(
    data: WorkScheduleCreate,
    token: TokenPayload = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    """Create new work schedule. Admin only."""
    return await service.create_work_schedule(data)
