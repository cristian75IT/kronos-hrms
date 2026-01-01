from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select, or_, func
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
from src.services.config.models import NationalContract, NationalContractVersion, NationalContractTypeConfig
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus, ConditionType, LeaveBalance
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

    async def preview_recalculate(self, year: int) -> list[dict]:
        """Preview recalculation without persisting changes."""
        from src.services.auth.models import User
        
        previews = []
        
        # Get all users with contracts
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()
        
        for user_id in user_ids:
            # Get current balance
            balance = await self._balance_repo.get_by_user_year(user_id, year)
            current_vacation = float(balance.vacation_accrued) if balance else 0
            current_rol = float(balance.rol_accrued) if balance else 0
            current_permits = float(balance.permits_total) if balance else 0
            
            # Calculate new values without persisting
            new_vacation, new_rol, new_permits = await self._calculate_accrual_preview(user_id, year)
            
            # Get user name
            user_query = select(User).where(User.keycloak_id == str(user_id))
            user_result = await self._session.execute(user_query)
            user = user_result.scalar_one_or_none()
            name = f"{user.first_name} {user.last_name}" if user else str(user_id)
            
            previews.append({
                "user_id": user_id,
                "name": name,
                "current_vacation": current_vacation,
                "new_vacation": new_vacation,
                "current_rol": current_rol,
                "new_rol": new_rol,
                "current_permits": current_permits,
                "new_permits": new_permits
            })
        
        return previews

    async def preview_rollover(self, from_year: int) -> list[dict]:
        """Preview rollover without persisting changes."""
        from src.services.auth.models import User
        
        previews = []
        to_year = from_year + 1
        
        # Get all balances for the source year
        query = select(LeaveBalance).where(LeaveBalance.year == from_year)
        result = await self._session.execute(query)
        source_balances = result.scalars().all()
        
        for src in source_balances:
            # Get current values
            vacation_rem = float(src.vacation_available_total)
            rol_rem = float(src.rol_available)
            permits_rem = float(src.permits_available)
            
            # Get destination balance if exists
            dst = await self._balance_repo.get_by_user_year(src.user_id, to_year)
            current_vacation_ap = float(dst.vacation_previous_year) if dst else 0
            current_rol_ap = float(dst.rol_previous_year) if dst else 0
            
            # Get user name
            user_query = select(User).where(User.keycloak_id == str(src.user_id))
            user_result = await self._session.execute(user_query)
            user = user_result.scalar_one_or_none()
            name = f"{user.first_name} {user.last_name}" if user else str(src.user_id)
            
            previews.append({
                "user_id": src.user_id,
                "name": name,
                "current_vacation": current_vacation_ap,
                "new_vacation": current_vacation_ap + vacation_rem,
                "current_rol": current_rol_ap,
                "new_rol": current_rol_ap + rol_rem,
                "current_permits": 0,
                "new_permits": permits_rem
            })
        
        return previews

    async def apply_recalculate_selected(self, year: int, user_ids: list[UUID]):
        """Apply recalculation only to selected users."""
        for user_id in user_ids:
            await self.recalculate_user_accrual(user_id, year)

    async def apply_rollover_selected(self, from_year: int, user_ids: list[UUID]):
        """Apply rollover only to selected users."""
        to_year = from_year + 1
        
        for user_id in user_ids:
            # Get source balance
            query = select(LeaveBalance).where(
                LeaveBalance.user_id == user_id,
                LeaveBalance.year == from_year
            )
            result = await self._session.execute(query)
            src = result.scalar_one_or_none()
            
            if not src:
                continue
                
            vacation_rem = src.vacation_available_total
            rol_rem = src.rol_available
            permits_rem = src.permits_available
            
            # Get/create destination balance
            dst = await self._balance_repo.get_or_create(user_id, to_year)
            
            vacation_expiry = date(to_year + 1, 6, 30)
            rol_expiry = date(to_year + 2, 12, 31)
            
            await self._balance_repo.update(
                dst.id,
                vacation_previous_year=vacation_rem,
                rol_previous_year=rol_rem,
                permits_total=permits_rem,
                ap_expiry_date=vacation_expiry
            )
            
            if vacation_rem > 0:
                await self._balance_repo.add_transaction(
                    balance_id=dst.id,
                    transaction_type="carry_over",
                    balance_type="vacation_ap",
                    amount=vacation_rem,
                    balance_after=vacation_rem,
                    reason=f"Recupero ferie residue anno {from_year}",
                    expiry_date=vacation_expiry
                )
            
            if rol_rem > 0:
                await self._balance_repo.add_transaction(
                    balance_id=dst.id,
                    transaction_type="carry_over",
                    balance_type="rol",
                    amount=rol_rem,
                    balance_after=rol_rem,
                    reason=f"Recupero ROL residui anno {from_year}",
                    expiry_date=rol_expiry
                )
        
        await self._session.commit()
        return len(user_ids)

    async def _calculate_accrual_preview(self, user_id: UUID, year: int) -> tuple[float, float, float]:
        """Calculate accrual values without persisting."""
        query = (
            select(EmployeeContract)
            .options(selectinload(EmployeeContract.contract_type))
            .where(EmployeeContract.user_id == user_id)
            .order_by(EmployeeContract.start_date)
        )
        result = await self._session.execute(query)
        contracts = result.scalars().all()

        if not contracts:
            return (0, 0, 0)

        total_vacation = Decimal(0)
        total_rol = Decimal(0)
        total_permits = Decimal(0)
        
        today = date.today()
        
        for month in range(1, 13):
            month_start = date(year, month, 1)
            _, last_day = monthrange(year, month)
            month_end = date(year, month, last_day)
            
            if month_start > today:
                break
                
            active_contract = None
            for contract in contracts:
                c_start = contract.start_date
                c_end = contract.end_date or date(9999, 12, 31)
                
                if c_start <= month_end and c_end >= month_start:
                    active_contract = contract
                    if c_start <= month_start:
                        break
            
            if active_contract:
                params = await self._get_monthly_accrual_params(active_contract, month_start)
                
                if params:
                    monthly_vacation = params["vacation"] / 12
                    monthly_rol = params["rol"] / 12
                    monthly_permits = params["permits"] / 12
                    full_time_base = params["full_time_hours"]
                    
                    if active_contract.weekly_hours is not None:
                        ratio = Decimal(active_contract.weekly_hours) / full_time_base
                    else:
                        ratio = Decimal(1.0)
                    
                    if ratio != Decimal(1.0):
                        monthly_vacation *= ratio
                        monthly_rol *= ratio
                        monthly_permits *= ratio
                    
                    total_vacation += monthly_vacation
                    total_rol += monthly_rol
                    total_permits += monthly_permits

        return (float(total_vacation), float(total_rol), float(total_permits))

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
            
            if active_contract:
                params = await self._get_monthly_accrual_params(active_contract, month_start)
                
                if params:
                    # Resolve Strategies
                    vac_mode = params.get("vacation_mode")
                    rol_mode = params.get("rol_mode")
                    
                    vac_strategy = StrategyFactory.get(vac_mode.function_name if vac_mode else "")
                    rol_strategy = StrategyFactory.get(rol_mode.function_name if rol_mode else "")
                    
                    # Prepare Params (handle 'divisors' mapping for MonthlyStandard)
                    vac_params = vac_mode.default_parameters.copy() if vac_mode and vac_mode.default_parameters else {}
                    rol_params = rol_mode.default_parameters.copy() if rol_mode and rol_mode.default_parameters else {}
                    
                    if "divisors" in vac_params and isinstance(vac_params["divisors"], dict):
                        vac_params["divisor"] = vac_params["divisors"].get("vacation", 12)
                        
                    if "divisors" in rol_params and isinstance(rol_params["divisors"], dict):
                        rol_params["divisor"] = rol_params["divisors"].get("rol", 12)

                    # Calculate
                    monthly_vacation = vac_strategy.calculate(
                        params["vacation"], active_contract, month_start, month_end, vac_params
                    )
                    monthly_rol = rol_strategy.calculate(
                        params["rol"], active_contract, month_start, month_end, rol_params
                    )
                    # Permits typically follow ROL strategy
                    monthly_permits = rol_strategy.calculate(
                        params["permits"], active_contract, month_start, month_end, rol_params
                    )
                    
                    full_time_base = params["full_time_hours"]
                    
                    # Adjust for Part-Time ratio
                    if active_contract.weekly_hours is not None:
                        ratio = Decimal(active_contract.weekly_hours) / full_time_base
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

    async def _get_monthly_accrual_params(self, contract: EmployeeContract, reference_date: date):
        """Resolve accrual parameters from CCNL config or legacy fallback."""
        # 1. Try CCNL config
        if contract.national_contract_id:
            query = (
                select(NationalContractVersion)
                .where(
                    NationalContractVersion.national_contract_id == contract.national_contract_id,
                    NationalContractVersion.valid_from <= reference_date,
                    or_(
                        NationalContractVersion.valid_to >= reference_date,
                        NationalContractVersion.valid_to == None
                    )
                )
                .options(
                selectinload(NationalContractVersion.contract_type_configs),
                selectinload(NationalContractVersion.vacation_calc_mode),
                selectinload(NationalContractVersion.rol_calc_mode)
            )
                .order_by(NationalContractVersion.valid_from.desc())
                .limit(1)
            )
            result = await self._session.execute(query)
            version = result.scalar_one_or_none()
            
            if version:
                # Find type config override
                type_config = next(
                    (c for c in version.contract_type_configs if c.contract_type_id == contract.contract_type_id),
                    None
                )
                
                if type_config:
                    return {
                        "vacation": Decimal(type_config.annual_vacation_days),
                        "rol": Decimal(type_config.annual_rol_hours),
                        "permits": Decimal(type_config.annual_ex_festivita_hours),
                        "full_time_hours": Decimal(type_config.weekly_hours if type_config.weekly_hours > 0 else version.weekly_hours_full_time),
                        "vacation_mode": version.vacation_calc_mode,
                        "rol_mode": version.rol_calc_mode
                    }
                
                # Fallback to version defaults
                return {
                    "vacation": Decimal(version.annual_vacation_days),
                    "rol": Decimal(version.annual_rol_hours),
                    "permits": Decimal(version.annual_ex_festivita_hours),
                    "full_time_hours": Decimal(version.weekly_hours_full_time),
                    "vacation_mode": version.vacation_calc_mode,
                    "rol_mode": version.rol_calc_mode
                }

        # 2. Legacy fallback to ContractType
        if contract.contract_type:
            ctype = contract.contract_type
            return {
                "vacation": Decimal(ctype.annual_vacation_days),
                "rol": Decimal(ctype.annual_rol_hours),
                "permits": Decimal(ctype.annual_permit_hours),
                "full_time_hours": Decimal(40.0)
            }
            
        return None

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

    async def get_excluded_days(self, start_date: date, end_date: date) -> dict:
        """Get detailed list of excluded days (weekends, holidays, closures) in a date range."""
        from datetime import timedelta
        
        excluded = []
        
        # Get holidays for the period
        holidays = await self._get_holidays(start_date.year, start_date, end_date)
        holiday_map = {}
        for h in holidays:
            h_date = h.get("date")
            if h_date:
                holiday_map[h_date] = h.get("name", "Festività")
        
        # Get company closures for the period
        closures = await self._get_company_closures(start_date, end_date)
        closure_map = {}
        for closure in closures:
            if closure.get("closure_type") == "total":
                closure_start = closure.get("start_date")
                closure_end = closure.get("end_date")
                closure_name = closure.get("name", "Chiusura Aziendale")
                if closure_start and closure_end:
                    try:
                        c_start = date.fromisoformat(closure_start) if isinstance(closure_start, str) else closure_start
                        c_end = date.fromisoformat(closure_end) if isinstance(closure_end, str) else closure_end
                        current_closure = c_start
                        while current_closure <= c_end:
                            closure_map[current_closure.isoformat()] = closure_name
                            current_closure += timedelta(days=1)
                    except (ValueError, TypeError):
                        pass
        
        # Get working days config (default 5: Mon-Fri)
        working_days_limit = await self._get_system_config("work_week_days", 5)
        try:
            working_days_limit = int(working_days_limit)
        except (ValueError, TypeError):
            working_days_limit = 5
        
        # Day names in Italian
        day_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        # Iterate through date range
        working_days = 0
        current = start_date
        while current <= end_date:
            current_iso = current.isoformat()
            weekday = current.weekday()
            
            # Check if weekend (based on config)
            if weekday >= working_days_limit:
                excluded.append({
                    "date": current,
                    "reason": "weekend",
                    "name": day_names[weekday]
                })
            # Check if holiday
            elif current_iso in holiday_map:
                excluded.append({
                    "date": current,
                    "reason": "holiday",
                    "name": holiday_map[current_iso]
                })
            # Check if closure
            elif current_iso in closure_map:
                excluded.append({
                    "date": current,
                    "reason": "closure",
                    "name": closure_map[current_iso]
                })
            else:
                working_days += 1
            
            current += timedelta(days=1)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "working_days": working_days,
            "excluded_days": excluded
        }

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
            expiry_date=data.expiry_date,
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
                    color="#EF4444" if h.get('is_national') else "#3B82F6" if h.get('is_regional') else "#F59E0B",
                    extendedProps={
                        "type": "holiday",
                        "is_national": h.get('is_national', False),
                        "is_regional": h.get('is_regional', False),
                    }
                )
                for h in raw_holidays
                if isinstance(h, dict) and 'id' in h and 'name' in h and 'date' in h
            ]
        
        # Get company closures
        closures = []
        raw_closures = await self._get_company_closures(request.start_date, request.end_date)
        for closure in raw_closures:
            closure_start = closure.get("start_date")
            closure_end = closure.get("end_date")
            if closure_start and closure_end:
                closures.append(CalendarEvent(
                    id=f"closure_{closure.get('id', 'unknown')}",
                    title=closure.get('name', 'Chiusura'),
                    start=closure_start,
                    end=closure_end,
                    allDay=True,
                    color="#9333EA",  # Purple for closures
                    extendedProps={
                        "type": "closure",
                        "closure_type": closure.get('closure_type', 'total'),
                        "is_paid": closure.get('is_paid', True),
                        "consumes_leave_balance": closure.get('consumes_leave_balance', False),
                        "description": closure.get('description', ''),
                    }
                ))
            
        return CalendarResponse(events=events, holidays=holidays, closures=closures)

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
        user_id: Optional[UUID] = None,
    ) -> Decimal:
        """Calculate working days between dates.
        
        Excludes:
        - Weekends (based on work_week_days config)
        - National, regional, and local holidays
        - Company closure days (total closures)
        """
        from datetime import timedelta
        
        # Get holidays for the period
        holidays = await self._get_holidays(
            start_date.year,
            start_date,
            end_date,
        )
        holiday_dates = {h.get("date") for h in holidays if h.get("date")}
        
        # Get company closures for the period
        closures = await self._get_company_closures(start_date, end_date)
        closure_dates = set()
        for closure in closures:
            # Only exclude dates from total closures (partial closures may still be workable)
            if closure.get("closure_type") == "total":
                closure_start = closure.get("start_date")
                closure_end = closure.get("end_date")
                if closure_start and closure_end:
                    try:
                        c_start = date.fromisoformat(closure_start) if isinstance(closure_start, str) else closure_start
                        c_end = date.fromisoformat(closure_end) if isinstance(closure_end, str) else closure_end
                        current_closure = c_start
                        while current_closure <= c_end:
                            closure_dates.add(current_closure.isoformat())
                            current_closure += timedelta(days=1)
                    except (ValueError, TypeError):
                        pass
        
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
            # Skip non-working days (based on config)
            if current.weekday() < working_days_limit:
                current_iso = current.isoformat()
                # Skip holidays
                if current_iso not in holiday_dates:
                    # Skip company closures (total)
                    if current_iso not in closure_dates:
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
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
            
            new_value = Decimal(0)
            if balance_type == "vacation_ap":
                new_value = balance.vacation_used_ap + amount_dec
                await self._balance_repo.update(balance.id, vacation_used_ap=new_value)
            elif balance_type == "vacation_ac":
                new_value = balance.vacation_used_ac + amount_dec
                await self._balance_repo.update(balance.id, vacation_used_ac=new_value)
            elif balance_type == "rol":
                new_value = balance.rol_used + amount_dec
                await self._balance_repo.update(balance.id, rol_used=new_value)
            elif balance_type == "permits":
                new_value = balance.permits_used + amount_dec
                await self._balance_repo.update(balance.id, permits_used=new_value)
            
            # Consume from specific buckets (FIFO)
            await self._consume_from_buckets(balance.id, balance_type, amount_dec)
            
            # Add transaction
            await self._balance_repo.add_transaction(
                balance_id=balance.id,
                leave_request_id=request.id,
                transaction_type="deduction",
                balance_type=balance_type,
                amount=-amount_dec,
                balance_after=new_value, # Simplified
            )
        
        await self._request_repo.update(request.id, balance_deducted=True)

    async def _consume_from_buckets(self, balance_id: UUID, balance_type: str, amount: Decimal):
        """FIFO consumption of leave amounts from individual transaction buckets."""
        query = (
            select(BalanceTransaction)
            .where(
                BalanceTransaction.balance_id == balance_id,
                BalanceTransaction.balance_type == balance_type,
                BalanceTransaction.remaining_amount > 0
            )
            .order_by(
                BalanceTransaction.expiry_date.nulls_last(),
                BalanceTransaction.created_at.asc()
            )
        )
        result = await self._session.execute(query)
        buckets = result.scalars().all()
        
        remaining = amount
        for bucket in buckets:
            if remaining <= 0:
                break
            consume = min(bucket.remaining_amount, remaining)
            bucket.remaining_amount -= consume
            remaining -= consume
        
        await self._session.flush()

    async def process_expirations(self):
        """Identify and process expired leave/ROL buckets."""
        today = date.today()
        query = (
            select(BalanceTransaction)
            .where(
                BalanceTransaction.expiry_date != None,
                BalanceTransaction.expiry_date < today,
                BalanceTransaction.remaining_amount > 0
            )
        )
        result = await self._session.execute(query)
        expired_buckets = result.scalars().all()
        
        field_map = {
            "vacation_ap": "vacation_previous_year",
            "vacation_ac": "vacation_accrued",
            "rol": "rol_accrued",
            "permits": "permits_total",
        }
        
        for bucket in expired_buckets:
            expired_amount = bucket.remaining_amount
            bucket.remaining_amount = Decimal(0)
            
            balance = await self._balance_repo.get(bucket.balance_id)
            if balance:
                field = field_map.get(bucket.balance_type)
                new_balance_val = Decimal(0)
                if field:
                    current = getattr(balance, field)
                    new_balance_val = max(Decimal(0), current - expired_amount)
                    await self._balance_repo.update(balance.id, **{field: new_balance_val})
                
                # Record expiration transaction
                await self._balance_repo.add_transaction(
                    balance_id=balance.id,
                    transaction_type="expiry",
                    balance_type=bucket.balance_type,
                    amount=-expired_amount,
                    balance_after=new_balance_val,
                    reason=f"Scadenza automatica carica del {bucket.created_at.date()}",
                )
        
        return len(expired_buckets)

    async def run_monthly_accruals(self, year: int, month: int):
        """Processes monthly accruals for all active employees.
        
        Rule: If an employee has an active contract for >= 15 days in the month, 
        they get 1/12th of their annual allowance.
        """
        # Get all users with contracts
        query = select(EmployeeContract.user_id).distinct()
        result = await self._session.execute(query)
        user_ids = result.scalars().all()
        
        accrual_date = date(year, month, 1)
        _, days_in_month = monthrange(year, month)
        month_end = date(year, month, days_in_month)
        
        processed_count = 0
        for user_id in user_ids:
            # Get contracts for this user that overlap with the month
            query = (
                select(EmployeeContract)
                .where(
                    EmployeeContract.user_id == user_id,
                    EmployeeContract.start_date <= month_end,
                    or_(EmployeeContract.end_date >= accrual_date, EmployeeContract.end_date == None)
                )
                .order_by(EmployeeContract.start_date.desc())
            )
            res = await self._session.execute(query)
            contracts = res.scalars().all()
            
            if not contracts:
                continue
                
            # Find the contract that covers at least 15 days
            active_contract = None
            for contract in contracts:
                overlap_start = max(contract.start_date, accrual_date)
                overlap_end = min(contract.end_date or date(9999, 12, 31), month_end)
                overlap_days = (overlap_end - overlap_start).days + 1
                
                if overlap_days >= 15:
                    active_contract = contract
                    break
            
            if active_contract:
                params = await self._get_monthly_accrual_params(active_contract, accrual_date)
                if params:
                    full_time_base = params["full_time_hours"]
                    ratio = Decimal(active_contract.weekly_hours or full_time_base) / full_time_base
                    
                    m_vacation = (params["vacation"] / 12) * ratio
                    m_rol = (params["rol"] / 12) * ratio
                    
                    balance = await self._balance_repo.get_or_create(user_id, year)
                    
                    if m_vacation > 0:
                        new_accrued = balance.vacation_accrued + m_vacation
                        await self._balance_repo.update(balance.id, vacation_accrued=new_accrued)
                        await self._balance_repo.add_transaction(
                            balance_id=balance.id,
                            transaction_type="accrual",
                            balance_type="vacation_ac",
                            amount=m_vacation,
                            balance_after=balance.vacation_available_total + m_vacation,
                            reason=f"Maturazione mensile {month}/{year}",
                            expiry_date=date(year + 1, 6, 30)
                        )

                    if m_rol > 0:
                        new_rol = balance.rol_accrued + m_rol
                        await self._balance_repo.update(balance.id, rol_accrued=new_rol)
                        await self._balance_repo.add_transaction(
                            balance_id=balance.id,
                            transaction_type="accrual",
                            balance_type="rol",
                            amount=m_rol,
                            balance_after=balance.rol_available + m_rol,
                            reason=f"Maturazione mensile ROL {month}/{year}",
                            expiry_date=date(year + 2, 12, 31)
                        )
                    processed_count += 1
        return processed_count

    async def run_year_end_rollover(self, from_year: int):
        """Processes year-end rollover from from_year to from_year + 1.
        
        Transfers remaining AC and AP balances to the new year's AP buckets.
        """
        to_year = from_year + 1
        
        # Get all balances for the source year
        query = select(LeaveBalance).where(LeaveBalance.year == from_year)
        result = await self._session.execute(query)
        source_balances = result.scalars().all()
        
        processed_count = 0
        for src in source_balances:
            # Calculate remaining totals
            vacation_rem = src.vacation_available_total
            rol_rem = src.rol_available
            permits_rem = src.permits_available
            
            # Create/Get new year balance
            dst = await self._balance_repo.get_or_create(src.user_id, to_year)
            
            # Use CCNL rules for expiry dates if possible
            # We fetch the contract active at the end of the year
            last_day = date(from_year, 12, 31)
            query = (
                select(EmployeeContract)
                .where(
                    EmployeeContract.user_id == src.user_id,
                    EmployeeContract.start_date <= last_day,
                    or_(EmployeeContract.end_date >= last_day, EmployeeContract.end_date == None)
                )
                .limit(1)
            )
            res = await self._session.execute(query)
            contract = res.scalar_one_or_none()
            
            vacation_expiry = date(to_year + 1, 6, 30) # Default 18 months
            rol_expiry = date(to_year + 2, 12, 31)    # Default 24 months
            
            if contract and contract.national_contract_id:
                # We can refine this using _get_monthly_accrual_params helper if extended
                # but for simplicity we use defaults or fetch the version once
                pass 

            # Update Destination Balance
            await self._balance_repo.update(
                dst.id,
                vacation_previous_year=vacation_rem,
                rol_previous_year=rol_rem,
                permits_total=permits_rem, # Permits usually just roll over as total
                ap_expiry_date=vacation_expiry # This often reflects the Vacation AP deadline
            )
            
            # Record Transactions in the NEW year with expiry dates
            if vacation_rem > 0:
                await self._balance_repo.add_transaction(
                    balance_id=dst.id,
                    transaction_type="carry_over",
                    balance_type="vacation_ap",
                    amount=vacation_rem,
                    balance_after=vacation_rem,
                    reason=f"Recupero ferie residue anno {from_year}",
                    expiry_date=vacation_expiry
                )
            
            if rol_rem > 0:
                await self._balance_repo.add_transaction(
                    balance_id=dst.id,
                    transaction_type="carry_over",
                    balance_type="rol",
                    amount=rol_rem,
                    balance_after=rol_rem,
                    reason=f"Recupero ROL residui anno {from_year}",
                    expiry_date=rol_expiry
                )
            
            processed_count += 1
            
        await self._session.commit()
        return processed_count

    async def _restore_balance(self, request: LeaveRequest) -> None:
        """Restore balance when request is cancelled/recalled."""
        breakdown = request.deduction_details or {}
        balance = await self._balance_repo.get_by_user_year(request.user_id, request.start_date.year)
        
        if not balance:
            return
        
        for balance_type, amount in breakdown.items():
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
                
            new_val = Decimal(0)
            if balance_type == "vacation_ap":
                new_val = max(Decimal(0), balance.vacation_used_ap - amount_dec)
                await self._balance_repo.update(balance.id, vacation_used_ap=new_val)
            elif balance_type == "vacation_ac":
                new_val = max(Decimal(0), balance.vacation_used_ac - amount_dec)
                await self._balance_repo.update(balance.id, vacation_used_ac=new_val)
            elif balance_type == "rol":
                new_val = max(Decimal(0), balance.rol_used - amount_dec)
                await self._balance_repo.update(balance.id, rol_used=new_val)
            elif balance_type == "permits":
                new_val = max(Decimal(0), balance.permits_used - amount_dec)
                await self._balance_repo.update(balance.id, permits_used=new_val)
            
            # Simple restoration as a positive transaction with no expiry
            await self._balance_repo.add_transaction(
                balance_id=balance.id,
                transaction_type="adjustment",
                balance_type=balance_type,
                amount=amount_dec,
                balance_after=0, # placeholder
                reason=f"Ripristino per cancellazione richiesta {request.id}",
                leave_request_id=request.id
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

    async def _get_company_closures(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """Get company closures from config service for date range.
        
        Returns closures that overlap with the given date range.
        Used to exclude closure days from working days calculation.
        """
        try:
            # Get closures for all years that overlap with the date range
            years = set()
            years.add(start_date.year)
            years.add(end_date.year)
            
            all_closures = []
            async with httpx.AsyncClient() as client:
                for year in years:
                    response = await client.get(
                        f"{settings.config_service_url}/api/v1/closures",
                        params={"year": year},
                        timeout=5.0,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        closures = data.get("items", []) if isinstance(data, dict) else []
                        
                        # Filter closures that overlap with our date range
                        for closure in closures:
                            closure_start = closure.get("start_date")
                            closure_end = closure.get("end_date")
                            if closure_start and closure_end:
                                try:
                                    c_start = date.fromisoformat(closure_start) if isinstance(closure_start, str) else closure_start
                                    c_end = date.fromisoformat(closure_end) if isinstance(closure_end, str) else closure_end
                                    # Check overlap
                                    if c_start <= end_date and c_end >= start_date:
                                        all_closures.append(closure)
                                except (ValueError, TypeError):
                                    pass
            
            return all_closures
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
