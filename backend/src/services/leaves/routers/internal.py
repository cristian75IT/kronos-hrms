"""
KRONOS - Leave Service Internal Router

Internal endpoints for inter-service communication (approval callbacks, etc.)
"""
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.leaves.service import LeaveService
from src.services.leaves.models import LeaveRequestStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


class ApprovalCallbackPayload(BaseModel):
    """Payload from approval service callback."""
    approval_request_id: UUID
    status: str  # APPROVED, REJECTED, EXPIRED, CANCELLED
    decided_by: Optional[UUID] = None
    decided_by_name: Optional[str] = None
    decision_notes: Optional[str] = None
    resolved_at: Optional[str] = None
    condition_type: Optional[str] = None
    condition_details: Optional[str] = None


@router.post("/approval-callback/{leave_id}")
async def handle_approval_callback(
    leave_id: UUID,
    payload: ApprovalCallbackPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle callback from Approval Service when a leave request is resolved.
    
    This endpoint is called by the approval service to notify the leave service
    of approval decisions.
    """
    logger.info(f"Received approval callback for leave {leave_id}: {payload.status}")
    
    service = LeaveService(db)
    
    try:
        # Get the leave request
        request = await service.get_request(leave_id)
        
        if request.status != LeaveRequestStatus.PENDING:
            logger.warning(f"Leave {leave_id} not in PENDING status, ignoring callback")
            return {"status": "ignored", "reason": "not_pending"}
        
        if payload.status == "APPROVED":
            # Auto-approve the leave request
            from src.services.leaves.schemas import ApproveRequest
            
            approver_id = payload.decided_by or UUID("00000000-0000-0000-0000-000000000000")
            
            approve_data = ApproveRequest(
                notes=payload.decision_notes or "Approvato tramite workflow"
            )
            
            await service.approve_request(
                id=leave_id,
                approver_id=approver_id,
                data=approve_data,
            )
            
            logger.info(f"Leave {leave_id} approved via workflow")
            return {"status": "approved"}
            
        elif payload.status == "REJECTED":
            from src.services.leaves.schemas import RejectRequest
            
            rejector_id = payload.decided_by or UUID("00000000-0000-0000-0000-000000000000")
            
            reject_data = RejectRequest(
                reason=payload.decision_notes or "Rifiutato tramite workflow"
            )
            
            await service.reject_request(
                id=leave_id,
                approver_id=rejector_id,
                data=reject_data,
            )
            
            logger.info(f"Leave {leave_id} rejected via workflow")
            return {"status": "rejected"}
            
        elif payload.status == "APPROVED_CONDITIONAL":
            from src.services.leaves.schemas import ApproveConditionalRequest
            
            approver_id = payload.decided_by or UUID("00000000-0000-0000-0000-000000000000")
            
            cond_data = ApproveConditionalRequest(
                condition_type=payload.condition_type or "GENERIC",
                condition_details=payload.condition_details or "Condizioni applicate da workflow esterno",
            )
            
            await service.approve_conditional(
                id=leave_id,
                approver_id=approver_id,
                data=cond_data,
            )
            
            logger.info(f"Leave {leave_id} approved with conditions via workflow")
            return {"status": "approved_conditional"}
            
        elif payload.status in ("EXPIRED", "CANCELLED"):
            # Handle expiration/cancellation by rejecting
            from src.services.leaves.schemas import RejectRequest
            
            reject_data = RejectRequest(
                reason=f"Richiesta {payload.status.lower()} dal sistema di approvazione"
            )
            
            await service.reject_request(
                id=leave_id,
                approver_id=UUID("00000000-0000-0000-0000-000000000000"),
                data=reject_data,
            )
            
            logger.info(f"Leave {leave_id} marked as {payload.status} via workflow")
            return {"status": payload.status.lower()}
            
        else:
            logger.warning(f"Unknown approval status: {payload.status}")
            return {"status": "ignored", "reason": "unknown_status"}
            
    except Exception as e:
        logger.error(f"Error handling approval callback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
