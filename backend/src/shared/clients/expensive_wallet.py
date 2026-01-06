"""
KRONOS - Expensive Wallet (Trip Expense) Service Client

Client for managing business trip budgets and expenses.
"""
import logging
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class ExpensiveWalletClient(BaseClient):
    """
    Client for Trip Wallet Service (Trasferte).
    
    Features:
    - Wallet queries and summaries
    - Budget reservation system
    - Policy limit checking
    - Reconciliation and settlement
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.expensive_wallet_service_url,
            service_name="expensive-wallet",
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Wallet Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_status(self, trip_id: UUID) -> Optional[dict]:
        """Get wallet status for a trip."""
        return await self.get_safe(f"/api/v1/expensive-wallets/{trip_id}")
    
    async def get_wallet_summary(self, trip_id: UUID) -> Optional[dict]:
        """Get comprehensive wallet summary."""
        return await self.get_safe(f"/api/v1/expensive-wallets/{trip_id}/summary")
    
    async def get_transactions(self, trip_id: UUID, limit: int = 100) -> list:
        """Get expense wallet transactions for a trip."""
        return await self.get_safe(
            f"/api/v1/expensive-wallets/{trip_id}/transactions",
            default=[],
            params={"limit": limit},
        )
    
    async def create_transaction(self, trip_id: UUID, data: dict) -> Optional[dict]:
        """Create a travel wallet transaction (advance, expense, refund)."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/{trip_id}/transactions",
            json=data,
        )
    
    async def initialize_wallet(
        self,
        trip_id: UUID,
        user_id: UUID,
        budget: float,
    ) -> Optional[dict]:
        """Initialize wallet for a trip (internal system call)."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/internal/initialize/{trip_id}",
            params={"user_id": str(user_id), "budget": budget},
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Budget Reservation (Internal API)
    # ═══════════════════════════════════════════════════════════════════════
    
    async def check_budget_available(self, trip_id: UUID, amount: float) -> tuple[bool, float]:
        """Check if budget is available for an expense."""
        data = await self.get_safe(
            f"/api/v1/expensive-wallets/internal/{trip_id}/check-budget",
            default={},
            params={"amount": amount},
        )
        return (data.get("available", False), data.get("available_amount", 0))
    
    async def reserve_budget(
        self,
        trip_id: UUID,
        amount: float,
        reference_id: UUID,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        """Reserve budget for a pending expense."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/internal/{trip_id}/reserve",
            json={
                "amount": amount,
                "reference_id": str(reference_id),
                "category": category,
                "description": description,
            },
        )
    
    async def confirm_expense(self, trip_id: UUID, reference_id: UUID) -> bool:
        """Confirm a reserved expense."""
        result = await self.post_safe(
            f"/api/v1/expensive-wallets/internal/{trip_id}/confirm/{reference_id}"
        )
        return result is not None
    
    async def cancel_expense(self, trip_id: UUID, reference_id: UUID) -> bool:
        """Cancel a reserved expense."""
        result = await self.post_safe(
            f"/api/v1/expensive-wallets/internal/{trip_id}/cancel/{reference_id}"
        )
        return result is not None
    
    async def check_policy_limit(
        self,
        trip_id: UUID,
        category: str,
        amount: float,
    ) -> dict:
        """Check if expense exceeds policy limits."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/internal/{trip_id}/check-policy",
            default={"allowed": True, "requires_approval": False},
            json={"category": category, "amount": amount},
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Admin Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def reconcile_wallet(
        self,
        trip_id: UUID,
        notes: Optional[str] = None,
        adjustments: Optional[list] = None,
    ) -> Optional[dict]:
        """Reconcile a trip wallet."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/admin/{trip_id}/reconcile",
            json={"notes": notes, "adjustments": adjustments or []},
            timeout=10.0,
        )
    
    async def settle_wallet(
        self,
        trip_id: UUID,
        payment_reference: Optional[str] = None,
    ) -> Optional[dict]:
        """Final settlement of a trip wallet."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/admin/{trip_id}/settle",
            json={"payment_reference": payment_reference},
            timeout=10.0,
        )
    
    async def update_budget(
        self,
        trip_id: UUID,
        new_budget: float,
        reason: str,
    ) -> Optional[dict]:
        """Update trip budget."""
        return await self.post_safe(
            f"/api/v1/expensive-wallets/admin/{trip_id}/update-budget",
            json={"new_budget": new_budget, "reason": reason},
        )
