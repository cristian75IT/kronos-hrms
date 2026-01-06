"""
KRONOS Trip Wallet Service - Enterprise Grade

Central authority for all expense financial operations:
- Budget management and validation
- Transaction ledger (expenses, advances, payments)
- Budget reservation system
- Policy limit enforcement
- Reconciliation workflow
- Audit trail integration
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationError, NotFoundError, BusinessRuleError
from src.shared.audit_client import get_audit_logger
from .models import TripWallet, TripWalletTransaction
from .repository import TripWalletRepository, TripWalletTransactionRepository


# Default policy limits (can be overridden by config)
DEFAULT_POLICY_LIMITS = {
    "FOOD": Decimal("50.00"),       # Per day
    "HOTEL": Decimal("150.00"),     # Per night
    "TRANSPORT": Decimal("200.00"), # Per trip segment
    "OTHER": Decimal("100.00"),     # Per item
}


class TripWalletService:
    """
    Enterprise Trip Wallet Service.
    
    Single source of truth for all expense financial operations.
    The Expense Service calls this for all budget/transaction operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._wallet_repo = TripWalletRepository(session)
        self._txn_repo = TripWalletTransactionRepository(session)
        self._audit = get_audit_logger("expense-wallet-service")

    # ═══════════════════════════════════════════════════════════
    # Query Operations
    # ═══════════════════════════════════════════════════════════

    async def get_wallet(self, trip_id: UUID) -> Optional[TripWallet]:
        """Get wallet for a trip."""
        return await self._wallet_repo.get_by_trip(trip_id)

    async def get_wallet_summary(self, trip_id: UUID) -> Dict[str, Any]:
        """Get comprehensive wallet summary."""
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            return None
        
        # Calculate reserved amount (pending expenses)
        reserved = await self._txn_repo.get_pending_reservations(wallet.id)
        
        # Note: wallet.total_budget, wallet.total_expenses etc are mapped columns.
        # Ensure Decimal -> float conversion for JSON response
        return {
            "wallet_id": str(wallet.id),
            "trip_id": str(wallet.trip_id),
            "user_id": str(wallet.user_id),
            "currency": wallet.currency,
            "status": wallet.status,
            "budget": {
                "total": float(wallet.total_budget),
                "reserved": float(reserved),
                "available": float(wallet.total_budget - wallet.total_expenses - reserved),
            },
            "expenses": {
                "total": float(wallet.total_expenses),
                "taxable": float(wallet.total_taxable),
                "non_taxable": float(wallet.total_non_taxable),
            },
            "advances": {
                "total": float(wallet.total_advances),
            },
            "settlement": {
                "current_balance": float(wallet.current_balance),
                "net_to_pay": float(wallet.net_to_pay),
            },
            "compliance": {
                "policy_violations_count": wallet.policy_violations_count,
                "is_reconciled": wallet.is_reconciled,
            },
            "timestamps": {
                "created_at": wallet.created_at.isoformat(),
                "updated_at": wallet.updated_at.isoformat(),
            },
        }

    async def get_transactions(self, wallet_id: UUID, limit: int = 100) -> List[TripWalletTransaction]:
        """Get all transactions for a wallet."""
        # Using Sequence to List conversion if needed
        return list(await self._txn_repo.get_by_wallet(wallet_id, limit=limit))

    # ═══════════════════════════════════════════════════════════
    # Wallet Lifecycle
    # ═══════════════════════════════════════════════════════════

    async def create_wallet(self, trip_id: UUID, user_id: UUID, budget: Decimal) -> TripWallet:
        """Initialize a new wallet for a trip."""
        existing = await self.get_wallet(trip_id)
        if existing:
            return existing

        wallet = TripWallet(
            trip_id=trip_id,
            user_id=user_id,
            total_budget=budget,
            total_advances=Decimal(0),
            total_expenses=Decimal(0),
            total_taxable=Decimal(0),
            total_non_taxable=Decimal(0),
            status="OPEN",
            currency="EUR"
        )
        wallet = await self._wallet_repo.create(wallet)
        
        # Initial transaction
        tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type="budget_allocation",
            amount=budget,
            description=f"Initial budget allocation for trip",
        )
        await self._txn_repo.create(tx)
        
        # Audit
        await self._audit.log_action(
            user_id=user_id,
            action="WALLET_CREATE",
            resource_type="TRIP_WALLET",
            resource_id=str(wallet.id),
            description=f"Created wallet for trip {trip_id} with budget {budget}",
            request_data={"trip_id": str(trip_id), "budget": float(budget)},
        )
        
        return wallet

    # ═══════════════════════════════════════════════════════════
    # Budget Management
    # ═══════════════════════════════════════════════════════════

    async def check_budget_available(self, trip_id: UUID, amount: Decimal) -> tuple[bool, Decimal]:
        """
        Check if budget is available for an expense.
        
        Returns (is_available, available_amount)
        """
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            return (False, Decimal(0))
        
        reserved = await self._txn_repo.get_pending_reservations(wallet.id)
        available = wallet.total_budget - wallet.total_expenses - reserved
        
        return (available >= amount, available)

    async def reserve_budget(
        self,
        trip_id: UUID,
        amount: Decimal,
        reference_id: UUID,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> TripWalletTransaction:
        """
        Reserve budget for a pending expense.
        
        Creates a 'reservation' transaction until expense is approved/rejected.
        """
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            raise NotFoundError("Wallet not found", entity_type="TripWallet", entity_id=str(trip_id))
        
        # Check budget
        is_available, available = await self.check_budget_available(trip_id, amount)
        if not is_available:
            raise BusinessRuleError(
                f"Budget insufficiente. Disponibile: €{available:.2f}, Richiesto: €{amount:.2f}"
            )
        
        tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type="reservation",
            amount=amount,
            category=category,
            reference_id=reference_id,
            description=description or "Budget reservation for pending expense",
        )
        return await self._txn_repo.create(tx)

    async def confirm_expense(self, trip_id: UUID, reference_id: UUID) -> Optional[TripWalletTransaction]:
        """
        Confirm a reserved expense when approved.
        
        Converts reservation to actual expense.
        """
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            return None
        
        # Find reservation calls repo
        # Use get_by_reference which returns list, find appropriate one
        txs = await self._txn_repo.get_by_reference(reference_id)
        reservation = next((t for t in txs if t.transaction_type == "reservation"), None)
        
        if not reservation:
            return None
        
        amount = reservation.amount
        category = reservation.category
        
        # Update wallet totals
        wallet.total_expenses += amount
        if reservation.is_taxable:
            wallet.total_taxable += amount
        else:
            wallet.total_non_taxable += amount
        
        # Mark reservation as consumed
        reservation.transaction_type = "reservation_converted"
        reservation.description = f"{reservation.description} → Confirmed"
        await self._txn_repo.update(reservation)
        
        # Create actual expense transaction
        expense_tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type="expense_confirmed",
            amount=amount,
            category=category,
            reference_id=reference_id,
            description="Expense confirmed from reservation",
            is_taxable=reservation.is_taxable,
            is_reimbursable=reservation.is_reimbursable,
            has_receipt=reservation.has_receipt,
        )
        await self._txn_repo.create(expense_tx)
        
        # Update Wallet persistence
        await self._wallet_repo.update(wallet)
        
        return expense_tx

    async def cancel_expense(self, trip_id: UUID, reference_id: UUID) -> bool:
        """
        Cancel a reserved expense (rejected/deleted).
        
        Releases the reserved budget.
        """
        # Logic similar to confirm
        txs = await self._txn_repo.get_by_reference(reference_id)
        reservation = next((t for t in txs if t.transaction_type == "reservation"), None)
        
        if not reservation:
            return False
        
        # Mark as cancelled (don't delete for audit trail)
        reservation.transaction_type = "reservation_cancelled"
        reservation.description = f"{reservation.description} → Cancelled"
        await self._txn_repo.update(reservation)
        
        return True

    # ═══════════════════════════════════════════════════════════
    # Transaction Processing
    # ═══════════════════════════════════════════════════════════

    async def process_transaction(
        self, 
        trip_id: UUID, 
        transaction_type: str, 
        amount: Decimal,
        reference_id: Optional[UUID] = None, 
        description: Optional[str] = None,
        created_by: Optional[UUID] = None, 
        category: Optional[str] = None,
        tax_rate: Optional[Decimal] = None, 
        is_taxable: bool = False,
        has_receipt: bool = True, 
        is_reimbursable: bool = True,
    ) -> TripWallet:
        """Process a movement in the wallet (Expense, Advance, Payment)."""
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            raise NotFoundError("Wallet not found", entity_type="TripWallet", entity_id=str(trip_id))

        # Calculate tax if rate provided
        tax_amount = Decimal(0)
        if tax_rate and amount:
            tax_amount = (amount * tax_rate / (Decimal(100) + tax_rate)).quantize(Decimal("0.01"))

        # Create Transaction record
        tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type=transaction_type,
            amount=amount,
            category=category,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            is_taxable=is_taxable,
            is_reimbursable=is_reimbursable,
            has_receipt=has_receipt,
            reference_id=reference_id,
            description=description,
            created_by=created_by
        )
        await self._txn_repo.create(tx)

        # Update Wallet Ledgers
        if transaction_type == "expense_approval":
            wallet.total_expenses += amount
            if is_taxable:
                wallet.total_taxable += amount
            else:
                wallet.total_non_taxable += amount
            
            # Policy audit
            if not has_receipt:
                wallet.policy_violations_count += 1
                tx.compliance_flags = "MISSING_RECEIPT"
                # Need to update tx if flags changed
                await self._txn_repo.update(tx)
                
        elif transaction_type == "advance_payment":
            wallet.total_advances += amount
            
        elif transaction_type == "budget_allocation":
            wallet.total_budget += amount
            
        elif transaction_type == "budget_adjustment":
            wallet.total_budget += amount  # Can be negative for reduction
            
        elif transaction_type == "refund":
            wallet.total_expenses -= amount
            
        elif transaction_type == "settlement":
            # Final settlement transaction
            wallet.status = "SETTLED"
        
        await self._wallet_repo.update(wallet)
        
        # Audit
        await self._audit.log_action(
            user_id=created_by,
            action=f"WALLET_{transaction_type.upper()}",
            resource_type="TRIP_WALLET_TRANSACTION",
            resource_id=str(tx.id),
            description=f"{transaction_type}: €{amount:.2f}",
            request_data={
                "trip_id": str(trip_id),
                "amount": float(amount),
                "category": category,
            },
        )
        
        return wallet

    # ═══════════════════════════════════════════════════════════
    # Policy Enforcement
    # ═══════════════════════════════════════════════════════════

    async def check_policy_limit(
        self,
        trip_id: UUID,
        category: str,
        amount: Decimal,
        policy_limits: Optional[Dict[str, Decimal]] = None,
    ) -> Dict[str, Any]:
        """
        Check if expense amount exceeds policy limits.
        
        Returns policy check result with details.
        """
        limits = policy_limits or DEFAULT_POLICY_LIMITS
        limit = limits.get(category.upper(), Decimal("999999.99"))
        
        exceeded = amount > limit
        
        result = {
            "allowed": not exceeded,
            "category": category,
            "amount": float(amount),
            "limit": float(limit),
            "exceeded_by": float(max(Decimal(0), amount - limit)),
            "policy_code": f"{category.upper()}_LIMIT",
            "requires_approval": exceeded,
        }
        
        # Log policy check
        if exceeded:
            await self._audit.log_action(
                action="POLICY_LIMIT_EXCEEDED",
                resource_type="TRIP_WALLET",
                resource_id=str(trip_id),
                description=f"Expense €{amount:.2f} exceeds {category} limit of €{limit:.2f}",
                request_data=result,
            )
        
        return result

    # ═══════════════════════════════════════════════════════════
    # Reconciliation & Settlement
    # ═══════════════════════════════════════════════════════════

    async def reconcile_wallet(
        self,
        trip_id: UUID,
        reconciled_by: UUID,
        notes: Optional[str] = None,
        adjustments: Optional[List[Dict]] = None,
    ) -> TripWallet:
        """
        Reconcile a trip wallet.
        
        Marks wallet as verified and ready for settlement.
        """
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            raise NotFoundError("Wallet not found", entity_type="TripWallet", entity_id=str(trip_id))
        
        if wallet.status == "SETTLED":
            raise BusinessRuleError("Wallet già regolato, non può essere riconciliato")
        
        # Process any adjustments
        if adjustments:
            for adj in adjustments:
                amount_diff = Decimal(str(adj.get("new_amount", 0))) - Decimal(str(adj.get("original_amount", 0)))
                if amount_diff != 0:
                    await self.process_transaction(
                        trip_id=trip_id,
                        transaction_type="adjustment",
                        amount=amount_diff,
                        reference_id=adj.get("item_id"),
                        description=adj.get("reason", "Adjustment during reconciliation"),
                        created_by=reconciled_by,
                    )
        
        wallet.is_reconciled = True
        wallet.status = "RECONCILED"
        await self._wallet_repo.update(wallet)
        
        # Audit
        await self._audit.log_action(
            user_id=reconciled_by,
            action="WALLET_RECONCILED",
            resource_type="TRIP_WALLET",
            resource_id=str(wallet.id),
            description=f"Wallet reconciled for trip {trip_id}",
            request_data={"notes": notes, "adjustments_count": len(adjustments or [])},
        )
        
        return wallet

    async def settle_wallet(
        self,
        trip_id: UUID,
        settled_by: UUID,
        payment_reference: Optional[str] = None,
    ) -> TripWallet:
        """
        Final settlement of a trip wallet.
        
        Closes the wallet and records final payment transaction.
        """
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            raise NotFoundError("Wallet not found", entity_type="TripWallet", entity_id=str(trip_id))
        
        if wallet.status == "SETTLED":
            raise BusinessRuleError("Wallet già regolato")
        
        if not wallet.is_reconciled:
            raise BusinessRuleError("Il wallet deve essere prima riconciliato")
        
        # Record settlement transaction
        settlement_amount = wallet.net_to_pay
        
        tx = TripWalletTransaction(
            wallet_id=wallet.id,
            transaction_type="settlement",
            amount=settlement_amount,
            description=f"Final settlement. Payment ref: {payment_reference or 'N/A'}",
            created_by=settled_by,
        )
        await self._txn_repo.create(tx)
        
        wallet.status = "SETTLED"
        await self._wallet_repo.update(wallet)
        
        # Audit
        await self._audit.log_action(
            user_id=settled_by,
            action="WALLET_SETTLED",
            resource_type="TRIP_WALLET",
            resource_id=str(wallet.id),
            description=f"Wallet settled: €{settlement_amount:.2f}",
            request_data={
                "net_to_pay": float(settlement_amount),
                "payment_reference": payment_reference,
            },
        )
        
        return wallet

    # ═══════════════════════════════════════════════════════════
    # Admin Operations
    # ═══════════════════════════════════════════════════════════

    async def update_budget(
        self,
        trip_id: UUID,
        new_budget: Decimal,
        reason: str,
        updated_by: UUID,
    ) -> TripWallet:
        """Update trip budget (increase or decrease)."""
        wallet = await self.get_wallet(trip_id)
        if not wallet:
            raise NotFoundError("Wallet not found", entity_type="TripWallet", entity_id=str(trip_id))
        
        if wallet.status in ["RECONCILED", "SETTLED"]:
            raise BusinessRuleError("Non si può modificare il budget di un wallet chiuso")
        
        difference = new_budget - wallet.total_budget
        
        await self.process_transaction(
            trip_id=trip_id,
            transaction_type="budget_adjustment",
            amount=difference,
            description=f"Budget adjustment: {reason}",
            created_by=updated_by,
        )
        
        return await self.get_wallet(trip_id)

    async def void_transaction(
        self,
        transaction_id: UUID,
        reason: str,
        voided_by: UUID,
    ) -> TripWalletTransaction:
        """Void a transaction (does not delete, marks as voided)."""
        tx = await self._txn_repo.get(transaction_id)
        
        if not tx:
            raise NotFoundError("Transaction not found", entity_type="TripWalletTransaction", entity_id=str(transaction_id))
        
        # Create reversal transaction
        wallet = await self._wallet_repo.get(tx.wallet_id)
        
        reversal = TripWalletTransaction(
            wallet_id=tx.wallet_id,
            transaction_type=f"{tx.transaction_type}_voided",
            amount=-tx.amount,  # Negative to reverse
            category=tx.category,
            reference_id=tx.reference_id,
            description=f"VOIDED: {reason}. Original: {tx.description}",
            created_by=voided_by,
        )
        await self._txn_repo.create(reversal)
        
        # Reverse wallet totals based on original type
        if tx.transaction_type == "expense_approval":
            wallet.total_expenses -= tx.amount
        elif tx.transaction_type == "advance_payment":
            wallet.total_advances -= tx.amount
        elif tx.transaction_type == "budget_allocation":
            wallet.total_budget -= tx.amount
        
        tx.compliance_flags = f"VOIDED:{reason}"
        await self._txn_repo.update(tx)
        
        await self._wallet_repo.update(wallet)
        
        # Audit
        await self._audit.log_action(
            user_id=voided_by,
            action="TRANSACTION_VOIDED",
            resource_type="TRIP_WALLET_TRANSACTION",
            resource_id=str(transaction_id),
            description=f"Transaction voided: {reason}",
            request_data={"reason": reason, "original_amount": float(tx.amount)},
        )
        
        return reversal

    async def get_open_wallets(self) -> List[TripWallet]:
        """Get all open (non-settled) wallets."""
        return list(await self._wallet_repo.get_open_wallets())

    async def get_policy_violations(
        self,
        user_id: Optional[UUID] = None,
        trip_id: Optional[UUID] = None,
    ) -> List[TripWalletTransaction]:
        """Get transactions with policy violations."""
        return list(await self._txn_repo.get_policy_violations(user_id=user_id, trip_id=trip_id))
