from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError, NotFoundError
from .models import EmployeeWallet, WalletTransaction
from .schemas import TransactionCreate


class WalletService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_transactions(self, wallet_id: UUID) -> List[WalletTransaction]:
        stmt = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet_id
        ).order_by(WalletTransaction.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_wallet(self, user_id: UUID, year: int) -> EmployeeWallet:
        stmt = select(EmployeeWallet).where(
            EmployeeWallet.user_id == user_id,
            EmployeeWallet.year == year
        )
        result = await self.session.execute(stmt)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            # Create if not exists (Lazy initialization)
            wallet = EmployeeWallet(user_id=user_id, year=year)
            self.session.add(wallet)
            await self.session.flush()
            
        return wallet

    async def process_transaction(self, transaction: TransactionCreate) -> WalletTransaction:
        wallet = await self.get_wallet(transaction.user_id, datetime.now().year)

        amount = transaction.amount
        balance_type = transaction.balance_type
        
        tx_id = None
        
        if transaction.transaction_type == 'deduction':
            await self._handle_deduction(wallet, balance_type, abs(amount))
            final_amount = -abs(amount)
            remaining_amount = Decimal(0)
        elif transaction.transaction_type in ['accrual', 'adjustment', 'refund', 'carry_over']:
            await self._handle_addition(wallet, balance_type, abs(amount))
            final_amount = abs(amount)
            remaining_amount = final_amount # New additions can be consumed
        else:
             raise ValidationError(f"Unknown transaction type: {transaction.transaction_type}")

        # Current balance after op
        balance_after = self._get_current_balance_value(wallet, balance_type)

        tx = WalletTransaction(
            wallet_id=wallet.id,
            reference_id=transaction.reference_id,
            transaction_type=transaction.transaction_type,
            balance_type=balance_type,
            amount=final_amount,
            remaining_amount=remaining_amount,
            balance_after=balance_after,
            expiry_date=transaction.expiry_date if hasattr(transaction, 'expiry_date') else None,
            description=transaction.description,
            created_by=transaction.created_by
        )
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def _handle_deduction(self, wallet: EmployeeWallet, balance_type: str, amount: Decimal):
        """Deduct with FIFO logic across buckets."""
        remaining = amount
        
        # 1. Update the aggregate counters on EmployeeWallet
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
        """Consume remaining_amount from previous transactions (accruals/adjustments)."""
        # Find transactions with remaining balance
        stmt = (
            select(WalletTransaction)
            .where(
                WalletTransaction.wallet_id == wallet_id,
                WalletTransaction.balance_type == balance_type,
                WalletTransaction.remaining_amount > 0
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
        
        # If remaining > 0, we are in negative balance territory. 
        # We don't have a bucket to consume from, which is technically okay for tracking.

    def _get_current_balance_value(self, wallet: EmployeeWallet, balance_type: str) -> Decimal:
        if balance_type in ['vacation', 'vacation_ac', 'vacation_ap']:
            return wallet.vacation_available_total
        elif balance_type == 'rol':
            return wallet.rol_available
        elif balance_type == 'permits':
            return wallet.permits_available
        return Decimal(0)
