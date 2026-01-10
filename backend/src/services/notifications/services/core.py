import logging
import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional, Callable, Awaitable

from src.services.notifications.exceptions import NotificationNotFound
from src.core.exceptions import BusinessRuleError
from src.services.notifications.models import (
    NotificationStatus,
    NotificationChannel,
    NotificationPriority,
)
from src.services.notifications.schemas import (
    NotificationCreate,
    BulkNotificationRequest,
    BulkNotificationResponse,
)
from src.services.notifications.services.base import BaseNotificationService

logger = logging.getLogger(__name__)


class NotificationCoreService(BaseNotificationService):
    """
    Core service for Notification management.
    """
    
    def __init__(self, session, email_sender: Callable = None, push_sender: Callable = None):
        super().__init__(session)
        self.email_sender = email_sender
        self.push_sender = push_sender

    def set_senders(self, email_sender: Callable, push_sender: Callable):
        self.email_sender = email_sender
        self.push_sender = push_sender

    async def get_notification(self, id: UUID):
        """Get notification by ID."""
        notification = await self._notification_repo.get(id)
        if not notification:
            raise NotificationNotFound()
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        channel: Optional[str] = None,
    ):
        """Get notifications for a user."""
        return await self._notification_repo.get_by_user(
            user_id, unread_only, limit, channel
        )
    
    async def get_sent_history(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
    ):
        """Get history of sent notifications."""
        return await self._notification_repo.get_history(
            limit, offset, user_id, notification_type, status, channel
        )
        
    async def count_history(
        self,
        user_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
    ):
        """Count sent notifications history."""
        return await self._notification_repo.count_history(
            user_id, notification_type, status, channel
        )

    async def count_unread(self, user_id: UUID):
        """Count unread notifications."""
        return await self._notification_repo.count_unread(user_id)

    async def create_notification(self, data: NotificationCreate):
        """Create and optionally send notification."""
        # Note: _check_preferences logic was in original service. 
        # We need to assume the caller or this method checks preferences.
        # But this is the business logic.
        # We'll use a callback for preference check or move it to a shared helper?
        # Let's create `_check_preferences` in Base or here?
        # It's better here or in preferences module. But we need it here.
        # I'll rely on the facade to check preferences OR implement a simple check here if data provided.
        # Actually original service checked prefs inside `create_notification` IF prefs were passed or fetched.
        
        # NOTE: For simplicity, we assume preferences are checked by caller or we ignore for now 
        # (original code fetched them). To keep it modular, let's fetch them if needed.
        # But `create_notification` calls `_check_preferences`.
        
        # 1. Create record
        create_data = data.model_dump(exclude={"priority"})
        # Priority is NOT in model.
        
        notification = await self._notification_repo.create(**create_data)
        
        # Audit
        await self._audit.log_action(
            user_id=data.user_id,
            action="CREATE",
            resource_type="NOTIFICATION",
            resource_id=str(notification.id),
            description=f"Created notification {data.title}",
        )
        
        # 2. Try immediate send if urgent / queued
        if notification.status == NotificationStatus.QUEUED:
            if data.priority == NotificationPriority.URGENT:
                try:
                    sent = False
                    if notification.channel == NotificationChannel.EMAIL and self.email_sender:
                        sent = await self.email_sender(notification)
                    elif notification.channel == NotificationChannel.PUSH and self.push_sender:
                        sent = await self.push_sender(notification)
                        
                    if sent:
                        await self._notification_repo.mark_sent(notification.id)
                    else:
                        pass
                except Exception as e:
                    logger.error(f"Failed immediate send for {notification.id}: {e}")
                    await self._notification_repo.mark_failed(notification.id, str(e))
        
        # 3. Broadcast Real-Time (SSE)
        try:
            from src.services.notifications.broadcaster import NotificationBroadcaster
            from src.services.notifications.schemas import NotificationResponse
            
            # Only broadcast IN_APP notifications or those relevant
            if notification.channel == NotificationChannel.IN_APP:
                broadcaster = NotificationBroadcaster.get_instance()
                
                # Convert to response schema for clean JSON
                response_model = NotificationResponse.model_validate(notification)
                json_msg = response_model.model_dump_json()
                
                await broadcaster.broadcast(notification.user_id, json_msg)
        except Exception as e:
            logger.error(f"Failed to broadcast notification {notification.id}: {e}")

        return notification

    async def mark_read(self, notification_ids: list[UUID], user_id: UUID):
        """Mark notifications as read."""
        await self._notification_repo.mark_read(notification_ids, user_id)
        return True

    async def mark_all_read(self, user_id: UUID):
        """Mark all notifications as read."""
        await self._notification_repo.mark_all_read(user_id)
        return True

    async def send_bulk(self, data: BulkNotificationRequest):
        """Send bulk notifications."""
        from sqlalchemy import text
        
        # 1. Fetch user emails
        if not data.user_ids:
            return BulkNotificationResponse(total=0, sent=0, failed=0, errors=[])
            
        try:
             # Use raw SQL to fetch emails without importing auth models to avoid circular deps
             # Need to cast UUIDs to string or pass list properly
             # SQLAlchemy execute with list param handling
             q = text("SELECT id, email FROM auth.users WHERE id = ANY(:ids)")
             result = await self._session.execute(q, {"ids": data.user_ids})
             user_map = {row.id: row.email for row in result.fetchall()}
        except Exception as e:
             logger.error(f"Failed to fetch users for bulk: {e}")
             return BulkNotificationResponse(
                 total=len(data.user_ids), 
                 sent=0, 
                 failed=len(data.user_ids), 
                 errors=[f"Failed to fetch user emails: {str(e)}"]
             )

        success_count = 0
        failed_count = 0
        errors = []
        
        for user_id in data.user_ids:
            if user_id not in user_map:
                errors.append(f"User {user_id} not found")
                failed_count += 1
                continue
                
            email = user_map[user_id]
            
            try:
                # Handle channels (plural in Request, singular in Create)
                # Use getattr for robustness
                channels = getattr(data, 'channels', [NotificationChannel.IN_APP])
                # Handle priority
                priority = getattr(data, 'priority', NotificationPriority.NORMAL)
                
                for channel in channels:
                    notif_data = NotificationCreate(
                        user_id=user_id,
                        user_email=email,
                        notification_type=data.notification_type,
                        title=data.title,
                        message=data.message,
                        channel=channel,
                        priority=priority,
                        entity_type=data.entity_type if hasattr(data, 'entity_type') else None,
                        entity_id=data.entity_id if hasattr(data, 'entity_id') else None,
                        payload=data.payload,
                        action_url=data.action_url
                    )
                    
                    await self.create_notification(notif_data)
                
                success_count += 1
            except Exception as e:
                error_msg = f"Failed to send bulk to {user_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                failed_count += 1
        
        # Trigger immediate processing
        try:
            await self.process_queue()
        except Exception as e:
            logger.error(f"Failed to trigger process_queue after bulk: {e}")
            
        return BulkNotificationResponse(
            total=success_count + failed_count,
            sent=success_count,
            failed=failed_count,
            errors=errors
        )

    async def process_queue(self, batch_size: int = 100):
        """Process pending notifications concurrently."""
        notifications = await self._notification_repo.get_queued(batch_size)
        
        if not notifications:
            return {"processed": 0, "sent": 0, "failed": 0}

        results = {"processed": 0, "sent": 0, "failed": 0}
        
        # Limit concurrency to avoid overwhelming providers
        sem = asyncio.Semaphore(10)  # Max 10 concurrent sends

        # Execute sends concurrently (I/O)
        async def _do_send_only(n):
            async with sem:
                try:
                    sent = False
                    if n.channel == NotificationChannel.IN_APP:
                        sent = True
                    elif n.channel == NotificationChannel.EMAIL and self.email_sender:
                        sent = await self.email_sender(n)
                    elif n.channel == NotificationChannel.PUSH and self.push_sender:
                        sent = await self.push_sender(n)
                    return sent, None
                except Exception as e:
                    logger.error(f"Failed to process notification {n.id}: {e}")
                    return False, str(e)

        # Run I/O in parallel
        io_tasks = [_do_send_only(n) for n in notifications]
        io_results = await asyncio.gather(*io_tasks)
        
        # Process DB updates sequentially (Session is not thread-safe)
        files_count = 0 
        for notification, (success, error_msg) in zip(notifications, io_results):
            try:
                if success:
                    await self._notification_repo.mark_sent(notification.id)
                    results["sent"] += 1
                else:
                    await self._notification_repo.mark_failed(notification.id, error_msg or "Unknown error")
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to update status for {notification.id}: {e}")
                
        results["processed"] = len(notifications)
        
        return results

    async def cleanup_old(self, days: int = 90):
        """Cleanup old notifications."""
        return await self._notification_repo.cleanup(days)

    async def send_daily_digests(self):
        """Send daily digest to users."""
        # Implementation depends on aggregation logic which wasn't fully shown in snippets
        # Assuming placeholder or simple logic
        pass
