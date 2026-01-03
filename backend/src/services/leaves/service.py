from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, or_, func, and_
from sqlalchemy.orm import selectinload, contains_eager
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import (
    NotFoundError,
    ConflictError,
    BusinessRuleError,
    ValidationError,
)
from src.services.auth.models import EmployeeContract, ContractType, User, UserProfile
from src.services.config.models import NationalContract, NationalContractVersion, NationalContractTypeConfig
from src.services.leaves.models import (
    LeaveRequest, 
    LeaveRequestStatus, 
    ConditionType,
    LeaveInterruption,
    ApprovalDelegation,
    BalanceReservation,
)
from src.services.leaves.repository import LeaveRequestRepository
from src.services.leaves.policy_engine import PolicyEngine
from src.services.leaves.strategies import StrategyFactory
from src.services.leaves.schemas import (
    LeaveRequestCreate,
    LeaveRequestUpdate,
    ApproveRequest,
    ApproveConditionalRequest,
    RejectRequest,
    AcceptConditionRequest,
    CancelRequest,
    RecallRequest,
    BalanceSummary,
    BalanceAdjustment,
    CalendarRequest,
    CalendarEvent,
    CalendarResponse,
    DaysCalculationRequest,
    DaysCalculationResponse,
    DailyAttendanceRequest,
    DailyAttendanceResponse,
    DailyAttendanceItem,
    AggregateReportRequest,
    AggregateReportResponse,
    AggregateReportItem,
    # Enterprise schemas
    PartialRecallRequest,
    SicknessInterruptionRequest,
    ModifyApprovedRequest,
    VoluntaryWorkRequest,
)
from src.shared.schemas import DataTableRequest
from src.shared.audit_client import get_audit_logger
from src.shared.clients import AuthClient, ConfigClient, NotificationClient
from src.services.leaves.calendar_utils import CalendarUtils
from src.services.leaves.report_service import LeaveReportService
from src.services.leaves.balance_service import LeaveBalanceService
from src.services.leaves.notification_handler import LeaveNotificationHandler




