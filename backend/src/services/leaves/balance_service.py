"""
KRONOS - Leave Balance Service

Manages leave balances by integrating with the Enterprise Time Ledger.
Legacy WalletService integration has been removed.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.leaves.repository import LeaveRequestRepository
from src.services.leaves.schemas import BalanceSummary, BalanceAdjustment
from src.services.leaves.models import LeaveRequest
from src.services.leaves.ledger import TimeLedgerService, TimeLedgerBalanceType


class LeaveBalanceService:
    """Service for managing leave balances via TimeLedgerService."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._request_repo = LeaveRequestRepository(session)
        self._ledger_service = TimeLedgerService(session)
    
    async def get_balance(self, user_id: UUID, year: int) -> dict:
        """Get balance data mapped to legacy format for backward compatibility."""
        summary = await self._ledger_service.get_balance_summary(user_id, year)
        
        # Helper to get values safely
        def get_val(item, key):
            return getattr(item, key, Decimal(0))

        return {
            "id": str(user_id),  # Ledger is user-centric, no wallet ID anymore
            "user_id": str(user_id),
            "year": year,
            # Vacation AP
            "vacation_previous_year": get_val(summary.vacation_ap, "current_balance"),
            "vacation_used_ap": get_val(summary.vacation_ap, "total_debited"),
            "vacation_available_ap": get_val(summary.vacation_ap, "available"),
            # Vacation AC
            "vacation_current_year": get_val(summary.vacation_ac, "total_credited"),
            "vacation_accrued": get_val(summary.vacation_ac, "total_credited"),
            "vacation_used_ac": get_val(summary.vacation_ac, "total_debited"),
            "vacation_available_ac": get_val(summary.vacation_ac, "available"),
            # Vacation Total
            "vacation_used": get_val(summary.vacation_ap, "total_debited") + get_val(summary.vacation_ac, "total_debited"),
            "vacation_available_total": summary.total_vacation_available,
            # ROL
            "rol_previous_year": Decimal(0), # Not tracked separately in basic view
            "rol_current_year": get_val(summary.rol, "total_credited"),
            "rol_accrued": get_val(summary.rol, "total_credited"),
            "rol_used": get_val(summary.rol, "total_debited"),
            "rol_available": get_val(summary.rol, "available"),
            # Permits
            "permits_total": get_val(summary.permits, "total_credited"),
            "permits_used": get_val(summary.permits, "total_debited"),
            "permits_available": get_val(summary.permits, "available"),
            # Metadata
            "last_accrual_date": None, # Not strictly tracked on user level easily
            "ap_expiry_date": date(year, 6, 30), # Standard rule
            "status": "ACTIVE",
        }
        
    async def get_transactions(self, balance_id: UUID) -> list:
        """Get transactions for a user (balance_id is user_id in ledger context)."""
        # If balance_id is passed, it might be user_id. Ledger doesn't have wallet_id.
        # Calling endpoint passes balance_id (which was wallet_id). 
        # But in new system, we expect user_id.
        # Since this method is admin-only and for debug, we might need to change how it's called
        # or assume balance_id IS user_id if we change the router.
        # For now, let's look up entries by user_id assuming balance_id passed IS user_id
        # OR we need to fetch user_id from wallet if it still existed.
        # Since we removed wallet, we should update router to pass user_id.
        
        entries = await self._ledger_service.get_entries(user_id=balance_id, limit=50)
        return [
            {
                "id": str(t.id),
                "transaction_type": t.entry_type,
                "balance_type": t.balance_type,
                "amount": float(t.amount),
                "balance_after": 0.0, # Ledger doesn't store running balance
                "description": t.notes or f"{t.entry_type} - {t.reference_type}",
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in entries
        ]

    async def get_balance_summary(self, user_id: UUID, year: int) -> BalanceSummary:
        """Get balance summary combining ledger data and pending requests."""
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
        
        pending_map = {
            TimeLedgerBalanceType.VACATION_AP: Decimal(0), # Usually not requested specifically
            TimeLedgerBalanceType.VACATION_AC: vacation_pending, # Assume current
            TimeLedgerBalanceType.ROL: rol_pending,
            TimeLedgerBalanceType.PERMITS: permits_pending
        }
        
        summary = await self._ledger_service.get_balance_summary(user_id, year, pending_by_type=pending_map)
        
        ap_expiry_date = date(year, 6, 30) # Default
        days_until_ap_expiry = max(0, (ap_expiry_date - date.today()).days)

        return BalanceSummary(
            vacation_total_available=summary.total_vacation_available,
            vacation_available_ap=summary.vacation_ap.available,
            vacation_available_ac=summary.vacation_ac.available,
            vacation_used=summary.vacation_ap.total_debited + summary.vacation_ac.total_debited,
            vacation_pending=vacation_pending,
            ap_expiry_date=ap_expiry_date,
            days_until_ap_expiry=days_until_ap_expiry,
            rol_available=summary.rol.available,
            rol_used=summary.rol.total_debited,
            rol_pending=rol_pending,
            permits_available=summary.permits.available,
            permits_used=summary.permits.total_debited,
            permits_pending=permits_pending
        )

    async def adjust_balance(
        self, user_id: UUID, year: int, data: BalanceAdjustment, admin_id: UUID
    ):
        """Manually adjust balance via Ledger."""
        # Create adjustment entry
        # Requires mapping BalanceAdjustment BalanceType to TimeLedgerBalanceType
        # BalanceAdjustment uses: vacation, rol, permits
        # TimeLedger uses: VACATION_AP, VACATION_AC, ROL, PERMITS
        
        legacy_type = data.balance_type.lower()
        ledger_type = TimeLedgerBalanceType.VACATION_AC
        
        if "rol" in legacy_type:
            ledger_type = TimeLedgerBalanceType.ROL
        elif "permits" in legacy_type or "permesso" in legacy_type:
            ledger_type = TimeLedgerBalanceType.PERMITS
        elif "ap" in legacy_type: # if specifcally AP
            ledger_type = TimeLedgerBalanceType.VACATION_AP
            
        entry_type = "ADJUSTMENT_ADD" if data.amount > 0 else "ADJUSTMENT_SUB"
        amount = abs(Decimal(str(data.amount)))
        
        # We need to use repo directly or add adjust capability to service
        # Service has record_usage (deduct) and reverse_usage (add).
        # We should use repo for raw adjustments.
        from src.services.leaves.ledger.repository import TimeLedgerRepository
        from src.services.leaves.ledger.models import TimeLedgerEntry, TimeLedgerEntryType
        
        repo = TimeLedgerRepository(self._session)
        
        entry = TimeLedgerEntry(
            user_id=user_id,
            year=year,
            entry_type=entry_type,
            balance_type=ledger_type,
            amount=amount,
            reference_type="MANUAL_ADJUSTMENT",
            reference_id=admin_id, # Linking to admin as ref? Or create a UUID?
            reference_status="COMPLETED",
            created_by=admin_id,
            notes=data.reason or "Manual adjustment"
        )
        await repo.create(entry)
        
        return await self.get_balance_summary(user_id, year)

    # Legacy methods removed or stubbed
    async def deduct_balance(self, *args, **kwargs): pass
    async def restore_balance(self, *args, **kwargs): pass
    async def restore_partial_balance(self, *args, **kwargs): pass
    
    async def process_expirations(self) -> int:
        return 0 # Not implemented in Ledger yet (needs job)

    async def preview_rollover(self, from_year: int) -> list[dict]:
        return []

    async def apply_rollover_selected(self, from_year: int, user_ids: list[UUID]) -> int:
        return 0

    async def run_year_end_rollover(self, year: int) -> int:
        """Run year end rollover."""
        return 0

    async def import_balances(self, admin_id: UUID, items: list["ImportBalanceItem"], mode: str = "APPEND") -> dict:
        """
        Import historical balances.
        
        Args:
            admin_id: Admin performing import
            items: List of ImportBalanceItem
            mode: APPEND (add to existing) or REPLACE (clear year/type before adding - NOT FULLY IMPLEMENTED)
        
        Returns:
            Dict with stats
        """
        from uuid import uuid4
        from sqlalchemy import select
        from src.auth.models import User
        from src.services.leaves.ledger.repository import TimeLedgerRepository
        from src.services.leaves.ledger.models import TimeLedgerEntry
        
        results = {"success": 0, "failed": 0, "errors": []}
        email_map = {}
        repo = TimeLedgerRepository(self._session)
        
        for item in items:
            try:
                # 1. Resolve User
                if item.email not in email_map:
                    stmt = select(User).where(User.email == item.email)
                    user = await self._session.scalar(stmt)
                    if not user:
                        results["failed"] += 1
                        results["errors"].append(f"User not found: {item.email}")
                        continue
                    email_map[item.email] = user.id
                
                user_id = email_map[item.email]
                
                # 2. Map Balance Type
                ledger_type = None
                legacy_type = item.balance_type.lower()
                
                if "vacation" in legacy_type:
                    # Default to VACATION_AC for import unless specified? 
                    # If importing past years, usually it's AC of that year.
                    # If importing "residui anno fa", it might be AP.
                    # Let's assume standard vacations are AC of that year.
                    ledger_type = TimeLedgerBalanceType.VACATION_AC
                elif "rol" in legacy_type:
                    ledger_type = TimeLedgerBalanceType.ROL
                elif "permi" in legacy_type or "festivita" in legacy_type:
                    ledger_type = TimeLedgerBalanceType.PERMITS
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Unknown balance type: {item.balance_type}")
                    continue

                # 3. Create Entry
                # Use ADJUSTMENT_ADD for positive, ADJUSTMENT_SUB for negative (if any)
                entry_type = "ADJUSTMENT_ADD"
                amount = item.amount
                if amount < 0:
                    entry_type = "ADJUSTMENT_SUB"
                    amount = abs(amount)
                
                entry = TimeLedgerEntry(
                    id=uuid4(),
                    user_id=user_id,
                    year=item.year,
                    entry_type=entry_type,
                    balance_type=ledger_type,
                    amount=amount,
                    reference_type="MANUAL_ADJUSTMENT",
                    reference_id=uuid4(), # Unique ID for this import line
                    reference_status="COMPLETED",
                    created_by=admin_id,
                    notes=item.notes or f"Historical Import ({mode})"
                )
                
                await repo.create(entry)
                results["success"] += 1
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                results["failed"] += 1
                results["errors"].append(f"Error processing {item.email}: {str(e)}")
        
        return results
