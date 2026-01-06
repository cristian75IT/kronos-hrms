"""
KRONOS - Notification Services Package

Modular notification service architecture.

Modules:
- core.py: CRUD, Queue, Management
- email.py: Email delivery
- push.py: Push delivery
- templates.py: Templates
- providers.py: Settings
- preferences.py: User Prefs

Usage:
    from src.services.notifications.services import NotificationService
"""
from typing import Optional, List, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notifications.models import Notification
from src.services.notifications.schemas import (
    NotificationCreate,
    BulkNotificationRequest,
    SendEmailRequest,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailProviderSettingsCreate,
    EmailProviderSettingsUpdate,
    TestEmailRequest,
    PushSubscriptionCreate,
    UserPreferencesUpdate,
    MarkReadRequest, # If exists
)

# Import sub-services
from src.services.notifications.services.base import BaseNotificationService
from src.services.notifications.services.core import NotificationCoreService
from src.services.notifications.services.email import NotificationEmailService
from src.services.notifications.services.push import NotificationPushService
from src.services.notifications.services.templates import NotificationTemplateService
from src.services.notifications.services.providers import NotificationProviderService
from src.services.notifications.services.preferences import NotificationPreferencesService

import logging
logger = logging.getLogger(__name__)


class NotificationService(BaseNotificationService):
    """
    Unified Notification Service façade.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        
        self._email = NotificationEmailService(session)
        self._push = NotificationPushService(session)
        
        # Core needs callables for sending
        self._core = NotificationCoreService(
            session,
            email_sender=self._email.send_email_notification,
            push_sender=self._push.send_push_notification
        )
        
        self._templates = NotificationTemplateService(session)
        self._providers = NotificationProviderService(session)
        self._prefs = NotificationPreferencesService(session)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Core (Notifications)
    # ═══════════════════════════════════════════════════════════════════════

    async def get_notification(self, id: UUID):
        return await self._core.get_notification(id)

    async def get_user_notifications(self, user_id: UUID, unread_only: bool = False, limit: int = 50, channel: Optional[str] = None):
        return await self._core.get_user_notifications(user_id, unread_only, limit, channel)

    async def get_sent_history(self, limit: int = 50, offset: int = 0, user_id: Optional[UUID] = None, notification_type: Optional[str] = None, status: Optional[str] = None, channel: Optional[str] = None):
        return await self._core.get_sent_history(limit, offset, user_id, notification_type, status, channel)
        
    async def count_history(self, user_id: Optional[UUID] = None, notification_type: Optional[str] = None, status: Optional[str] = None, channel: Optional[str] = None):
        return await self._core.count_history(user_id, notification_type, status, channel)

    async def count_unread(self, user_id: UUID):
        return await self._core.count_unread(user_id)

    async def create_notification(self, data: NotificationCreate):
        return await self._core.create_notification(data)

    async def mark_read(self, notification_ids: list[UUID], user_id: UUID):
        return await self._core.mark_read(notification_ids, user_id)

    async def mark_all_read(self, user_id: UUID):
        return await self._core.mark_all_read(user_id)

    async def send_bulk(self, data: BulkNotificationRequest):
        return await self._core.send_bulk(data)
    
    async def process_queue(self, batch_size: int = 100):
        return await self._core.process_queue(batch_size)

    async def cleanup_old(self, days: int = 90):
        return await self._core.cleanup_old(days)
    
    async def send_daily_digests(self):
        return await self._core.send_daily_digests()

    # ═══════════════════════════════════════════════════════════════════════
    # Email
    # ═══════════════════════════════════════════════════════════════════════

    async def send_email(self, data: SendEmailRequest):
        return await self._email.send_email(data)
    
    async def get_email_logs(self, status: Optional[str] = None, template_code: Optional[str] = None, to_email: Optional[str] = None, limit: int = 50, offset: int = 0):
        return await self._email.get_email_logs(status, template_code, to_email, limit, offset)

    async def get_email_stats(self, days: int = 7):
        return await self._email.get_email_stats(days)

    async def retry_email(self, log_id: UUID):
        return await self._email.retry_email(log_id)

    async def get_email_events(self, log_id: UUID, permissive: bool = False):
        return await self._email.get_email_events(log_id, permissive)

    # ═══════════════════════════════════════════════════════════════════════
    # Push
    # ═══════════════════════════════════════════════════════════════════════

    async def subscribe_to_push(self, user_id: UUID, data: PushSubscriptionCreate):
        return await self._push.subscribe(user_id, data)

    async def unsubscribe_from_push(self, id: UUID, user_id: UUID):
        return await self._push.unsubscribe(id, user_id)

    async def get_my_push_subscriptions(self, user_id: UUID):
        return await self._push.get_my_subscriptions(user_id)

    # ═══════════════════════════════════════════════════════════════════════
    # Templates
    # ═══════════════════════════════════════════════════════════════════════

    async def get_templates(self, active_only: bool = True):
        return await self._templates.get_templates(active_only)

    async def get_template(self, id: UUID):
        return await self._templates.get_template(id)

    async def create_template(self, data: EmailTemplateCreate):
        return await self._templates.create_template(data)

    async def update_template(self, id: UUID, data: EmailTemplateUpdate, user_id: Optional[UUID] = None):
        return await self._templates.update_template(id, data, user_id)

    async def sync_template_to_brevo(self, id: UUID, user_id: Optional[UUID] = None):
        return await self._templates.sync_template_to_brevo(id, user_id)

    # ═══════════════════════════════════════════════════════════════════════
    # Providers
    # ═══════════════════════════════════════════════════════════════════════

    async def get_email_provider_settings(self):
        return await self._providers.get_active_settings() # Or get all? Wrapper

    async def create_email_provider_settings(self, data: EmailProviderSettingsCreate):
        return await self._providers.create_settings(data)
        
    async def update_email_provider_settings(self, id: UUID, data: EmailProviderSettingsUpdate):
        return await self._providers.update_settings(id, data)

    async def test_email_settings(self, data: TestEmailRequest):
        return await self._providers.test_settings(data)

    # ═══════════════════════════════════════════════════════════════════════
    # Preferences
    # ═══════════════════════════════════════════════════════════════════════

    async def get_my_preferences(self, user_id: UUID):
        return await self._prefs.get_preferences(user_id)

    async def update_my_preferences(self, user_id: UUID, data: UserPreferencesUpdate):
        return await self._prefs.update_preferences(user_id, data)

# Export
__all__ = ["NotificationService"]
