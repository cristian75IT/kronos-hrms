from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, or_, func
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
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus, ConditionType, LeaveBalance, BalanceTransaction
from src.services.leaves.repository import LeaveRequestRepository, LeaveBalanceRepository
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

        self._balance_repo = LeaveBalanceRepository(session)
        self._audit = get_audit_logger("leave-service")
        
        # Shared Clients
        self._auth_client = AuthClient()
        self._config_client = ConfigClient()
        self._notifier = LeaveNotificationHandler()
        self._calendar_utils = CalendarUtils(self._config_client)
        self._balance_service = LeaveBalanceService(session)
        
        self._policy_engine = PolicyEngine(
            session,
            self._request_repo,
            self._balance_repo,
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
        
        return await self._request_repo.update(id, **update_data)


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
        await self._notifier.notify_submission(request)
        
        return await self.get_request(id)

    async def approve_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: ApproveRequest,
    ) -> LeaveRequest:
        """Approve a pending request."""
        request = await self.get_request(id)
        
        if request.status != LeaveRequestStatus.PENDING:
            raise BusinessRuleError("Only pending requests can be approved")
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.APPROVED,
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=data.notes,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=LeaveRequestStatus.PENDING,
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
        
        # Deduct balance
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
        await self._notifier.notify_conditional_approval(request, data.condition_details)
        
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
        
        return await self.get_request(id)

    async def reject_request(
        self,
        id: UUID,
        approver_id: UUID,
        data: RejectRequest,
    ) -> LeaveRequest:
        """Reject a pending request."""
        request = await self.get_request(id)
        
        if request.status != LeaveRequestStatus.PENDING:
            raise BusinessRuleError("Only pending requests can be rejected")
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.REJECTED,
            approver_id=approver_id,
            approver_notes=data.reason,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=LeaveRequestStatus.PENDING,
            to_status=LeaveRequestStatus.REJECTED,
            changed_by=approver_id,
            reason=data.reason,
        )
        
        # Send notification
        # Send notification
        await self._notifier.notify_rejected(request, data.reason)
        
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
        await self._notifier.notify_revoked(request, reason)
        
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
        await self._notifier.notify_reopened(request)
        
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
            
        return await self._request_repo.delete(id)

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
            start_date, end_date, start_half, end_half
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



    async def _get_user_info(self, user_id: UUID) -> Optional[dict]:
        """Get user info from auth service."""
        return await self._auth_client.get_user_info(user_id)



    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        return await self._auth_client.get_user_email(user_id)


