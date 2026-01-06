"""
KRONOS - Leave Enterprise Service

Italian Labor Law compliance features.

This module handles advanced leave management operations specific to Italian regulations:
- Employee recall during vacation (Richiamo in servizio)
- Sickness during vacation (Art. 6 D.Lgs 66/2003)
- Partial recall for specific days
- Voluntary work requests
- Approved request modifications
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
import logging

from sqlalchemy import select, and_

from src.core.exceptions import BusinessRuleError, NotFoundError
from src.services.leaves.models import (
    LeaveRequest,
    LeaveRequestStatus,
    LeaveInterruption,
)
from src.services.leaves.schemas import (
    RecallRequest,
    PartialRecallRequest,
    SicknessInterruptionRequest,
    ModifyApprovedRequest,
    VoluntaryWorkRequest,
)
from src.services.leaves.services.base import BaseLeaveService

logger = logging.getLogger(__name__)


class LeaveEnterpriseService(BaseLeaveService):
    """
    Italian Labor Law compliance features for leave management.
    
    Handles:
    - Full recall (richiamo in servizio completo)
    - Partial recall (richiamo parziale per giorni specifici)
    - Sickness interruption (malattia durante ferie)
    - Voluntary work (dipendente richiede di lavorare durante ferie)
    - Modification of approved requests
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # Full Recall Operations
    # ═══════════════════════════════════════════════════════════════════════
    
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
        request = await self._get_request(id)
        
        # Can recall from APPROVED or APPROVED_CONDITIONAL
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError(
                "Solo le richieste approvate possono essere richiamate"
            )
        
        # Verify recall is during the leave period
        today = date.today()
        
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
            start_half=request.start_half_day,
            end_half=False,  # Full day before return
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
        
        return await self._get_request(id)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Partial Recall Operations
    # ═══════════════════════════════════════════════════════════════════════
    
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
        request = await self._get_request(request_id)
        
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
        
        # Create interruption record using repository
        interruption = await self._interruption_repo.create(
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
        
        # Refund balance
        if request.balance_deducted and days_to_refund > 0:
            await self._balance_service.restore_partial_balance(request, days_to_refund)
        
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # Sickness Interruption Operations
    # ═══════════════════════════════════════════════════════════════════════
    
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
        request = await self._get_request(request_id)
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le ferie approvate possono essere interrotte")
        
        # Validate sick period is within leave period
        if data.sick_start_date < request.start_date or data.sick_end_date > request.end_date:
            raise BusinessRuleError(
                f"Il periodo di malattia deve rientrare nel periodo di ferie "
                f"({request.start_date.isoformat()} - {request.end_date.isoformat()})"
            )
        
        # Check for overlapping sickness interruptions using repository
        existing = await self._interruption_repo.check_overlap(
            request_id=request_id,
            interruption_type="SICKNESS",
            start_date=data.sick_start_date,
            end_date=data.sick_end_date,
        )
        if existing:
            raise BusinessRuleError("Esiste già una registrazione di malattia per questo periodo")
        
        # Calculate days to refund
        days_to_refund = await self._calculate_days(
            data.sick_start_date,
            data.sick_end_date,
            False,  # Full days
            False,
            request.user_id,
        )
        
        # Create interruption record using repository
        interruption = await self._interruption_repo.create(
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
        request = await self._get_request(request_id)
        
        if request.user_id != user_id:
            raise BusinessRuleError("Non puoi segnalare malattia per la richiesta di un altro utente")
        
        return await self.create_sickness_interruption(request_id, user_id, data)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Voluntary Work Operations
    # ═══════════════════════════════════════════════════════════════════════
    
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
        request = await self._get_request(request_id)
        
        if request.user_id != user_id:
            raise BusinessRuleError("Non puoi richiedere di lavorare durante le ferie di un altro")
        
        if request.status not in [LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL]:
            raise BusinessRuleError("Solo le ferie approvate possono essere interrotte")
        
        # Validate work days are within leave period
        for day in data.work_days:
            if day < request.start_date or day > request.end_date:
                raise BusinessRuleError(
                    f"Il giorno {day.isoformat()} non rientra nel periodo di ferie"
                )
        
        # Calculate potential days to refund
        days_to_refund = await self._calculate_recalled_days(data.work_days, user_id)
        
        # Create pending interruption using repository
        interruption = await self._interruption_repo.create(
            leave_request_id=request_id,
            interruption_type="VOLUNTARY_WORK",
            start_date=min(data.work_days),
            end_date=max(data.work_days),
            specific_days=[d.isoformat() for d in data.work_days],
            days_refunded=days_to_refund,
            initiated_by=user_id,
            initiated_by_role="EMPLOYEE",
            reason=data.reason,
            status="PENDING_APPROVAL",
        )
        
        # Audit
        await self._audit.log_action(
            user_id=user_id,
            action="REQUEST_VOLUNTARY_WORK",
            resource_type="LEAVE_REQUEST",
            resource_id=str(request_id),
            description=f"Requested to work {len(data.work_days)} days during vacation",
            request_data={
                "work_days": [d.isoformat() for d in data.work_days],
                "potential_refund": float(days_to_refund),
                "reason": data.reason,
            },
        )
        
        return interruption
    
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
        # 1. Fetch and check status before update
        interruption = await self._interruption_repo.get(interruption_id)
        if not interruption:
            raise NotFoundError("Voluntary work request not found")
        
        if interruption.status != "PENDING_APPROVAL":
            raise BusinessRuleError("Questa richiesta non è in attesa di approvazione")
            
        request = await self._get_request(interruption.leave_request_id)
        
        # 2. Approve using repository
        interruption = await self._interruption_repo.update(
            interruption_id,
            status="APPROVED",
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=notes,
        )
        
        # Refund balance
        if request.balance_deducted and interruption.days_refunded > 0:
            await self._balance_service.restore_partial_balance(request, interruption.days_refunded)
        
        # Mark request as having interruptions
        request.has_interruptions = True
        
        # Audit
        await self._audit.log_action(
            user_id=approver_id,
            action="APPROVE_VOLUNTARY_WORK",
            resource_type="LEAVE_INTERRUPTION",
            resource_id=str(interruption_id),
            description=f"Approved voluntary work request",
            request_data={"days_refunded": float(interruption.days_refunded), "notes": notes},
        )
        
        return interruption
    
    async def reject_voluntary_work(
        self,
        interruption_id: UUID,
        approver_id: UUID,
        reason: str,
    ) -> LeaveInterruption:
        """
        Manager rejects employee's request to work during vacation.
        
        The vacation remains as originally approved.
        """
        # Reject using repository
        interruption = await self._interruption_repo.get(interruption_id)
        if not interruption:
            raise NotFoundError("Voluntary work request not found")
        
        if interruption.status != "PENDING_APPROVAL":
            raise BusinessRuleError("Questa richiesta non è in attesa di approvazione")
            
        interruption = await self._interruption_repo.update(
            interruption_id,
            status="REJECTED",
            approver_id=approver_id,
            approved_at=datetime.utcnow(),
            approver_notes=reason,
        )
        
        # Audit
        await self._audit.log_action(
            user_id=approver_id,
            action="REJECT_VOLUNTARY_WORK",
            resource_type="LEAVE_INTERRUPTION",
            resource_id=str(interruption_id),
            description=f"Rejected voluntary work request: {reason}",
        )
        
        return interruption
    
    # ═══════════════════════════════════════════════════════════════════════
    # Modification of Approved Requests
    # ═══════════════════════════════════════════════════════════════════════
    
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
        request = await self._get_request(request_id)
        
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # Closure Recalculation
    # ═══════════════════════════════════════════════════════════════════════
    
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
        # Find overlapping approved requests
        requests = await self._request_repo.get_by_date_range(
            closure_start,
            closure_end,
            status=[LeaveRequestStatus.APPROVED, LeaveRequestStatus.APPROVED_CONDITIONAL],
        )
        
        affected = []
        
        for request in requests:
            old_days = request.days_requested
            
            # Recalculate days
            new_days = await self._calculate_days(
                request.start_date,
                request.end_date,
                request.start_half_day,
                request.end_half_day,
                request.user_id,
            )
            
            if new_days != old_days:
                # Update request
                request.days_requested = new_days
                
                # Adjust balance
                days_diff = old_days - new_days
                if days_diff > 0 and request.balance_deducted:
                    await self._balance_service.restore_partial_balance(request, days_diff)
                
                affected.append({
                    "request_id": str(request.id),
                    "user_id": str(request.user_id),
                    "old_days": float(old_days),
                    "new_days": float(new_days),
                    "days_refunded": float(days_diff),
                })
        
        return affected
    
    # ═══════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _get_request(self, id: UUID) -> LeaveRequest:
        """Get leave request by ID (internal use)."""
        request = await self._request_repo.get(id)
        if not request:
            raise NotFoundError("Leave request not found", entity_type="LeaveRequest", entity_id=str(id))
        return request
    
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
    
    async def _calculate_recalled_days(self, days: list[date], user_id: UUID) -> Decimal:
        """Calculate working days to refund for recalled days."""
        total = Decimal("0")
        for day in days:
            day_count = await self._calculate_days(day, day, False, False, user_id)
            total += day_count
        return total
