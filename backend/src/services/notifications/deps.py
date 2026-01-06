from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.services.notifications.services import NotificationService

async def get_notification_service(
    session: AsyncSession = Depends(get_db),
) -> NotificationService:
    """Dependency for NotificationService."""
    return NotificationService(session)
