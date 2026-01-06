"""
KRONOS - Notification Service Base

Shared dependencies and repositories for Notification sub-services.
"""
import logging
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.audit_client import get_audit_logger
from src.shared.clients import AuthClient, ConfigClient

from src.services.notifications.repository import (
    NotificationRepository,
    EmailTemplateRepository,
    EmailLogRepository,
    EmailProviderSettingsRepository,
    PushSubscriptionRepository,
)

logger = logging.getLogger(__name__)


class BaseNotificationService:
    """Base class for notification sub-services."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._notification_repo = NotificationRepository(session)
        self._template_repo = EmailTemplateRepository(session)
        self._email_log_repo = EmailLogRepository(session)
        self._provider_repo = EmailProviderSettingsRepository(session)
        self._push_repo = PushSubscriptionRepository(session)
        
        self._audit = get_audit_logger("notification-service")
        
        # Shared Clients
        self._auth_client = AuthClient()
        self._config_client = ConfigClient()
    
    @property
    def db(self) -> AsyncSession:
        return self._session

    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        return await self._auth_client.get_user_email(user_id)
