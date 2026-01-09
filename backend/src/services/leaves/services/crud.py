"""
KRONOS - Leave CRUD Service

Create, Update, Delete operations for leave requests.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.core.exceptions import BusinessRuleError, ValidationError
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus
from src.services.leaves.schemas import LeaveRequestCreate, LeaveRequestUpdate
from src.services.leaves.services.base import BaseLeaveService


class LeaveCrudService(BaseLeaveService):
    """
    CRUD operations for leave requests.
    
    Handles:
    - Create new requests (as draft)
    - Update draft requests
    - Delete draft requests
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # Create Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_request(
        self,
        user_id: UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request (as draft)."""
        # Validate System Configuration (Workflow)
        health = await self._approval_client.check_workflow_health()
        leave_workflow_ok = False
        if health and health.get("items"):
            for item in health.get("items", []):
                if item.get("config_type") == "WORKFLOW_LEAVE" and item.get("status") == "ok":
                    leave_workflow_ok = True
                    break
        
        if not leave_workflow_ok:
            raise BusinessRuleError(
                "Impossibile creare la richiesta: Il Workflow Approvazioni Ferie non è configurato nel sistema. Contatta l'amministratore.",
                rule="WORKFLOW_CONFIG_MISSING"
            )

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

        # Validate notice period
        min_notice = leave_type.get("min_notice_days")
        if min_notice is not None:
            today = date.today()
            days_notice = (data.start_date - today).days
            if days_notice < min_notice:
                msg_suffix = "nel passato" if days_notice < 0 else f"tra {days_notice} giorni"
                raise BusinessRuleError(
                    f"Il tipo '{leave_type.get('name')}' richiede un preavviso minimo di {min_notice} giorni. "
                    f"La richiesta inizia {msg_suffix}.",
                    rule="MIN_NOTICE_PERIOD_REQUIRED"
                )

        # Calculate days
        days = await self._calculate_days(
            data.start_date,
            data.end_date,
            data.start_half_day,
            data.end_half_day,
            user_id,
        )
        
        # Validate max single request days
        max_days = leave_type.get("max_single_request_days")
        if max_days and days > max_days:
            raise BusinessRuleError(
                f"Il tipo '{leave_type.get('name')}' consente un massimo di {max_days} giorni per richiesta. "
                f"Hai richiesto {days} giorni.",
                rule="MAX_SINGLE_REQUEST_DAYS_EXCEEDED"
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # Update Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def update_request(
        self,
        id: UUID,
        user_id: UUID,
        data: LeaveRequestUpdate,
    ) -> LeaveRequest:
        """Update a draft request."""
        request = await self._get_request(id)
        
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
    
    # ═══════════════════════════════════════════════════════════════════════
    # Delete Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def delete_request(
        self,
        id: UUID,
        user_id: UUID,
    ) -> None:
        """Delete a draft request."""
        request = await self._get_request(id)
        
        if request.status != LeaveRequestStatus.DRAFT:
            raise BusinessRuleError(
                "Solo le bozze possono essere eliminate. Per le richieste inviate, usa 'Annulla'.",
                rule="DRAFT_ONLY",
            )
        
        if request.user_id != user_id:
            raise BusinessRuleError("Non puoi eliminare la richiesta di un altro utente.")
        
        await self._request_repo.delete(id)
        
        # Audit Log
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="LEAVE_REQUEST",
            resource_id=str(id),
            description=f"Deleted leave request {id}",
        )
    
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
    
    async def _calculate_days(
        self,
        start_date: date,
        end_date: date,
        start_half: bool,
        end_half: bool,
        user_id: Optional[UUID] = None,
    ) -> Decimal:
        """Calculate working days between dates."""
        count_saturday = False
        if user_id:
            count_saturday = await self._get_saturday_rule(user_id, start_date)
            
        return await self._calendar_utils.calculate_working_days(
            start_date, end_date, start_half, end_half, user_id=user_id, count_saturday=count_saturday
        )
