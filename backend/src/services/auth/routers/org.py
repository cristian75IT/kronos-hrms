"""KRONOS Auth Service - Organization Router (Legacy Areas/Locations)."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, ConflictError

from src.services.auth.service import UserService
from src.services.auth.schemas import (
    AreaResponse,
    AreaCreate,
    AreaUpdate,
    AreaWithUsersResponse,
    LocationResponse,
    LocationCreate,
)

router = APIRouter()

async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)

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