class LeaveService:
    """Service for leave request management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._request_repo = LeaveRequestRepository(session)


        self._audit = get_audit_logger("leave-service")
        
        # Shared Clients
        from src.shared.clients import AuthClient, ConfigClient, NotificationClient, LeavesWalletClient as WalletClient
        self._auth_client = AuthClient()
        self._config_client = ConfigClient()
        self._wallet_client = WalletClient()

        self._notifier = LeaveNotificationHandler()
        self._calendar_utils = CalendarUtils(self._config_client)
        self._balance_service = LeaveBalanceService(session, self._wallet_client)
        
        self._policy_engine = PolicyEngine(
            session,
            self._request_repo,
            self._balance_service,
            config_client=self._config_client,
        )





    # ═══════════════════════════════════════════════════════════
    # Leave Request Operations
    # ═══════════════════════════════════════════════════════════

    async def get_request(self, id: UUID) -> LeaveRequest:
        """Get leave request by ID."""
        request = await self._request_repo.get(id)
        if not request:
            raise NotFoundError("Leave request not found", entity_type="LeaveRequest", entity_id=str(id))
        return request

    async def get_user_requests(
        self,
        user_id: UUID,
        year: Optional[int] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
    ) -> list[LeaveRequest]:
        """Get requests for a user."""
        return await self._request_repo.get_by_user(user_id, year, status)

    async def get_pending_approval(
        self,
        approver_id: Optional[UUID] = None,
    ) -> list[LeaveRequest]:
        """Get requests pending approval."""
        return await self._request_repo.get_pending_approval(approver_id)

    async def get_requests_datatable(
        self,
        request: DataTableRequest,
        user_id: Optional[UUID] = None,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
    ):
        """Get requests for DataTable."""
        return await self._request_repo.get_datatable(request, user_id, status, year)

    async def get_all_requests(
        self,
        status: Optional[list[LeaveRequestStatus]] = None,
        year: Optional[int] = None,
        limit: int = 50,
    ) -> list[LeaveRequest]:
        """Get all requests with optional filters (for approval history)."""
        return await self._request_repo.get_all(status=status, year=year, limit=limit)

    async def create_request(
        self,
        user_id: UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request (as draft)."""
        # Get leave type info
        leave_type = await self._config_client.get_leave_type(data.leave_type_id)
        if not leave_type:
            raise ValidationError("Leave type not found", field="leave_type_id")
        
        # Check for overlapping requests (approved or pending)
        overlapping = await self._request_repo.check_overlap(
            user_id=user_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        if overlapping:
            overlap_info = overlapping[0]
            raise BusinessRuleError(
                f"Esiste già una richiesta di ferie ({overlap_info.leave_type_code}) "
                f"dal {overlap_info.start_date.strftime('%d/%m/%Y')} al {overlap_info.end_date.strftime('%d/%m/%Y')} "
                f"che si sovrappone a queste date. Stato: {overlap_info.status.value}",
                rule="OVERLAP_EXISTING",
            )

        # Validate protocol requirement (INPS code for sick leave)
        if leave_type.get("requires_protocol") and not data.protocol_number:
            raise BusinessRuleError(
                f"Il codice iNPS (protocollo telematico) è obbligatorio per le richieste di {leave_type.get('name')}.",
                rule="PROTOCOL_REQUIRED"
            )

        
        # Calculate days
        days = await self._calculate_days(
            data.start_date,
            data.end_date,
            data.start_half_day,
            data.end_half_day,
            user_id,
        )
        
        # Create request
        request = await self._request_repo.create(
            user_id=user_id,
            leave_type_id=data.leave_type_id,
            leave_type_code=leave_type.get("code", ""),
            start_date=data.start_date,
            end_date=data.end_date,
            start_half_day=data.start_half_day,
            end_half_day=data.end_half_day,
            days_requested=days,
            employee_notes=data.employee_notes,
            protocol_number=data.protocol_number,
            status=LeaveRequestStatus.DRAFT,
        )

        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="LEAVE_REQUEST",
            resource_id=str(request.id),
            description=f"Created leave request {request.id}",
            request_data=data.model_dump(mode="json"),
        )
        
        # Add history
        await self._request_repo.add_history(
            leave_request_id=request.id,
            from_status=None,
            to_status=LeaveRequestStatus.DRAFT,
            changed_by=user_id,
        )
        
        return request

    async def update_request(
        self,
        id: UUID,
        user_id: UUID,
        data: LeaveRequestUpdate,
    ) -> LeaveRequest:
        """Update a draft request."""
        request = await self.get_request(id)
        
        # Only drafts can be updated
        if request.status != LeaveRequestStatus.DRAFT:
            raise BusinessRuleError(
                "Only draft requests can be updated",
                rule="DRAFT_ONLY",
            )
        
        # Only owner can update
        if request.user_id != user_id:
            raise BusinessRuleError("Cannot update another user's request")
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Recalculate days if dates changed
        if "start_date" in update_data or "end_date" in update_data:
            start = update_data.get("start_date", request.start_date)
            end = update_data.get("end_date", request.end_date)
            start_half = update_data.get("start_half_day", request.start_half_day)
            end_half = update_data.get("end_half_day", request.end_half_day)
            
            # Check for overlapping requests (exclude current request)
            overlapping = await self._request_repo.check_overlap(
                user_id=user_id,
                start_date=start,
                end_date=end,
                exclude_id=id,
            )
            if overlapping:
                overlap_info = overlapping[0]
                raise BusinessRuleError(
                    f"Esiste già una richiesta di ferie ({overlap_info.leave_type_code}) "
                    f"dal {overlap_info.start_date.strftime('%d/%m/%Y')} al {overlap_info.end_date.strftime('%d/%m/%Y')} "
                    f"che si sovrappone a queste date. Stato: {overlap_info.status.value}",
                    rule="OVERLAP_EXISTING",
                )
            
            update_data["days_requested"] = await self._calculate_days(
                start, end, start_half, end_half, user_id
            )
        
        # Re-validate protocol if leave type or protocol changed
        if "leave_type_id" in update_data or "protocol_number" in update_data:
            lt_id = update_data.get("leave_type_id", request.leave_type_id)
            protocol = update_data.get("protocol_number", request.protocol_number)
            
            leave_type = await self._config_client.get_leave_type(lt_id)
            if leave_type and leave_type.get("requires_protocol") and not protocol:
                raise BusinessRuleError(
                    f"Il codice iNPS (protocollo telematico) è obbligatorio per le richieste di {leave_type.get('name')}.",
                    rule="PROTOCOL_REQUIRED"
                )
        
        updated_request = await self._request_repo.update(id, **update_data)

        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Updated leave request {id}",
            request_data=update_data,
        )

        return updated_request


    async def submit_request(
        self,
        id: UUID,
        user_id: UUID,
    ) -> LeaveRequest:
        """Submit a draft request for approval."""
        request = await self.get_request(id)
        
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
        
        # If auto-approved, deduct balance
        if new_status == LeaveRequestStatus.APPROVED:
            await self._deduct_balance(request, validation.balance_breakdown)
        
        # Send notification
        # Send notification
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
        
        return await self.get_request(id)

    async def approve_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveRequest,
    ) -> LeaveRequest:
        """Approve a pending request."""
        request = await self.get_request(id)
        
        if request.status == LeaveRequestStatus.DRAFT:
            raise BusinessRuleError("Non è possibile approvare una bozza")
        
        old_status = request.status
        if old_status == LeaveRequestStatus.APPROVED:
            return request # Già approvata
        
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
            await self._deduct_balance(request, request.deduction_details or {})
        
        # Send notification
        # Send notification
        await self._notifier.notify_approved(request)
        
        return await self.get_request(id)

    async def approve_conditional(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveConditionalRequest,
    ) -> LeaveRequest:
        """Approve with conditions."""
        request = await self.get_request(id)
        
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
        # Send notification to employee for acceptance
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
        
        return await self.get_request(id)

    async def accept_condition(
        self,
        id: UUID,
        user_id: UUID,
        data: AcceptConditionRequest,
    ) -> LeaveRequest:
        """Employee accepts or rejects conditions."""
        request = await self.get_request(id)
        
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
        
        return await self.get_request(id)

    async def reject_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: RejectRequest,
    ) -> LeaveRequest:
        """Reject a pending request."""
        request = await self.get_request(id)
        
        if request.status == LeaveRequestStatus.DRAFT:
            raise BusinessRuleError("Non è possibile rifiutare una bozza")
        
        old_status = request.status
        if old_status == LeaveRequestStatus.REJECTED:
            return request # Già rifiutata
        
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
        # Send notification
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
        
        return await self.get_request(id)

    async def revoke_approval(
        self,
        id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> LeaveRequest:
        """Revoke an approved request. Only allowed before start_date (Italian law compliance)."""
        request = await self.get_request(id)
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le richieste approvate possono essere revocate")
        
        # Check if request already started (legal deadline)
        from datetime import date as dt_date
        if request.start_date <= dt_date.today():
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
        # Notify employee
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
        
        return await self.get_request(id)

    async def reopen_request(
        self,
        id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveRequest:
        """Reopen a rejected/cancelled request back to pending. Only before original start_date."""
        request = await self.get_request(id)
        
        if request.status not in [LeaveRequestStatus.REJECTED, LeaveRequestStatus.CANCELLED]:
            raise BusinessRuleError("Solo le richieste rifiutate o annullate possono essere riaperte")
        
        # Check if request period has passed
        from datetime import date as dt_date
        if request.start_date < dt_date.today():
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
        # Notify employee
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
        
        return await self.get_request(id)

    async def cancel_request(
        self,
        id: UUID,
        user_id: UUID,
        data: CancelRequest,
    ) -> LeaveRequest:
        """Cancel own request."""
        request = await self.get_request(id)
        
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
        
        return await self.get_request(id)

    async def recall_request(
        self,
        id: UUID,
        manager_id: UUID,
        data: RecallRequest,
    ) -> LeaveRequest:
        """
        Recall an employee from approved leave (richiamo in servizio).
        
        Italian Labor Law allows recall for justified business needs, especially
        when leave was approved with condition RIC (Riserva di Richiamo).
        
        This method:
        - Calculates days actually used before recall
        - Restores only unused days to balance
        - Tracks all details for audit/compensation
        """
        request = await self.get_request(id)
        
        # Can recall from APPROVED or APPROVED_CONDITIONAL
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError(
                "Solo le richieste approvate possono essere richiamate"
            )
        
        # Verify recall is during the leave period
        from datetime import date as dt_date
        today = dt_date.today()
        
        if data.recall_date < request.start_date:
            raise BusinessRuleError(
                "La data di rientro non può essere precedente all'inizio delle ferie"
            )
        
        if data.recall_date > request.end_date:
            raise BusinessRuleError(
                "La data di rientro non può essere successiva alla fine delle ferie. "
                "Usare la revoca invece."
            )
        
        # Check if leave has started
        if today < request.start_date:
            raise BusinessRuleError(
                "Le ferie non sono ancora iniziate. Usare la revoca invece del richiamo."
            )
        
        # Calculate days actually used before recall
        days_used = await self._calculate_days(
            start_date=request.start_date,
            end_date=data.recall_date - timedelta(days=1),  # Day before return
            start_half_day=request.start_half_day,
            end_half_day=False,  # Full day before return
            user_id=request.user_id,
        )
        
        # Make sure days_used is at least 0
        if days_used < 0:
            days_used = Decimal("0")
        
        days_to_restore = request.days_requested - days_used
        
        old_status = request.status
        
        # Update request
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.RECALLED,
            recalled_at=datetime.utcnow(),
            recall_reason=data.reason,
            recall_date=data.recall_date,
            days_used_before_recall=days_used,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=old_status,
            to_status=LeaveRequestStatus.RECALLED,
            changed_by=manager_id,
            reason=f"Richiamo in servizio: {data.reason}. Giorni goduti: {days_used}, Giorni da recuperare: {days_to_restore}",
        )
        
        # Restore only unused balance
        # Restore only unused balance
        if request.balance_deducted and days_to_restore > 0:
            await self._balance_service.restore_partial_balance(request, days_to_restore)
        
        # Send notification with compensation info
        await self._notifier.notify_recalled(request, data.reason, data.recall_date, days_used, days_to_restore)

        # Audit Log
        await self._audit.log_action(
            user_id=manager_id,
            action="RECALL",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Recalled employee from leave request {id}",
            request_data=data.model_dump(mode="json"),
        )
        
        return await self.get_request(id)
    


    
    async def delete_request(
        self,
        id: UUID,
        user_id: UUID,
    ) -> bool:
        """Delete a draft request."""
        request = await self.get_request(id)
        
        # Only drafts can be deleted
        if request.status != LeaveRequestStatus.DRAFT:
            raise BusinessRuleError(
                "Only draft requests can be deleted",
                rule="DRAFT_ONLY_DELETE",
            )
        
        # Only owner can delete
        if request.user_id != user_id:
            raise BusinessRuleError("Cannot delete another user's request")
            
        success = await self._request_repo.delete(id)
        
        if success:
            # Audit Log
            await self._audit.log_action(
                user_id=user_id,
                action="DELETE",
                resource_type="LEAVE_REQUEST",
                resource_id=str(id),
                description=f"Deleted draft leave request {id}",
            )
            
        return success

    async def calculate_preview(self, request: DaysCalculationRequest) -> DaysCalculationResponse:
        """Calculate days for a preview (no persistence)."""
        days = await self._calculate_days(
            request.start_date,
            request.end_date,
            request.start_half_day,
            request.end_half_day,
        )
        return DaysCalculationResponse(
            days=days,
            hours=days * Decimal("8"), # Approximation
            message=f"Calcolati {days} giorni lavorativi escludendo festività e chiusure."
        )

    async def _calculate_days(
        self,
        start_date: date,
        end_date: date,
        start_half: bool,
        end_half: bool,
        user_id: Optional[UUID] = None,
    ) -> Decimal:
        """Calculate working days between dates."""
        return await self._calendar_utils.calculate_working_days(
            start_date, end_date, start_half, end_half, user_id=user_id
        )
        


    async def _deduct_balance(
        self,
        request: LeaveRequest,
        breakdown: dict,
    ) -> None:
        """Deduct balance based on breakdown."""
        await self._balance_service.deduct_balance(request, breakdown)
        await self._request_repo.update(request.id, balance_deducted=True)



    async def _restore_balance(self, request: LeaveRequest) -> None:
        """Restore balance when request is cancelled/recalled."""
        await self._balance_service.restore_balance(request)
        await self._request_repo.update(request.id, balance_deducted=False)


    def _get_event_color(self, status: LeaveRequestStatus, leave_type: str) -> str:
        """Get color for calendar event."""
        status_colors = {
            LeaveRequestStatus.APPROVED: "#22C55E",       # Green
            LeaveRequestStatus.PENDING: "#F59E0B",        # Orange
            LeaveRequestStatus.APPROVED_CONDITIONAL: "#EAB308",  # Yellow
        }
        return status_colors.get(status, "#3B82F6")

    async def _get_subordinates(self, manager_id: UUID) -> list[UUID]:
        """Get subordinate user IDs from auth service."""
        return await self._auth_client.get_subordinates(manager_id)



    async def get_excluded_days(self, start_date: date, end_date: date, user_id: Optional[UUID] = None) -> dict:
        """Get list of excluded days (holidays/weekends) for UI."""
        return await self._calendar_utils.get_excluded_list(start_date, end_date, user_id=user_id)



    async def _get_user_info(self, user_id: UUID) -> Optional[dict]:
        """Get user info from auth service."""
        return await self._auth_client.get_user_info(user_id)


    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        return await self._auth_client.get_user_email(user_id)

    async def recalculate_for_closure(
        self,
        closure_start: date,
        closure_end: date,
    ) -> list[dict]:
        """
        Recalculate days_requested for approved leave requests that overlap with a new closure.
        
        When a company closure is added (or modified), any approved leave requests that
        overlap should have their days recalculated to exclude the closure days.
        
        Returns list of affected requests with their updated days.
        """
        from src.services.leaves.models import LeaveRequest, LeaveRequestStatus
        
        # Find all approved/approved_conditional requests that overlap with the closure dates
        stmt = select(LeaveRequest).where(
            LeaveRequest.status.in_([
                LeaveRequestStatus.APPROVED,
                LeaveRequestStatus.APPROVED_CONDITIONAL,
            ]),
            # Overlap check: request overlaps with closure if:
            # request.start_date <= closure_end AND request.end_date >= closure_start
            LeaveRequest.start_date <= closure_end,
            LeaveRequest.end_date >= closure_start,
        )
        
        result = await self._session.execute(stmt)
        affected_requests = result.scalars().all()
        
        updates = []
        
        for request in affected_requests:
            old_days = request.days_requested
            
            # Recalculate working days with the new closure
            new_days = await self._calculate_days(
                request.start_date,
                request.end_date,
                request.start_half_day,
                request.end_half_day,
                user_id=request.user_id,
            )
            
            if old_days != new_days:
                # Update the request
                request.days_requested = new_days
                if request.hours_requested is not None:
                    request.hours_requested = new_days * Decimal("8")
                
                # Log the update
                await self._audit.log_action(
                    user_id=None,  # System action
                    action="RECALCULATE",
                    resource_type="LEAVE_REQUEST",
                    resource_id=str(request.id),
                    description=f"Days recalculated due to closure: {old_days} -> {new_days}",
                    request_data={
                        "closure_start": closure_start.isoformat(),
                        "closure_end": closure_end.isoformat(),
                        "old_days": float(old_days),
                        "new_days": float(new_days),
                    },
                )
                
                updates.append({
                    "request_id": str(request.id),
                    "user_id": str(request.user_id),
                    "start_date": request.start_date.isoformat(),
                    "end_date": request.end_date.isoformat(),
                    "old_days": float(old_days),
                    "new_days": float(new_days),
                    "days_refunded": float(old_days - new_days),
                })
        
        await self._session.commit()
        
        return updates

    # ═══════════════════════════════════════════════════════════
    # Enterprise Features - Interruptions
    # ═══════════════════════════════════════════════════════════

    async def create_partial_recall(
        self,
        request_id: UUID,
        manager_id: UUID,
        data: PartialRecallRequest,
    ) -> LeaveInterruption:
        """
        Create a partial recall - employee works specific days during vacation.
        
        Unlike full recall which ends the vacation, this only interrupts specific days.
        The vacation continues after the recalled day(s).
        """
        request = await self.get_request(request_id)
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le richieste approvate possono essere richiamate")
        
        # Validate all recall days are within the leave period
        for day in data.recall_days:
            if day < request.start_date or day > request.end_date:
                raise BusinessRuleError(
                    f"Il giorno {day.isoformat()} non rientra nel periodo di ferie "
                    f"({request.start_date.isoformat()} - {request.end_date.isoformat()})"
                )
        
        # Calculate days to refund (each recalled day = 1 day refunded)
        days_to_refund = await self._calculate_recalled_days(data.recall_days, request.user_id)
        
        # Create interruption record
        interruption = LeaveInterruption(
            leave_request_id=request_id,
            interruption_type="PARTIAL_RECALL",
            start_date=min(data.recall_days),
            end_date=max(data.recall_days),
            specific_days=[d.isoformat() for d in data.recall_days],
            days_refunded=days_to_refund,
            initiated_by=manager_id,
            initiated_by_role="MANAGER",
            reason=data.reason,
            status="ACTIVE",
        )
        
        self._session.add(interruption)
        await self._session.flush()
        
        # Refund balance
        if request.balance_deducted and days_to_refund > 0:
            await self._balance_service.restore_partial_balance(request, days_to_refund)
            interruption.refund_transaction_id = None  # Would be set from wallet response
        
        # Mark request as having interruptions
        request.has_interruptions = True
        
        # Audit
        await self._audit.log_action(
            user_id=manager_id,
            action="PARTIAL_RECALL",
            resource_type="LEAVE_REQUEST",
            resource_id=str(request_id),
            description=f"Partial recall for {len(data.recall_days)} days",
            request_data={
                "recall_days": [d.isoformat() for d in data.recall_days],
                "days_refunded": float(days_to_refund),
                "reason": data.reason,
            },
        )
        
        return interruption

    async def create_sickness_interruption(
        self,
        request_id: UUID,
        user_id: UUID,
        data: SicknessInterruptionRequest,
    ) -> LeaveInterruption:
        """
        Record sickness during vacation.
        
        Per Italian law (Art. 6 D.Lgs 66/2003), sick days during vacation
        are NOT counted as vacation days. This creates an interruption
        record and refunds the sick days to the employee's balance.
        """
        request = await self.get_request(request_id)
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le ferie approvate possono essere interrotte")
        
        # Validate sick period is within leave period
        if data.sick_start_date < request.start_date or data.sick_end_date > request.end_date:
            raise BusinessRuleError(
                f"Il periodo di malattia deve rientrare nel periodo di ferie "
                f"({request.start_date.isoformat()} - {request.end_date.isoformat()})"
            )
        
        # Check for overlapping sickness interruptions
        existing = await self._session.execute(
            select(LeaveInterruption).where(
                and_(
                    LeaveInterruption.leave_request_id == request_id,
                    LeaveInterruption.interruption_type == "SICKNESS",
                    LeaveInterruption.status == "ACTIVE",
                    LeaveInterruption.start_date <= data.sick_end_date,
                    LeaveInterruption.end_date >= data.sick_start_date,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise BusinessRuleError("Esiste già una registrazione di malattia per questo periodo")
        
        # Calculate days to refund
        days_to_refund = await self._calculate_days(
            data.sick_start_date,
            data.sick_end_date,
            False,  # Full days
            False,
            request.user_id,
        )
        
        # Create interruption record
        interruption = LeaveInterruption(
            leave_request_id=request_id,
            interruption_type="SICKNESS",
            start_date=data.sick_start_date,
            end_date=data.sick_end_date,
            days_refunded=days_to_refund,
            protocol_number=data.protocol_number,
            attachment_path=data.attachment_path,
            initiated_by=user_id,
            initiated_by_role="EMPLOYEE",
            reason=data.notes,
            status="ACTIVE",
        )
        
        self._session.add(interruption)
        await self._session.flush()
        
        # Refund balance
        if request.balance_deducted and days_to_refund > 0:
            await self._balance_service.restore_partial_balance(request, days_to_refund)
        
        # Mark request as having interruptions
        request.has_interruptions = True
        
        # Audit
        await self._audit.log_action(
            user_id=user_id,
            action="SICKNESS_INTERRUPTION",
            resource_type="LEAVE_REQUEST",
            resource_id=str(request_id),
            description=f"Sickness during vacation: {data.sick_start_date} - {data.sick_end_date}",
            request_data={
                "sick_start": data.sick_start_date.isoformat(),
                "sick_end": data.sick_end_date.isoformat(),
                "protocol": data.protocol_number,
                "days_refunded": float(days_to_refund),
            },
        )
        
        return interruption

    async def report_user_sickness(
        self,
        request_id: UUID,
        user_id: UUID,
        data: SicknessInterruptionRequest,
    ) -> LeaveInterruption:
        """
        Employee reports sickness during their own vacation.
        
        Wrapper for create_sickness_interruption with ownership check.
        """
        request = await self.get_request(request_id)
        
        if request.user_id != user_id:
            raise BusinessRuleError("Non puoi segnalare malattia per la richiesta di un altro utente")
        
        return await self.create_sickness_interruption(request_id, user_id, data)

    async def get_request_interruptions(self, request_id: UUID) -> list[LeaveInterruption]:
        """Get all interruptions for a leave request."""
        result = await self._session.execute(
            select(LeaveInterruption)
            .where(LeaveInterruption.leave_request_id == request_id)
            .order_by(LeaveInterruption.start_date)
        )
        return list(result.scalars().all())

    async def _calculate_recalled_days(self, days: list[date], user_id: UUID) -> Decimal:
        """Calculate working days to refund for recalled days."""
        # Each recalled day that is a working day = 1 day refund
        total = Decimal("0")
        for day in days:
            day_count = await self._calculate_days(day, day, False, False, user_id)
            total += day_count
        return total

    # ═══════════════════════════════════════════════════════════
    # Enterprise Features - Delegation Support
    # ═══════════════════════════════════════════════════════════

    async def get_delegated_pending_requests(self, delegate_id: UUID) -> list[LeaveRequest]:
        """
        Get pending requests that a delegate can approve on behalf of others.
        
        Finds all active delegations where this user is the delegate,
        then finds pending requests for those delegators' subordinates.
        """
        today = date.today()
        
        # Find active delegations for this user
        delegations = await self._session.execute(
            select(ApprovalDelegation).where(
                and_(
                    ApprovalDelegation.delegate_id == delegate_id,
                    ApprovalDelegation.is_active == True,
                    ApprovalDelegation.delegation_type == "FULL",
                    ApprovalDelegation.start_date <= today,
                    ApprovalDelegation.end_date >= today,
                )
            )
        )
        active_delegations = delegations.scalars().all()
        
        if not active_delegations:
            return []
        
        # Get pending requests for each delegator
        all_requests = []
        for delegation in active_delegations:
            # Get the delegator's pending requests
            delegator_requests = await self.get_pending_approval(approver_id=delegation.delegator_id)
            
            # Filter by leave type scope if specified
            if delegation.scope_leave_types:
                delegator_requests = [
                    r for r in delegator_requests 
                    if r.leave_type_code in delegation.scope_leave_types
                ]
            
            all_requests.extend(delegator_requests)
        
        return all_requests

    async def get_pending_datatable(
        self,
        request: DataTableRequest,
        approver_id: UUID,
        include_delegated: bool = True,
    ):
        """Get pending requests for DataTable with pagination."""
        # This would need a more sophisticated implementation for true pagination
        # For now, we get all and then paginate in memory
        direct = await self.get_pending_approval(approver_id=approver_id)
        
        if include_delegated:
            delegated = await self.get_delegated_pending_requests(approver_id)
            direct.extend(delegated)
        
        # Apply pagination
        start = request.start or 0
        length = request.length or 10
        
        from src.services.leaves.schemas import LeaveRequestListItem
        
        return {
            "draw": request.draw,
            "recordsTotal": len(direct),
            "recordsFiltered": len(direct),
            "data": [
                LeaveRequestListItem.model_validate(r, from_attributes=True) 
                for r in direct[start:start + length]
            ],
        }

    # ═══════════════════════════════════════════════════════════
    # Enterprise Features - Modify Approved Request
    # ═══════════════════════════════════════════════════════════

    async def modify_approved_request(
        self,
        request_id: UUID,
        modifier_id: UUID,
        data: ModifyApprovedRequest,
    ) -> LeaveRequest:
        """
        Modify an already approved request (only future dates).
        
        Creates full audit trail of changes with before/after values.
        Adjusts balance if days change.
        """
        request = await self.get_request(request_id)
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le richieste approvate possono essere modificate")
        
        # Only future requests can be modified
        if request.start_date <= date.today():
            raise BusinessRuleError(
                "Non è possibile modificare una richiesta già iniziata. "
                "Usare il richiamo o l'interruzione."
            )
        
        # Store original values for audit
        original = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "start_half_day": request.start_half_day,
            "end_half_day": request.end_half_day,
            "days_requested": float(request.days_requested),
        }
        
        # Apply changes
        new_start = data.new_start_date or request.start_date
        new_end = data.new_end_date or request.end_date
        new_start_half = data.new_start_half_day if data.new_start_half_day is not None else request.start_half_day
        new_end_half = data.new_end_half_day if data.new_end_half_day is not None else request.end_half_day
        
        # Validate new dates
        if new_end < new_start:
            raise BusinessRuleError("La data di fine deve essere successiva alla data di inizio")
        
        if new_start < date.today():
            raise BusinessRuleError("La nuova data di inizio deve essere futura")
        
        # Calculate new days
        new_days = await self._calculate_days(new_start, new_end, new_start_half, new_end_half, request.user_id)
        old_days = request.days_requested
        
        # Update request
        request.start_date = new_start
        request.end_date = new_end
        request.start_half_day = new_start_half
        request.end_half_day = new_end_half
        request.days_requested = new_days
        
        # Adjust balance if days changed
        days_diff = new_days - old_days
        if days_diff != 0 and request.balance_deducted:
            if days_diff > 0:
                # Need more days - deduct additional
                await self._balance_service.deduct_balance(
                    request,
                    {request.leave_type_code.lower(): float(days_diff)},
                )
            else:
                # Need fewer days - refund
                await self._balance_service.restore_partial_balance(request, abs(days_diff))
        
        # Add history
        await self._request_repo.add_history(
            leave_request_id=request_id,
            from_status=request.status,
            to_status=request.status,  # Status doesn't change
            changed_by=modifier_id,
            reason=f"Modifica richiesta: {data.reason}",
        )
        
        # Audit with before/after
        await self._audit.log_action(
            user_id=modifier_id,
            action="MODIFY_APPROVED",
            resource_type="LEAVE_REQUEST",
            resource_id=str(request_id),
            description=f"Modified approved request: {data.reason}",
            request_data={
                "original": original,
                "modified": {
                    "start_date": new_start.isoformat(),
                    "end_date": new_end.isoformat(),
                    "start_half_day": new_start_half,
                    "end_half_day": new_end_half,
                    "days_requested": float(new_days),
                },
                "days_adjustment": float(days_diff),
                "reason": data.reason,
            },
        )
        
        return request

    # ═══════════════════════════════════════════════════════════
    # Enterprise Features - Calendar
    # ═══════════════════════════════════════════════════════════

    async def get_user_calendar(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
        include_holidays: bool = True,
    ) -> CalendarResponse:
        """Get calendar for a specific user."""
        # Get user's leave requests
        requests = await self._request_repo.get_by_user(
            user_id,
            year=start_date.year,
            status=[LeaveRequestStatus.APPROVED, LeaveRequestStatus.PENDING, LeaveRequestStatus.APPROVED_CONDITIONAL],
        )
        
        events = [
            CalendarEvent(
                id=str(r.id),
                title=f"{r.leave_type_code} - {r.status.value}",
                start=r.start_date,
                end=r.end_date,
                allDay=True,
                color=self._get_event_color(r.status, r.leave_type_code),
                extendedProps={"status": r.status.value, "type": r.leave_type_code},
            )
            for r in requests
            if r.start_date <= end_date and r.end_date >= start_date
        ]
        
        holidays = []
        closures = []
        
        if include_holidays:
            # Get holidays from config service
            holidays_data = await self._config_client.get_holidays(start_date.year)
            holidays = [
                CalendarEvent(
                    id=f"holiday-{h.get('date')}",
                    title=h.get("name", "Festività"),
                    start=date.fromisoformat(h.get("date")),
                    end=date.fromisoformat(h.get("date")),
                    allDay=True,
                    color="#EF4444",
                    extendedProps={"type": "holiday"},
                )
                for h in (holidays_data or [])
            ]
        
        return CalendarResponse(events=events, holidays=holidays, closures=closures)

    async def get_team_calendar(
        self,
        manager_id: UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Get calendar view for manager's team."""
        # Get subordinates
        subordinates = await self._get_subordinates(manager_id)
        
        all_events = []
        
        for sub_id in subordinates:
            # Get each subordinate's calendar
            sub_calendar = await self.get_user_calendar(sub_id, start_date, end_date, include_holidays=False)
            for event in sub_calendar.events:
                event.extendedProps["user_id"] = str(sub_id)
            all_events.extend(sub_calendar.events)
        
        return {
            "events": all_events,
            "team_size": len(subordinates),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    # ═══════════════════════════════════════════════════════════
    # Enterprise Features - Voluntary Work (Employee Requests)
    # ═══════════════════════════════════════════════════════════

    async def request_voluntary_work(
        self,
        request_id: UUID,
        user_id: UUID,
        data: VoluntaryWorkRequest,
    ) -> LeaveInterruption:
        """
        Employee requests to convert vacation days to working days.
        
        Creates an interruption with status PENDING_APPROVAL.
        Manager must approve before the balance is refunded.
        """
        request = await self.get_request(request_id)
        
        # Ownership check
        if request.user_id != user_id:
            raise BusinessRuleError("Non puoi richiedere lavoro per la richiesta di un altro utente")
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le ferie approvate possono essere convertite in giorni lavorativi")
        
        # Validate all work days are within the leave period
        for day in data.work_days:
            if day < request.start_date or day > request.end_date:
                raise BusinessRuleError(
                    f"Il giorno {day.isoformat()} non rientra nel periodo di ferie "
                    f"({request.start_date.isoformat()} - {request.end_date.isoformat()})"
                )
        
        # Check if days are in the future
        today = date.today()
        past_days = [d for d in data.work_days if d <= today]
        if past_days:
            raise BusinessRuleError(
                f"Non puoi richiedere lavoro per giorni passati o odierni: {[d.isoformat() for d in past_days]}"
            )
        
        # Check for existing pending requests on same days
        existing = await self._session.execute(
            select(LeaveInterruption).where(
                and_(
                    LeaveInterruption.leave_request_id == request_id,
                    LeaveInterruption.interruption_type == "VOLUNTARY_WORK",
                    LeaveInterruption.status == "PENDING_APPROVAL",
                )
            )
        )
        existing_interruption = existing.scalar_one_or_none()
        if existing_interruption:
            # Check for overlapping days
            existing_days = set(existing_interruption.specific_days or [])
            new_days = set(d.isoformat() for d in data.work_days)
            overlap = existing_days & new_days
            if overlap:
                raise BusinessRuleError(
                    f"Esiste già una richiesta pendente per i giorni: {list(overlap)}"
                )
        
        # Calculate days to potentially refund
        days_to_refund = await self._calculate_recalled_days(data.work_days, user_id)
        
        # Create interruption with PENDING_APPROVAL status
        interruption = LeaveInterruption(
            leave_request_id=request_id,
            interruption_type="VOLUNTARY_WORK",
            start_date=min(data.work_days),
            end_date=max(data.work_days),
            specific_days=[d.isoformat() for d in data.work_days],
            days_refunded=Decimal("0"),  # Not refunded until approved
            initiated_by=user_id,
            initiated_by_role="EMPLOYEE",
            reason=data.reason,
            status="PENDING_APPROVAL",  # Requires manager approval
        )
        
        self._session.add(interruption)
        await self._session.flush()
        
        # Audit
        await self._audit.log_action(
            user_id=user_id,
            action="VOLUNTARY_WORK_REQUEST",
            resource_type="LEAVE_REQUEST",
            resource_id=str(request_id),
            description=f"Employee requests to work {len(data.work_days)} day(s) during vacation",
            request_data={
                "work_days": [d.isoformat() for d in data.work_days],
                "potential_days_refund": float(days_to_refund),
                "reason": data.reason,
            },
        )
        
        # Notify manager
        await self._notifier.notify_voluntary_work_request(request, interruption)
        
        return interruption

    async def get_voluntary_work_requests(self, request_id: UUID) -> list[LeaveInterruption]:
        """Get all voluntary work requests for a leave request."""
        result = await self._session.execute(
            select(LeaveInterruption)
            .where(
                LeaveInterruption.leave_request_id == request_id,
                LeaveInterruption.interruption_type == "VOLUNTARY_WORK",
            )
            .order_by(LeaveInterruption.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_pending_voluntary_work_requests(self, manager_id: UUID) -> list[LeaveInterruption]:
        """Get all pending voluntary work requests for manager's subordinates."""
        # Get subordinates
        subordinates = await self._get_subordinates(manager_id)
        
        if not subordinates:
            return []
        
        # Find pending VOLUNTARY_WORK interruptions for subordinates' requests
        result = await self._session.execute(
            select(LeaveInterruption)
            .join(LeaveRequest, LeaveInterruption.leave_request_id == LeaveRequest.id)
            .where(
                LeaveRequest.user_id.in_(subordinates),
                LeaveInterruption.interruption_type == "VOLUNTARY_WORK",
                LeaveInterruption.status == "PENDING_APPROVAL",
            )
            .order_by(LeaveInterruption.created_at.asc())
        )
        return list(result.scalars().all())

    async def approve_voluntary_work(
        self,
        interruption_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> LeaveInterruption:
        """
        Manager approves employee's request to work during vacation.
        
        Upon approval:
        - Status changes to APPROVED
        - Vacation days are refunded to balance
        - Leave request marked as having interruptions
        """
        result = await self._session.execute(
            select(LeaveInterruption).where(LeaveInterruption.id == interruption_id)
        )
        interruption = result.scalar_one_or_none()
        
        if not interruption:
            raise NotFoundError("Voluntary work request not found", entity_type="LeaveInterruption", entity_id=str(interruption_id))
        
        if interruption.interruption_type != "VOLUNTARY_WORK":
            raise BusinessRuleError("Questo non è una richiesta di lavoro volontario")
        
        if interruption.status != "PENDING_APPROVAL":
            raise BusinessRuleError(f"La richiesta non è in attesa di approvazione (stato: {interruption.status})")
        
        # Get the leave request
        request = await self.get_request(interruption.leave_request_id)
        
        # Calculate days to refund
        work_days = [date.fromisoformat(d) for d in (interruption.specific_days or [])]
        days_to_refund = await self._calculate_recalled_days(work_days, request.user_id)
        
        # Update interruption
        interruption.status = "APPROVED"
        interruption.days_refunded = days_to_refund
        
        # Refund balance
        if request.balance_deducted and days_to_refund > 0:
            await self._balance_service.restore_partial_balance(request, days_to_refund)
        
        # Mark request as having interruptions
        request.has_interruptions = True
        
        # Audit
        await self._audit.log_action(
            user_id=approver_id,
            action="VOLUNTARY_WORK_APPROVED",
            resource_type="LEAVE_INTERRUPTION",
            resource_id=str(interruption_id),
            description=f"Approved voluntary work request for {len(work_days)} day(s)",
            request_data={
                "work_days": [d.isoformat() for d in work_days],
                "days_refunded": float(days_to_refund),
                "employee_id": str(request.user_id),
                "notes": notes,
            },
        )
        
        # Notify employee
        await self._notifier.notify_voluntary_work_approved(request, interruption)
        
        return interruption

    async def reject_voluntary_work(
        self,
        interruption_id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> None:
        """
        Manager rejects employee's request to work during vacation.
        
        The vacation remains as originally approved.
        """
        result = await self._session.execute(
            select(LeaveInterruption).where(LeaveInterruption.id == interruption_id)
        )
        interruption = result.scalar_one_or_none()
        
        if not interruption:
            raise NotFoundError("Voluntary work request not found", entity_type="LeaveInterruption", entity_id=str(interruption_id))
        
        if interruption.interruption_type != "VOLUNTARY_WORK":
            raise BusinessRuleError("Questo non è una richiesta di lavoro volontario")
        
        if interruption.status != "PENDING_APPROVAL":
            raise BusinessRuleError(f"La richiesta non è in attesa di approvazione (stato: {interruption.status})")
        
        # Get the leave request for audit
        request = await self.get_request(interruption.leave_request_id)
        
        # Update interruption
        interruption.status = "REJECTED"
        interruption.reason = f"{interruption.reason}\n\n[RIFIUTO] {reason}" if interruption.reason else f"[RIFIUTO] {reason}"
        
        # Audit
        await self._audit.log_action(
            user_id=approver_id,
            action="VOLUNTARY_WORK_REJECTED",
            resource_type="LEAVE_INTERRUPTION",
            resource_id=str(interruption_id),
            description=f"Rejected voluntary work request",
            request_data={
                "work_days": interruption.specific_days,
                "employee_id": str(request.user_id),
                "rejection_reason": reason,
            },
        )
        
        # Notify employee
        await self._notifier.notify_voluntary_work_rejected(request, interruption, reason)



