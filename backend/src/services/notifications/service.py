"""KRONOS Notification Service - Business Logic."""
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import NotFoundError
from src.services.notifications.models import (
    NotificationStatus,
    NotificationType,
    NotificationChannel,
)
from src.services.notifications.repository import (
    NotificationRepository,
    EmailTemplateRepository,
    UserPreferenceRepository,
)
from src.services.notifications.schemas import (
    NotificationCreate,
    SendEmailRequest,
    SendEmailResponse,
    BulkNotificationRequest,
    BulkNotificationResponse,
    UserPreferencesUpdate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
)


class NotificationService:
    """Service for notification management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._notification_repo = NotificationRepository(session)
        self._template_repo = EmailTemplateRepository(session)
        self._preference_repo = UserPreferenceRepository(session)

    # ═══════════════════════════════════════════════════════════
    # Notification Operations
    # ═══════════════════════════════════════════════════════════

    async def get_notification(self, id: UUID):
        """Get notification by ID."""
        notification = await self._notification_repo.get(id)
        if not notification:
            raise NotFoundError("Notification not found")
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
    ):
        """Get notifications for a user."""
        return await self._notification_repo.get_by_user(user_id, unread_only, limit)

    async def count_unread(self, user_id: UUID) -> int:
        """Count unread notifications."""
        return await self._notification_repo.count_unread(user_id)

    async def create_notification(self, data: NotificationCreate):
        """Create and optionally send notification."""
        # Check user preferences
        prefs = await self._preference_repo.get_or_create(data.user_id)
        
        # Check if user wants this type of notification
        should_send = self._check_preferences(prefs, data.notification_type, data.channel)
        
        if not should_send:
            return None
        
        # Create notification
        notification = await self._notification_repo.create(
            user_id=data.user_id,
            user_email=data.user_email,
            notification_type=data.notification_type,
            title=data.title,
            message=data.message,
            channel=data.channel,
            status=NotificationStatus.PENDING,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            action_url=data.action_url,
            payload=data.payload,
        )
        
        # Send immediately if email
        if data.channel == NotificationChannel.EMAIL:
            await self._send_email_notification(notification)
        else:
            # Mark as sent for in-app
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow(),
            )
        
        return notification

    async def mark_read(self, notification_ids: list[UUID], user_id: UUID) -> int:
        """Mark notifications as read."""
        return await self._notification_repo.mark_read(notification_ids, user_id)

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read."""
        return await self._notification_repo.mark_all_read(user_id)

    async def send_bulk(self, data: BulkNotificationRequest) -> BulkNotificationResponse:
        """Send bulk notifications."""
        total = len(data.user_ids)
        sent = 0
        failed = 0
        errors = []
        
        for user_id in data.user_ids:
            try:
                # Get user email from auth service
                user_email = await self._get_user_email(user_id)
                if not user_email:
                    errors.append(f"Email not found for user {user_id}")
                    failed += 1
                    continue
                
                for channel in data.channels:
                    await self.create_notification(NotificationCreate(
                        user_id=user_id,
                        user_email=user_email,
                        notification_type=data.notification_type,
                        title=data.title,
                        message=data.message,
                        channel=channel,
                        action_url=data.action_url,
                        payload=data.payload,
                    ))
                
                sent += 1
            except Exception as e:
                errors.append(f"Failed for user {user_id}: {str(e)}")
                failed += 1
        
        return BulkNotificationResponse(
            total=total,
            sent=sent,
            failed=failed,
            errors=errors,
        )

    # ═══════════════════════════════════════════════════════════
    # Email Operations
    # ═══════════════════════════════════════════════════════════

    async def send_email(self, data: SendEmailRequest) -> SendEmailResponse:
        """Send email using Brevo."""
        # Get template
        template = await self._template_repo.get_by_code(data.template_code)
        if not template:
            return SendEmailResponse(
                success=False,
                error=f"Template not found: {data.template_code}",
            )
        
        try:
            # Send via Brevo
            result = await self._send_brevo_email(
                to_email=data.to_email,
                to_name=data.to_name,
                template=template,
                variables=data.variables,
            )
            
            # Update notification if linked
            if data.notification_id:
                await self._notification_repo.update(
                    data.notification_id,
                    status=NotificationStatus.SENT,
                    sent_at=datetime.utcnow(),
                )
            
            return SendEmailResponse(
                success=True,
                message_id=result.get("messageId"),
            )
            
        except Exception as e:
            if data.notification_id:
                notification = await self._notification_repo.get(data.notification_id)
                await self._notification_repo.update(
                    data.notification_id,
                    status=NotificationStatus.FAILED,
                    error_message=str(e),
                    retry_count=(notification.retry_count or 0) + 1,
                )
            
            return SendEmailResponse(
                success=False,
                error=str(e),
            )

    async def _send_email_notification(self, notification) -> None:
        """Send email for a notification."""
        # Get template for notification type
        template = await self._template_repo.get_by_notification_type(
            notification.notification_type
        )
        
        if not template:
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.FAILED,
                error_message="No template found for notification type",
            )
            return
        
        # Build variables
        variables = {
            "title": notification.title,
            "message": notification.message,
            "action_url": notification.action_url or "",
            **(notification.payload or {}),
        }
        
        try:
            await self._send_brevo_email(
                to_email=notification.user_email,
                template=template,
                variables=variables,
            )
            
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow(),
            )
            
        except Exception as e:
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.FAILED,
                error_message=str(e),
                retry_count=(notification.retry_count or 0) + 1,
            )

    async def _send_brevo_email(
        self,
        to_email: str,
        template,
        variables: dict,
        to_name: Optional[str] = None,
    ) -> dict:
        """Send email via Brevo API."""
        if not settings.brevo_api_key:
            # Development mode - just log
            print(f"[DEV] Would send email to {to_email}: {template.subject}")
            return {"messageId": "dev-mode"}
        
        headers = {
            "api-key": settings.brevo_api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "to": [{"email": to_email, "name": to_name or to_email}],
            "sender": {
                "email": settings.brevo_sender_email,
                "name": settings.brevo_sender_name,
            },
            "params": variables,
        }
        
        if template.brevo_template_id:
            # Use Brevo template
            payload["templateId"] = template.brevo_template_id
        else:
            # Use inline content
            payload["subject"] = template.subject
            if template.html_content:
                payload["htmlContent"] = self._render_template(
                    template.html_content,
                    variables,
                )
            if template.text_content:
                payload["textContent"] = self._render_template(
                    template.text_content,
                    variables,
                )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    def _render_template(self, content: str, variables: dict) -> str:
        """Simple template rendering with {{variable}} syntax."""
        result = content
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value or ""))
        return result

    # ═══════════════════════════════════════════════════════════
    # Template Operations
    # ═══════════════════════════════════════════════════════════

    async def get_templates(self, active_only: bool = True):
        """Get all templates."""
        return await self._template_repo.get_all(active_only)

    async def get_template(self, id: UUID):
        """Get template by ID."""
        template = await self._template_repo.get(id)
        if not template:
            raise NotFoundError("Template not found")
        return template

    async def create_template(self, data: EmailTemplateCreate):
        """Create email template."""
        return await self._template_repo.create(**data.model_dump())

    async def update_template(self, id: UUID, data: EmailTemplateUpdate):
        """Update email template."""
        template = await self._template_repo.update(
            id,
            **data.model_dump(exclude_unset=True),
        )
        if not template:
            raise NotFoundError("Template not found")
        return template

    # ═══════════════════════════════════════════════════════════
    # Preferences Operations
    # ═══════════════════════════════════════════════════════════

    async def get_preferences(self, user_id: UUID):
        """Get user preferences."""
        return await self._preference_repo.get_or_create(user_id)

    async def update_preferences(self, user_id: UUID, data: UserPreferencesUpdate):
        """Update user preferences."""
        return await self._preference_repo.update(
            user_id,
            **data.model_dump(exclude_unset=True),
        )

    # ═══════════════════════════════════════════════════════════
    # Private Helpers
    # ═══════════════════════════════════════════════════════════

    def _check_preferences(
        self,
        prefs,
        notification_type: NotificationType,
        channel: NotificationChannel,
    ) -> bool:
        """Check if user wants this notification."""
        if channel == NotificationChannel.EMAIL:
            if not prefs.email_enabled:
                return False
            
            # Check specific type
            if notification_type.value.startswith("leave_"):
                return prefs.email_leave_updates
            elif notification_type.value.startswith(("trip_", "expense_")):
                return prefs.email_expense_updates
            elif notification_type == NotificationType.SYSTEM_ANNOUNCEMENT:
                return prefs.email_system_announcements
            elif notification_type == NotificationType.COMPLIANCE_ALERT:
                return prefs.email_compliance_alerts
        
        elif channel == NotificationChannel.IN_APP:
            return prefs.in_app_enabled
        
        return True

    async def _get_user_email(self, user_id: UUID) -> Optional[str]:
        """Get user email from auth service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/api/v1/users/{user_id}",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return response.json().get("email")
        except Exception:
            pass
        return None
