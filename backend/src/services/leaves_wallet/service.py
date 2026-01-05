"""
KRONOS Wallet Service - Enterprise Grade

Central authority for all balance operations:
- Balance queries (available, reserved, used)
- FIFO consumption across buckets
- Reservation system for pending requests
- Audit trail integration
- Admin operations (adjustments, accruals, rollovers)
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError, NotFoundError, BusinessRuleError
from src.shared.audit_client import get_audit_logger
from .models import EmployeeWallet, WalletTransaction
from .schemas import TransactionCreate


class WalletService:
    """
    Enterprise Wallet Service.
    
    Single source of truth for all balance operations.
    The Leave Service calls this for all balance changes.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._audit = get_audit_logger("wallet-service")

    # ═══════════════════════════════════════════════════════════
    # Query Operations
    # ═══════════════════════════════════════════════════════════

    async def get_wallet(self, user_id: UUID, year: int = None) -> EmployeeWallet:
        """Get or create wallet for user/year."""
        if not year:
            year = datetime.now().year
            
        stmt = select(EmployeeWallet).where(
            EmployeeWallet.user_id == user_id,
            EmployeeWallet.year == year
        )
        result = await self.session.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            # Lazy initialization
            wallet = EmployeeWallet(user_id=user_id, year=year)
            self.session.add(wallet)
            await self.session.commit()
            await self.session.refresh(wallet)
            
        return wallet

    async def get_transactions(self, wallet_id: UUID, limit: int = 100) -> List[WalletTransaction]:
        """Get transactions for a wallet."""
        stmt = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet_id
        ).order_by(WalletTransaction.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
        wallet = await self.get_wallet(user_id, year or datetime.now().year)
        
        available = self._get_current_balance_value(wallet, balance_type)
        
        if exclude_reserved:
            reserved = await self._get_reserved_amount(wallet.id, balance_type)
            available -= reserved
        
        # Allow negative balances (e.g. if insufficient balance block is disabled)
        return available

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
        return (available >= amount, available)

    async def get_balance_summary(self, user_id: UUID, year: int = None) -> dict:
        """Get comprehensive balance summary for a user."""
        wallet = await self.get_wallet(user_id, year or datetime.now().year)
        
        # Helper to safely float
        def f(val): 
            return float(val) if val is not None else 0.0

        return {
            "vacation_available_total": f(wallet.vacation_available_total),
            "vacation_available_ap": f(wallet.vacation_available_ap),
            "vacation_available_ac": f(wallet.vacation_available_ac),
            "vacation_used": f(wallet.vacation_used_ap) + f(wallet.vacation_used_ac),
            
            "rol_available": f(wallet.rol_available),
            "rol_used": f(wallet.rol_used),
            
            "permits_available": f(wallet.permits_available),
            "permits_used": f(wallet.permits_used),
            
            "ap_expiry_date": wallet.ap_expiry_date.isoformat() if wallet.ap_expiry_date else None,
            "wallet_id": str(wallet.id),
            "year": wallet.year,
        }

    # ═══════════════════════════════════════════════════════════
    # Transaction Processing
    # ═══════════════════════════════════════════════════════════

    async def process_transaction(self, transaction: TransactionCreate) -> WalletTransaction:
        """
        Process a balance transaction.
        
        This is the main entry point for all balance changes.
        """
        wallet = await self.get_wallet(transaction.user_id, datetime.now().year)

        amount = transaction.amount
        balance_type = transaction.balance_type
        
        # Map category automatically if not provided
        category = transaction.category
        if not category:
            category = self._map_category(transaction.transaction_type)
        
        if transaction.transaction_type == 'deduction':
            await self._handle_deduction(wallet, balance_type, abs(amount))
            final_amount = -abs(amount)
            remaining_amount = Decimal(0)
            
            # Compliance: Track mandatory minimum rest (only for vacation)
            if balance_type in ['vacation', 'vacation_ac', 'vacation_ap']:
                wallet.legal_minimum_taken += abs(amount)
                
        elif transaction.transaction_type in ['accrual', 'adjustment', 'refund', 'carry_over']:
            await self._handle_addition(wallet, balance_type, abs(amount))
            final_amount = abs(amount)
            remaining_amount = final_amount  # New additions can be consumed
        else:
            raise ValidationError(f"Unknown transaction type: {transaction.transaction_type}")

        # Current balance after op
        balance_after = self._get_current_balance_value(wallet, balance_type)

        tx = WalletTransaction(
            wallet_id=wallet.id,
            reference_id=transaction.reference_id,
            transaction_type=transaction.transaction_type,
            balance_type=balance_type,
            category=category,
            amount=final_amount,
            remaining_amount=remaining_amount,
            monetary_value=transaction.monetary_value,
            balance_after=balance_after,
            expiry_date=transaction.expiry_date if hasattr(transaction, 'expiry_date') else None,
            description=transaction.description,
            created_by=transaction.created_by
        )
        self.session.add(tx)
        await self.session.flush()
        
        # Audit
        await self._audit.log_action(
            user_id=transaction.created_by or transaction.user_id,
            action=f"WALLET_{transaction.transaction_type.upper()}",
            resource_type="WALLET_TRANSACTION",
            resource_id=str(tx.id),
            description=f"{transaction.transaction_type}: {abs(amount)} {balance_type}",
            request_data={
                "amount": float(amount),
                "balance_type": balance_type,
                "balance_after": float(balance_after),
                "reference_id": str(transaction.reference_id) if transaction.reference_id else None,
            },
        )
        
        return tx

    # ═══════════════════════════════════════════════════════════
    # Reservation System (Pre-approval Hold)
    # ═══════════════════════════════════════════════════════════

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
        # Check sufficient balance
        is_sufficient, available = await self.check_balance_sufficient(user_id, balance_type, amount)
        if not is_sufficient:
            raise BusinessRuleError(
                f"Saldo {balance_type} insufficiente. Disponibile: {available}, Richiesto: {amount}"
            )
        
        wallet = await self.get_wallet(user_id, datetime.now().year)
        
        tx = WalletTransaction(
            wallet_id=wallet.id,
            reference_id=reference_id,
            transaction_type="reservation",
            balance_type=balance_type,
            category="RESERVATION",
            amount=-abs(amount),  # Negative to reduce available
            remaining_amount=abs(amount),  # Tracks reserved amount
            balance_after=self._get_current_balance_value(wallet, balance_type) - abs(amount),
            expiry_date=expiry_date,
            description=f"Reserved for pending request",
        )
        self.session.add(tx)
        await self.session.flush()
        
        return tx

    async def confirm_reservation(self, reference_id: UUID) -> Optional[WalletTransaction]:
        """
        Confirm a reservation when request is approved.
        
        Converts reservation to actual deduction.
        """
        # Find reservation
        stmt = select(WalletTransaction).where(
            WalletTransaction.reference_id == reference_id,
            WalletTransaction.transaction_type == "reservation",
            WalletTransaction.remaining_amount > 0,
        )
        result = await self.session.execute(stmt)
        reservation = result.scalar_one_or_none()
        
        if not reservation:
            return None
        
        # Convert to deduction
        wallet = await self.session.get(EmployeeWallet, reservation.wallet_id)
        if not wallet:
            return None
        
        amount = reservation.remaining_amount
        balance_type = reservation.balance_type
        
        # Process actual deduction
        await self._handle_deduction(wallet, balance_type, amount)
        
        if balance_type in ['vacation', 'vacation_ac', 'vacation_ap']:
            wallet.legal_minimum_taken += amount
        
        # Mark reservation as consumed
        reservation.remaining_amount = Decimal(0)
        reservation.description = "Reservation confirmed (approved)"
        
        # Create confirmation transaction
        confirm_tx = WalletTransaction(
            wallet_id=wallet.id,
            reference_id=reference_id,
            transaction_type="deduction",
            balance_type=balance_type,
            category="CONSUMPTION",
            amount=-abs(amount),
            remaining_amount=Decimal(0),
            balance_after=self._get_current_balance_value(wallet, balance_type),
            description="Confirmed from reservation",
            created_by=reservation.created_by,
        )
        self.session.add(confirm_tx)
        await self.session.flush()
        
        return confirm_tx

    async def cancel_reservation(self, reference_id: UUID) -> bool:
        """
        Cancel a reservation when request is rejected.
        
        Releases the held balance back to available.
        """
        stmt = select(WalletTransaction).where(
            WalletTransaction.reference_id == reference_id,
            WalletTransaction.transaction_type == "reservation",
            WalletTransaction.remaining_amount > 0,
        )
        result = await self.session.execute(stmt)
        reservation = result.scalar_one_or_none()
        
        if not reservation:
            return False
        
        # Simply zero out the remaining_amount to release the hold
        reservation.remaining_amount = Decimal(0)
        reservation.description = "Reservation cancelled (rejected)"
        
        return True

    async def _get_reserved_amount(self, wallet_id: UUID, balance_type: str) -> Decimal:
        """Get total reserved (pending) amount for a balance type."""
        stmt = select(func.coalesce(func.sum(WalletTransaction.remaining_amount), Decimal(0))).where(
            WalletTransaction.wallet_id == wallet_id,
            WalletTransaction.balance_type == balance_type,
            WalletTransaction.transaction_type == "reservation",
            WalletTransaction.remaining_amount > 0,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or Decimal(0)

    # ═══════════════════════════════════════════════════════════
    # Internal Methods
    # ═══════════════════════════════════════════════════════════

    def _map_category(self, transaction_type: str) -> str:
        """Map transaction type to category."""
        mapping = {
            'deduction': 'CONSUMPTION',
            'accrual': 'ACCRUAL',
            'adjustment': 'ADJUSTMENT',
            'refund': 'SETTLEMENT',
            'carry_over': 'CARRY_OVER',
            'reservation': 'RESERVATION',
            'expiration': 'EXPIRATION',
        }
        return mapping.get(transaction_type, 'OTHER')

    async def _handle_deduction(self, wallet: EmployeeWallet, balance_type: str, amount: Decimal):
        """Deduct with FIFO logic across buckets."""
        remaining = amount
        
        if balance_type == 'vacation':
            # FIFO for vacation: AP first, then AC
            available_ap = wallet.vacation_available_ap
            to_deduct_ap = min(available_ap, remaining)
            
            if to_deduct_ap > 0:
                wallet.vacation_used_ap += to_deduct_ap
                await self._consume_buckets(wallet.id, 'vacation_ap', to_deduct_ap)
                remaining -= to_deduct_ap
            
            if remaining > 0:
                wallet.vacation_used_ac += remaining
                await self._consume_buckets(wallet.id, 'vacation_ac', remaining)
                
        elif balance_type in ['vacation_ap', 'vacation_ac', 'rol', 'permits']:
            # Direct deduction from specific bucket
            if balance_type == 'vacation_ap':
                wallet.vacation_used_ap += remaining
            elif balance_type == 'vacation_ac':
                wallet.vacation_used_ac += remaining
            elif balance_type == 'rol':
                wallet.rol_used += remaining
            elif balance_type == 'permits':
                wallet.permits_used += remaining
            
            await self._consume_buckets(wallet.id, balance_type, remaining)
        else:
            raise ValidationError(f"Unknown balance type for deduction: {balance_type}")

    async def _handle_addition(self, wallet: EmployeeWallet, balance_type: str, amount: Decimal):
        """Add to balance aggregates."""
        if balance_type == 'vacation' or balance_type == 'vacation_ac':
            wallet.vacation_accrued += amount
        elif balance_type == 'vacation_ap':
            wallet.vacation_previous_year += amount
        elif balance_type == 'rol':
            wallet.rol_accrued += amount
        elif balance_type == 'permits':
            wallet.permits_total += amount
        else:
            raise ValidationError(f"Unknown balance type for addition: {balance_type}")

    async def _consume_buckets(self, wallet_id: UUID, balance_type: str, amount: Decimal):
        """Consume remaining_amount from previous transactions (FIFO)."""
        stmt = (
            select(WalletTransaction)
            .where(
                WalletTransaction.wallet_id == wallet_id,
                WalletTransaction.balance_type == balance_type,
                WalletTransaction.remaining_amount > 0,
                WalletTransaction.transaction_type.in_(['accrual', 'adjustment', 'refund', 'carry_over']),
            )
            .order_by(
                WalletTransaction.expiry_date.nulls_last(),
                WalletTransaction.created_at.asc()
            )
        )
        result = await self.session.execute(stmt)
        buckets = result.scalars().all()
        
        remaining = amount
        for bucket in buckets:
            if remaining <= 0:
                break
            consume = min(bucket.remaining_amount, remaining)
            bucket.remaining_amount -= consume
            remaining -= consume

    def _get_current_balance_value(self, wallet: EmployeeWallet, balance_type: str) -> Decimal:
        """Get current balance value for a type."""
        if balance_type in ['vacation', 'vacation_ac', 'vacation_ap']:
            return wallet.vacation_available_total
        elif balance_type == 'rol':
            return wallet.rol_available
        elif balance_type == 'permits':
            return wallet.permits_available
        return Decimal(0)

    # ═══════════════════════════════════════════════════════════
    # Admin Operations
    # ═══════════════════════════════════════════════════════════

    async def process_expiration(self, wallet_id: UUID, balance_type: str, amount: Decimal) -> WalletTransaction:
        """Process balance expiration (e.g., AP expires on June 30)."""
        wallet = await self.session.get(EmployeeWallet, wallet_id)
        if not wallet:
            raise NotFoundError("Wallet not found")
        
        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="expiration",
            balance_type=balance_type,
            category="EXPIRATION",
            amount=-abs(amount),
            remaining_amount=Decimal(0),
            balance_after=self._get_current_balance_value(wallet, balance_type) - abs(amount),
            description=f"Balance expired: {balance_type}",
        )
        self.session.add(tx)
        
        # Update wallet totals based on balance type
        if balance_type == 'vacation_ap':
            wallet.vacation_previous_year = max(Decimal(0), wallet.vacation_previous_year - amount)
        elif balance_type == 'rol':
            # ROL previous year expires
            wallet.rol_previous_year = max(Decimal(0), wallet.rol_previous_year - amount)
        
        await self.session.flush()
        return tx

    async def get_wallets_for_accrual(self, year: int) -> List[EmployeeWallet]:
        """Get all wallets that need monthly accrual processing."""
        stmt = select(EmployeeWallet).where(
            EmployeeWallet.year == year,
            EmployeeWallet.status == 'active',
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_expiring_balances(self, expiry_date: date) -> List[WalletTransaction]:
        """Get all transactions expiring on or before a date."""
        stmt = select(WalletTransaction).where(
            WalletTransaction.expiry_date <= expiry_date,
            WalletTransaction.remaining_amount > 0,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

