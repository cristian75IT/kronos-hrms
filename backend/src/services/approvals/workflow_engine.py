"""
KRONOS Approval Service - Workflow Engine.

Core engine for processing approval workflows.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from .models import (
    WorkflowConfig,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalHistory,
    ApprovalReminder,
    ApprovalMode,
    ExpirationAction,
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

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Enterprise workflow engine for processing approvals.
    
    Handles:
    - Workflow selection based on conditions
    - Approver assignment
    - Decision processing
    - Status updates
    - Expiration handling
    """
    
    def __init__(
        self,
        config_repo: WorkflowConfigRepository,
        request_repo: ApprovalRequestRepository,
        decision_repo: ApprovalDecisionRepository,
        history_repo: ApprovalHistoryRepository,
        reminder_repo: ApprovalReminderRepository,
    ):
        self._config_repo = config_repo
        self._request_repo = request_repo
        self._decision_repo = decision_repo
        self._history_repo = history_repo
        self._reminder_repo = reminder_repo
    
    # ═══════════════════════════════════════════════════════════
    # Workflow Selection
    # ═══════════════════════════════════════════════════════════
    
    async def select_workflow(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
    ) -> Optional[WorkflowConfig]:
        """
        Select the best matching workflow for an entity.
        
        Evaluates conditions and returns the highest priority match.
        """
        configs = await self._config_repo.get_active_by_entity_type(entity_type)
        
        for config in configs:
            if await self._evaluate_conditions(config.conditions, entity_data):
                logger.info(f"Selected workflow '{config.name}' for {entity_type}")
                return config
        
        # Fallback to default
        default = await self._config_repo.get_default_for_entity_type(entity_type)
        if default:
            logger.info(f"Using default workflow '{default.name}' for {entity_type}")
            return default
        
        logger.warning(f"No workflow found for entity type: {entity_type}")
        return None
    
    async def _evaluate_conditions(
        self,
        conditions: Optional[Dict[str, Any]],
        entity_data: Dict[str, Any],
    ) -> bool:
        """Evaluate workflow conditions against entity data."""
        if not conditions:
            return True
        
        # Check amount conditions
        if "min_amount" in conditions:
            amount = entity_data.get("amount", 0)
            if amount < conditions["min_amount"]:
                return False
        
        if "max_amount" in conditions:
            amount = entity_data.get("amount", 0)
            if amount > conditions["max_amount"]:
                return False
        
        # Check days conditions
        if "min_days" in conditions:
            days = entity_data.get("days", 0)
            if days < conditions["min_days"]:
                return False
        
        if "max_days" in conditions:
            days = entity_data.get("days", 0)
            if days > conditions["max_days"]:
                return False
        
        # Check entity subtypes
        if "entity_subtypes" in conditions:
            subtype = entity_data.get("subtype") or entity_data.get("leave_type")
            if subtype and subtype not in conditions["entity_subtypes"]:
                return False
        
        # Check departments
        if "departments" in conditions:
            dept = entity_data.get("department")
            if dept and dept not in conditions["departments"]:
                return False
        
        return True
    
    # ═══════════════════════════════════════════════════════════
    # Approver Assignment
    # ═══════════════════════════════════════════════════════════
    
    async def assign_approvers(
        self,
        request: ApprovalRequest,
        workflow: WorkflowConfig,
        approver_ids: Optional[List[UUID]] = None,
        approver_info: Optional[Dict[UUID, Dict[str, str]]] = None,
    ) -> List[ApprovalDecision]:
        """
        Assign approvers to an approval request.
        
        If approver_ids is provided, use those directly.
        Otherwise, this should be called after fetching approvers from AuthClient.
        """
        if not approver_ids:
            logger.warning(f"No approvers provided for request {request.id}")
            return []
        
        approver_info = approver_info or {}
        
        decisions = []
        for i, approver_id in enumerate(approver_ids):
            info = approver_info.get(approver_id, {})
            
            # Determine approval level
            if workflow.approval_mode == ApprovalMode.SEQUENTIAL.value:
                level = i + 1
            else:
                level = 1
            
            decision = ApprovalDecision(
                approval_request_id=request.id,
                approver_id=approver_id,
                approver_name=info.get("name"),
                approver_role=info.get("role"),
                approval_level=level,
            )
            decisions.append(decision)
        
        await self._decision_repo.create_bulk(decisions)
        
        # Update request tracking
        request.required_approvals = self._calculate_required_approvals(
            workflow, len(approver_ids)
        )
        request.max_level = max(d.approval_level for d in decisions)
        await self._request_repo.update(request)
        
        # Log history
        await self._history_repo.create(ApprovalHistory(
            approval_request_id=request.id,
            action=HistoryAction.ASSIGNED.value,
            actor_type="SYSTEM",
            details={
                "approver_count": len(approver_ids),
                "approver_ids": [str(a) for a in approver_ids],
            },
        ))
        
        logger.info(f"Assigned {len(decisions)} approvers to request {request.id}")
        return decisions
    
    def _calculate_required_approvals(
        self,
        workflow: WorkflowConfig,
        total_approvers: int,
    ) -> int:
        """Calculate how many approvals are needed."""
        mode = workflow.approval_mode
        
        if mode == ApprovalMode.ANY.value:
            return 1
        elif mode == ApprovalMode.ALL.value:
            return total_approvers
        elif mode == ApprovalMode.SEQUENTIAL.value:
            return total_approvers
        elif mode == ApprovalMode.MAJORITY.value:
            return (total_approvers // 2) + 1
        else:
            return workflow.min_approvers
    
    # ═══════════════════════════════════════════════════════════
    # Decision Processing
    # ═══════════════════════════════════════════════════════════
    
    async def process_decision(
        self,
        request: ApprovalRequest,
        approver_id: UUID,
        decision_type: str,
        notes: Optional[str] = None,
        delegated_to_id: Optional[UUID] = None,
        delegated_to_name: Optional[str] = None,
        override_authority: bool = False,
    ) -> ApprovalRequest:
        """
        Process an approver's decision.
        
        Updates the decision record and recalculates request status.
        Args:
            override_authority: If True, allows processing even if approver_id is not assigned (Admin override)
        """
        # Get the decision record
        decision = await self._decision_repo.get_by_request_and_approver(
            request.id, approver_id
        )
        
        # Admin Override Logic: If decision not found for this user, look for ANY pending decision at current level
        if not decision and override_authority:
            logger.info(f"Admin override for request {request.id} by {approver_id}")
            # Find pending decisions for current level
            pending_decisions = await self._decision_repo.get_pending_by_request(request.id)
            
            # Filter for current level if sequential
            workflow = await self._config_repo.get_by_id(request.workflow_config_id)
            if workflow and workflow.approval_mode == ApprovalMode.SEQUENTIAL.value:
                current_level_pending = [d for d in pending_decisions if d.approval_level == request.current_level]
                if current_level_pending:
                    decision = current_level_pending[0]
            elif pending_decisions:
                # Pick the first available pending decision
                decision = pending_decisions[0]
                
            if decision:
                notes = f"[ADMIN OVERRIDE by {approver_id}] {notes or ''}"
        
        if not decision:
            raise ValueError(f"Approver {approver_id} is not assigned to this request")
        
        if decision.decision:
            raise ValueError("Decision already made")
        
        if request.status != ApprovalStatus.PENDING.value:
            raise ValueError(f"Request is not pending (status: {request.status})")
        
        # For sequential mode, check if it's this approver's turn
        if not override_authority:
            workflow = await self._config_repo.get_by_id(request.workflow_config_id)
            if workflow and workflow.approval_mode == ApprovalMode.SEQUENTIAL.value:
                if decision.approval_level != request.current_level:
                    raise ValueError(
                        f"Not your turn. Current level: {request.current_level}, "
                        f"your level: {decision.approval_level}"
                    )
        
        # Update decision
        decision.decision = decision_type
        decision.decision_notes = notes
        decision.decided_at = datetime.utcnow()
        
        if decision_type == DecisionType.DELEGATED.value:
            decision.delegated_to_id = delegated_to_id
            decision.delegated_to_name = delegated_to_name
        
        await self._decision_repo.update(decision)
        
        # Log history
        await self._history_repo.create(ApprovalHistory(
            approval_request_id=request.id,
            action=decision_type,
            actor_id=approver_id,
            actor_type="USER",
            details={"notes": notes} if notes else None,
        ))
        
        # Update request counts and status
        await self._update_request_status(request, workflow, decision_type)
        
        return request
    
    async def _update_request_status(
        self,
        request: ApprovalRequest,
        workflow: Optional[WorkflowConfig],
        last_decision: str,
    ):
        """Update request status based on decisions."""
        if not workflow:
            workflow = await self._config_repo.get_by_id(request.workflow_config_id)
        
        mode = workflow.approval_mode if workflow else ApprovalMode.ANY.value
        
        # Count decisions
        pending_decisions = await self._decision_repo.get_pending_by_request(request.id)
        
        # Calculate current counts
        all_decisions = request.decisions if hasattr(request, 'decisions') else []
        approvals = sum(1 for d in all_decisions if d.decision in (DecisionType.APPROVED.value, DecisionType.APPROVED_CONDITIONAL.value))
        rejections = sum(1 for d in all_decisions if d.decision == DecisionType.REJECTED.value)
        has_conditional = any(d.decision == DecisionType.APPROVED_CONDITIONAL.value for d in all_decisions)
        
        request.received_approvals = approvals
        request.received_rejections = rejections
        
        # Determine new status
        new_status = None
        
        if mode == ApprovalMode.ANY.value:
            if last_decision in (DecisionType.APPROVED.value, DecisionType.APPROVED_CONDITIONAL.value):
                new_status = ApprovalStatus.APPROVED_CONDITIONAL.value if last_decision == DecisionType.APPROVED_CONDITIONAL.value else ApprovalStatus.APPROVED.value
            elif last_decision == DecisionType.REJECTED.value:
                new_status = ApprovalStatus.REJECTED.value
        
        elif mode == ApprovalMode.ALL.value:
            if rejections > 0:
                new_status = ApprovalStatus.REJECTED.value
            elif len(pending_decisions) == 0 and approvals >= request.required_approvals:
                new_status = ApprovalStatus.APPROVED_CONDITIONAL.value if has_conditional else ApprovalStatus.APPROVED.value
        
        elif mode == ApprovalMode.SEQUENTIAL.value:
            if last_decision == DecisionType.REJECTED.value:
                new_status = ApprovalStatus.REJECTED.value
            elif last_decision in (DecisionType.APPROVED.value, DecisionType.APPROVED_CONDITIONAL.value):
                # Check if there are more levels
                current_level_pending = [
                    d for d in pending_decisions
                    if d.approval_level == request.current_level
                ]
                if not current_level_pending:
                    if request.current_level < request.max_level:
                        # Move to next level
                        request.current_level += 1
                    else:
                        # All levels complete
                        new_status = ApprovalStatus.APPROVED_CONDITIONAL.value if has_conditional else ApprovalStatus.APPROVED.value
        
        elif mode == ApprovalMode.MAJORITY.value:
            total_decided = approvals + rejections
            total_approvers = len(all_decisions) if all_decisions else request.required_approvals * 2 - 1
            
            if approvals >= request.required_approvals:
                new_status = ApprovalStatus.APPROVED_CONDITIONAL.value if has_conditional else ApprovalStatus.APPROVED.value
            elif rejections > total_approvers - request.required_approvals:
                new_status = ApprovalStatus.REJECTED.value
        
        # Update status if resolved
        if new_status:
            request.status = new_status
            request.resolved_at = datetime.utcnow()
            
            # Delete pending reminders
            await self._reminder_repo.delete_for_request(request.id)
            
            logger.info(f"Request {request.id} resolved: {new_status}")
        
        await self._request_repo.update(request)
    
    # ═══════════════════════════════════════════════════════════
    # Expiration Handling
    # ═══════════════════════════════════════════════════════════
    
    async def handle_expiration(
        self,
        request: ApprovalRequest,
        workflow: Optional[WorkflowConfig] = None,
    ) -> ApprovalRequest:
        """
        Handle an expired approval request.
        
        Applies the configured expiration action.
        """
        if not workflow:
            workflow = await self._config_repo.get_by_id(request.workflow_config_id)
        
        action = workflow.expiration_action if workflow else ExpirationAction.REJECT.value
        
        logger.info(f"Handling expiration for request {request.id}, action: {action}")
        
        if action == ExpirationAction.REJECT.value:
            request.status = ApprovalStatus.EXPIRED.value
            request.resolved_at = datetime.utcnow()
            request.resolution_notes = "Scaduto automaticamente"
        
        elif action == ExpirationAction.AUTO_APPROVE.value:
            request.status = ApprovalStatus.APPROVED.value
            request.resolved_at = datetime.utcnow()
            request.resolution_notes = "Approvato automaticamente per scadenza"
        
        elif action == ExpirationAction.ESCALATE.value:
            request.status = ApprovalStatus.ESCALATED.value
            # Would need to assign new approvers from escalation role
            # This is handled by the expiration handler
        
        elif action == ExpirationAction.NOTIFY_ONLY.value:
            # Just mark that we processed it, keep pending
            request.expired_action_taken = True
            # Send notification (handled externally)
        
        request.expired_action_taken = True
        await self._request_repo.update(request)
        
        # Log history
        await self._history_repo.create(ApprovalHistory(
            approval_request_id=request.id,
            action=HistoryAction.EXPIRED.value,
            actor_type="SCHEDULER",
            details={
                "action_taken": action,
                "expired_at": datetime.utcnow().isoformat(),
            },
        ))
        
        # Delete reminders if resolved
        if request.status != ApprovalStatus.PENDING.value:
            await self._reminder_repo.delete_for_request(request.id)
        
        return request
    
    # ═══════════════════════════════════════════════════════════
    # Reminders
    # ═══════════════════════════════════════════════════════════
    
    async def schedule_reminders(
        self,
        request: ApprovalRequest,
        workflow: WorkflowConfig,
        approver_ids: List[UUID],
    ):
        """Schedule reminders for approvers."""
        if not workflow.send_reminders:
            return
        
        hours_before = workflow.reminder_hours_before or 24
        
        reminders = []
        for approver_id in approver_ids:
            # First reminder
            if request.expires_at:
                reminder_time = request.expires_at - timedelta(hours=hours_before)
                if reminder_time > datetime.utcnow():
                    reminders.append(ApprovalReminder(
                        approval_request_id=request.id,
                        approver_id=approver_id,
                        reminder_type="FIRST",
                        scheduled_at=reminder_time,
                    ))
                
                # Final reminder (2 hours before)
                final_reminder = request.expires_at - timedelta(hours=2)
                if final_reminder > datetime.utcnow():
                    reminders.append(ApprovalReminder(
                        approval_request_id=request.id,
                        approver_id=approver_id,
                        reminder_type="FINAL",
                        scheduled_at=final_reminder,
                    ))
        
        if reminders:
            await self._reminder_repo.create_bulk(reminders)
            logger.info(f"Scheduled {len(reminders)} reminders for request {request.id}")
