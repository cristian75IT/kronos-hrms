"""KRONOS Notification Service - Repository Layer."""
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notifications.models import (
    Notification,
    NotificationStatus,
    NotificationType,
    NotificationChannel,
    EmailTemplate,
    UserNotificationPreference,
    PushSubscription,
)
from src.shared.schemas import DataTableRequest


class NotificationRepository:
    """Repository for notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Notification]:
        """Get notification by ID."""
        result = await self._session.execute(
            select(Notification).where(Notification.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.read_at.is_(None))
        
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_unread(self, user_id: UUID) -> int:
        """Count unread notifications."""
        result = await self._session.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                    Notification.channel == "in_app",
                )
            )
        )
        return result.scalar() or 0

    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[Notification]:
        """Get notification history with filters."""
        query = select(Notification).order_by(Notification.created_at.desc())
        
        if user_id:
            query = query.where(Notification.user_id == user_id)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if status:
            query = query.where(Notification.status == status)
            
        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_history(
        self,
        user_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count total notifications matching filters."""
        query = select(func.count(Notification.id))
        
        if user_id:
            query = query.where(Notification.user_id == user_id)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if status:
            query = query.where(Notification.status == status)
            
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def get_pending(self, limit: int = 100) -> list[Notification]:
        """Get pending notifications for processing."""
        result = await self._session.execute(
            select(Notification)
            .where(Notification.status == "pending")
            .order_by(Notification.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Notification:
        """Create notification."""
        notification = Notification(**kwargs)
        self._session.add(notification)
        await self._session.flush()
        return notification

    async def update(self, id: UUID, **kwargs: Any) -> Optional[Notification]:
        """Update notification."""
        notification = await self.get(id)
        if not notification:
            return None
        
        for field, value in kwargs.items():
            if hasattr(notification, field) and value is not None:
                setattr(notification, field, value)
        
        await self._session.flush()
        return notification

    async def mark_read(self, notification_ids: list[UUID], user_id: UUID) -> int:
        """Mark multiple notifications as read."""
        result = await self._session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.id.in_(notification_ids),
                    Notification.user_id == user_id,
                )
            )
            .values(
                read_at=datetime.utcnow(),
                status="read",
            )
        )
        await self._session.flush()
        return result.rowcount

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        result = await self._session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                )
            )
            .values(
                read_at=datetime.utcnow(),
                status="read",
            )
        )
        await self._session.flush()
        return result.rowcount

    async def delete_old(self, days: int = 90) -> int:
        """Delete old notifications."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self._session.execute(
            delete(Notification).where(Notification.created_at < cutoff_date)
        )
        return result.rowcount


class EmailTemplateRepository:
    """Repository for email templates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[EmailTemplate]:
        """Get template by ID."""
        result = await self._session.execute(
            select(EmailTemplate).where(EmailTemplate.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[EmailTemplate]:
        """Get template by code."""
        result = await self._session.execute(
            select(EmailTemplate)
            .where(
                and_(
                    EmailTemplate.code == code,
                    EmailTemplate.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_notification_type(
        self,
        notification_type: NotificationType,
    ) -> Optional[EmailTemplate]:
        """Get template by notification type."""
        result = await self._session.execute(
            select(EmailTemplate)
            .where(
                and_(
                    EmailTemplate.notification_type == notification_type,
                    EmailTemplate.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[EmailTemplate]:
        """Get all templates."""
        query = select(EmailTemplate).order_by(EmailTemplate.code)
        
        if active_only:
            query = query.where(EmailTemplate.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> EmailTemplate:
        """Create template."""
        template = EmailTemplate(**kwargs)
        self._session.add(template)
        await self._session.flush()
        return template

    async def update(self, id: UUID, **kwargs: Any) -> Optional[EmailTemplate]:
        """Update template."""
        template = await self.get(id)
        if not template:
            return None
        
        for field, value in kwargs.items():
            if hasattr(template, field) and value is not None:
                setattr(template, field, value)
        
        await self._session.flush()
        return template


class UserPreferenceRepository:
    """Repository for user notification preferences."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> Optional[UserNotificationPreference]:
        """Get preferences for a user."""
        result = await self._session.execute(
            select(UserNotificationPreference)
            .where(UserNotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: UUID) -> UserNotificationPreference:
        """Get existing preferences or create defaults."""
        prefs = await self.get(user_id)
        if prefs:
            return prefs
        
        prefs = UserNotificationPreference(user_id=user_id)
        self._session.add(prefs)
        await self._session.flush()
        return prefs

    async def update(self, user_id: UUID, **kwargs: Any) -> UserNotificationPreference:
        """Update preferences."""
        prefs = await self.get_or_create(user_id)
        
        for field, value in kwargs.items():
            if hasattr(prefs, field) and value is not None:
                setattr(prefs, field, value)
        
        await self._session.flush()
        return prefs


class PushSubscriptionRepository:
    """Repository for Web Push subscriptions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[PushSubscription]:
        """Get subscription by ID."""
        result = await self._session.execute(
            select(PushSubscription).where(PushSubscription.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[PushSubscription]:
        """Get all active subscriptions for a user."""
        result = await self._session.execute(
            select(PushSubscription)
            .where(
                and_(
                    PushSubscription.user_id == user_id,
                    PushSubscription.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    async def get_by_endpoint(self, endpoint: str) -> Optional[PushSubscription]:
        """Get subscription by endpoint URL."""
        result = await self._session.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: UUID,
        endpoint: str,
        p256dh: str,
        auth: str,
        device_info: Optional[dict] = None,
    ) -> PushSubscription:
        """Create or update subscription."""
        # Check if subscription already exists for this endpoint
        existing = await self.get_by_endpoint(endpoint)
        if existing:
            existing.user_id = user_id
            existing.p256dh = p256dh
            existing.auth = auth
            existing.device_info = device_info
            existing.is_active = True
            await self._session.flush()
            return existing
        
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            device_info=device_info,
        )
        self._session.add(subscription)
        await self._session.flush()
        return subscription

    async def deactivate(self, id: UUID) -> bool:
        """Deactivate a subscription."""
        subscription = await self.get(id)
        if not subscription:
            return False
        subscription.is_active = False
        await self._session.flush()
        return True

    async def delete_by_endpoint(self, endpoint: str) -> bool:
        """Delete subscription by endpoint."""
        result = await self._session.execute(
            delete(PushSubscription).where(PushSubscription.endpoint == endpoint)
        )
        return result.rowcount > 0

    async def delete_by_user(self, user_id: UUID) -> int:
        """Delete all subscriptions for a user."""
        result = await self._session.execute(
            delete(PushSubscription).where(PushSubscription.user_id == user_id)
        )
        return result.rowcount
