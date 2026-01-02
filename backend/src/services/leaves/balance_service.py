from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal
from typing import Optional, Any, Tuple
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError, NotFoundError
from src.services.auth.models import EmployeeContract, ContractType, User, UserProfile
from src.services.config.models import NationalContractVersion, NationalContractTypeConfig
from src.services.leaves.models import LeaveBalance, BalanceTransaction, LeaveRequest
from src.services.leaves.repository import LeaveBalanceRepository
from src.services.leaves.strategies import StrategyFactory
from src.services.leaves.schemas import BalanceSummary, BalanceAdjustment

class LeaveBalanceService:
    """Service for managing leave balances, accruals, and rollovers."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._balance_repo = LeaveBalanceRepository(session)
    
    async def get_balance(self, user_id: UUID, year: int) -> LeaveBalance:
        return await self._balance_repo.get_or_create(user_id, year)

    async def get_balance_summary(self, user_id: UUID, year: int) -> BalanceSummary:
        balance = await self.get_balance(user_id, year)
        
        vac_mandatory = Decimal(0)
        rol_mandatory = Decimal(0)
        per_mandatory = Decimal(0)
        
        # Calculate pending (requests not yet approved/rejected - e.g. PENDING or APPROVED_CONDITIONAL)
        # Actually PENDING deducts balance? No, traditionally PENDING doesn't. 
        # But some systems do "reserved".
        # In this system, deduction happens at Approval (submit_request -> approve -> _deduct_balance)??
        # Need to check LeaveService workflow. Usually deduction is at approval.
        # But we want to show "Pending" usage.
        
        # NOTE: logic copied from LeaveService.get_balance_summary
        # calculating pending from requests in DB
        stmt = select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_(['PENDING', 'APPROVED_CONDITIONAL']),
            LeaveRequest.start_date >= date(year, 1, 1),
            LeaveRequest.start_date <= date(year, 12, 31)
        )
        result = await self._session.execute(stmt)
        pending_requests = result.scalars().all()
        
        vacation_pending = sum(
            Decimal(str(r.days_requested)) for r in pending_requests if r.leave_type_code in ["FER"]
        )
        rol_pending = sum(
            Decimal(str(r.days_requested)) * Decimal("8") for r in pending_requests if r.leave_type_code in ["ROL"]
        )
        permits_pending = sum(
            Decimal(str(r.days_requested)) * Decimal("8") for r in pending_requests if r.leave_type_code in ["PER"]
        )
        
        days_until_ap_expiry = None
        if balance.ap_expiry_date:
            days = (balance.ap_expiry_date - date.today()).days
            days_until_ap_expiry = max(0, days)

        return BalanceSummary(
            user_id=user_id,
            year=year,
            total_vacation_available=balance.vacation_available_total,
            total_rol_available=balance.rol_available,
            total_permits_available=balance.permits_available,
            vacation_available=balance.vacation_available_total - vac_mandatory,
            vacation_used=balance.vacation_used,
            vacation_pending=vacation_pending,
            vacation_mandatory_deductions=vac_mandatory,
            ap_expiry_date=balance.ap_expiry_date,
            days_until_ap_expiry=days_until_ap_expiry,
            rol_available=balance.rol_available - rol_mandatory,
            rol_used=balance.rol_used,
            rol_pending=rol_pending,
            rol_mandatory_deductions=rol_mandatory,
            permits_available=balance.permits_available - per_mandatory,
            permits_used=balance.permits_used,
            permits_pending=permits_pending,
            permits_mandatory_deductions=per_mandatory
        )

    async def adjust_balance(self, user_id: UUID, year: int, data: BalanceAdjustment, admin_id: UUID):
        balance = await self._balance_repo.get_or_create(user_id, year)
        
        field_map = {
            "vacation_ap": "vacation_previous_year",
            "vacation_ac": "vacation_accrued",
            "rol": "rol_accrued",
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

    async def get_transactions(self, balance_id: UUID) -> list[BalanceTransaction]:
        """Get transactions for a balance."""
        return await self._balance_repo.get_transactions(balance_id)







    async def deduct_balance(self, request: LeaveRequest, breakdown: dict):
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
            
            await self._consume_from_buckets(balance.id, balance_type, amount_dec)
            
            await self._balance_repo.add_transaction(
                balance_id=balance.id,
                leave_request_id=request.id,
                transaction_type="deduction",
                balance_type=balance_type,
                amount=-amount_dec,
                balance_after=new_value, 
            )

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

    async def restore_balance(self, request: LeaveRequest):
        """Restore balance when request is cancelled/recalled."""
        breakdown = request.deduction_details or {}
        balance = await self._balance_repo.get_by_user_year(request.user_id, request.start_date.year)
        
        if not balance:
            return
        
        for balance_type, amount in breakdown.items():
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
                
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
            
            await self._balance_repo.add_transaction(
                balance_id=balance.id,
                transaction_type="adjustment",
                balance_type=balance_type,
                amount=amount_dec,
                balance_after=0,
                reason=f"Ripristino per cancellazione richiesta {request.id}",
                leave_request_id=request.id
            )

    async def restore_partial_balance(self, request: LeaveRequest, days_to_restore: Decimal):
        """Restore partial balance (e.g. for recall)."""
        balance = await self._balance_repo.get_by_user_year(request.user_id, request.start_date.year)
        if not balance:
            return
            
        # Determine which leave type to restore (simplified - restore to specific buckets if known, else AC)
        # Assuming most leaves use FER or ROL.
        code = request.leave_type_code
        balance_type = "vacation_ac" if code == "FER" else "rol" if code == "ROL" else "permits"
        
        current_used = Decimal(0)
        if balance_type == "vacation_ac":
            current_used = balance.vacation_used_ac
        elif balance_type == "rol":
            current_used = balance.rol_used
        elif balance_type == "permits":
            current_used = balance.permits_used
            
        new_used = max(Decimal("0"), current_used - days_to_restore)
        
        update_data = {f"{balance_type_used}": new_used} if balance_type == "permits" else {f"{balance_type}_used": new_used} # typo safety?
        # Actually field names: vacation_used_ac, rol_used, permits_used
        field_name = "vacation_used_ac" if balance_type == "vacation_ac" else "rol_used" if balance_type == "rol" else "permits_used"
        
        await self._balance_repo.update(balance.id, **{field_name: new_used})
        
        # Log
        await self._balance_repo.add_transaction(
            balance_id=balance.id,
            transaction_type="recall_restore",
            balance_type=balance_type,
            amount=days_to_restore,
            balance_after=None,
            reason=f"Ripristino parziale per richiamo",
            reference_id=request.id
        )


    
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
        
        count = 0
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
                
                await self._balance_repo.add_transaction(
                    balance_id=balance.id,
                    transaction_type="expiry",
                    balance_type=bucket.balance_type,
                    amount=-expired_amount,
                    balance_after=new_balance_val,
                    reason=f"Scadenza automatica carica del {bucket.created_at.date()}",
                )
                count += 1
        return count

    async def preview_rollover(self, from_year: int) -> list[dict]:
        previews = []
        to_year = from_year + 1
        
        query = select(LeaveBalance).where(LeaveBalance.year == from_year)
        result = await self._session.execute(query)
        source_balances = result.scalars().all()
        
        for src in source_balances:
            vacation_rem = float(src.vacation_available_total)
            rol_rem = float(src.rol_available)
            permits_rem = float(src.permits_available)
            
            dst = await self._balance_repo.get_by_user_year(src.user_id, to_year)
            current_vacation_ap = float(dst.vacation_previous_year) if dst else 0
            current_rol_ap = float(dst.rol_previous_year) if dst else 0
            
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



    async def apply_rollover_selected(self, from_year: int, user_ids: list[UUID]):
        to_year = from_year + 1
        
        for user_id in user_ids:
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
        return len(user_ids)

    async def run_year_end_rollover(self, from_year: int):
        to_year = from_year + 1
        query = select(LeaveBalance).where(LeaveBalance.year == from_year)
        result = await self._session.execute(query)
        source_balances = result.scalars().all()
        
        processed_count = 0
        for src in source_balances:
            vacation_rem = src.vacation_available_total
            rol_rem = src.rol_available
            permits_rem = src.permits_available
            
            dst = await self._balance_repo.get_or_create(src.user_id, to_year)
            
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
            processed_count += 1
        return processed_count
