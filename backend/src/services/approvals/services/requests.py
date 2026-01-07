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
             config = await self._engine.select_workflow(data.entity_type, data.metadata or {})
        except Exception as e:
             import logging
             logging.getLogger(__name__).error(f"Error selecting workflow: {e}", exc_info=True)
             config = None
             
        if not config:
             raise BusinessRuleError(f"No matching workflow configuration for {data.entity_type}")
             
        # 3. Create Request
        request = ApprovalRequest(
            entity_type=data.entity_type, 
            entity_id=data.entity_id,
            requester_id=data.requester_id,
            requester_name=data.requester_name,
            workflow_config_id=config.id,
            title=data.title,
            description=data.description,
            request_metadata=data.metadata,
            callback_url=data.callback_url,
            status="PENDING"
        )
        await self._request_repo.create(request)
        
        # 4. Resolve approvers from workflow config
        approver_ids = []
        approver_info = {}
        
        # Get approvers from configured role IDs
        role_ids = config.approver_role_ids or []
        if role_ids and config.auto_assign_approvers:
            for role_id_str in role_ids:
                # Skip dynamic role placeholders (e.g., DYNAMIC:DEPARTMENT_MANAGER)
                if role_id_str.startswith("DYNAMIC:"):
                    continue
                    
                try:
                    role_id = UUID(role_id_str)
                    users = await self._auth_client.get_users_by_role(role_id)
                    for user in users:
                        user_id = UUID(user["id"])
                        # Don't allow self-approval unless explicitly configured
                        if not config.allow_self_approval and user_id == data.requester_id:
                            continue
                        if user_id not in approver_ids:
                            approver_ids.append(user_id)
                            approver_info[user_id] = {
                                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                                "role": role_id_str,
                            }
                except (ValueError, TypeError) as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Invalid role ID '{role_id_str}': {e}")
        
        # Limit to max approvers if configured
        if config.max_approvers and len(approver_ids) > config.max_approvers:
            approver_ids = approver_ids[:config.max_approvers]
        
        # 5. Assign approvers via engine
        if approver_ids:
            await self._engine.assign_approvers(request, config, approver_ids, approver_info)
        else:
            import logging
            logging.getLogger(__name__).warning(
                f"No approvers found for request {request.id} with role_ids {role_ids}"
            )
        
        return request

    async def get_approval_request(self, request_id: UUID, include_history: bool = False):
        req = await self._request_repo.get_by_id(request_id, include_history=include_history)
        if not req:
             raise NotFoundError("Approval request not found")
        return req

    async def get_approval_by_entity(self, entity_type: str, entity_id: UUID):
        return await self._request_repo.get_by_entity(entity_type, entity_id)

    async def get_pending_approvals(self, approver_id: UUID, entity_type: Optional[str] = None, include_all: bool = False):
        if include_all:
             items = await self._request_repo.get_all_pending(entity_type)
        else:
            items = await self._request_repo.get_pending_for_approver(approver_id, entity_type)
        
        # Convert and map to schema
        results = []
        now = datetime.utcnow().replace(tzinfo=None) # naive comparison if db is naive, or use timezone aware if needed
        # Assuming created_at is timezone aware, let's just make sure we handle it.
        # Ideally import timezone from datetime
        from datetime import timezone
        now_aware = datetime.now(timezone.utc)

        for item in (items or []):
            created_at = item.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            days = (now_aware - created_at).days
            
            results.append({
                "request_id": item.id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "entity_ref": item.entity_ref,
                "title": item.title,
                "description": item.description,
                "requester_name": item.requester_name,
                "approval_level": item.current_level,
                "is_urgent": False, # Basic logic for now
                "expires_at": item.expires_at,
                "days_pending": days,
                "created_at": item.created_at
            })
        
        # Return structure matching PendingApprovalsResponse schema
        return {
            "total": len(results),
            "urgent_count": 0,
            "items": results
        }


    async def get_archived_approvals(self, approver_id: UUID, status_filter: Optional[str] = None, entity_type: Optional[str] = None):
        decisions = await self._decision_repo.get_decided_by_approver(
             approver_id, 
             status_filter=status_filter, 
             entity_type=entity_type
        )
        
        items = []
        for d in decisions:
            # Load request details (eager loaded in repo but good to be safe)
            req = d.approval_request
            if not req:
                continue
                
            items.append({
                "request_id": req.id,
                "entity_type": req.entity_type,
                "entity_id": req.entity_id,
                "entity_ref": req.entity_ref,
                "title": req.title,
                "description": req.description,
                "requester_name": req.requester_name,
                "decision": d.decision,
                "decision_notes": d.decision_notes,
                "decided_at": d.decided_at,
                "created_at": req.created_at,
            })
            
        return {
            "total": len(items),
            "items": items
        }

    async def get_pending_count(self, approver_id: UUID):
        counts = await self._request_repo.count_pending_for_approver(approver_id)
        
        # Extract total which is included in the counts dict
        total = counts.pop("total", 0)
        
        return {
            "total": total,
            "urgent": 0,  # TODO: implement urgent count based on expires_at
            "by_type": counts
        }

