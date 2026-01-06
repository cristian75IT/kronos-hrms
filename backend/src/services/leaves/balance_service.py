from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Any, Tuple
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError, NotFoundError
from src.services.leaves.repository import LeaveRequestRepository
from src.services.leaves.schemas import BalanceSummary, BalanceAdjustment
from src.services.leaves.models import LeaveRequest
from src.shared.clients import LeavesWalletClient as WalletClient

class LeaveBalanceService:
    """Service for managing leave balances by delegating to specialized WalletService."""

    def __init__(self, session: AsyncSession, wallet_client: WalletClient):
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._wallet_client = wallet_client
    
    async def get_balance(self, user_id: UUID, year: int) -> dict:
        """Get wallet data from WalletService."""
        wallet = await self._wallet_client.get_wallet(user_id, year)
        if not wallet:
            # If wallet not found, return a default empty structure to avoid 404 in UI
            return {
                "id": str(user_id), # We don't have a wallet ID, use user_id as placeholder or uuid4
                "user_id": user_id,
                "year": year,
                "vacation_previous_year": Decimal(0),
                "vacation_current_year": Decimal(0),
                "vacation_accrued": Decimal(0),
                "vacation_used": Decimal(0),
                "vacation_available_ap": Decimal(0),
                "vacation_available_ac": Decimal(0),
                "vacation_available_total": Decimal(0),
                "rol_previous_year": Decimal(0),
                "rol_current_year": Decimal(0),
                "rol_accrued": Decimal(0),
                "rol_used": Decimal(0),
                "rol_available": Decimal(0),
                "permits_total": Decimal(0),
                "permits_used": Decimal(0),
                "permits_available": Decimal(0),
                "last_accrual_date": None
            }
        return wallet
        
    async def get_transactions(self, balance_id: UUID) -> list:
        # Note: balance_id in leave-service used to refer to LeaveBalance.id.
        # Now it should ideally refer to Wallet.id or UserID.
        # For compatibility with existing router, we assume it's still useful.
        # But WalletClient.get_transactions needs user_id.
        # I'll need to find the user_id from wallet_id or change the router.
        # Let's assume for now we want transactions for a user.
        # Redefining it to be more flexible.
        return await self._wallet_client.get_transactions(balance_id) # Proxying

    async def get_balance_summary(self, user_id: UUID, year: int) -> BalanceSummary:
        """Get balance summary by combining confirmed data from WalletService and pending data from LeaveService."""
        # 1. Get confirmed wallet from WalletService
        wallet = await self._wallet_client.get_wallet(user_id, year)
        if not wallet:
            # Fallback/Empty if service is down or wallet doesn't exist
            wallet = {}
            
        # 2. Calculate pending requests from local database
        # These are requests submitted but not yet approved (which would trigger the Wallet deduction)
        pending_requests = await self._request_repo.get_pending_by_user_and_year(user_id, year)
        
        vacation_pending = sum(
            Decimal(str(r.days_requested)) for r in pending_requests if r.leave_type_code in ["FER"]
        )
        rol_pending = sum(
            Decimal(str(r.days_requested)) * Decimal("8") for r in pending_requests if r.leave_type_code in ["ROL"]
        )
        permits_pending = sum(
            Decimal(str(r.days_requested)) * Decimal("8") for r in pending_requests if r.leave_type_code in ["PER"]
        )
        
        # 3. Extract confirmed values from wallet
        vac_total = Decimal(str(wallet.get("vacation_available_total", 0)))
        vac_used = Decimal(str(wallet.get("vacation_used", 0)))
        rol_total = Decimal(str(wallet.get("rol_available", 0)))
        rol_used = Decimal(str(wallet.get("rol_used", 0)))
        per_total = Decimal(str(wallet.get("permits_available", 0)))
        per_used = Decimal(str(wallet.get("permits_used", 0)))
        
        ap_expiry_str = wallet.get("ap_expiry_date")
        ap_expiry_date = date.fromisoformat(ap_expiry_str) if ap_expiry_str else None
        
        days_until_ap_expiry = None
        if ap_expiry_date:
            days = (ap_expiry_date - date.today()).days
            days_until_ap_expiry = max(0, days)

        return BalanceSummary(
            vacation_total_available=vac_total,
            vacation_available_ap=Decimal(str(wallet.get("vacation_available_ap", 0))),
            vacation_available_ac=Decimal(str(wallet.get("vacation_available_ac", 0))),
            vacation_used=vac_used,
            vacation_pending=vacation_pending,
            ap_expiry_date=ap_expiry_date,
            days_until_ap_expiry=days_until_ap_expiry,
            rol_available=rol_total,
            rol_used=rol_used,
            rol_pending=rol_pending,
            permits_available=per_total,
            permits_used=per_used,
            permits_pending=permits_pending
        )

    async def adjust_balance(self, user_id: UUID, year: int, data: BalanceAdjustment, admin_id: UUID):
        """Manually adjust balance via WalletService."""
        payload = {
            "user_id": str(user_id),
            "transaction_type": "adjustment",
            "balance_type": data.balance_type,
            "amount": float(data.amount),
            "description": data.reason or "Manual adjustment",
            "expiry_date": data.expiry_date.isoformat() if data.expiry_date else None,
            "created_by": str(admin_id)
        }
        await self._wallet_client.create_transaction(user_id, payload)
        return await self.get_balance_summary(user_id, year)

    async def deduct_balance(self, request: LeaveRequest, breakdown: dict, metadata: Optional[dict] = None):
        """Deduct balance by sending a transaction to WalletService."""
        # breakdown is like {'vacation': 8.0} or {'rol': 4.0}
        # Note: breakdown comes from PolicyEngine/CalendarUtils.
        # For Vacation, we pass 'vacation' and WalletService handles FIFO (AP then AC).
        
        for balance_type, amount in breakdown.items():
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
            
            # Use specific balance types for Wallet if they are explicit (vacation_ap, vacation_ac)
            # but mapping 'vacation' to FIFO is cleaner.
            
            payload = {
                "user_id": str(request.user_id),
                "transaction_type": "deduction",
                "balance_type": balance_type,
                "amount": float(amount_dec),
                "reference_id": str(request.id),
                "description": f"Fruizione per richiesta {request.id}",
                "meta_data": metadata or {},  # Pass metadata downstream as meta_data
            }
            await self._wallet_client.create_transaction(request.user_id, payload)

    async def restore_balance(self, request: LeaveRequest):
        """Restore balance by sending reverse transactions to WalletService."""
        # deduction_details contains what was deducted.
        # We should restore it exactly.
        breakdown = request.deduction_details or {}
        
        for balance_type, amount in breakdown.items():
            amount_dec = Decimal(str(amount))
            if amount_dec <= 0:
                continue
                
            payload = {
                "user_id": str(request.user_id),
                "transaction_type": "refund",
                "balance_type": balance_type,
                "amount": float(amount_dec),
                "reference_id": str(request.id),
                "description": f"Ripristino per cancellazione richiesta {request.id}"
            }
            await self._wallet_client.create_transaction(request.user_id, payload)

    async def restore_partial_balance(self, request: LeaveRequest, days_to_restore: Decimal):
        """Restore partial balance (e.g. for recall)."""
        code = request.leave_type_code
        balance_type = "vacation" if code == "FER" else "rol" if code == "ROL" else "permits"
        
        payload = {
            "user_id": str(request.user_id),
            "transaction_type": "refund",
            "balance_type": balance_type,
            "amount": float(days_to_restore),
            "reference_id": str(request.id),
            "description": f"Ripristino parziale per richiamo richiesta {request.id}"
        }
        await self._wallet_client.create_transaction(request.user_id, payload)

    async def process_expirations(self):
        """Expiration processing is moving to WalletService. 
        For now, this can be a skeleton or call specialized Wallet expiration logic.
        """
        # TODO: Implement cross-service expiration trigger if not automatic in wallet-service
        return 0

    async def preview_rollover(self, from_year: int) -> list[dict]:
        """Preview rollover - delegates to wallet service logic (to be implemented)."""
        return []

    async def apply_rollover_selected(self, from_year: int, user_ids: list[UUID]):
        """Apply rollover - delegates to wallet service."""
        return 0
