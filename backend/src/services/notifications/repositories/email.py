from datetime import datetime, timedelta
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notifications.models import (
    EmailLog,
    EmailTemplate,
    EmailLogStatus,
    NotificationType
)

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

    async def create_pending(
        self,
        to_email: str,
        template_code: Optional[str] = None,
        to_name: Optional[str] = None,
        user_id: Optional[UUID] = None,
        subject: Optional[str] = None,
        variables: Optional[dict] = None,
        notification_id: Optional[UUID] = None,
    ) -> EmailLog:
        """Create email log entry in pending status."""
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

    async def mark_sent(self, id: UUID, message_id: str) -> None:
        """Mark log as sent."""
        await self.update_status(id, status=EmailLogStatus.SENT.value, message_id=message_id)

    async def mark_failed(self, id: UUID, error: str) -> None:
        """Mark log as failed."""
        await self.update_status(id, status=EmailLogStatus.FAILED.value, error_message=error)

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

    async def get_logs(
        self,
        status: Optional[str] = None,
        template_code: Optional[str] = None,
        to_email: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[EmailLog]:
        """Get email logs history."""
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

    async def get_pending_retries(self, limit: int = 50) -> list[EmailLog]:
        """Get failed emails eligible for retry."""
        result = await self._session.execute(
            select(EmailLog)
            .where(
                and_(
                    EmailLog.status == EmailLogStatus.FAILED.value,
                    EmailLog.retry_count < 3,  # Max 3 retries
                )
            )
            .order_by(EmailLog.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def schedule_retry(self, id: UUID) -> None:
        """Schedule email for retry (just updates status back to pending)."""
        log = await self.get(id)
        if log:
            log.status = EmailLogStatus.PENDING.value
            await self._session.flush()


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
