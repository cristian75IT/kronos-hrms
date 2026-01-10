from datetime import datetime, timedelta
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notifications.models import Notification
from src.services.auth.models import User

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
        channel: Optional[str] = None,
    ) -> list[Notification]:
        """Get notifications for a user."""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.read_at.is_(None))
            
        if channel and channel != 'all':
            query = query.where(Notification.channel == channel)
        
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
        channel: Optional[str] = None,
    ) -> list[Notification]:
        """Get notification history with filters."""
        query = (
            select(Notification, User)
            .join(User, Notification.user_id == User.id)
            .order_by(Notification.created_at.desc())
        )
        
        if user_id:
            query = query.where(Notification.user_id == user_id)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if status:
            query = query.where(Notification.status == status)
        if channel and channel != 'all':
            query = query.where(Notification.channel == channel)
            
        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        
        items = []
        for notification, user in result:
            notification.recipient_name = f"{user.first_name} {user.last_name}"
            items.append(notification)
            
        return items

    async def count_history(
        self,
        user_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> int:
        """Count total notifications matching filters."""
        query = select(func.count(Notification.id))
        
        if user_id:
            query = query.where(Notification.user_id == user_id)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if status:
            query = query.where(Notification.status == status)
        if channel and channel != 'all':
            query = query.where(Notification.channel == channel)
            
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def get_queued(self, limit: int = 100) -> list[Notification]:
        """Get queued notifications for processing."""
        # Original code used 'pending' status but 'queued' is also used in other places. 
        # Assuming we align with models.NotificationStatus or simple string 'pending'
        # Looking at original repo it used string 'pending' in get_pending.
        # But core service uses NotificationStatus.QUEUED.
        # Let's support both or fix it. Original code: .where(Notification.status == "pending")
        # We'll stick to string for now to match original behavior logic unless we see enum usage.
        # Core service does: if notification.status == NotificationStatus.QUEUED try immediate.
        # So we likely want to fetch QUEUED items.
        
        result = await self._session.execute(
            select(Notification)
            .where(Notification.status.in_(["pending", "queued"]))
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

    async def mark_sent(self, id: UUID) -> None:
        """Mark notification as sent."""
        await self.update(id, status="sent", sent_at=datetime.utcnow())

    async def mark_failed(self, id: UUID, error: str) -> None:
        """Mark notification as failed."""
        await self.update(id, status="failed", error_message=error)

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

    async def cleanup(self, days: int = 90) -> int:
        """Delete old notifications."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self._session.execute(
            delete(Notification).where(Notification.created_at < cutoff_date)
        )
        await self._session.flush()
        return result.rowcount
