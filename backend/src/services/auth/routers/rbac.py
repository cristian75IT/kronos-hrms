"""KRONOS Auth Service - RBAC Router."""
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload
from src.core.exceptions import NotFoundError

from src.services.auth.service import RBACService
from src.services.auth.schemas import (
    RoleRead,
    PermissionRead,
    RolePermissionUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_rbac_service(session: AsyncSession = Depends(get_db)) -> RBACService:
    return RBACService(session)

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
