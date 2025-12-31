from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import (
    NotFoundError,
    ConflictError,
    BusinessRuleError,
    ValidationError,
)
from src.services.auth.models import EmployeeContract, ContractType
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus, ConditionType, LeaveBalance
from src.services.leaves.repository import LeaveRequestRepository, LeaveBalanceRepository
from src.services.leaves.policy_engine import PolicyEngine
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
)
from src.shared.schemas import DataTableRequest


class LeaveService:
    """Service for leave request management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._balance_repo = LeaveBalanceRepository(session)
        self._policy_engine = PolicyEngine(
            session,
            self._request_repo,
            self._balance_repo,
        )

    async def recalculate_all_balances(self, year: int):
        """Recalculate accruals for all users based on their contracts."""
        # Get all users with contracts
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()

        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def recalculate_user_accrual(self, user_id: UUID, year: int):
        """Recalculate annual accrual based on contracts history."""
        # Get contracts with types
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.user_id == user_id)
            .order_by(EmployeeContract.start_date)
        )
        result = await self._session.execute(query)
        contracts = result.scalars().all()

        if not contracts:
            return

        total_vacation = Decimal(0)
        total_rol = Decimal(0)
        total_permits = Decimal(0)
        
        today = date.today()
        
        # Calculate for each month
        for month in range(1, 13):
            month_start = date(year, month, 1)
            _, last_day = monthrange(year, month)
            month_end = date(year, month, last_day)
            
            # Stop if future month (accrue only past/current months)
            if month_start > today:
                break
                
            # Find active contract for this month (at start of month)
            active_contract = None
            for contract in contracts:
                c_start = contract.start_date
                c_end = contract.end_date or date(9999, 12, 31)
                
                # Overlap check
                if c_start <= month_end and c_end >= month_start:
                    active_contract = contract
                    # Prefer contract active at start of month
                    if c_start <= month_start:
                        break
            
            if active_contract and active_contract.contract_type:
                ctype = active_contract.contract_type
                
                # Monthly rates
                monthly_vacation = Decimal(ctype.annual_vacation_days) / 12
                monthly_rol = Decimal(ctype.annual_rol_hours) / 12
                monthly_permits = Decimal(ctype.annual_permit_hours) / 12
                
                # Adjust for Part-Time or Effective Weekly Hours
                # We assume 40h as standard weekly base for 100% accrual
                if active_contract.weekly_hours is not None:
                    ratio = Decimal(active_contract.weekly_hours) / 40
                elif ctype.is_part_time:
                    ratio = Decimal(ctype.part_time_percentage) / 100
                else:
                    ratio = Decimal(1.0)
                
                if ratio != Decimal(1.0):
                    monthly_vacation *= ratio
                    monthly_rol *= ratio
                    monthly_permits *= ratio
                
                total_vacation += monthly_vacation
                total_rol += monthly_rol
                total_permits += monthly_permits

        # Update balance
        balance = await self._balance_repo.get_or_create(user_id, year)
        
        await self._balance_repo.update(
            balance.id, 
            vacation_accrued=total_vacation,
            rol_accrued=total_rol,
            permits_total=total_permits,
            last_accrual_date=today
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

    async def create_request(
        self,
        user_id: UUID,
        data: LeaveRequestCreate,
    ) -> LeaveRequest:
        """Create a new leave request (as draft)."""
        # Get leave type info
        leave_type = await self._get_leave_type(data.leave_type_id)
        if not leave_type:
            raise ValidationError("Leave type not found", field="leave_type_id")
        
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
        await self._send_notification(
            user_id=user_id,
            notification_type="leave_request_submitted",
            title="Richiesta ferie sottomessa",
            message=f"Richiesta {request.leave_type_code} dal {request.start_date} sottomessa",
            entity_type="LeaveRequest",
            entity_id=str(request.id),
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
        
        # Deduct balance
        await self._deduct_balance(request, request.deduction_details or {})
        
        # Send notification
        await self._send_notification(
            user_id=request.user_id,
            notification_type="leave_request_approved",
            title="Richiesta approvata",
            message=f"La tua richiesta {request.leave_type_code} è stata approvata",
            entity_type="LeaveRequest",
            entity_id=str(id),
        )
        
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
        await self._send_notification(
            user_id=request.user_id,
            notification_type="leave_conditional_approval",
            title="Approvazione condizionale",
            message=f"La tua richiesta è stata approvata con condizioni: {data.condition_details}",
            entity_type="LeaveRequest",
            entity_id=str(id),
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
        await self._send_notification(
            user_id=request.user_id,
            notification_type="leave_request_rejected",
            title="Richiesta rifiutata",
            message=f"La tua richiesta {request.leave_type_code} è stata rifiutata: {data.reason}",
            entity_type="LeaveRequest",
            entity_id=str(id),
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
        
        return await self.get_request(id)

    async def recall_request(
        self,
        id: UUID,
        manager_id: UUID,
        data: RecallRequest,
    ) -> LeaveRequest:
        """Recall an approved request (right of recall)."""
        request = await self.get_request(id)
        
        if request.status != LeaveRequestStatus.APPROVED:
            raise BusinessRuleError("Only approved requests can be recalled")
        
        await self._request_repo.update(
            id,
            status=LeaveRequestStatus.RECALLED,
            recalled_at=datetime.utcnow(),
            recall_reason=data.reason,
        )
        
        await self._request_repo.add_history(
            leave_request_id=id,
            from_status=LeaveRequestStatus.APPROVED,
            to_status=LeaveRequestStatus.RECALLED,
            changed_by=manager_id,
            reason=data.reason,
        )
        
        # Restore balance
        if request.balance_deducted:
            await self._restore_balance(request)
        
        # Send notification with compensation info
        await self._send_notification(
            user_id=request.user_id,
            notification_type="leave_request_recalled",
            title="Richiamo da ferie",
            message=f"Sei stato richiamato dal periodo di ferie: {data.reason}. Hai diritto a compensazione.",
            entity_type="LeaveRequest",
            entity_id=str(id),
        )
        
        return await self.get_request(id)

    # ═══════════════════════════════════════════════════════════
    # Balance Operations
    # ═══════════════════════════════════════════════════════════

    async def get_balance(self, user_id: UUID, year: int):
        """Get user balance for year."""
        balance = await self._balance_repo.get_by_user_year(user_id, year)
        if not balance:
            # Create empty balance
            balance = await self._balance_repo.get_or_create(user_id, year)
        return balance

    async def get_balance_summary(self, user_id: UUID, year: int) -> BalanceSummary:
        """Get balance summary including pending requests."""
        balance = await self.get_balance(user_id, year)
        
        # Get pending requests to calculate reserved
        pending = await self._request_repo.get_by_user(
            user_id,
            year=year,
            status=[LeaveRequestStatus.PENDING, LeaveRequestStatus.APPROVED_CONDITIONAL],
        )
        
        vacation_pending = sum(
            r.days_requested for r in pending if r.leave_type_code in ["FER"]
        )
        rol_pending = sum(
            r.days_requested * 8 for r in pending if r.leave_type_code in ["ROL"]
        )
        permits_pending = sum(
            r.days_requested * 8 for r in pending if r.leave_type_code in ["PER"]
        )
        
        days_until_ap_expiry = None
        if balance.ap_expiry_date:
            days_until_ap_expiry = (balance.ap_expiry_date - date.today()).days

        return BalanceSummary(
            vacation_total_available=balance.vacation_available_total,
            vacation_available_ap=balance.vacation_available_ap,
            vacation_available_ac=balance.vacation_available_ac,
            vacation_used=balance.vacation_used,
            vacation_pending=vacation_pending,
            ap_expiry_date=balance.ap_expiry_date,
            days_until_ap_expiry=days_until_ap_expiry,
            rol_available=balance.rol_available,
            rol_used=balance.rol_used,
            rol_pending=rol_pending,
            permits_available=balance.permits_available,
            permits_used=balance.permits_used,
            permits_pending=permits_pending,
        )

    async def adjust_balance(
        self,
        user_id: UUID,
        year: int,
        data: BalanceAdjustment,
        admin_id: UUID,
    ):
        """Manually adjust a balance (admin only)."""
        balance = await self._balance_repo.get_or_create(user_id, year)
        
        # Map balance type to field
        field_map = {
            "vacation_ap": "vacation_previous_year",
            "vacation_ac": "vacation_current_year",
            "rol": "rol_current_year",
            "permits": "permits_total",
        }
        
        field = field_map.get(data.balance_type)
        if not field:
            raise ValidationError(f"Invalid balance type: {data.balance_type}")
        
        current = getattr(balance, field)
        new_value = current + data.amount
        
        await self._balance_repo.update(balance.id, **{field: new_value})
        
        await self._balance_repo.add_transaction(
            balance_id=balance.id,
            transaction_type="adjustment",
            balance_type=data.balance_type,
            amount=data.amount,
            balance_after=new_value,
            reason=data.reason,
            created_by=admin_id,
        )
        
        return await self.get_balance(user_id, year)

    # ═══════════════════════════════════════════════════════════
    # Calendar Operations
    # ═══════════════════════════════════════════════════════════

    async def get_calendar(
        self,
        request: CalendarRequest,
        user_id: UUID,
        is_manager: bool = False,
    ) -> CalendarResponse:
        """Get calendar events for FullCalendar."""
        events = []
        
        # Determine which users to include
        user_ids = [user_id]
        if request.include_team and is_manager:
            # Get subordinates from auth service
            subordinates = await self._get_subordinates(user_id)
            user_ids.extend(subordinates)
        
        # Get requests
        requests = await self._request_repo.get_by_date_range(
            start_date=request.start_date,
            end_date=request.end_date,
            user_ids=user_ids,
            status=[
                LeaveRequestStatus.APPROVED,
                LeaveRequestStatus.PENDING,
                LeaveRequestStatus.APPROVED_CONDITIONAL,
            ],
        )
        
        for req in requests:
            color = self._get_event_color(req.status, req.leave_type_code)
            events.append(CalendarEvent(
                id=str(req.id),
                title=f"{req.leave_type_code}",
                start=req.start_date,
                end=req.end_date,
                color=color,
                extendedProps={
                    "status": req.status.value,
                    "days": float(req.days_requested),
                    "user_id": str(req.user_id),
                },
            ))
        
        # Get holidays
        holidays = []
        if request.include_holidays:
            raw_holidays = await self._get_holidays(
                request.start_date.year,
                request.start_date,
                request.end_date,
            )
            holidays = [
                CalendarEvent(
                    id=f"hol_{h['id']}",
                    title=h['name'],
                    start=h['date'],
                    end=h['date'],
                    allDay=True,
                    color="#F59E0B",  # Orange for holidays
                    extendedProps={"type": "holiday"}
                )
                for h in raw_holidays
                if isinstance(h, dict) and 'id' in h and 'name' in h and 'date' in h
            ]
            
        return CalendarResponse(events=events, holidays=holidays)

    # ═══════════════════════════════════════════════════════════
    # Private Helpers
    # ═══════════════════════════════════════════════════════════

    async def _get_system_config(self, key: str, default: any = None) -> any:
        """Get global system config."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/config/{key}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("value", default)
        except Exception:
            pass
        return default

    async def _get_leave_type(self, leave_type_id: UUID) -> Optional[dict]:
        """Get leave type from config service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/leave-types/{leave_type_id}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    async def _calculate_days(
        self,
        start_date: date,
        end_date: date,
        start_half: bool,
        end_half: bool,
        user_id: UUID,
    ) -> Decimal:
        """Calculate working days between dates.
        
        Excludes weekends. Holidays can be excluded via config.
        """
        from datetime import timedelta
        
        # Get holidays for the period
        holidays = await self._get_holidays(
            start_date.year,
            start_date,
            end_date,
        )
        holiday_dates = {h.get("date") for h in holidays if h.get("date")}
        
        # Get working days config (default 5: Mon-Fri)
        working_days_limit = await self._get_system_config("work_week_days", 5)
        try:
            working_days_limit = int(working_days_limit)
        except (ValueError, TypeError):
            working_days_limit = 5
        
        # Count working days
        working_days = 0
        current = start_date
        while current <= end_date:
            # Skip non-working days (based on config, e.g. < 5 for Mon-Fri, < 6 for Mon-Sat)
            if current.weekday() < working_days_limit:
                # Skip holidays
                if current.isoformat() not in holiday_dates:
                    working_days += 1
            current += timedelta(days=1)
        
        # Apply half-day adjustments
        if start_half and working_days > 0:
            working_days -= 0.5
        if end_half and working_days > 0:
            working_days -= 0.5
        
        return Decimal(str(max(working_days, 0)))

    async def _deduct_balance(
        self,
        request: LeaveRequest,
        breakdown: dict,
    ) -> None:
        """Deduct balance based on breakdown."""
        if not breakdown:
            return
        
        balance = await self._balance_repo.get_or_create(
            request.user_id,
            request.start_date.year,
        )
        
        for balance_type, amount in breakdown.items():
            if amount <= 0:
                continue
            
            if balance_type == "vacation_ap":
                new_value = balance.vacation_used_ap + Decimal(str(amount))
                await self._balance_repo.update(balance.id, vacation_used_ap=new_value)
            elif balance_type == "vacation_ac":
                new_value = balance.vacation_used_ac + Decimal(str(amount))
                await self._balance_repo.update(balance.id, vacation_used_ac=new_value)
            elif balance_type == "rol":
                new_value = balance.rol_used + Decimal(str(amount))
                await self._balance_repo.update(balance.id, rol_used=new_value)
            elif balance_type == "permits":
                new_value = balance.permits_used + Decimal(str(amount))
                await self._balance_repo.update(balance.id, permits_used=new_value)
            
            await self._balance_repo.add_transaction(
                balance_id=balance.id,
                leave_request_id=request.id,
                transaction_type="deduction",
                balance_type=balance_type,
                amount=-Decimal(str(amount)),
                balance_after=new_value,
            )
        
        await self._request_repo.update(request.id, balance_deducted=True)

    async def _restore_balance(self, request: LeaveRequest) -> None:
        """Restore balance when request is cancelled/recalled."""
        breakdown = request.deduction_details or {}
        
        balance = await self._balance_repo.get_by_user_year(
            request.user_id,
            request.start_date.year,
        )
        
        if not balance:
            return
        
        for balance_type, amount in breakdown.items():
            if amount <= 0:
                continue
            
            if balance_type == "vacation_ap":
                new_value = balance.vacation_used_ap - Decimal(str(amount))
                await self._balance_repo.update(balance.id, vacation_used_ap=new_value)
            elif balance_type == "vacation_ac":
                new_value = balance.vacation_used_ac - Decimal(str(amount))
                await self._balance_repo.update(balance.id, vacation_used_ac=new_value)
            elif balance_type == "rol":
                new_value = balance.rol_used - Decimal(str(amount))
                await self._balance_repo.update(balance.id, rol_used=new_value)
            elif balance_type == "permits":
                new_value = balance.permits_used - Decimal(str(amount))
                await self._balance_repo.update(balance.id, permits_used=new_value)
            
            await self._balance_repo.add_transaction(
                balance_id=balance.id,
                leave_request_id=request.id,
                transaction_type="restore",
                balance_type=balance_type,
                amount=Decimal(str(amount)),
                balance_after=new_value,
            )
        
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
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/users/subordinates/{manager_id}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return [UUID(u.get("id")) for u in data if u.get("id")]
        except Exception:
            pass
        return []

    async def _get_holidays(
        self,
        year: int,
        start_date: date = None,
        end_date: date = None,
    ) -> list[dict]:
        """Get holidays from config service."""
        try:
            async with httpx.AsyncClient() as client:
                params = {"year": year}
                if start_date:
                    params["start_date"] = start_date.isoformat()
                if end_date:
                    params["end_date"] = end_date.isoformat()
                
                response = await client.get(
                    f"{settings.config_service_url}/api/v1/holidays",
                    params=params,
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        return data.get("items", [])
                    return data if isinstance(data, list) else []
        except Exception:
            pass
        return []

    async def _send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        entity_type: str = None,
        entity_id: str = None,
    ) -> None:
        """Send notification via notification-service."""
        try:
            # Get user email from auth service
            user_email = await self._get_user_email(user_id)
            if not user_email:
                return
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.notification_service_url}/api/v1/notifications",
                    json={
                        "user_id": str(user_id),
                        "user_email": user_email,
                        "notification_type": notification_type,
                        "title": title,
                        "message": message,
                        "channel": "in_app",
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                    },
                    timeout=5.0,
                )
        except Exception:
            # Notifications are not critical - fail silently
            pass

    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/users/{user_id}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return response.json().get("email")
        except Exception:
            pass
        return None
