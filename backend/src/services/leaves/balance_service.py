"""
KRONOS - Leave Balance Service

Manages leave balances by integrating with the Wallet module (now local).
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.leaves.repository import LeaveRequestRepository
from src.services.leaves.schemas import BalanceSummary, BalanceAdjustment
from src.services.leaves.models import LeaveRequest
from src.services.leaves.wallet import WalletService, TransactionCreate


class LeaveBalanceService:
    """Service for managing leave balances - now uses local WalletService."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._wallet_service = WalletService(session)
    
    async def get_balance(self, user_id: UUID, year: int) -> dict:
        """Get wallet data from local WalletService."""
        wallet = await self._wallet_service.get_wallet(user_id, year)
        
        return {
            "id": str(wallet.id),
            "user_id": str(wallet.user_id),
            "year": wallet.year,
            "vacation_previous_year": wallet.vacation_previous_year,
            "vacation_current_year": wallet.vacation_current_year,
            "vacation_accrued": wallet.vacation_accrued,
            "vacation_used": wallet.vacation_used,
            "vacation_used_ap": wallet.vacation_used_ap,
            "vacation_used_ac": wallet.vacation_used_ac,
            "vacation_available_ap": wallet.vacation_available_ap,
            "vacation_available_ac": wallet.vacation_available_ac,
            "vacation_available_total": wallet.vacation_available_total,
            "rol_previous_year": wallet.rol_previous_year,
            "rol_current_year": wallet.rol_current_year,
            "rol_accrued": wallet.rol_accrued,
            "rol_used": wallet.rol_used,
            "rol_available": wallet.rol_available,
            "permits_total": wallet.permits_total,
            "permits_used": wallet.permits_used,
            "permits_available": wallet.permits_available,
            "last_accrual_date": wallet.last_accrual_date,
            "ap_expiry_date": wallet.ap_expiry_date,
            "status": wallet.status,
        }
        
    async def get_transactions(self, wallet_id: UUID) -> list:
        """Get transactions for a wallet."""
        txns = await self._wallet_service.get_transactions(wallet_id)
        return [
            {
                "id": str(t.id),
                "transaction_type": t.transaction_type,
                "balance_type": t.balance_type,
                "amount": float(t.amount),
                "balance_after": float(t.balance_after),
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in txns
        ]

    async def get_balance_summary(self, user_id: UUID, year: int) -> BalanceSummary:
        """Get balance summary combining wallet data and pending requests."""
        wallet = await self._wallet_service.get_wallet(user_id, year)
        
        # Calculate pending requests from local database
        pending_requests = await self._request_repo.get_pending_by_user_and_year(user_id, year)
        
        vacation_pending = sum(
            Decimal(str(r.days_requested)) for r in pending_requests if r.leave_type_code == "FER"
        )
        rol_pending = sum(
            Decimal(str(r.days_requested)) * Decimal("8") for r in pending_requests if r.leave_type_code == "ROL"
        )
        permits_pending = sum(
            Decimal(str(r.days_requested)) * Decimal("8") for r in pending_requests if r.leave_type_code == "PER"
        )
        
        ap_expiry_date = wallet.ap_expiry_date
        days_until_ap_expiry = None
        if ap_expiry_date:
            days = (ap_expiry_date - date.today()).days
            days_until_ap_expiry = max(0, days)

        return BalanceSummary(
            vacation_total_available=wallet.vacation_available_total,
            vacation_available_ap=wallet.vacation_available_ap,
            vacation_available_ac=wallet.vacation_available_ac,
            vacation_used=wallet.vacation_used,
            vacation_pending=vacation_pending,
            ap_expiry_date=ap_expiry_date,
            days_until_ap_expiry=days_until_ap_expiry,
            rol_available=wallet.rol_available,
            rol_used=wallet.rol_used,
            rol_pending=rol_pending,
            permits_available=wallet.permits_available,
            permits_used=wallet.permits_used,
            permits_pending=permits_pending
        )

    async def adjust_balance(
        self, user_id: UUID, year: int, data: BalanceAdjustment, admin_id: UUID
    ):
        """Manually adjust balance via local WalletService."""
        txn = TransactionCreate(
            user_id=user_id,
            year=year,
            transaction_type="ADJUSTMENT_ADD" if data.amount > 0 else "ADJUSTMENT_SUB",
            balance_type=data.balance_type,
            amount=abs(data.amount),
            description=data.reason or "Manual adjustment",
            expires_at=data.expiry_date,
            created_by=admin_id
        )
        await self._wallet_service.process_transaction(txn)
        return await self.get_balance_summary(user_id, year)

    async def deduct_balance(
        self, request: LeaveRequest, breakdown: dict, metadata: Optional[dict] = None
    ):
        """Deduct balance for an approved leave request."""
        for balance_type, amount in breakdown.items():
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
            
            txn = TransactionCreate(
                user_id=request.user_id,
                transaction_type="LEAVE_DEDUCTION",
                balance_type=balance_type,
                amount=amount_dec,
                reference_id=request.id,
                description=f"Fruizione per richiesta {request.id}",
            )
            await self._wallet_service.process_transaction(txn)

    async def restore_balance(self, request: LeaveRequest):
        """Restore balance when a request is cancelled."""
        breakdown = request.deduction_details or {}
        
        for balance_type, amount in breakdown.items():
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
                
            txn = TransactionCreate(
                user_id=request.user_id,
                transaction_type="ACCRUAL",  # Refund = add back
                balance_type=balance_type,
                amount=amount_dec,
                reference_id=request.id,
                description=f"Ripristino per cancellazione richiesta {request.id}"
            )
            await self._wallet_service.process_transaction(txn)

    async def restore_partial_balance(self, request: LeaveRequest, days_to_restore: Decimal):
        """Restore partial balance (e.g. for recall)."""
        code = request.leave_type_code
        balance_type = "vacation" if code == "FER" else "rol" if code == "ROL" else "permits"
        
        txn = TransactionCreate(
            user_id=request.user_id,
            transaction_type="ACCRUAL",
            balance_type=balance_type,
            amount=days_to_restore,
            reference_id=request.id,
            description=f"Ripristino parziale per richiamo richiesta {request.id}"
        )
        await self._wallet_service.process_transaction(txn)

    async def process_expirations(self) -> int:
        """Process expired balances."""
        # Expiration logic now handled by WalletService
        expired = await self._wallet_service.get_expiring_balances(date.today())
        return len(expired)

    async def preview_rollover(self, from_year: int) -> list[dict]:
        """Preview rollover."""
        return []

    async def apply_rollover_selected(self, from_year: int, user_ids: list[UUID]) -> int:
        """Apply rollover."""
        return 0
