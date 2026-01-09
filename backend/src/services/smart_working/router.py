"""
KRONOS - Smart Working Router
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.security import get_current_user, require_hr, TokenPayload
from src.services.smart_working.service import SmartWorkingService
from src.services.smart_working.schemas import (
    SWAgreementCreate, SWAgreementResponse,
    SWRequestCreate, SWRequestResponse,
    SWAttendanceCheckIn, SWAttendanceCheckOut, SWAttendanceResponse,
    ApprovalCallback, SWPresenceCreate
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/smart-working", tags=["Smart Working"])

async def get_service(session: AsyncSession = Depends(get_db)):
    return SmartWorkingService(session)


async def verify_internal_token(x_internal_token: str = Header(..., alias="X-Internal-Token")):
    """Verify internal service-to-service token for callback endpoints."""
    expected = getattr(settings, 'internal_service_token', settings.secret_key)
    if x_internal_token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal service token"
        )
    return True


# -----------------------------------------------------------------------
# Agreements (HR/Admin Only)
# -----------------------------------------------------------------------

@router.post(
    "/agreements",
    response_model=SWAgreementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Smart Working Agreement",
    description="Creates a new remote work agreement for an employee. Requires HR or Admin role."
)
async def create_agreement(
    data: SWAgreementCreate,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(require_hr)
):
    return await service.create_agreement(data, created_by=token.user_id)


@router.get(
    "/agreements/me",
    response_model=List[SWAgreementResponse],
    summary="Get My Agreements",
    description="Returns all Smart Working agreements for the current user."
)
async def get_my_agreements(
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    return await service.get_user_agreements(token.user_id)


@router.get(
    "/agreements/user/{user_id}",
    response_model=List[SWAgreementResponse],
    summary="Get User Agreements (HR)",
    description="Returns all Smart Working agreements for a specific user. Requires HR role."
)
async def get_user_agreements_by_id(
    user_id: UUID,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(require_hr)
):
    return await service.get_user_agreements(user_id)


@router.put(
    "/agreements/{id}",
    response_model=SWAgreementResponse,
    summary="Update Agreement (HR)",
    description="Updates a Smart Working agreement. Requires HR or Admin role."
)
async def update_agreement(
    id: UUID,
    data: SWAgreementCreate,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(require_hr)
):
    return await service.update_agreement(id, data, token.user_id)


@router.put(
    "/agreements/{id}/terminate",
    response_model=SWAgreementResponse,
    summary="Terminate Agreement",
    description="Terminates an active Smart Working agreement. Requires HR or Admin role."
)
async def terminate_agreement(
    id: UUID,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(require_hr)
):
    return await service.terminate_agreement(id, token.user_id)


# -----------------------------------------------------------------------
# Requests (Employee Self-Service)
# -----------------------------------------------------------------------

@router.post(
    "/requests",
    response_model=SWRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Smart Working Request",
    description="Submits a new Smart Working request for a specific date. Requires an active agreement."
)
async def submit_request(
    data: SWRequestCreate,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    return await service.submit_request(data, token.user_id)


@router.get(
    "/requests/me",
    response_model=List[SWRequestResponse],
    summary="Get My Requests",
    description="Returns the current user's Smart Working requests (max 50, most recent first)."
)
async def get_my_requests(
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    return await service.get_user_requests(token.user_id)


@router.put(
    "/requests/{id}/cancel",
    response_model=SWRequestResponse,
    summary="Cancel Request",
    description="Cancels a pending or future Smart Working request."
)
async def cancel_request(
    id: UUID,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    return await service.cancel_request(id, token.user_id)

@router.post(
    "/requests/presence",
    response_model=SWRequestResponse,
    summary="Declare Presence",
    description="Declares presence for a specific date, effectively cancelling any automatic Smart Working day."
)
async def declare_presence(
    data: SWPresenceCreate,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    # Convert SWPresenceCreate to SWRequestCreate internal format (needs agreement ID which is fetched in service)
    # We pass data directly as it has date and notes
    return await service.submit_presence(data, token.user_id)


# -----------------------------------------------------------------------
# Attendance (Employee Self-Service)
# -----------------------------------------------------------------------

@router.post(
    "/attendance/check-in",
    response_model=SWAttendanceResponse,
    summary="Check-In",
    description="Records check-in for an approved Smart Working day."
)
async def check_in(
    data: SWAttendanceCheckIn,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    return await service.check_in(data, token.user_id)


@router.post(
    "/attendance/check-out",
    response_model=SWAttendanceResponse,
    summary="Check-Out",
    description="Records check-out for a Smart Working day."
)
async def check_out(
    data: SWAttendanceCheckOut,
    service: SmartWorkingService = Depends(get_service),
    token: TokenPayload = Depends(get_current_user)
):
    return await service.check_out(data, token.user_id)


# -----------------------------------------------------------------------
# Internal / Callbacks (Service-to-Service)
# -----------------------------------------------------------------------

@router.post(
    "/internal/approval-callback/{id}",
    include_in_schema=False,
    summary="Approval Callback",
    description="Internal endpoint for approval service callbacks. Protected by service token."
)
async def approval_callback(
    id: UUID,
    callback_data: ApprovalCallback,
    service: SmartWorkingService = Depends(get_service),
    _: bool = Depends(verify_internal_token)
):
    await service.handle_approval_callback(id, callback_data)
    return {"status": "ok"}
