"""KRONOS Auth Service - Security Router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, get_current_user, TokenPayload
from src.core.exceptions import ConflictError
from src.shared.schemas import MessageResponse

from src.services.auth.service import UserService, RBACService
from src.services.auth.schemas import (
    CurrentUserResponse,
    MfaSetupResponse,
    MfaVerifyRequest,
    MfaDisableRequest,
    PasswordChangeRequest,
)

router = APIRouter()

# Dependencies
async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(session)

async def get_rbac_service(session: AsyncSession = Depends(get_db)) -> RBACService:
    return RBACService(session)

# ═══════════════════════════════════════════════════════════
# Auth / Security Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/auth/me", response_model=CurrentUserResponse)
async def read_current_user(
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Get current authenticated user with profile."""
    # Ensure user exists in local DB (creates on first login)
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


@router.post("/auth/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    token: TokenPayload = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Initialize MFA setup to get secret and QR code URL."""
    return await service.setup_mfa(token.user_id, token.email, actor_id=token.user_id)


@router.post("/auth/mfa/enable", response_model=MessageResponse)
async def enable_mfa(
    data: MfaVerifyRequest,
    token: TokenPayload = Depends(get_current_token),
    service: UserService = Depends(get_user_service),
):
    """Verify code and enable MFA on Keycloak."""
    try:
        await service.enable_mfa(token.user_id, request=data, actor_id=token.user_id)
        return MessageResponse(message="MFA enabled successfully")
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/mfa/disable", response_model=MessageResponse)
async def disable_mfa(
    data: MfaDisableRequest,
    token: TokenPayload = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Disable MFA for the current user."""
    try:
        await service.disable_mfa(token.user_id, code=data.code, actor_id=token.user_id)
        return MessageResponse(message="MFA disabled successfully")
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/password/change", response_model=MessageResponse)
async def change_password(
    data: PasswordChangeRequest,
    token: TokenPayload = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Change the current user's password."""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Le password non coincidono")
    
    try:
        await service.change_password(
            token.user_id, 
            current_password=data.current_password,
            new_password=data.new_password,
            actor_id=token.user_id
        )
        return MessageResponse(message="Password changed successfully")
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))
