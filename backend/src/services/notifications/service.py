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
    EmailLogRepository,
    EmailProviderSettingsRepository,
)
from src.services.notifications.models import EmailLogStatus
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
        self._email_log_repo = EmailLogRepository(session)
        self._settings_repo = EmailProviderSettingsRepository(session)
        self._audit_logger = get_audit_logger("notification-service")
        self._cached_settings = None  # Cache loaded settings

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
        count = await self._notification_repo.mark_read(notification_ids, user_id)
        
        await self._audit_logger.log_action(
            user_id=user_id,
            action="NOTIFICATIONS_MARK_READ",
            resource_type="NOTIFICATION",
            description=f"Marked {count} notifications as read",
            request_data={"count": count}
        )
        return count

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read."""
        count = await self._notification_repo.mark_all_read(user_id)
        
        await self._audit_logger.log_action(
            user_id=user_id,
            action="NOTIFICATIONS_MARK_ALL_READ",
            resource_type="NOTIFICATION",
            description="Marked all notifications as read"
        )
        return count

    async def send_bulk(self, data: BulkNotificationRequest) -> BulkNotificationResponse:
        """Send bulk notifications."""
        total = len(data.user_ids)
        sent = 0
        failed = 0
        errors = []
        
        if not data.user_ids:
            return BulkNotificationResponse(
                total=0,
                sent=0,
                failed=0,
                errors=["No recipients selected"]
            )
        
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
        """Send email using Brevo with enterprise-grade logging and tracking."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Get template first
        template = await self._template_repo.get_by_code(data.template_code)
        if not template:
            error_msg = f"Template not found: {data.template_code}"
            logger.error(f"Email sending failed: {error_msg}")
            
            # Create a failed log explicitly since we can't proceed
            email_log = await self._email_log_repo.create(
                to_email=data.to_email,
                to_name=data.to_name,
                template_code=data.template_code, # Use the requested code
                variables=data.variables,
                notification_id=data.notification_id,
            )
            
            await self._email_log_repo.update_status(
                email_log.id,
                status=EmailLogStatus.FAILED.value,
                error_message=error_msg,
            )
            await self._session.commit()
            
            await self._audit_logger.log_action(
                action="EMAIL_FAILED",
                resource_type="EMAIL",
                resource_id=str(email_log.id),
                status="FAILURE",
                error_message=error_msg,
                description=f"Failed to send email to {data.to_email}: Template not found",
            )
            
            return SendEmailResponse(
                success=False,
                error=error_msg,
            )
        
        try:
            # Delegate to shared method
            result = await self._send_email_with_log(
                to_email=data.to_email,
                template=template,
                variables=data.variables,
                to_name=data.to_name,
                notification_id=data.notification_id,
            )
            
            if not result.get("success"):
                return SendEmailResponse(success=False, error=result.get("error"))
                
            return SendEmailResponse(
                success=True,
                message_id=result.get("message_id"),
            )
            
        except Exception as e:
            return SendEmailResponse(success=False, error=str(e))

    async def retry_email(self, log_id: UUID) -> None:
        """Manually retry sending a specific email log."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Get log
        log = await self._email_log_repo.get(log_id)
        if not log:
            raise NotFoundError("Email log not found")
            
        # Get template
        template = await self._template_repo.get_by_code(log.template_code)
        if not template:
            error_msg = f"Template {log.template_code} not found"
            await self._email_log_repo.update_status(
                log.id, 
                status=EmailLogStatus.FAILED.value, 
                error_message=error_msg
            )
            await self._session.commit()
            raise ValueError(error_msg)

        try:
            # Update to processing
            log.status = EmailLogStatus.QUEUED.value
            await self._session.flush()
            
            logger.info(f"Retrying email {log_id} to {log.to_email}")
            
            # Send (using updated internal method to allow dev mode success)
            # We can use _send_email_with_log but we already have the log object.
            # Using _send_brevo_email directly as before is fine for RETRY logic 
            # since we are manipulating an existing log.
            
            result = await self._send_brevo_email(
                to_email=log.to_email,
                to_name=log.to_name,
                template=template,
                variables=log.variables or {},
            )
            
            # Update success
            await self._email_log_repo.update_status(
                log.id,
                status=EmailLogStatus.SENT.value,
                message_id=result.get("messageId"),
                provider_response=result,
            )
            
            # Audit log
            await self._audit_logger.log_action(
                action="EMAIL_SENT",
                resource_type="EMAIL",
                resource_id=str(log.id),
                status="SUCCESS",
                description=f"Retried sending {log.template_code} to {log.to_email}",
            )
            
            return log
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Retry failed for {log_id}: {error_msg}")
            
            await self._email_log_repo.update_status(
                log.id,
                status=EmailLogStatus.FAILED.value,
                error_message=error_msg,
            )
            await self._session.commit()
            raise e

    async def get_email_events(self, log_id: UUID) -> list[dict]:
        """Fetch email events from Brevo for a specific email log."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Get log
        log = await self._email_log_repo.get(log_id)
        if not log:
            raise NotFoundError("Email log not found")
        
        # Get provider settings for API key
        provider_settings = await self._settings_repo.get_active("brevo")
        if not provider_settings or not provider_settings.api_key:
            raise ValueError("Brevo API key not configured")
        
        headers = {
            "api-key": provider_settings.api_key,
            "Content-Type": "application/json",
        }
        
        # Build query params - filter by email address
        params = {
            "email": log.to_email,
            "limit": 50,
            "sort": "desc",
        }
        
        # If we have a message_id, we can filter by that too
        if log.message_id:
            params["messageId"] = log.message_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.brevo.com/v3/smtp/statistics/events",
                headers=headers,
                params=params,
                timeout=30.0,
            )
            
            if response.status_code >= 400:
                error_body = response.text
                logger.error(f"Brevo API error {response.status_code}: {error_body}")
                raise ValueError(f"Errore API Brevo: {error_body}")
            
            data = response.json()
            events = data.get("events", [])
            
            # Transform events for frontend display
            result = []
            for event in events:
                result.append({
                    "event": event.get("event"),
                    "email": event.get("email"),
                    "date": event.get("date"),
                    "messageId": event.get("messageId"),
                    "subject": event.get("subject"),
                    "tag": event.get("tag"),
                    "from": event.get("from"),
                    "templateId": event.get("templateId"),
                })
            
            return result

    async def _send_email_notification(self, notification) -> None:
        """Send email for a notification."""
        # 1. Get template for notification type
        template = await self._template_repo.get_by_notification_type(
            notification.notification_type
        )
        
        # 2. Fallback to generic template
        if not template:
            template = await self._template_repo.get_by_code("generic_notification")
        
        if not template:
            import logging
            logger = logging.getLogger(__name__)
            error_msg = f"No email template found for type: {notification.notification_type}"
            logger.error(error_msg)
            
            # Update Notification status
            await self._notification_repo.update(
                notification.id,
                status=NotificationStatus.FAILED,
                error_message=error_msg,
            )
            
            # Create FAILED EmailLog so it appears in Admin UI
            log = await self._email_log_repo.create(
                to_email=notification.user_email,
                template_code=f"MISSING:{notification.notification_type}",
                notification_id=notification.id,
                user_id=notification.user_id,
            )
            
            await self._email_log_repo.update_status(
                log.id,
                status=EmailLogStatus.FAILED.value,
                error_message=error_msg
            )
            await self._session.commit()
            return
        
        # Build variables
        variables = {
            "title": notification.title,
            "message": notification.message,
            "action_url": notification.action_url or "",
            **(notification.payload or {}),
        }
        
        try:
            # Delegate to shared method to ensure logging
            await self._send_email_with_log(
                to_email=notification.user_email,
                template=template,
                variables=variables,
                notification_id=notification.id,
                user_id=notification.user_id
            )
            
        except Exception as e:
            # Exception handling is mostly done inside _send_email_with_log 
            # (which updates notification status), but it re-raises.
            # We catch here to ensure process doesn't crash if used in loop.
            pass

    async def _send_email_with_log(
        self,
        to_email: str,
        template,
        variables: dict,
        to_name: Optional[str] = None,
        notification_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> dict:
        """Shared method to send email with full logging."""
        import logging
        logger = logging.getLogger(__name__)

        # 1. Create Log
        email_log = await self._email_log_repo.create(
            to_email=to_email,
            to_name=to_name,
            template_code=template.code,
            variables=variables,
            notification_id=notification_id,
            user_id=user_id,
            subject=template.subject # Pre-fill if available
        )
        await self._session.commit()

        # 2. Check API Key
        # Check DB settings first (cached if available)
        if not self._cached_settings:
            self._cached_settings = await self._settings_repo.get_active("brevo")
        
        provider_settings = self._cached_settings

        if not provider_settings or not provider_settings.api_key:
            error_msg = "Brevo API Key is not configured. Emails cannot be sent."
            logger.error(f"Email sending failed: {error_msg}")
            
            await self._email_log_repo.update_status(
                email_log.id,
                status=EmailLogStatus.FAILED.value,
                error_message=error_msg,
            )
            
            if notification_id:
                 await self._notification_repo.update(
                    notification_id,
                    status=NotificationStatus.FAILED,
                    error_message=error_msg,
                )
            
            await self._session.commit()
            
            await self._audit_logger.log_action(
                action="EMAIL_FAILED",
                resource_type="EMAIL",
                resource_id=str(email_log.id),
                status="FAILURE",
                error_message=error_msg,
                description=f"Failed to send email to {to_email}: Missing API Key",
                request_data={"to": to_email, "template": template.code}
            )
            return {"error": error_msg, "success": False}

        try:
             # 3. Send
             logger.info(f"Sending email to {to_email} using template {template.code}")
             result = await self._send_brevo_email(
                to_email=to_email,
                to_name=to_name,
                template=template,
                variables=variables
             )
             message_id = result.get("messageId")

             # 4. Success
             await self._email_log_repo.update_status(
                email_log.id,
                status=EmailLogStatus.SENT.value,
                message_id=message_id,
                provider_response=result,
             )
             
             if notification_id:
                await self._notification_repo.update(
                    notification_id,
                    status=NotificationStatus.SENT,
                    sent_at=datetime.utcnow(),
                )

             await self._session.commit()

             await self._audit_logger.log_action(
                action="EMAIL_SENT",
                resource_type="EMAIL",
                resource_id=str(email_log.id),
                status="SUCCESS",
                description=f"Sent {template.code} email to {to_email}",
                request_data={
                    "to": to_email, 
                    "template": template.code,
                    "message_id": message_id
                }
             )
             
             return {"success": True, "message_id": message_id, "provider_response": result}

        except Exception as e:
            # 5. Failure
            error_msg = str(e)
            logger.error(f"Email sending failed to {to_email}: {error_msg}")

            await self._email_log_repo.update_status(
                email_log.id,
                status=EmailLogStatus.FAILED.value,
                error_message=error_msg,
            )
             
            # Schedule retry
            if email_log.retry_count < 3:
                await self._email_log_repo.schedule_retry(email_log.id)
            
            if notification_id:
                 notification = await self._notification_repo.get(notification_id)
                 await self._notification_repo.update(
                    notification_id,
                    status=NotificationStatus.FAILED,
                    error_message=error_msg,
                    retry_count=(notification.retry_count or 0) + 1,
                )
            
            await self._session.commit()

            await self._audit_logger.log_action(
                action="EMAIL_FAILED",
                resource_type="EMAIL",
                resource_id=str(email_log.id),
                status="FAILURE",
                error_message=error_msg,
                description=f"Failed to send email to {to_email}",
            )
            raise e

    async def _send_brevo_email(
        self,
        to_email: str,
        template,
        variables: dict,
        to_name: Optional[str] = None,
    ) -> dict:
        """Send email via Brevo API using database-stored credentials."""
        
        # Fetch settings from database (with caching)
        if not self._cached_settings:
            self._cached_settings = await self._settings_repo.get_active("brevo")
        
        provider_settings = self._cached_settings
        
        if not provider_settings:
            raise ValueError("Email provider not configured. Configure Brevo settings in Admin.")
        
        if not provider_settings.api_key:
            raise ValueError("Brevo API key not configured.")
        
        # Check rate limiting
        if provider_settings.daily_limit:
            can_send = await self._settings_repo.can_send_email(provider_settings.id)
            if not can_send:
                raise ValueError(f"Daily email limit ({provider_settings.daily_limit}) reached.")
        
        # Apply test mode: redirect all emails to test address
        actual_to_email = to_email
        if provider_settings.test_mode and provider_settings.test_email:
            actual_to_email = provider_settings.test_email
        
        headers = {
            "api-key": provider_settings.api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "to": [{"email": actual_to_email, "name": to_name or actual_to_email}],
            "sender": {
                "email": provider_settings.sender_email,
                "name": provider_settings.sender_name,
            },
            "params": variables,
        }
        
        # Add reply-to if configured
        if provider_settings.reply_to_email:
            payload["replyTo"] = {
                "email": provider_settings.reply_to_email,
                "name": provider_settings.reply_to_name or provider_settings.reply_to_email,
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
            
            # Increment email counter
            await self._settings_repo.increment_emails_sent(provider_settings.id)
            
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

    def _convert_to_brevo_syntax(self, content: str) -> str:
        """Convert Handlebars-style syntax to Brevo (Jinja2) syntax.
        
        Brevo uses Jinja2-like templating:
        - Variables: {{ variable }}
        - Conditionals: {% if condition %}...{% endif %}
        
        Our templates use Handlebars-like syntax:
        - Variables: {{variable}}
        - Conditionals: {{#if variable}}...{{/if}}
        """
        import re
        
        result = content
        
        # Convert {{#if variable}} to {% if params.variable %}
        result = re.sub(
            r'\{\{#if\s+(\w+)\}\}',
            r'{% if params.\1 %}',
            result
        )
        
        # Convert {{/if}} to {% endif %}
        result = result.replace('{{/if}}', '{% endif %}')
        
        # Convert {{variable}} to {{ params.variable }}
        # But skip variables that are already in params format
        result = re.sub(
            r'\{\{(\w+)\}\}',
            r'{{ params.\1 }}',
            result
        )
        
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

    async def update_template(self, id: UUID, data: EmailTemplateUpdate, user_id: Optional[UUID] = None):
        """Update email template."""
        template = await self._template_repo.update(
            id,
            **data.model_dump(exclude_unset=True),
        )
        if not template:
            raise NotFoundError("Template not found")

        await self._audit_logger.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="EMAIL_TEMPLATE",
            resource_id=str(id),
            description=f"Updated email template: {template.name}",
            request_data=data.model_dump(mode="json")
        )
        return template

    async def sync_template_to_brevo(self, id: UUID, user_id: Optional[UUID] = None) -> dict:
        """Sync a local template to Brevo.
        
        Creates or updates the template in Brevo and stores the brevo_template_id.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        template = await self._template_repo.get(id)
        if not template:
            raise NotFoundError("Template not found")
        
        # Get provider settings
        provider_settings = await self._settings_repo.get_active("brevo")
        if not provider_settings or not provider_settings.api_key:
            raise ValueError("Brevo API key not configured")
        
        headers = {
            "api-key": provider_settings.api_key,
            "Content-Type": "application/json",
        }
        
        # Convert HTML content from Handlebars to Brevo (Jinja2) syntax
        html_content = self._convert_to_brevo_syntax(template.html_content or "<p>{{message}}</p>")
        
        # Prepare template payload for Brevo
        brevo_payload = {
            "sender": {
                "email": provider_settings.sender_email,
                "name": provider_settings.sender_name,
            },
            "templateName": template.code,
            "subject": template.subject or "{{title}}",
            "htmlContent": html_content,
        }
        
        if provider_settings.reply_to_email:
            brevo_payload["replyTo"] = provider_settings.reply_to_email
        
        async with httpx.AsyncClient() as client:
            if template.brevo_template_id:
                # Update existing template
                logger.info(f"Updating Brevo template {template.brevo_template_id}")
                response = await client.put(
                    f"https://api.brevo.com/v3/smtp/templates/{template.brevo_template_id}",
                    headers=headers,
                    json=brevo_payload,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = {"updated": True, "brevo_template_id": template.brevo_template_id}
            else:
                # Create new template
                logger.info(f"Creating new Brevo template for {template.code}")
                response = await client.post(
                    "https://api.brevo.com/v3/smtp/templates",
                    headers=headers,
                    json=brevo_payload,
                    timeout=30.0,
                )
                if response.status_code >= 400:
                    error_body = response.text
                    logger.error(f"Brevo API error {response.status_code}: {error_body}")
                    # Provide user-friendly messages for common errors
                    if "Sender is invalid" in error_body:
                        raise ValueError(
                            f"Il mittente '{provider_settings.sender_email}' non è verificato in Brevo. "
                            "Accedi al tuo account Brevo e verifica l'indirizzo email del mittente."
                        )
                    raise ValueError(f"Errore API Brevo: {error_body}")
                data = response.json()
                brevo_id = data.get("id")
                
                # Store the brevo_template_id
                await self._template_repo.update(id, brevo_template_id=brevo_id)
                await self._session.commit()
                
                result = {"created": True, "brevo_template_id": brevo_id}
        
        await self._audit_logger.log_action(
            user_id=user_id,
            action="SYNC_TO_BREVO",
            resource_type="EMAIL_TEMPLATE",
            resource_id=str(id),
            description=f"Synced template {template.code} to Brevo",
            request_data=result
        )
        
        return result

    # ═══════════════════════════════════════════════════════════
    # Preferences Operations
    # ═══════════════════════════════════════════════════════════

    async def get_preferences(self, user_id: UUID):
        """Get user preferences."""
        return await self._preference_repo.get_or_create(user_id)

    async def update_preferences(self, user_id: UUID, data: UserPreferencesUpdate):
        """Update user preferences."""
        prefs = await self._preference_repo.update(
            user_id,
            **data.model_dump(exclude_unset=True),
        )
        
        await self._audit_logger.log_action(
            user_id=user_id,
            action="UPDATE_PREFERENCES",
            resource_type="USER_PREFERENCES",
            description="Updated notification preferences"
        )
        return prefs

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
