"""KRONOS Auth Service - Training Router."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError

from src.services.auth.service import UserService
from src.services.auth.schemas import (
    EmployeeTrainingCreate,
    EmployeeTrainingUpdate,
    EmployeeTrainingResponse,
)

router = APIRouter()

async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)

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
