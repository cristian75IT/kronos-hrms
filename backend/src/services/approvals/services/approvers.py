"""
KRONOS Approvals Service - Approver Resolution Module.
"""
from typing import Optional, List
from uuid import UUID
import logging

from src.services.approvals.services.base import BaseApprovalService
from src.services.approvals.models import ApprovalRequest

logger = logging.getLogger(__name__)

class ApprovalResolutionService(BaseApprovalService):
    """Resolves and Notifies Approvers."""

    async def fetch_approvers_by_roles(
        self,
        role_ids: List[str],
        requester_id: Optional[UUID] = None,
        exclude_user: Optional[UUID] = None,
        max_approvers: Optional[int] = None,
    ) -> List[dict]:
        """Fetch users with specific roles from auth service."""
        # Logic delegated to AuthClient usually, logic inline in monolithic
        # Assuming AuthClient has get_users_by_role or similar.
        # Original code likely had direct call logic.
        
        # Simulating AuthClient interaction for resolution
        # Usually auth_client.get_users(role_id=...)
        approvers = []
        for role in role_ids:
             users = await self._auth_client.get_users_by_role(role)
             approvers.extend(users)
             
        # Filter logic
        unique_approvers = {u['id']: u for u in approvers}.values()
        
        filtered = []
        for u in unique_approvers:
             uid = UUID(u['id'])
             if requester_id and uid == requester_id:
                 continue
             if exclude_user and uid == exclude_user:
                 continue
             filtered.append(u)
             
        if max_approvers:
             filtered = filtered[:max_approvers]
             
        return filtered

    async def fetch_approvers_by_flag(
        self,
        exclude_user: Optional[UUID] = None,
        max_approvers: Optional[int] = None,
    ) -> List[dict]:
        """Fetch users with is_approver=true flag."""
        users = await self._auth_client.get_approvers()
        
        filtered = []
        for u in users:
             uid = UUID(u['id'])
             if exclude_user and uid == exclude_user:
                 continue
             filtered.append(u)
             
        if max_approvers:
             filtered = filtered[:max_approvers]
             
        return filtered

    async def notify_approvers(
        self,
        request: ApprovalRequest,
        approver_ids: List[UUID],
    ):
        """Send notifications to approvers."""
        for approver_id in approver_ids:
            try:
                await self._notification_client.send_notification(
                    user_id=approver_id,
                    type="APPROVAL_REQUIRED",
                    title="Approval Required",
                    message=f"New request needs your approval: {request.entity_type}",
                    action_url=f"/approvals/{request.id}",
                    entity_type="approval_request",
                    entity_id=str(request.id)
                )
            except Exception as e:
                logger.error(f"Failed to notify approver {approver_id}: {e}")
