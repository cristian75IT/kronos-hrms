"""
KRONOS - Leave Workflow Service

Approval workflow operations for leave requests.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
import logging

from src.core.exceptions import BusinessRuleError
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus
from src.services.leaves.schemas import (
    ApproveRequest,
    ApproveConditionalRequest,
    RejectRequest,
    AcceptConditionRequest,
    CancelRequest,
)
from src.services.leaves.services.base import BaseLeaveService

logger = logging.getLogger(__name__)


class LeaveWorkflowService(BaseLeaveService):
    """
    Workflow operations for leave requests.
    
    Handles state transitions:
    - Submit (DRAFT → PENDING/APPROVED)
    - Approve (PENDING → APPROVED)
    - Conditional Approve (PENDING → APPROVED_CONDITIONAL)
    - Accept Condition (APPROVED_CONDITIONAL → APPROVED/CANCELLED)
    - Reject (PENDING → REJECTED)
    - Revoke (APPROVED → REJECTED)
    - Reopen (REJECTED/CANCELLED → PENDING)
    - Cancel (any → CANCELLED)
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # Submit Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def submit_request(
        self,
        id: UUID,
        user_id: UUID,
    ) -> LeaveRequest:
        """Submit a draft request for approval."""
        request = await self._get_request(id)
        
        if request.status != LeaveRequestStatus.DRAFT:
            raise BusinessRuleError("Only draft requests can be submitted")
        
        if request.user_id != user_id:
            raise BusinessRuleError("Cannot submit another user's request")
        
        # Validate against policies
        validation = await self._policy_engine.validate_request(
            user_id=user_id,
            leave_type_id=request.leave_type_id,
            start_date=request.start_date,
            end_date=request.end_date,
            days_requested=request.days_requested,
            exclude_request_id=request.id,
        )
        
        if not validation.is_valid:
            raise BusinessRuleError(
                "\n".join(validation.errors),
                rule="POLICY_VALIDATION",
                details={"errors": validation.errors, "warnings": validation.warnings},
            )
        
        # Update status
        new_status = (
            LeaveRequestStatus.PENDING
            if validation.requires_approval
            else LeaveRequestStatus.APPROVED
        )
        
        await self._request_repo.update(
            id,
            status=new_status,
            policy_violations={"warnings": validation.warnings} if validation.warnings else None,
            deduction_details=validation.balance_breakdown,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=LeaveRequestStatus.DRAFT,
            to_status=new_status,
            changed_by=user_id,
        )
        
        # If requires approval, create approval request
        if validation.requires_approval:
            try:
                # Get requester name
                user_info = await self._auth_client.get_user_info(user_id)
                requester_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() if user_info else None
                
                # Create approval request
                await self._approval_client.create_request(
                    entity_type="LEAVE",
                    entity_id=id,
                    requester_id=user_id,
                    title=f"Richiesta ferie: {request.start_date} - {request.end_date}",
                    entity_ref=request.leave_type_code,
                    requester_name=requester_name,
                    description=request.employee_notes,
                    metadata={
                        "days_requested": float(request.days_requested),
                        "leave_type_id": str(request.leave_type_id),
                    },
                    callback_url=f"http://leave-service:8002/api/v1/leaves/internal/approval-callback/{id}",
                )
            except Exception as e:
                # Revert status to DRAFT
                logger.error(f"Failed to create approval request: {e}. Reverting to DRAFT.")
                
                await self._request_repo.update(
                    id,
                    status=LeaveRequestStatus.DRAFT,
                )
                
                await self._request_repo.add_history(
                    leave_request_id=id,
                    from_status=new_status,
                    to_status=LeaveRequestStatus.DRAFT,
                    changed_by=user_id,
                    notes=f"System rollback: Failed to create approval request. Error: {str(e)}"
                )
                
                raise BusinessRuleError(
                    f"Failed to initiate approval process: {str(e)}",
                    rule="APPROVAL_CREATION_FAILED"
                )
        
        # If auto-approved, deduct balance
        if new_status == LeaveRequestStatus.APPROVED:
            metadata = {
                "request_date": request.created_at.isoformat(),
                "approved_at": datetime.utcnow().isoformat(),
                "approver_id": str(user_id) if user_id else None,
                "approver_name": "Sistema (Auto-approvazione)",
                "notes": "Auto-approved by policy",
            }
            await self._deduct_balance(request, validation.balance_breakdown, metadata=metadata)
        
        # Send notification
        await self._notifier.notify_submission(request)

        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="SUBMIT",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Submitted leave request {id}",
        )
        
        return await self._get_request(id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Approval Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def approve_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveRequest,
        metadata: Optional[dict] = None,
    ) -> LeaveRequest:
        """
        Approve a pending request.
        
        NOTE: This method is now only called internally via the approval callback
        from the Central Approvals Service.
        """
        request = await self._get_request(id)
        
        if request.status == LeaveRequestStatus.DRAFT:
            raise BusinessRuleError("Non è possibile approvare una bozza")
        
        old_status = request.status
        if old_status == LeaveRequestStatus.APPROVED:
            return request  # Already approved
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.APPROVED,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=old_status,
            to_status=LeaveRequestStatus.APPROVED,
            changed_by=approver_id,
            reason=data.notes,
        )
        
        # Audit Log
        await self._audit.log_action(
            user_id=approver_id,
            action="APPROVE",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Approved leave request {id}",
            request_data=data.model_dump(mode="json"),
        )
        
        # Deduct balance only if newly approved
        if old_status != LeaveRequestStatus.APPROVED:
            await self._deduct_balance(request, request.deduction_details or {}, metadata=metadata)
        
        # Send notification
        await self._notifier.notify_approved(request)
        
        return await self._get_request(id)
    
    async def approve_conditional(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveConditionalRequest,
    ) -> LeaveRequest:
        """Approve with conditions."""
        request = await self._get_request(id)
        
        if request.status != LeaveRequestStatus.PENDING:
            raise BusinessRuleError("Only pending requests can be approved")
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.APPROVED_CONDITIONAL,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
            has_conditions=True,
            condition_type=data.condition_type,
            condition_details=data.condition_details,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=LeaveRequestStatus.PENDING,
            to_status=LeaveRequestStatus.APPROVED_CONDITIONAL,
            changed_by=approver_id,
            reason=f"{data.condition_type.value}: {data.condition_details}",
        )
        
        # Send notification to employee for acceptance
        await self._notifier.notify_conditional_approval(request, data.condition_details)

        # Audit Log
        await self._audit.log_action(
            user_id=approver_id,
            action="APPROVE_CONDITIONAL",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Conditionally approved leave request {id}",
            request_data=data.model_dump(mode="json"),
        )
        
        return await self._get_request(id)
    
    async def accept_condition(
        self,
        id: UUID,
        user_id: UUID,
        data: AcceptConditionRequest,
    ) -> LeaveRequest:
        """Employee accepts or rejects conditions."""
        request = await self._get_request(id)
        
        if request.status != LeaveRequestStatus.APPROVED_CONDITIONAL:
            raise BusinessRuleError("Request is not awaiting condition acceptance")
        
        if request.user_id != user_id:
            raise BusinessRuleError("Only the requester can accept/reject conditions")
        
        if data.accept:
            await self._request_repo.update(
                id,
                status=LeaveRequestStatus.APPROVED,
                condition_accepted=True,
                condition_accepted_at=datetime.utcnow(),
            )
            
            await self._request_repo.add_history(
                leave_request_id=id,
                from_status=LeaveRequestStatus.APPROVED_CONDITIONAL,
                to_status=LeaveRequestStatus.APPROVED,
                changed_by=user_id,
                reason="Conditions accepted",
            )
            
            # Deduct balance
            await self._deduct_balance(request, request.deduction_details or {})
        else:
            await self._request_repo.update(
                id,
                status=LeaveRequestStatus.CANCELLED,
                condition_accepted=False,
            )
            
            await self._request_repo.add_history(
                leave_request_id=id,
                from_status=LeaveRequestStatus.APPROVED_CONDITIONAL,
                to_status=LeaveRequestStatus.CANCELLED,
                changed_by=user_id,
                reason="Conditions rejected by employee",
            )
        
        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="ACCEPT_CONDITION" if data.accept else "REJECT_CONDITION",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"User {'accepted' if data.accept else 'rejected'} conditions for request {id}",
            request_data=data.model_dump(mode="json"),
        )
        
        return await self._get_request(id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Rejection Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def reject_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: RejectRequest,
    ) -> LeaveRequest:
        """
        Reject a pending request.
        
        NOTE: This method is now only called internally via the approval callback
        from the Central Approvals Service.
        """
        request = await self._get_request(id)
        
        if request.status == LeaveRequestStatus.DRAFT:
            raise BusinessRuleError("Non è possibile rifiutare una bozza")
        
        old_status = request.status
        if old_status == LeaveRequestStatus.REJECTED:
            return request  # Already rejected
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.REJECTED,
            approver_id=approver_id,
            approver_notes=data.reason,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=old_status,
            to_status=LeaveRequestStatus.REJECTED,
            changed_by=approver_id,
            reason=data.reason,
        )
        
        # Restore balance if it was deducted
        if old_status == LeaveRequestStatus.APPROVED:
            await self._restore_balance(request)
        
        # Send notification
        await self._notifier.notify_rejected(request, data.reason)

        # Audit Log
        await self._audit.log_action(
            user_id=approver_id,
            action="REJECT",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Rejected leave request {id}",
            request_data=data.model_dump(mode="json"),
        )
        
        return await self._get_request(id)
    
    async def revoke_approval(
        self,
        id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> LeaveRequest:
        """Revoke an approved request. Only allowed before start_date (Italian law compliance)."""
        request = await self._get_request(id)
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le richieste approvate possono essere revocate")
        
        # Check if request already started (legal deadline)
        if request.start_date <= date.today():
            raise BusinessRuleError(
                "Non è possibile revocare una richiesta già iniziata. "
                "Per le ferie in corso, contattare HR."
            )
        
        old_status = request.status
        
        # Restore balance if it was deducted
        if old_status == LeaveRequestStatus.APPROVED:
            await self._restore_balance(request)
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.REJECTED,
            rejection_reason=f"[REVOCATA] {reason}",
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=old_status,
            to_status=LeaveRequestStatus.REJECTED,
            changed_by=approver_id,
            reason=f"Approvazione revocata: {reason}",
        )
        
        # Notify employee
        await self._notifier.notify_revoked(request, reason)

        # Audit Log
        await self._audit.log_action(
            user_id=approver_id,
            action="REVOKE",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Revoked approval for leave request {id}",
            request_data={"reason": reason},
        )
        
        return await self._get_request(id)
    
    async def reopen_request(
        self,
        id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveRequest:
        """Reopen a rejected/cancelled request back to pending. Only before original start_date."""
        request = await self._get_request(id)
        
        if request.status not in [LeaveRequestStatus.REJECTED, LeaveRequestStatus.CANCELLED]:
            raise BusinessRuleError("Solo le richieste rifiutate o annullate possono essere riaperte")
        
        # Check if request period has passed
        if request.start_date < date.today():
            raise BusinessRuleError(
                "Non è possibile riaprire una richiesta per date passate"
            )
        
        old_status = request.status
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.PENDING,
            rejection_reason=None,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=old_status,
            to_status=LeaveRequestStatus.PENDING,
            changed_by=approver_id,
            reason=notes or "Richiesta riaperta per revisione",
        )
        
        # Notify employee
        await self._notifier.notify_reopened(request)

        # Audit Log
        await self._audit.log_action(
            user_id=approver_id,
            action="REOPEN",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Reopened leave request {id}",
            request_data={"notes": notes},
        )
        
        return await self._get_request(id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Cancel Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def cancel_request(
        self,
        id: UUID,
        user_id: UUID,
        data: CancelRequest,
    ) -> LeaveRequest:
        """Cancel own request."""
        request = await self._get_request(id)
        
        if request.user_id != user_id:
            raise BusinessRuleError("Cannot cancel another user's request")
        
        if request.status not in [
            LeaveRequestStatus.DRAFT,
            LeaveRequestStatus.PENDING,
            LeaveRequestStatus.APPROVED,
        ]:
            raise BusinessRuleError("Cannot cancel request in current status")
        
        old_status = request.status
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.CANCELLED,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=old_status,
            to_status=LeaveRequestStatus.CANCELLED,
            changed_by=user_id,
            reason=data.reason,
        )
        
        # If was approved, restore balance
        if old_status == LeaveRequestStatus.APPROVED and request.balance_deducted:
            await self._restore_balance(request)
        
        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="CANCEL",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Cancelled leave request {id}",
            request_data=data.model_dump(mode="json"),
        )
        
        return await self._get_request(id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_request(self, id: UUID) -> LeaveRequest:
        """Get leave request by ID (internal use)."""
        from src.core.exceptions import NotFoundError
        request = await self._request_repo.get(id)
        if not request:
            raise NotFoundError("Leave request not found", entity_type="LeaveRequest", entity_id=str(id))
        return request
    
    async def _deduct_balance(
        self,
        request: LeaveRequest,
        breakdown: dict,
        metadata: Optional[dict] = None,
    ) -> None:
        """Deduct balance based on breakdown."""
        await self._balance_service.deduct_balance(request, breakdown, metadata=metadata)
        await self._request_repo.update(request.id, balance_deducted=True)
    
    async def _restore_balance(self, request: LeaveRequest) -> None:
        """Restore balance when request is cancelled/recalled."""
        await self._balance_service.restore_balance(request)
        await self._request_repo.update(request.id, balance_deducted=False)
