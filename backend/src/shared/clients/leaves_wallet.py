"""
KRONOS - Leaves Wallet Service Client

Client for managing leave balances (Ferie, ROL, Permessi).
"""
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from src.core.config import settings
from src.shared.clients.base import BaseClient

logger = logging.getLogger(__name__)


class LeavesWalletClient(BaseClient):
    """
    Client for Leaves Wallet Service.
    
    Features:
    - Balance queries
    - Reservation system integration
    - Transaction processing
    """
    
    def __init__(self):
        super().__init__(
            base_url=settings.leaves_wallet_service_url,
            service_name="leaves-wallet",
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Balance Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_wallet(self, user_id: UUID, year: Optional[int] = None) -> Optional[dict]:
        """Get user leaves wallet."""
        params = {}
        if year:
            params["year"] = year
        
        return await self.get_safe(
            f"/api/v1/leaves-wallets/internal/wallets/{user_id}",
            params=params if params else None,
        )
    
    async def get_balance_summary(self, user_id: UUID, year: Optional[int] = None) -> Optional[dict]:
        """Get comprehensive balance summary."""
        params = {"year": year} if year else {}
        return await self.get_safe(
            f"/api/v1/leaves-wallets/internal/wallets/{user_id}/summary",
            params=params if params else None,
        )
    
    async def get_available_balance(
        self,
        user_id: UUID,
        balance_type: str,
        year: Optional[int] = None,
        exclude_reserved: bool = True,
    ) -> Optional[float]:
        """Get available balance for a specific type."""
        params = {"exclude_reserved": exclude_reserved}
        if year:
            params["year"] = year
        
        data = await self.get_safe(
            f"/api/v1/leaves-wallets/{user_id}/available/{balance_type}",
            params=params,
        )
        return data.get("available") if data else None
    
    async def check_balance_sufficient(
        self,
        user_id: UUID,
        balance_type: str,
        amount: float,
        year: Optional[int] = None,
    ) -> tuple[bool, float]:
        """Check if balance is sufficient for a request."""
        params = {
            "user_id": str(user_id),
            "balance_type": balance_type,
            "amount": amount,
        }
        if year:
            params["year"] = year
        
        data = await self.get_safe(
            "/api/v1/leaves-wallets/internal/check",
            default={},
            params=params,
        )
        return (data.get("sufficient", False), data.get("available", 0))
    
    # ═══════════════════════════════════════════════════════════════════════
    # Transaction Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_transaction(self, user_id: UUID, data: dict) -> Optional[dict]:
        """Create a wallet transaction."""
        return await self.post_safe(
            "/api/v1/leaves-wallets/internal/transactions",
            json=data,
        )
    
    async def get_transactions(self, identifier: UUID, limit: int = 100) -> list:
        """Get wallet transactions by wallet_id."""
        return await self.get_safe(
            f"/api/v1/leaves-wallets/transactions/{identifier}",
            default=[],
            params={"limit": limit},
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # Reservation Operations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def reserve_balance(
        self,
        user_id: UUID,
        balance_type: str,
        amount: float,
        reference_id: UUID,
        expiry_date: Optional[date] = None,
    ) -> Optional[dict]:
        """Reserve balance for a pending request."""
        params = {
            "user_id": str(user_id),
            "balance_type": balance_type,
            "amount": amount,
            "reference_id": str(reference_id),
        }
        if expiry_date:
            params["expiry_date"] = expiry_date.isoformat()
        
        return await self.post_safe(
            "/api/v1/leaves-wallets/internal/reserve",
            params=params,
        )
    
    async def confirm_reservation(self, reference_id: UUID) -> bool:
        """Confirm a reservation when request is approved."""
        result = await self.post_safe(
            f"/api/v1/leaves-wallets/internal/confirm/{reference_id}"
        )
        return result is not None
    
    async def cancel_reservation(self, reference_id: UUID) -> bool:
        """Cancel a reservation when request is rejected."""
        result = await self.post_safe(
            f"/api/v1/leaves-wallets/internal/cancel/{reference_id}"
        )
        return result is not None
