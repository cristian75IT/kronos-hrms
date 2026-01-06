from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.expensive_wallet.service import TripWalletService

async def get_wallet_service(
    session: AsyncSession = Depends(get_db),
) -> TripWalletService:
    """Dependency for TripWalletService."""
    return TripWalletService(session)
