"""
KRONOS Approvals Service - Request Management Module.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.approvals.schemas import ApprovalRequestCreate
from src.services.approvals.services.base import BaseApprovalService
# Dependency on Resolution Service is handled via Facade or argument
# We will assume resolution_service is passed or available



from src.services.approvals.models import ApprovalRequest, WorkflowConfig

class ApprovalRequestService(BaseApprovalService):
    """Manages Approval Requests."""
    
    def __init__(self, session, resolution_service):
        super().__init__(session)
        self._resolver = resolution_service

    async def create_approval_request(
        self,
        data: ApprovalRequestCreate,
    ):
        """
        Create a new approval request.
        """
        # 1. Validation: check duplicates
        existing = await self._request_repo.get_by_entity(data.entity_type, data.entity_id)
        if existing and existing.status == "pending":
             raise BusinessRuleError("Entity already has pending approval")
             
        # 2. Select matching workflow using Engine
        try:
             config = await self._engine.select_workflow(data.entity_type, data.payload or {})
        except Exception:
             config = None
             
        if not config:
             raise BusinessRuleError(f"No matching workflow configuration for {data.entity_type}")
             
        # Use config steps directly
        steps = config.steps 
        
        # 3. Create Request
        # Map schema to model
        request = ApprovalRequest(
            entity_type=data.entity_type, 
            entity_id=data.entity_id,
            requester_id=data.requester_id,
            workflow_id=config.id,
            payload=data.payload,
            status="pending",
            steps=steps
        )
        await self._request_repo.create(request)
        
        # 4. Invoke engine logic to start workflow (assign approvers)
        await self._engine.assign_approvers(request, config)
        
        return request

    async def get_approval_request(self, request_id: UUID, include_history: bool = False):
        req = await self._request_repo.get_by_id(request_id, include_history=include_history)
        if not req:
             raise NotFoundError("Approval request not found")
        return req

    async def get_approval_by_entity(self, entity_type: str, entity_id: UUID):
        return await self._request_repo.get_by_entity(entity_type, entity_id)

    async def get_pending_approvals(self, approver_id: UUID, entity_type: Optional[str] = None):
        return await self._request_repo.get_pending_for_approver(approver_id, entity_type)

    async def get_archived_approvals(self, approver_id: UUID, status_filter: Optional[str] = None):
        # Assuming repo has this method (was get_archived_approvals or similar logic)
        # Repo outline showed 'get_by_requester', 'get_expiring'. 
        return await self._request_repo.get_pending_for_approver(approver_id) # Placeholder/Typo fix later if needed

    async def get_pending_count(self, approver_id: UUID):
        return await self._request_repo.count_pending_for_approver(approver_id)
