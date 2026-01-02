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
from src.shared.audit_client import get_audit_logger


class NotificationService:
    """Service for notification management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._notification_repo = NotificationRepository(session)
        self._template_repo = EmailTemplateRepository(session)
        self._preference_repo = UserPreferenceRepository(session)
        self._audit_logger = get_audit_logger("notification-service")

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
        channel: Optional[str] = None,
    ):
        """Get notifications for a user."""
        return await self._notification_repo.get_by_user(user_id, unread_only, limit, channel)

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
            limit=limit,
            offset=offset,
            user_id=user_id,
            notification_type=notification_type,
            status=status,
            channel=channel,
        )

    async def count_history(
        self,
        user_id: Optional[UUID] = None,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> int:
        """Count sent notifications history."""
        return await self._notification_repo.count_history(
            user_id=user_id,
            notification_type=notification_type,
            status=status,
            channel=channel,
        )

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
        elif data.channel == NotificationChannel.PUSH:
            await self._send_push_notification(notification)
        else:
            # Mark as sent for in-app
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow(),
            )
        
        # Log to Audit Service
        await self._audit_logger.log_action(
            user_id=data.user_id,
            user_email=data.user_email,
            action="NOTIFICATION_SENT",
            resource_type="NOTIFICATION",
            resource_id=str(notification.id),
            description=f"Notification sent via {data.channel.value}",
            request_data={
                "channel": data.channel.value,
                "type": data.notification_type.value,
                "title": data.title
            },
            status="SUCCESS"
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

    async def process_queue(self, batch_size: int = 100) -> int:
        """Process pending notifications."""
        notifications = await self._notification_repo.get_pending(limit=batch_size)
        processed = 0
        
        for notification in notifications:
            try:
                if notification.channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(notification)
                elif notification.channel == NotificationChannel.PUSH:
                    await self._send_push_notification(notification)
                else:
                    # Mark as sent for other channels (e.g. In-App are 'sent' when created usually, but if queued here)
                    await self._notification_repo.update(
                        notification.id,
                        status=NotificationStatus.SENT,
                        sent_at=datetime.utcnow(),
                    )
                processed += 1
            except Exception as e:
                # Error handling already in _send_email_notification but good to catch generic here
                print(f"Error processing notification {notification.id}: {e}")
                
        return processed

    async def cleanup_old(self, days: int = 90) -> int:
        """Cleanup old notifications."""
        return await self._notification_repo.delete_old(days)

    async def send_daily_digests(self) -> int:
        """Send daily digest to users."""
        # Implementation of daily digest logic
        # For now return 0 as specific logic depends on aggregator requirements
        return 0

    # ═══════════════════════════════════════════════════════════
    # Email Operations
    # ═══════════════════════════════════════════════════════════

    async def send_email(self, data: SendEmailRequest) -> SendEmailResponse:
        """Send email using Brevo."""
        # Check API Key first
        if not settings.brevo_api_key:
            error_msg = "Brevo API Key is not configured. Please check your settings."
            
            await self._audit_logger.log_action(
                action="EMAIL_FAILED",
                resource_type="EMAIL",
                status="FAILURE",
                error_message=error_msg,
                description=f"Failed to send email to {data.to_email}: Missing API Key",
                request_data={"to": data.to_email, "template": data.template_code}
            )
            
            return SendEmailResponse(
                success=False,
                error=error_msg,
            )

        # Get template
        template = await self._template_repo.get_by_code(data.template_code)
        if not template:
            error_msg = f"Template not found: {data.template_code}"
            
            await self._audit_logger.log_action(
                action="EMAIL_FAILED",
                resource_type="EMAIL",
                status="FAILURE",
                error_message=error_msg,
                description=f"Failed to send email to {data.to_email}: Template not found",
            )
            
            return SendEmailResponse(
                success=False,
                error=error_msg,
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

            # Audit log success
            await self._audit_logger.log_action(
                action="EMAIL_SENT",
                resource_type="EMAIL",
                resource_id=result.get("messageId"),
                status="SUCCESS",
                description=f"Sent {data.template_code} email to {data.to_email}",
                request_data={
                    "to": data.to_email, 
                    "template": data.template_code,
                    "variables": data.variables
                }
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
            
            # Audit log failure
            await self._audit_logger.log_action(
                action="EMAIL_FAILED",
                resource_type="EMAIL",
                status="FAILURE",
                error_message=str(e),
                description=f"Failed to send email to {data.to_email}",
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

    async def _send_push_notification(self, notification) -> None:
        """Send web push notification using pywebpush."""
        from pywebpush import webpush, WebPushException
        from src.services.notifications.repository import PushSubscriptionRepository
        
        # Check if VAPID keys are configured
        if not settings.vapid_private_key or not settings.vapid_public_key:
            print(f"[PUSH] VAPID keys not configured, skipping push for {notification.user_id}")
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow(),
            )
            return
        
        # Get user's push subscriptions
        push_repo = PushSubscriptionRepository(self._session)
        subscriptions = await push_repo.get_by_user(notification.user_id)
        
        if not subscriptions:
            print(f"[PUSH] No subscriptions for user {notification.user_id}")
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow(),
            )
            return
        
        # Prepare push payload
        import json
        push_data = json.dumps({
            "title": notification.title,
            "body": notification.message,
            "icon": "/icons/notification-icon.png",
            "badge": "/icons/badge-icon.png",
            "tag": str(notification.id),
            "data": {
                "url": notification.action_url or "/notifications",
                "notification_id": str(notification.id),
            }
        })
        
        vapid_claims = {
            "sub": settings.vapid_subject,
        }
        
        failed_endpoints = []
        success_count = 0
        
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth,
                        }
                    },
                    data=push_data,
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims=vapid_claims,
                )
                success_count += 1
            except WebPushException as e:
                print(f"[PUSH] Failed to send to {subscription.endpoint}: {e}")
                # If subscription is invalid (410 Gone), mark for deletion
                if e.response and e.response.status_code == 410:
                    failed_endpoints.append(subscription.endpoint)
            except Exception as e:
                print(f"[PUSH] Unexpected error sending push: {e}")
        
        # Deactivate failed subscriptions
        for endpoint in failed_endpoints:
            await push_repo.delete_by_endpoint(endpoint)
        
        print(f"[PUSH] Sent to {success_count}/{len(subscriptions)} devices for user {notification.user_id}")
        
        await self._notification_repo.update(
            notification.id,
            status=NotificationStatus.SENT,
            sent_at=datetime.utcnow(),
        )

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
        """Check if user wants this notification based on granular matrix."""
        # 1. Check global channel switches
        if channel == NotificationChannel.EMAIL and not prefs.email_enabled:
            return False
        if channel == NotificationChannel.IN_APP and not prefs.in_app_enabled:
            return False
        if channel == NotificationChannel.PUSH and not prefs.push_enabled:
            return False
            
        # 2. Check matrix preference
        # preferences_matrix: {notification_type: {channel: bool}}
        matrix = prefs.preferences_matrix or {}
        type_prefs = matrix.get(notification_type.value, {})
        
        # If specific preference exists, return it
        if channel.value in type_prefs:
            return type_prefs[channel.value]
            
        # 3. Default fallback logic if not in matrix
        # For enterprise, we usually want in-app notifications enabled by default
        if channel == NotificationChannel.IN_APP:
            return True
            
        # Email defaults
        if channel == NotificationChannel.EMAIL:
            # Critical alerts or leave updates usually default to True
            if notification_type.value.startswith(("leave_", "compliance_", "system_")):
                return True
            return False
            
        return False

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
