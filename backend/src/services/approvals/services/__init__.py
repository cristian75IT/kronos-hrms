"""
KRONOS Approvals Service Package.

Modular approval service.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from src.services.approvals.schemas import (
    ApprovalRequestCreate,
    WorkflowConfigCreate,
    WorkflowConfigUpdate
)

from src.services.approvals.services.base import BaseApprovalService
from src.services.approvals.services.configs import ApprovalConfigService
from src.services.approvals.services.approvers import ApprovalResolutionService
from src.services.approvals.services.requests import ApprovalRequestService
from src.services.approvals.services.actions import ApprovalActionService

class ApprovalService(BaseApprovalService):
    """Facade for Approval Service."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._configs = ApprovalConfigService(session)
        self._resolver = ApprovalResolutionService(session)
        self._requests = ApprovalRequestService(session, self._resolver)
        self._actions = ApprovalActionService(session, self._resolver)
        
    # Configs
    async def create_workflow_config(self, data: WorkflowConfigCreate, created_by: Optional[UUID] = None):
        return await self._configs.create_workflow_config(data, created_by)
        
    async def get_workflow_config(self, config_id: UUID):
        return await self._configs.get_workflow_config(config_id)
        
    async def list_workflow_configs(self, entity_type: Optional[str] = None, active_only: bool = True):
        return await self._configs.list_workflow_configs(entity_type, active_only)
        
    async def update_workflow_config(self, config_id: UUID, data: WorkflowConfigUpdate):
        return await self._configs.update_workflow_config(config_id, data)
        
    async def delete_workflow_config(self, config_id: UUID):
        return await self._configs.delete_workflow_config(config_id)

    # Requests
    async def create_approval_request(self, data: ApprovalRequestCreate):
        return await self._requests.create_approval_request(data)
        
    async def get_approval_request(self, request_id: UUID, include_history: bool = False):
        return await self._requests.get_approval_request(request_id, include_history)

    async def get_approval_by_entity(self, entity_type: str, entity_id: UUID):
        return await self._requests.get_approval_by_entity(entity_type, entity_id)

    async def get_pending_approvals(self, approver_id: UUID, entity_type: Optional[str] = None, include_all: bool = False):
        return await self._requests.get_pending_approvals(approver_id, entity_type, include_all)

    async def get_archived_approvals(self, approver_id: UUID, status_filter: Optional[str] = None, entity_type: Optional[str] = None):
        return await self._requests.get_archived_approvals(approver_id, status_filter, entity_type)

    async def get_pending_count(self, approver_id: UUID):
        return await self._requests.get_pending_count(approver_id)

    # Actions
    async def approve_request(self, request_id: UUID, approver_id: UUID, notes: Optional[str] = None, override_authority: bool = False):
        return await self._actions.approve_request(request_id, approver_id, notes, override_authority)
        
    async def reject_request(self, request_id: UUID, approver_id: UUID, notes: Optional[str] = None, override_authority: bool = False):
        return await self._actions.reject_request(request_id, approver_id, notes, override_authority)
        
    async def approve_conditional_request(self, request_id: UUID, approver_id: UUID, condition_type: str, condition_details: str, notes: Optional[str] = None, override_authority: bool = False):
        return await self._actions.approve_conditional_request(request_id, approver_id, condition_type, condition_details, notes, override_authority)
        
    async def delegate_request(self, request_id: UUID, approver_id: UUID, delegate_to_id: UUID, delegate_to_name: Optional[str] = None, notes: Optional[str] = None, override_authority: bool = False):
        return await self._actions.delegate_request(request_id, approver_id, delegate_to_id, delegate_to_name, notes, override_authority)
        
    async def cancel_request(self, request_id: UUID, cancelled_by: UUID, reason: Optional[str] = None):
        return await self._actions.cancel_request(request_id, cancelled_by, reason)

# Export
__all__ = ["ApprovalService"]
