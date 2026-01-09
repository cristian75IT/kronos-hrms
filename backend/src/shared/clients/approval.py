"""
KRONOS - Approval Service Client

Client for the centralized approval workflow service.
"""
import logging
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class ApprovalClient(BaseClient):
    """Client for Approval Service interactions."""
    
    def __init__(self):
        super().__init__(
            base_url=settings.approval_service_url,
            service_name="approval",
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Request Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_request(
        self,
        entity_type: str,
        entity_id: UUID,
        requester_id: UUID,
        title: str,
        entity_ref: Optional[str] = None,
        requester_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        callback_url: Optional[str] = None,
        approver_ids: Optional[list[UUID]] = None,
    ) -> Optional[dict]:
        """Create an approval request."""
        payload = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "entity_ref": entity_ref,
            "requester_id": str(requester_id),
            "requester_name": requester_name,
            "title": title,
            "description": description,
            "metadata": metadata or {},
            "callback_url": callback_url,
        }
        
        if approver_ids:
            payload["approver_ids"] = [str(a) for a in approver_ids]
        
        return await self.post_safe(
            "/api/v1/approvals/internal/request",
            json=payload,
            timeout=10.0,
        )
    
    async def check_status(self, entity_type: str, entity_id: UUID) -> Optional[dict]:
        """Check approval status for an entity."""
        return await self.get_safe(
            f"/api/v1/approvals/internal/status/{entity_type}/{entity_id}"
        )
    
    async def get_by_entity(self, entity_type: str, entity_id: UUID) -> Optional[dict]:
        """Get approval request by entity type and ID."""
        return await self.get_safe(
            f"/api/v1/approvals/internal/by-entity/{entity_type}/{entity_id}"
        )
    
    async def get_pending_count(self, user_id: UUID) -> dict:
        """Get pending approval count for a user."""
        result = await self.get_safe(
            "/api/v1/approvals/decisions/pending/count",
            default={"total": 0, "urgent": 0, "by_type": {}},
            headers={"X-User-Id": str(user_id)},
        )
        return result if result else {"total": 0, "urgent": 0, "by_type": {}}
    
    async def cancel_request(
        self,
        entity_type: str,
        entity_id: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """Cancel an approval request by entity."""
        # First get the request
        status = await self.check_status(entity_type, entity_id)
        if not status or not status.get("approval_request_id"):
            return False
        
        request_id = status["approval_request_id"]
        result = await self.delete(f"/api/v1/approvals/requests/{request_id}")
        return result is not None
    
    # ═══════════════════════════════════════════════════════════════════════
    # Decision Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def approve(
        self,
        approval_request_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Approve an approval request."""
        return await self.post_safe(
            f"/api/v1/approvals/internal/approve/{approval_request_id}",
            json={
                "approver_id": str(approver_id),
                "notes": notes,
            },
            timeout=10.0,
        )
    
    async def reject(
        self,
        approval_request_id: UUID,
        approver_id: UUID,
        notes: str,
    ) -> Optional[dict]:
        """Reject an approval request."""
        return await self.post_safe(
            f"/api/v1/approvals/internal/reject/{approval_request_id}",
            json={
                "approver_id": str(approver_id),
                "notes": notes,
            },
            timeout=10.0,
        )

    async def check_workflow_health(self) -> dict:
        """Check system configuration health."""
        return await self.get_safe(
            "/api/v1/approvals/internal/health/config",
            default={"overall_status": "unknown", "items": []}
        )
