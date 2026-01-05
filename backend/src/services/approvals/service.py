"""
KRONOS Approval Service - Business Logic Layer.

Main service class for approval operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.clients import AuthClient, NotificationClient

from .models import (
    WorkflowConfig,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalHistory,
    ApprovalReminder,
    ApprovalStatus,
    DecisionType,
    HistoryAction,
)
from .repository import (
    WorkflowConfigRepository,
    ApprovalRequestRepository,
    ApprovalDecisionRepository,
    ApprovalHistoryRepository,
    ApprovalReminderRepository,
)
from .workflow_engine import WorkflowEngine
from .schemas import (
    WorkflowConfigCreate,
    WorkflowConfigUpdate,
    WorkflowConfigResponse,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalDecisionCreate,
    PendingApprovalItem,
    PendingApprovalsResponse,
    PendingCountResponse,
    ApprovalCallbackPayload,
    ApprovalStatusCheck,
)

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Main service for approval operations.
    
    Coordinates between repositories, workflow engine, and external services.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        
        # Repositories
        self._config_repo = WorkflowConfigRepository(session)
        self._request_repo = ApprovalRequestRepository(session)
        self._decision_repo = ApprovalDecisionRepository(session)
        self._history_repo = ApprovalHistoryRepository(session)
        self._reminder_repo = ApprovalReminderRepository(session)
        
        # Workflow engine
        self._engine = WorkflowEngine(
            self._config_repo,
            self._request_repo,
            self._decision_repo,
            self._history_repo,
            self._reminder_repo,
        )
        
        # External clients
        self._auth_client = AuthClient()
        self._notification_client = NotificationClient()
    
    # ═══════════════════════════════════════════════════════════
    # Workflow Configuration
    # ═══════════════════════════════════════════════════════════
    
    async def create_workflow_config(
        self,
        data: WorkflowConfigCreate,
        created_by: Optional[UUID] = None,
    ) -> WorkflowConfig:
        """Create a new workflow configuration."""
        config = WorkflowConfig(
            entity_type=data.entity_type,
            name=data.name,
            description=data.description,
            min_approvers=data.min_approvers,
            max_approvers=data.max_approvers,
            approval_mode=data.approval_mode,
            approver_role_ids=data.approver_role_ids,
            auto_assign_approvers=data.auto_assign_approvers,
            allow_self_approval=data.allow_self_approval,
            expiration_hours=data.expiration_hours,
            expiration_action=data.expiration_action,
            escalation_role_id=UUID(data.escalation_role_id) if data.escalation_role_id else None,
            reminder_hours_before=data.reminder_hours_before,
            send_reminders=data.send_reminders,
            conditions=data.conditions.model_dump() if data.conditions else None,
            priority=data.priority,
            is_active=data.is_active,
            is_default=data.is_default,
            created_by=created_by,
        )
        
        return await self._config_repo.create(config)
    
    async def get_workflow_config(self, config_id: UUID) -> Optional[WorkflowConfig]:
        """Get workflow config by ID."""
        return await self._config_repo.get_by_id(config_id)
    
    async def list_workflow_configs(
        self,
        entity_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[WorkflowConfig]:
        """List workflow configurations."""
        return await self._config_repo.list_all(
            entity_type=entity_type,
            active_only=active_only,
        )
    
    async def update_workflow_config(
        self,
        config_id: UUID,
        data: WorkflowConfigUpdate,
    ) -> Optional[WorkflowConfig]:
        """Update workflow configuration."""
        config = await self._config_repo.get_by_id(config_id)
        if not config:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "conditions" and value:
                value = value.model_dump() if hasattr(value, 'model_dump') else value
            if field == "escalation_role_id" and value:
                value = UUID(value) if isinstance(value, str) else value
            setattr(config, field, value)
        
        return await self._config_repo.update(config)
    
    async def delete_workflow_config(self, config_id: UUID) -> bool:
        """Deactivate workflow configuration."""
        return await self._config_repo.soft_delete(config_id)
    
    # ═══════════════════════════════════════════════════════════
    # Approval Requests
    # ═══════════════════════════════════════════════════════════
    
    async def create_approval_request(
        self,
        data: ApprovalRequestCreate,
    ) -> ApprovalRequest:
        """
        Create a new approval request.
        
        1. Selects appropriate workflow
        2. Creates the request
        3. Assigns approvers
        4. Schedules reminders
        5. Notifies approvers
        """
        # Check for existing request
        existing = await self._request_repo.get_by_entity(
            data.entity_type, data.entity_id
        )
        if existing and existing.status == ApprovalStatus.PENDING.value:
            logger.warning(f"Approval request already exists for {data.entity_type}/{data.entity_id}")
            return existing
        
        # Select workflow
        workflow = None
        if data.workflow_config_id:
            workflow = await self._config_repo.get_by_id(data.workflow_config_id)
        
        if not workflow:
            metadata = data.metadata or {}
            workflow = await self._engine.select_workflow(data.entity_type, metadata)
        
        if not workflow:
            raise ValueError(f"No workflow configured for entity type: {data.entity_type}")
        
        # Calculate expiration
        expires_at = None
        if workflow.expiration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=workflow.expiration_hours)
        
        # Create request
        request = ApprovalRequest(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            entity_ref=data.entity_ref,
            workflow_config_id=workflow.id,
            requester_id=data.requester_id,
            requester_name=data.requester_name,
            title=data.title,
            description=data.description,
            request_metadata=data.metadata,
            callback_url=data.callback_url,
            status=ApprovalStatus.PENDING.value,
            required_approvals=workflow.min_approvers,
            expires_at=expires_at,
        )
        
        request = await self._request_repo.create(request)
        
        # Log creation
        await self._history_repo.create(ApprovalHistory(
            approval_request_id=request.id,
            action=HistoryAction.CREATED.value,
            actor_id=data.requester_id,
            actor_name=data.requester_name,
            actor_type="USER",
        ))
        
        # Get approvers
        approver_ids = list(data.approver_ids) if data.approver_ids else []
        approver_info = {}
        
        if not approver_ids and workflow.approver_role_ids:
            # Fetch users with specified roles from auth service
            approver_ids, approver_info = await self._fetch_approvers_by_roles(
                workflow.approver_role_ids,
                requester_id=data.requester_id,
                exclude_user=data.requester_id if not workflow.allow_self_approval else None,
                max_approvers=workflow.max_approvers,
            )
        
        # Fallback: fetch approvers by is_approver flag if no role-based approvers found
        if not approver_ids and workflow.auto_assign_approvers:
            approver_ids, approver_info = await self._fetch_approvers_by_flag(
                exclude_user=data.requester_id if not workflow.allow_self_approval else None,
                max_approvers=workflow.max_approvers,
            )
        
        # Assign approvers
        if approver_ids:
            await self._engine.assign_approvers(
                request, workflow, approver_ids, approver_info
            )
            
            # Schedule reminders
            await self._engine.schedule_reminders(request, workflow, approver_ids)
            
            # Notify approvers
            await self._notify_approvers(request, approver_ids)
        else:
            logger.warning(f"No approvers found for request {request.id}")
        
        return request
    
    async def _fetch_approvers_by_roles(
        self,
        role_ids: List[str],
        requester_id: Optional[UUID] = None,
        exclude_user: Optional[UUID] = None,
        max_approvers: Optional[int] = None,
    ) -> tuple[List[UUID], Dict[UUID, Dict[str, str]]]:
        """Fetch users with specific roles from auth service."""
        try:
            approver_ids = []
            approver_info = {}
            
            # Separate roles by type
            dynamic_roles = [r for r in role_ids if str(r).startswith("DYNAMIC:")]
            executive_roles = [r for r in role_ids if str(r).startswith("EXECUTIVE_LEVEL:")]
            static_roles = [r for r in role_ids if not str(r).startswith("DYNAMIC:") and not str(r).startswith("EXECUTIVE_LEVEL:")]
            
            # 1. Process Static Roles (UUIDs) and Executive Levels
            if static_roles or executive_roles:
                users = await self._auth_client.get_users(active_only=True)
                
                for user in users:
                    user_id = UUID(user["id"]) if isinstance(user["id"], str) else user["id"]
                    
                    # Check if user should be excluded
                    if exclude_user and user_id == exclude_user:
                        continue
                    
                    # Check Static Roles
                    user_roles = user.get("roles", [])
                    user_role_ids = [r.get("id") if isinstance(r, dict) else r for r in user_roles]
                    role_match = any(str(rid) in [str(uid) for uid in user_role_ids] for rid in static_roles)
                    
                    # Check Executive Levels
                    exec_match = False
                    if executive_roles:
                        user_exec_level = user.get("executive_level_id")
                        if user_exec_level:
                            for er in executive_roles:
                                target_level_id = er.split(":")[1]
                                if str(user_exec_level) == target_level_id:
                                    exec_match = True
                                    break

                    if role_match or exec_match:
                        if user_id not in approver_ids:
                            approver_ids.append(user_id)
                            approver_info[user_id] = {
                                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                                "role": "Executive" if exec_match and not role_match else (user_roles[0].get("name") if user_roles and isinstance(user_roles[0], dict) else str(user_roles[0]) if user_roles else None),
                            }
            
            # 2. Process Dynamic Roles
            if dynamic_roles and requester_id:
                requester = await self._auth_client.get_user(requester_id)
                if requester:
                    for role in dynamic_roles:
                        target_id = None
                        role_name = "Approver"
                        
                        if role == "DYNAMIC:DEPARTMENT_MANAGER":
                            # Get requester's department
                            dept_id = requester.get("department_id")
                            if dept_id:
                                dept = await self._auth_client.get_department(dept_id)
                                if dept and dept.get("manager_id"):
                                    target_id = dept.get("manager_id")
                                    role_name = "Department Manager"
                                    
                        elif role == "DYNAMIC:SERVICE_COORDINATOR":
                             # Get requester's service
                            srv_id = requester.get("service_id")
                            if srv_id:
                                srv = await self._auth_client.get_service(srv_id)
                                if srv and srv.get("coordinator_id"):
                                    target_id = srv.get("coordinator_id")
                                    role_name = "Service Coordinator"
                        
                        # Add resolved approver if found
                        if target_id:
                            target_uuid = UUID(str(target_id)) if isinstance(target_id, str) else target_id
                            
                            if exclude_user and target_uuid == exclude_user:
                                continue
                                
                            if target_uuid not in approver_ids:
                                # Fetch target user details if not already known
                                if target_uuid not in approver_info:
                                    target_user = await self._auth_client.get_user(target_uuid)
                                    if target_user:
                                        approver_ids.append(target_uuid)
                                        approver_info[target_uuid] = {
                                            "name": f"{target_user.get('first_name', '')} {target_user.get('last_name', '')}".strip(),
                                            "role": role_name
                                        }

            # Limit approvers if max specified
            if max_approvers and len(approver_ids) > max_approvers:
                approver_ids = approver_ids[:max_approvers]
                
            return approver_ids, approver_info
        
        except Exception as e:
            logger.error(f"Error fetching approvers: {e}")
            return [], {}
    
    async def _fetch_approvers_by_flag(
        self,
        exclude_user: Optional[UUID] = None,
        max_approvers: Optional[int] = None,
    ) -> tuple[List[UUID], Dict[UUID, Dict[str, str]]]:
        """Fetch users with is_approver=true flag from auth service."""
        try:
            # Use the internal approvers endpoint (no auth required)
            users = await self._auth_client.get_approvers()
            
            approver_ids = []
            approver_info = {}
            
            for user in users:
                user_id = UUID(user["id"]) if isinstance(user["id"], str) else user["id"]
                
                # Check if user should be excluded
                if exclude_user and user_id == exclude_user:
                    continue
                
                approver_ids.append(user_id)
                # Use full_name if available, otherwise construct from first/last
                name = user.get("full_name")
                if not name:
                    name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                
                approver_info[user_id] = {
                    "name": name,
                    "role": "Approver",
                }
                
                # Limit approvers if max specified
                if max_approvers and len(approver_ids) >= max_approvers:
                    break
            
            logger.info(f"Found {len(approver_ids)} approvers by flag")
            return approver_ids, approver_info
        
        except Exception as e:
            logger.error(f"Error fetching approvers by flag: {e}")
            return [], {}
    
    async def _notify_approvers(
        self,
        request: ApprovalRequest,
        approver_ids: List[UUID],
    ):
        """Send notifications to approvers."""
        try:
            # Exclude requester if they are in the approver list
            # They already got a "submission" notification from the source service
            target_ids = [uid for uid in approver_ids if uid != request.requester_id]
            
            for approver_id in target_ids:
                await self._notification_client.send_notification(
                    user_id=approver_id,
                    title="Nuova Approvazione Richiesta",
                    message=f"Hai una nuova richiesta da approvare: {request.title}",
                    notification_type="APPROVAL_REQUEST",
                    data={
                        "approval_request_id": str(request.id),
                        "entity_type": request.entity_type,
                        "entity_id": str(request.entity_id),
                    },
                )
        except Exception as e:
            logger.error(f"Error notifying approvers: {e}")
    
    async def get_approval_request(
        self,
        request_id: UUID,
        include_history: bool = False,
    ) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        return await self._request_repo.get_by_id(
            request_id,
            include_decisions=True,
            include_history=include_history,
        )
    
    async def get_approval_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> Optional[ApprovalRequest]:
        """Get approval request by entity."""
        return await self._request_repo.get_by_entity(entity_type, entity_id)
    
    async def cancel_approval_request(
        self,
        request_id: UUID,
        cancelled_by: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """Cancel an approval request."""
        request = await self._request_repo.get_by_id(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING.value:
            raise ValueError("Can only cancel pending requests")
        
        request.status = ApprovalStatus.CANCELLED.value
        request.resolved_at = datetime.utcnow()
        request.resolution_notes = reason
        
        await self._request_repo.update(request)
        
        # Log history
        await self._history_repo.create(ApprovalHistory(
            approval_request_id=request.id,
            action=HistoryAction.CANCELLED.value,
            actor_id=cancelled_by,
            actor_type="USER",
            details={"reason": reason} if reason else None,
        ))
        
        # Delete reminders
        await self._reminder_repo.delete_for_request(request.id)
        
        # Trigger callback
        await self._send_callback(request)
        
        return True
    
    # ═══════════════════════════════════════════════════════════
    # Approver Actions
    # ═══════════════════════════════════════════════════════════
    
    async def get_pending_approvals(
        self,
        approver_id: UUID,
        entity_type: Optional[str] = None,
        include_all: bool = False,
    ) -> PendingApprovalsResponse:
        """Get pending approvals for an approver."""
        if include_all:
             requests = await self._request_repo.get_all_pending(entity_type)
        else:
             requests = await self._request_repo.get_pending_for_approver(
                approver_id, entity_type
            )
        
        from datetime import timezone
        now = datetime.now(timezone.utc)
        items = []
        urgent_count = 0
        
        for req in requests:
            is_urgent = False
            if req.expires_at:
                hours_remaining = (req.expires_at - now).total_seconds() / 3600
                is_urgent = hours_remaining < 24
            
            if is_urgent:
                urgent_count += 1
            
            days_pending = (now - req.created_at).days
            
            items.append(PendingApprovalItem(
                request_id=req.id,
                entity_type=req.entity_type,
                entity_id=req.entity_id,
                entity_ref=req.entity_ref,
                title=req.title,
                description=req.description,
                requester_name=req.requester_name,
                approval_level=req.current_level,
                is_urgent=is_urgent,
                expires_at=req.expires_at,
                days_pending=days_pending,
                created_at=req.created_at,
            ))
        
        return PendingApprovalsResponse(
            total=len(items),
            urgent_count=urgent_count,
            items=items,
        )
    
    async def get_pending_count(self, approver_id: UUID) -> PendingCountResponse:
        """Get count of pending approvals."""
        counts = await self._request_repo.count_pending_for_approver(approver_id)
        
        # Calculate urgent (would need additional query, simplify for now)
        return PendingCountResponse(
            total=counts.get("total", 0),
            urgent=0,  # Would need separate calculation
            by_type={k: v for k, v in counts.items() if k != "total"},
        )
    
    async def get_archived_approvals(
        self,
        approver_id: UUID,
        status_filter: Optional[str] = None,
        entity_type: Optional[str] = None,
    ):
        """Get archived (decided) approvals for an approver."""
        from .schemas import ArchivedApprovalItem, ArchivedApprovalsResponse
        
        decisions = await self._decision_repo.get_decided_by_approver(
            approver_id, status_filter, entity_type
        )
        
        items = []
        for decision in decisions:
            request = decision.approval_request
            if not request:
                continue
            
            items.append(ArchivedApprovalItem(
                request_id=request.id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                entity_ref=request.entity_ref,
                title=request.title,
                description=request.description,
                requester_name=request.requester_name,
                decision=decision.decision,
                decision_notes=decision.decision_notes,
                decided_at=decision.decided_at,
                created_at=request.created_at,
            ))
        
        return ArchivedApprovalsResponse(
            total=len(items),
            items=items,
        )
    
    async def approve_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """Approve a request."""
        request = await self._request_repo.get_by_id(request_id, include_decisions=True)
        if not request:
            raise ValueError("Approval request not found")
        
        request = await self._engine.process_decision(
            request, approver_id, DecisionType.APPROVED.value, notes
        )
        
        # If resolved, trigger callback
        if request.status != ApprovalStatus.PENDING.value:
            await self._send_callback(request)
        
        return request

    async def approve_conditional_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        condition_type: str,
        condition_details: str,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """Approve a request with conditions."""
        request = await self._request_repo.get_by_id(request_id, include_decisions=True)
        if not request:
            raise ValueError("Approval request not found")
        
        # Store conditions in notes/details if needed, but the engine handles the status
        # For now we'll put them in notes if not provided, or we can use the details param of process_decision if we add it
        combined_notes = f"[CONDITION: {condition_type}] {condition_details}"
        if notes:
            combined_notes += f"\nNotes: {notes}"
        
        # We need to pass the conditions to the callback, so we might want to store them in the decision or request metadata
        # Let's update the decision metadata or just pass them through the request
        
        request = await self._engine.process_decision(
            request, approver_id, DecisionType.APPROVED_CONDITIONAL.value, combined_notes
        )
        
        # Store conditions in request metadata for the callback
        if not request.request_metadata:
            request.request_metadata = {}
        request.request_metadata["condition_type"] = condition_type
        request.request_metadata["condition_details"] = condition_details
        await self._request_repo.update(request)
        
        # If resolved, trigger callback
        if request.status != ApprovalStatus.PENDING.value:
            await self._send_callback(request)
        
        return request
    
    async def reject_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """Reject a request."""
        request = await self._request_repo.get_by_id(request_id, include_decisions=True)
        if not request:
            raise ValueError("Approval request not found")
        
        request = await self._engine.process_decision(
            request, approver_id, DecisionType.REJECTED.value, notes
        )
        
        # If resolved, trigger callback
        if request.status != ApprovalStatus.PENDING.value:
            await self._send_callback(request)
        
        return request
    
    async def delegate_request(
        self,
        request_id: UUID,
        approver_id: UUID,
        delegate_to_id: UUID,
        delegate_to_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """Delegate approval to another user."""
        request = await self._request_repo.get_by_id(request_id, include_decisions=True)
        if not request:
            raise ValueError("Approval request not found")
        
        # Get delegate info if not provided
        if not delegate_to_name:
            try:
                user = await self._auth_client.get_user(delegate_to_id)
                if user:
                    delegate_to_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            except Exception:
                pass
        
        # Process delegation
        request = await self._engine.process_decision(
            request, approver_id, DecisionType.DELEGATED.value, notes,
            delegated_to_id=delegate_to_id, delegated_to_name=delegate_to_name
        )
        
        # Create new decision for delegate
        decision = await self._decision_repo.get_by_request_and_approver(
            request_id, approver_id
        )
        
        new_decision = ApprovalDecision(
            approval_request_id=request_id,
            approver_id=delegate_to_id,
            approver_name=delegate_to_name,
            approval_level=decision.approval_level if decision else 1,
        )
        await self._decision_repo.create(new_decision)
        
        # Notify delegate
        await self._notify_approvers(request, [delegate_to_id])
        
        return request
    
    # ═══════════════════════════════════════════════════════════
    # Callbacks
    # ═══════════════════════════════════════════════════════════
    
    async def _send_callback(self, request: ApprovalRequest):
        """Send callback to originating service."""
        if not request.callback_url:
            return
        
        # Refresh decisions
        request = await self._request_repo.get_by_id(request.id, include_decisions=True)
        
        payload = ApprovalCallbackPayload(
            approval_request_id=request.id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            status=request.status,
            resolved_at=request.resolved_at or datetime.utcnow(),
            resolution_notes=request.resolution_notes,
            final_decision_by=request.final_decision_by,
            condition_type=request.request_metadata.get("condition_type") if request.request_metadata else None,
            condition_details=request.request_metadata.get("condition_details") if request.request_metadata else None,
            decisions=[
                {
                    "id": d.id,
                    "approval_request_id": d.approval_request_id,
                    "approver_id": d.approver_id,
                    "approver_name": d.approver_name,
                    "approver_role": d.approver_role,
                    "approval_level": d.approval_level,
                    "decision": d.decision,
                    "decision_notes": d.decision_notes,
                    "delegated_to_id": d.delegated_to_id,
                    "delegated_to_name": d.delegated_to_name,
                    "assigned_at": d.assigned_at,
                    "decided_at": d.decided_at,
                }
                for d in request.decisions
            ],
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    request.callback_url,
                    json=payload.model_dump(mode="json"),
                    timeout=10.0,
                )
                logger.info(f"Callback sent to {request.callback_url}: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send callback: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # Status Checks
    # ═══════════════════════════════════════════════════════════
    
    async def check_approval_status(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> ApprovalStatusCheck:
        """Check if an entity has a pending approval."""
        request = await self._request_repo.get_by_entity(entity_type, entity_id)
        
        if not request:
            return ApprovalStatusCheck(
                entity_type=entity_type,
                entity_id=entity_id,
                has_pending_request=False,
            )
        
        return ApprovalStatusCheck(
            entity_type=entity_type,
            entity_id=entity_id,
            has_pending_request=request.status == ApprovalStatus.PENDING.value,
            approval_request_id=request.id,
            status=request.status,
            required_approvals=request.required_approvals,
            received_approvals=request.received_approvals,
        )
