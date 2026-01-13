"""KRONOS Auth Service - Contracts Router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError

from src.services.auth.service import UserService
from src.services.auth.schemas import (
    ContractTypeResponse,
    ContractTypeCreate,
    ContractTypeUpdate,
    WorkScheduleResponse,
    WorkScheduleCreate,
    EmployeeContractCreate,
    EmployeeContractUpdate,
    EmployeeContractResponse,
)

router = APIRouter()

async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)

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


@router.put("/contracts/{id}", response_model=EmployeeContractResponse)
async def update_user_contract(
    id: UUID,
    data: EmployeeContractUpdate,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Update contract. Admin/HR only."""
    try:
        return await service.update_employee_contract(id, data, actor_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/contracts/{id}", status_code=204)
async def delete_user_contract(
    id: UUID,
    token: TokenPayload = Depends(require_permission("users:edit")),
    service: UserService = Depends(get_user_service),
):
    """Delete contract. Admin/HR only."""
    try:
        await service.delete_employee_contract(id, actor_id=token.user_id)
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
