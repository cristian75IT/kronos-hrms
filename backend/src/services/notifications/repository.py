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
    EmailLog,
    EmailLogStatus,
)
from src.services.auth.models import User
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


class EmailLogRepository:
    """Repository for email logs - enterprise email tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[EmailLog]:
        """Get email log by ID."""
        result = await self._session.execute(
            select(EmailLog).where(EmailLog.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_message_id(self, message_id: str) -> Optional[EmailLog]:
        """Get email log by external message ID."""
        result = await self._session.execute(
            select(EmailLog).where(EmailLog.message_id == message_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        to_email: str,
        template_code: str,
        to_name: Optional[str] = None,
        user_id: Optional[UUID] = None,
        subject: Optional[str] = None,
        variables: Optional[dict] = None,
        notification_id: Optional[UUID] = None,
    ) -> EmailLog:
        """Create email log entry."""
        log = EmailLog(
            to_email=to_email,
            to_name=to_name,
            user_id=user_id,
            template_code=template_code,
            subject=subject,
            variables=variables,
            notification_id=notification_id,
            status=EmailLogStatus.PENDING.value,
        )
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def update_status(
        self,
        id: UUID,
        status: str,
        message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        provider_response: Optional[dict] = None,
    ) -> Optional[EmailLog]:
        """Update email log status."""
        log = await self.get(id)
        if not log:
            return None

        log.status = status
        if message_id:
            log.message_id = message_id
        if error_message:
            log.error_message = error_message
        if provider_response:
            log.provider_response = provider_response

        # Set timestamp based on status
        now = datetime.utcnow()
        if status == EmailLogStatus.SENT.value:
            log.sent_at = now
        elif status == EmailLogStatus.DELIVERED.value:
            log.delivered_at = now
        elif status == EmailLogStatus.OPENED.value:
            log.opened_at = now
        elif status == EmailLogStatus.CLICKED.value:
            log.clicked_at = now
        elif status == EmailLogStatus.BOUNCED.value:
            log.bounced_at = now
        elif status == EmailLogStatus.FAILED.value:
            log.failed_at = now
            log.retry_count = (log.retry_count or 0) + 1

        await self._session.flush()
        return log

    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        template_code: Optional[str] = None,
        to_email: Optional[str] = None,
    ) -> list[EmailLog]:
        """Get email log history with filters."""
        query = select(EmailLog).order_by(EmailLog.created_at.desc())

        if status:
            query = query.where(EmailLog.status == status)
        if template_code:
            query = query.where(EmailLog.template_code == template_code)
        if to_email:
            query = query.where(EmailLog.to_email.ilike(f"%{to_email}%"))

        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_history(
        self,
        status: Optional[str] = None,
        template_code: Optional[str] = None,
    ) -> int:
        """Count email logs with filters."""
        query = select(func.count(EmailLog.id))

        if status:
            query = query.where(EmailLog.status == status)
        if template_code:
            query = query.where(EmailLog.template_code == template_code)

        result = await self._session.execute(query)
        return result.scalar() or 0

    async def get_pending_retries(self, limit: int = 50) -> list[EmailLog]:
        """Get emails pending retry."""
        now = datetime.utcnow()
        query = (
            select(EmailLog)
            .where(
                and_(
                    EmailLog.status == EmailLogStatus.FAILED.value,
                    EmailLog.retry_count < 3,  # Max 3 retries
                    EmailLog.next_retry_at <= now,
                )
            )
            .order_by(EmailLog.next_retry_at)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def schedule_retry(self, id: UUID, delay_minutes: int = 5) -> Optional[EmailLog]:
        """Schedule email for retry with exponential backoff."""
        log = await self.get(id)
        if not log:
            return None

        # Exponential backoff: 5min, 15min, 45min
        backoff_multiplier = 3 ** log.retry_count
        actual_delay = delay_minutes * backoff_multiplier

        log.next_retry_at = datetime.utcnow() + timedelta(minutes=actual_delay)
        log.status = EmailLogStatus.PENDING.value
        await self._session.flush()
        return log

    async def get_stats(self, days: int = 7) -> dict:
        """Get email delivery statistics."""
        since = datetime.utcnow() - timedelta(days=days)

        # Total count
        total_result = await self._session.execute(
            select(func.count(EmailLog.id)).where(EmailLog.created_at >= since)
        )
        total = total_result.scalar() or 0

        # Status breakdown
        stats = {"total": total, "by_status": {}}
        for status in EmailLogStatus:
            count_result = await self._session.execute(
                select(func.count(EmailLog.id)).where(
                    and_(
                        EmailLog.created_at >= since,
                        EmailLog.status == status.value,
                    )
                )
            )
            stats["by_status"][status.value] = count_result.scalar() or 0

        # Calculate success rate
        successful = stats["by_status"].get("sent", 0) + stats["by_status"].get("delivered", 0)
        stats["success_rate"] = round(100 * successful / total, 2) if total > 0 else 0

        return stats


class EmailProviderSettingsRepository:
    """Repository for email provider settings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self, provider: str = "brevo") -> Optional["EmailProviderSettings"]:
        """Get the active settings for a provider."""
        from src.services.notifications.models import EmailProviderSettings
        
        result = await self._session.execute(
            select(EmailProviderSettings)
            .where(
                and_(
                    EmailProviderSettings.provider == provider,
                    EmailProviderSettings.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider: str = "brevo") -> Optional["EmailProviderSettings"]:
        """Get settings for a provider (active or inactive)."""
        from src.services.notifications.models import EmailProviderSettings
        
        result = await self._session.execute(
            select(EmailProviderSettings).where(EmailProviderSettings.provider == provider)
        )
        return result.scalar_one_or_none()

    async def get(self, id: UUID) -> Optional["EmailProviderSettings"]:
        """Get settings by ID."""
        from src.services.notifications.models import EmailProviderSettings
        
        result = await self._session.execute(
            select(EmailProviderSettings).where(EmailProviderSettings.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list:
        """Get all provider settings."""
        from src.services.notifications.models import EmailProviderSettings
        
        result = await self._session.execute(
            select(EmailProviderSettings).order_by(EmailProviderSettings.provider)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> "EmailProviderSettings":
        """Create provider settings."""
        from src.services.notifications.models import EmailProviderSettings
        
        settings = EmailProviderSettings(**kwargs)
        self._session.add(settings)
        await self._session.flush()
        return settings

    async def update(self, id: UUID, **kwargs) -> Optional["EmailProviderSettings"]:
        """Update provider settings."""
        settings = await self.get(id)
        if not settings:
            return None

        for field, value in kwargs.items():
            if hasattr(settings, field) and value is not None:
                setattr(settings, field, value)

        await self._session.flush()
        return settings

    async def increment_emails_sent(self, id: UUID) -> None:
        """Increment daily email counter."""
        from src.services.notifications.models import EmailProviderSettings
        
        settings = await self.get(id)
        if settings:
            today = datetime.utcnow().date()
            if settings.last_reset_date and settings.last_reset_date.date() != today:
                # Reset counter for new day
                settings.emails_sent_today = 1
                settings.last_reset_date = datetime.utcnow()
            else:
                settings.emails_sent_today = (settings.emails_sent_today or 0) + 1
                if not settings.last_reset_date:
                    settings.last_reset_date = datetime.utcnow()
            await self._session.flush()

    async def can_send_email(self, id: UUID) -> bool:
        """Check if daily limit allows sending."""
        settings = await self.get(id)
        if not settings:
            return False
        
        if not settings.daily_limit:
            return True  # No limit configured
        
        today = datetime.utcnow().date()
        if settings.last_reset_date and settings.last_reset_date.date() != today:
            return True  # New day, counter will reset
        
        return (settings.emails_sent_today or 0) < settings.daily_limit


class CalendarExternalRepository:
    """Repository for accessing calendar data from notification service.
    
    NOTE: This violates strict microservice isolation but centralizes queries
    until a full API-based integration is implemented.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_upcoming_closures(self, target_date: Any) -> list:
        """Get closures starting on a specific date."""
        from src.services.calendar.models import CalendarClosure
        result = await self._session.execute(
            select(CalendarClosure).where(
                and_(
                    CalendarClosure.start_date == target_date,
                    CalendarClosure.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    async def get_upcoming_holidays(self, target_date: Any, scope: str = "national") -> list:
        """Get holidays on a specific date with given scope."""
        from src.services.calendar.models import CalendarHoliday
        result = await self._session.execute(
            select(CalendarHoliday).where(
                and_(
                    CalendarHoliday.date == target_date,
                    CalendarHoliday.is_active == True,
                    CalendarHoliday.scope == scope,
                )
            )
        )
        return list(result.scalars().all())

    async def get_upcoming_personal_events(self, target_date: Any) -> list:
        """Get personal events starting on a specific date."""
        from src.services.calendar.models import CalendarEvent
        result = await self._session.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.start_date == target_date,
                    CalendarEvent.status == "confirmed",
                    CalendarEvent.user_id.isnot(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_upcoming_shared_events(self, target_date: Any) -> list:
        """Get shared/team events starting on a specific date."""
        from src.services.calendar.models import CalendarEvent
        result = await self._session.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.start_date == target_date,
                    CalendarEvent.status == "confirmed",
                    CalendarEvent.calendar_id.isnot(None),
                    CalendarEvent.visibility.in_(["team", "public"]),
                )
            )
        )
        return list(result.scalars().all())

    async def get_calendar_shares(self, calendar_id: UUID) -> list:
        """Get shares for a specific calendar."""
        from src.services.calendar.models import CalendarShare
        result = await self._session.execute(
            select(CalendarShare).where(CalendarShare.calendar_id == calendar_id)
        )
        return list(result.scalars().all())
