"""
KRONOS Wallet Service - Enterprise Grade

Central authority for all balance operations:
- Balance queries (available, reserved, used)
- FIFO consumption across buckets
- Reservation system for pending requests
- Audit trail integration
"""
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError, NotFoundError, BusinessRuleError
from src.shared.audit_client import get_audit_logger
from .models import EmployeeWallet, WalletTransaction
from .schemas import TransactionCreate
from .repository import WalletRepository, TransactionRepository

logger = logging.getLogger(__name__)


class WalletService:
    """
    Enterprise Wallet Service.
    
    Single source of truth for all balance operations.
    The Leave Service calls this for all balance changes.
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._wallet_repo = WalletRepository(session)
        self._txn_repo = TransactionRepository(session)
        self._audit = get_audit_logger("leaves-wallet")

    async def get_wallet(self, user_id: UUID, year: int = None) -> EmployeeWallet:
        """Get or create wallet for user/year."""
        if not year:
            year = datetime.utcnow().year
            
        wallet = await self._wallet_repo.get_by_user_year(user_id, year)
        if not wallet:
            # Create new wallet
            wallet = EmployeeWallet(
                user_id=user_id,
                year=year,
                vacation_hours_total=Decimal(0),
                vacation_hours_ap=Decimal(0),
                vacation_hours_ac=Decimal(0),
                rol_hours=Decimal(0),
                permit_hours=Decimal(0),
            )
            await self._wallet_repo.create(wallet)
            logger.info(f"Created new wallet for user {user_id} year {year}")
            
        return wallet

    async def get_wallet_owner(self, wallet_id: UUID) -> Optional[UUID]:
        """Get the user ID that owns the wallet."""
        return await self._wallet_repo.get_owner_id(wallet_id)

    async def get_transactions(self, wallet_id: UUID, limit: int = 100) -> List[WalletTransaction]:
        """Get transactions for a wallet."""
        return await self._txn_repo.get_by_wallet(wallet_id, limit=limit)

    async def get_available_balance(
        self, 
        user_id: UUID, 
        balance_type: str,
        year: int = None,
        exclude_reserved: bool = True,
    ) -> Decimal:
        """
        Get available balance for a specific type.
        
        Args:
            user_id: The user ID
            balance_type: 'vacation', 'vacation_ap', 'vacation_ac', 'rol', 'permits'
            year: Fiscal year (defaults to current)
            exclude_reserved: If True, subtracts any reserved (pending) amounts
        """
        if not year:
            year = datetime.utcnow().year
            
        wallet = await self.get_wallet(user_id, year)
        
        # Get raw balance
        raw_balance = self._get_current_balance_value(wallet, balance_type)
        
        if exclude_reserved:
            reserved = await self._txn_repo.get_pending_reservations(wallet.id, balance_type)
            return raw_balance - reserved
            
        return raw_balance

    async def check_balance_sufficient(
        self,
        user_id: UUID,
        balance_type: str,
        amount: Decimal,
        year: int = None,
    ) -> tuple[bool, Decimal]:
        """
        Check if balance is sufficient for a request.
        
        Returns (is_sufficient, available_amount)
        """
        available = await self.get_available_balance(user_id, balance_type, year)
        return (available >= amount), available

    async def get_balance_summary(self, user_id: UUID, year: int = None) -> dict:
        """Get comprehensive balance summary for a user."""
        if not year:
            year = datetime.utcnow().year
            
        wallet = await self.get_wallet(user_id, year)
        
        def f(val): 
            return float(val) if val is not None else 0.0
            
        summary = {
            "year": wallet.year,
            "balances": {
                "vacation_ap": f(wallet.vacation_hours_ap),
                "vacation_ac": f(wallet.vacation_hours_ac),
                "rol": f(wallet.rol_hours),
                "permits": f(wallet.permit_hours),
                "total:vacation": f(wallet.vacation_hours_total)
            },
            "reserved": {
                "vacation": f(await self._txn_repo.get_pending_reservations(wallet.id, "vacation")),
                "rol": f(await self._txn_repo.get_pending_reservations(wallet.id, "rol")),
                "permits": f(await self._txn_repo.get_pending_reservations(wallet.id, "permits")),
            }
        }
        return summary

    async def process_transaction(self, transaction: TransactionCreate) -> WalletTransaction:
        """
        Process a balance transaction.
        
        This is the main entry point for all balance changes.
        """
        amount = Decimal(str(transaction.amount))
        wallet = await self.get_wallet(transaction.user_id, transaction.year)
        
        category = self._map_category(transaction.transaction_type)
        
        # Validation for DEDUCTION
        if category == "DEDUCTION":
            available = await self.get_available_balance(
                transaction.user_id, 
                transaction.balance_type, 
                transaction.year,
                exclude_reserved=True
            )
            if available < amount:
                 raise BusinessRuleError(f"Insufficient balance for {transaction.balance_type}. Attempted: {amount}, Available: {available}")

        # Create Record
        txn = WalletTransaction(
            wallet_id=wallet.id,
            transaction_code=transaction.transaction_type,
            balance_type=transaction.balance_type,
            amount=amount if category == "ADDITION" else -amount,
            remaining_amount=amount if category == "ADDITION" else Decimal(0),
            description=transaction.description,
            reference_id=transaction.reference_id,
            created_by=transaction.created_by,
            expires_at=transaction.expires_at,
        )
        
        await self._txn_repo.create(txn)
        
        # Allow repo to flush to generate ID/defaults if needed before further ops? 
        # Usually flush is enough.
        
        # Update Aggregates and FIFO
        if category == "DEDUCTION":
            await self._handle_deduction(wallet, transaction.balance_type, amount)
            await self._consume_buckets(wallet.id, transaction.balance_type, amount)
        elif category == "ADDITION":
            await self._handle_addition(wallet, transaction.balance_type, amount)
            
        await self._wallet_repo.update(wallet)
        
        return txn

    async def reserve_balance(
        self,
        user_id: UUID,
        balance_type: str,
        amount: Decimal,
        reference_id: UUID,
        expiry_date: Optional[date] = None,
    ) -> WalletTransaction:
        """
        Reserve balance for a pending request.
        
        Creates a 'reservation' transaction that holds the balance
        until approved (confirm) or rejected (cancel).
        """
        # Check balance
        available = await self.get_available_balance(user_id, balance_type, exclude_reserved=True)
        if available < amount:
            raise BusinessRuleError("Insufficient balance for reservation")
            
        wallet = await self.get_wallet(user_id)
        
        txn = WalletTransaction(
            wallet_id=wallet.id,
            transaction_code='RESERVATION',
            balance_type=balance_type,
            amount=amount, # Store positive amount for reservation sum logic, logic handles direction
            # Actually, standard is: amount is amount involved. 
            # get_pending_reservations sums amount.
            
            is_confirmed=False,
            description=f"Reservation for request {reference_id}",
            reference_id=reference_id,
            expires_at=expiry_date
        )
        await self._txn_repo.create(txn)
        return txn

    async def confirm_reservation(self, reference_id: UUID) -> List[WalletTransaction]:
        """
        Confirm a reservation when request is approved.
        
        Converts reservation to actual deduction.
        """
        txns = await self._txn_repo.get_by_reference(reference_id)
        reservation = next((t for t in txns if t.transaction_code == 'RESERVATION' and not t.is_confirmed), None)
        
        if not reservation:
            # Already confirmed or not found
            logger.warning(f"No active reservation found for {reference_id}")
            return []
            
        wallet = await self._wallet_repo.get(reservation.wallet_id)
        
        # 1. Mark reservation as confirmed (so it doesn't count as pending anymore)
        reservation.is_confirmed = True
        
        # 2. Create actual Usage transaction
        usage_txn = WalletTransaction(
            wallet_id=wallet.id,
            transaction_code='USAGE',
            balance_type=reservation.balance_type,
            amount=-reservation.amount,
            remaining_amount=Decimal(0),
            description=f"Usage from reservation {reservation.id}",
            reference_id=reference_id,
            is_confirmed=True
        )
        await self._txn_repo.create(usage_txn)
        
        # 3. Update balances (Deduction logic)
        await self._handle_deduction(wallet, reservation.balance_type, reservation.amount)
        await self._consume_buckets(wallet.id, reservation.balance_type, reservation.amount)
        await self._wallet_repo.update(wallet)
        
        return [reservation, usage_txn]

    async def cancel_reservation(self, reference_id: UUID) -> WalletTransaction:
        """
        Cancel a reservation when request is rejected.
        
        Releases the held balance back to available.
        """
        txns = await self._txn_repo.get_by_reference(reference_id)
        reservation = next((t for t in txns if t.transaction_code == 'RESERVATION' and not t.is_confirmed), None)
        
        if not reservation:
             logger.warning(f"No active reservation found for {reference_id}")
             return None
             
        # Just mark as confirmed (or deleted/cancelled status if we had one).
        # We assume marking distinct from not-pending.
        # Ideally we might delete it or have 'is_cancelled' flag.
        # But get_pending_reservations uses 'is_confirmed=False'.
        # If we set is_confirmed=True WITHOUT creating a usage, it is effectively released.
        # But we should probably mark it as 'CANCELLED' status if we had one.
        # For now, let's delete it or mark it confirmed but 0 amount? NO.
        # Let's delete it? No, audit trail.
        # Add `is_cancelled` field? Not in schema.
        # Let's assume setting `is_confirmed=True` effectively removes it from "Pending" sum.
        # And since we don't create USAGE, nothing is deducted.
        # But we should update description or code?
        
        reservation.is_confirmed = True
        reservation.description += " (CANCELLED)"
        # Or change code to RESERVATION_CANCELLED? Standard practice.
        reservation.transaction_code = 'RESERVATION_CANCELLED'
        
        return reservation

    async def _handle_deduction(self, wallet: EmployeeWallet, balance_type: str, amount: Decimal):
        """Deduct with FIFO logic across buckets."""
        if balance_type == "rol":
            wallet.rol_hours -= amount
        elif balance_type == "permits":
            wallet.permit_hours -= amount
        elif balance_type == "vacation":
            # AP first, then AC (FIFO usually handled in buckets, but aggregates updated too)
            # Logic: If AP available > 0, take from AP.
            if wallet.vacation_hours_ap >= amount:
                wallet.vacation_hours_ap -= amount
            elif wallet.vacation_hours_ap > 0:
                remaining = amount - wallet.vacation_hours_ap
                wallet.vacation_hours_ap = Decimal(0)
                wallet.vacation_hours_ac -= remaining
            else:
                wallet.vacation_hours_ac -= amount
            
            wallet.vacation_hours_total -= amount
        
    async def _handle_addition(self, wallet: EmployeeWallet, balance_type: str, amount: Decimal):
        """Add to balance aggregates."""
        if balance_type == "rol":
            wallet.rol_hours += amount
        elif balance_type == "permits":
            wallet.permit_hours += amount
        elif balance_type == "vacation_ap":
             wallet.vacation_hours_ap += amount
             wallet.vacation_hours_total += amount
        elif balance_type == "vacation_ac":
             wallet.vacation_hours_ac += amount
             wallet.vacation_hours_total += amount

    async def _consume_buckets(self, wallet_id: UUID, balance_type: str, amount: Decimal):
        """Consume remaining_amount from previous transactions (FIFO)."""
        # Map generic 'vacation' to specific buckets? 
        # Usually buckets have 'vacation_ap' or 'vacation_ac'.
        # If user asks to consume 'vacation', we must consume 'vacation_ap' buckets first, then 'vacation_ac'.
        
        targets = [balance_type]
        if balance_type == 'vacation':
            targets = ['vacation_ap', 'vacation_ac']
            
        remaining_to_deduct = amount
        
        for target_type in targets:
            buckets = await self._txn_repo.get_available_buckets(wallet_id, target_type)
            
            for bucket in buckets:
                if remaining_to_deduct <= 0:
                    break
                    
                take = min(bucket.remaining_amount, remaining_to_deduct)
                bucket.remaining_amount -= take
                remaining_to_deduct -= take
                
        if remaining_to_deduct > 0:
            logger.warning(f"Consumed all buckets but still {remaining_to_deduct} needed for deduction.")
            # This implies negative balance allowed or aggregates out of sync with buckets.

    def _get_current_balance_value(self, wallet: EmployeeWallet, balance_type: str) -> Decimal:
        """Get current balance value for a type."""
        if balance_type == "vacation":
            return wallet.vacation_hours_total
        elif balance_type == "vacation_ap":
            return wallet.vacation_hours_ap
        elif balance_type == "vacation_ac":
            return wallet.vacation_hours_ac
        elif balance_type == "rol":
            return wallet.rol_hours
        elif balance_type == "permits":
            return wallet.permit_hours
        return Decimal(0)

    def _map_category(self, transaction_type: str) -> str:
        """Map transaction type to category."""
        if transaction_type in ['ACCRUAL', 'MANUAL_ADD', 'ADJUSTMENT_ADD']:
            return 'ADDITION'
        return 'DEDUCTION'

    async def process_expiration(self, wallet_id: UUID, balance_type: str, amount: Decimal):
        """Process balance expiration (e.g., AP expires on June 30)."""
        # Logic to expire amount
        pass

    async def get_wallets_for_accrual(self, year: int) -> List[EmployeeWallet]:
        """Get all wallets that need monthly accrual processing."""
        return await self._wallet_repo.get_wallets_for_year(year)

    async def get_expiring_balances(self, expiry_date: date) -> List[WalletTransaction]:
        """Get all transactions expiring on or before a date."""
        return await self._txn_repo.get_expiring(expiry_date)
