"""
KRONOS - Notification Service - Push Module

Handles Web Push Notifications and Subscriptions.
"""
import logging
import json
from uuid import UUID

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.notifications.models import Notification
from src.services.notifications.schemas import PushSubscriptionCreate
from src.services.notifications.services.base import BaseNotificationService
from src.core.config import settings

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None

logger = logging.getLogger(__name__)


class NotificationPushService(BaseNotificationService):
    """
    Sub-service for Push Notifications.
    """

    async def subscribe(self, user_id: UUID, data: PushSubscriptionCreate):
        """Subscribe to push notifications."""
        # Check if already exists? Repo handles upsert/check
        return await self._push_repo.create(user_id, **data.model_dump())

    async def unsubscribe(self, id: UUID, user_id: UUID):
        """Unsubscribe."""
        sub = await self._push_repo.get(id)
        if not sub:
             raise NotFoundError("Subscription not found")
        
        if sub.user_id != user_id:
             raise BusinessRuleError("Cannot delete another user's subscription")
             
        await self._push_repo.delete(id)
        return True

    async def get_my_subscriptions(self, user_id: UUID):
        """Get user subscriptions."""
        return await self._push_repo.get_by_user(user_id)

    async def send_push_notification(self, notification: Notification) -> bool:
        """Send web push notification."""
        if not webpush:
             logger.warning("pywebpush not installed")
             return False
             
        subs = await self._push_repo.get_by_user(notification.user_id)
        if not subs:
             return False
        
        payload = json.dumps({
            "title": notification.title,
            "body": notification.message,
            "data": {
                "url": f"{settings.FRONTEND_URL}/notifications/{notification.id}",
                "entity_type": notification.entity_type,
                "entity_id": str(notification.entity_id) if notification.entity_id else None
            }
        })
        
        # VAPID keys from config
        vapid_private = settings.VAPID_PRIVATE_KEY
        vapid_claims = {"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"}
        
        if not vapid_private:
             logger.warning("VAPID keys not configured")
             return False
             
        sent_count = 0
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth
                        }
                    },
                    data=payload,
                    vapid_private_key=vapid_private,
                    vapid_claims=vapid_claims
                )
                sent_count += 1
            except WebPushException as e:
                if e.response and e.response.status_code == 410:
                    # Expired, remove
                    await self._push_repo.delete(sub.id)
                else:
                    logger.error(f"Push failed: {e}")
            except Exception as e:
                logger.error(f"Push error: {e}")
                
        return sent_count > 0
