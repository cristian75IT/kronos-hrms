"""
KRONOS Approvals Service - Actions Module.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.approvals.models import ApprovalStatus
from src.services.approvals.services.base import BaseApprovalService

class ApprovalActionService(BaseApprovalService):
    """Manages Approval Actions (Approve, Reject, etc)."""
    
    def __init__(self, session, resolution_service):
        super().__init__(session)
        self._resolver = resolution_service

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
            
        # ... logic ...
        
        # Using placeholder update via repo
        request.status = ApprovalStatus.APPROVED
        await self._request_repo.update(request)
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
        return request
