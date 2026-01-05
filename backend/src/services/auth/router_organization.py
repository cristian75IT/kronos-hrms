
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError, ConflictError
from src.services.auth.service import OrganizationService
from src.services.auth.models import User
from src.services.auth.schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    OrganizationalServiceCreate,
    OrganizationalServiceUpdate,
    OrganizationalServiceResponse,
    ExecutiveLevelCreate,
    ExecutiveLevelUpdate,
    ExecutiveLevelResponse,
)

router = APIRouter(prefix="/organization", tags=["Organization"])

async def get_org_service(
    session: AsyncSession = Depends(get_db),
) -> OrganizationService:
    """Dependency for OrganizationService."""
    return OrganizationService(session)

# ═══════════════════════════════════════════════════════════
# Executive Levels
# ═══════════════════════════════════════════════════════════

@router.get("/executive-levels", response_model=List[ExecutiveLevelResponse])
async def get_executive_levels(
    active_only: bool = True,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get all executive levels."""
    return await service.get_executive_levels(active_only=active_only)

@router.get("/executive-levels/{id}", response_model=ExecutiveLevelResponse)
async def get_executive_level(
    id: UUID,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get executive level by ID."""
    return await service.get_executive_level(id)

@router.post("/executive-levels", response_model=ExecutiveLevelResponse, status_code=status.HTTP_201_CREATED)
async def create_executive_level(
    data: ExecutiveLevelCreate,
    service: OrganizationService = Depends(get_org_service),
    user: User = Depends(get_current_user),
):
    """Create executive level."""
    if not user.is_admin:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await service.create_executive_level(data, actor_id=user.id)

@router.put("/executive-levels/{id}", response_model=ExecutiveLevelResponse)
async def update_executive_level(
    id: UUID,
    data: ExecutiveLevelUpdate,
    service: OrganizationService = Depends(get_org_service),
    user: User = Depends(get_current_user),
):
    """Update executive level."""
    if not user.is_admin:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await service.update_executive_level(id, data, actor_id=user.id)

# ═══════════════════════════════════════════════════════════
# Departments
# ═══════════════════════════════════════════════════════════

@router.get("/departments", response_model=List[DepartmentResponse])
async def get_departments(
    active_only: bool = True,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get all departments."""
    return await service.get_departments(active_only=active_only)

@router.get("/departments/tree", response_model=List[DepartmentResponse])
async def get_department_tree(
    active_only: bool = True,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get department tree (roots with children loaded)."""
    return await service.get_department_tree(active_only=active_only)

@router.get("/departments/{id}", response_model=DepartmentResponse)
async def get_department(
    id: UUID,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get department by ID."""
    return await service.get_department(id)

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    service: OrganizationService = Depends(get_org_service),
    user: User = Depends(get_current_user),
):
    """Create department."""
    if not user.is_admin and not user.is_hr:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await service.create_department(data, actor_id=user.id)

@router.put("/departments/{id}", response_model=DepartmentResponse)
async def update_department(
    id: UUID,
    data: DepartmentUpdate,
    service: OrganizationService = Depends(get_org_service),
    user: User = Depends(get_current_user),
):
    """Update department."""
    if not user.is_admin and not user.is_hr:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await service.update_department(id, data, actor_id=user.id)

# ═══════════════════════════════════════════════════════════
# Services
# ═══════════════════════════════════════════════════════════

@router.get("/services", response_model=List[OrganizationalServiceResponse])
async def get_services(
    active_only: bool = True,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get all organizational services."""
    return await service.get_services(active_only=active_only)

@router.get("/departments/{department_id}/services", response_model=List[OrganizationalServiceResponse])
async def get_services_by_department(
    department_id: UUID,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get services by department."""
    return await service.get_services_by_department(department_id)

@router.get("/services/{id}", response_model=OrganizationalServiceResponse)
async def get_service(
    id: UUID,
    service: OrganizationService = Depends(get_org_service),
    token: TokenPayload = Depends(get_current_token),
):
    """Get organizational service by ID."""
    return await service.get_service(id)

@router.post("/services", response_model=OrganizationalServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: OrganizationalServiceCreate,
    service: OrganizationService = Depends(get_org_service),
    user: User = Depends(get_current_user),
):
    """Create organizational service."""
    if not user.is_admin and not user.is_hr:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await service.create_service(data, actor_id=user.id)

@router.put("/services/{id}", response_model=OrganizationalServiceResponse)
async def update_service(
    id: UUID,
    data: OrganizationalServiceUpdate,
    service: OrganizationService = Depends(get_org_service),
    user: User = Depends(get_current_user),
):
    """Update organizational service."""
    if not user.is_admin and not user.is_hr:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return await service.update_service(id, data, actor_id=user.id)
