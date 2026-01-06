"""
KRONOS Approvals Service - Actions Module.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

import httpx

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.approvals.models import ApprovalStatus
from src.services.approvals.services.base import BaseApprovalService

logger = logging.getLogger(__name__)


class ApprovalActionService(BaseApprovalService):
    """Manages Approval Actions (Approve, Reject, etc)."""
    
    def __init__(self, session, resolution_service):
        super().__init__(session)
        self._resolver = resolution_service

    async def _invoke_callback(self, request, status: str, notes: Optional[str] = None) -> bool:
        """
        Invoke the callback URL to notify the source service of the decision.
        
        Returns True if callback was successful, False otherwise.
        """
        if not request.callback_url:
            logger.debug(f"No callback_url for request {request.id}")
            return True  # No callback needed
        
        # Build payload matching ApprovalCallbackPayload schema
        # Include both approval_request_id (for Leave) and entity_type/entity_id (for Expenses)
        payload = {
            "approval_request_id": str(request.id),
            "entity_type": request.entity_type,
            "entity_id": str(request.entity_id),
            "status": status.upper(),  # APPROVED, REJECTED, CANCELLED, APPROVED_CONDITIONAL
            "decided_by": None,  # Could be extracted from workflow if needed
            "final_decision_by": None,
            "decided_by_name": None,
            "resolution_notes": notes,
            "resolved_at": datetime.utcnow().isoformat(),
            "condition_type": None,
            "condition_details": None,
            "decisions": [],
        }

        
        # Handle conditional approval
        if status.upper() == "APPROVED_CONDITIONAL" and notes:
            # Try to extract condition type from notes format: [TYPE] details
            if notes.startswith("[") and "]" in notes:
                end_bracket = notes.index("]")
                payload["condition_type"] = notes[1:end_bracket]
                payload["condition_details"] = notes[end_bracket+1:].strip()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    request.callback_url,
                    json=payload,
                    timeout=10.0
                )
                if response.status_code in (200, 201, 204):
                    logger.info(f"Callback successful for {request.entity_type}/{request.entity_id}: {status}")
                    return True
                else:
                    logger.error(f"Callback failed for {request.id}: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Callback error for {request.id}: {e}")
            return False


    async def approve_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
        override_authority: bool = False,
    ):
        """Approve a request."""
        request = await self._request_repo.get_by_id(request_id)
        if not request:
            raise NotFoundError("Request not found")
        
        # Update status
        request.status = ApprovalStatus.APPROVED
        await self._request_repo.update(request)
        
        # Invoke callback to source service
        await self._invoke_callback(request, "approved", notes)
        
        return request

    async def reject_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
        override_authority: bool = False,
    ):
        """Reject a request."""
        request = await self._request_repo.get_by_id(request_id)
        if not request:
            raise NotFoundError("Request not found")
            
        request.status = ApprovalStatus.REJECTED
        await self._request_repo.update(request)
        
        # Invoke callback to source service
        await self._invoke_callback(request, "rejected", notes)
        
        return request

    async def cancel_request(
        self,
        request_id: UUID,
        cancelled_by: UUID,
        reason: Optional[str] = None,
    ):
        """Cancel a request."""
        request = await self._request_repo.get_by_id(request_id)
        if not request:
            raise NotFoundError("Request not found")
            
        request.status = ApprovalStatus.CANCELLED
        await self._request_repo.update(request)
        
        # Invoke callback to source service
        await self._invoke_callback(request, "cancelled", reason)
        
        return request

    async def approve_conditional_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        condition_type: str,
        condition_details: str,
        notes: Optional[str] = None,
        override_authority: bool = False,
    ):
        """Approve with conditions."""
        request = await self._request_repo.get_by_id(request_id)
        if not request:
            raise NotFoundError("Request not found")
            
        await self._engine.process_decision(
            request, 
            approver_id, 
            "APPROVED_CONDITIONAL", 
            notes=f"[{condition_type}] {condition_details}\n{notes or ''}",
            override_authority=override_authority
        )
        
        # Invoke callback to source service
        full_notes = f"[{condition_type}] {condition_details}\n{notes or ''}"
        await self._invoke_callback(request, "approved_conditional", full_notes)
        
        return request

    async def delegate_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        delegate_to_id: UUID,
        delegate_to_name: Optional[str] = None,
        notes: Optional[str] = None,
        override_authority: bool = False,
    ):
        """Delegate request."""
        request = await self._request_repo.get_by_id(request_id)
        if not request:
            raise NotFoundError("Request not found")
            
        await self._engine.process_decision(
            request, 
            approver_id, 
            "DELEGATED", 
            notes=notes,
            delegated_to_id=delegate_to_id,
            delegated_to_name=delegate_to_name,
            override_authority=override_authority
        )
        # No callback for delegation - request is still pending
        return request
