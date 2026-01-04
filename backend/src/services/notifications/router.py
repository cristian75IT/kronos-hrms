"""KRONOS Notification Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import NotFoundError
from src.shared.schemas import MessageResponse, DataTableRequest, DataTableResponse
from src.services.notifications.service import NotificationService
from src.services.auth.service import UserService
from src.services.notifications.schemas import (
    NotificationResponse,
    NotificationListItem,
    NotificationCreate,
    MarkReadRequest,
    UnreadCountResponse,
    EmailTemplateResponse,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    SendEmailRequest,
    SendEmailResponse,
    BulkNotificationRequest,
    BulkNotificationResponse,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    EmailLogResponse,
    EmailProviderSettingsResponse,
    EmailProviderSettingsCreate,
    EmailProviderSettingsUpdate,
    TestEmailRequest,
)
from src.services.notifications.repository import (
    PushSubscriptionRepository,
    EmailLogRepository,
    EmailProviderSettingsRepository,
)


class NotificationDataTableRequest(DataTableRequest):
    """DataTable request including channel filter."""
    channel: Optional[str] = None


router = APIRouter()


async def get_notification_service(
    session: AsyncSession = Depends(get_db),
) -> NotificationService:
    """Dependency for NotificationService."""
    return NotificationService(session)


async def get_user_service(
    session: AsyncSession = Depends(get_db),
) -> UserService:
    """Dependency for UserService."""
    return UserService(session)


# ═══════════════════════════════════════════════════════════
# Notification Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/notifications", response_model=list[NotificationListItem])
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    channel: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notifications."""
    notifications = await service.get_user_notifications(current_user.user_id, unread_only, limit, channel)
    return [NotificationListItem.model_validate(n) for n in notifications]


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get unread notification count."""
    count = await service.count_unread(current_user.user_id)
    return UnreadCountResponse(count=count)


@router.get("/notifications/history", response_model=list[NotificationResponse])
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[UUID] = None,
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    current_user: TokenPayload = Depends(require_permission("notifications:view")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get history of sent notifications. Admin only."""
    return await service.get_sent_history(
        limit=limit,
        offset=offset,
        user_id=user_id,
        notification_type=notification_type,
        status=status,
        channel=channel,
    )


@router.post("/notifications/history/datatable", response_model=DataTableResponse[NotificationResponse])
async def get_notification_history_datatable(
    data: NotificationDataTableRequest,
    current_user: TokenPayload = Depends(require_permission("notifications:view")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get history of sent notifications for DataTables."""
    # 1. Total records (unfiltered)
    total_records = await service.count_history()
    
    # 2. Filtered records (basic search + channel)
    filtered_records = await service.count_history(
        channel=data.channel
        # TODO: Add global search support if needed (data.search.value)
    )
    
    # 3. Get page data
    items = await service.get_sent_history(
        limit=data.length,
        offset=data.start,
        channel=data.channel
        # TODO: Map data.order to sort field if needed
    )
    
    return DataTableResponse(
        draw=data.draw,
        recordsTotal=total_records,
        recordsFiltered=filtered_records,
        data=[NotificationResponse.model_validate(item) for item in items],
    )


# ═══════════════════════════════════════════════════════════
# Preferences Endpoints (MUST be before /notifications/{id})
# ═══════════════════════════════════════════════════════════

@router.get("/notifications/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notification preferences."""
    return await service.get_preferences(current_user.user_id)


@router.put("/notifications/preferences", response_model=UserPreferencesResponse)
async def update_my_preferences(
    data: UserPreferencesUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Update current user's notification preferences."""
    return await service.update_preferences(current_user.user_id, data)


# ═══════════════════════════════════════════════════════════
# Email Log Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/notifications/email-logs", response_model=list[EmailLogResponse])
async def get_email_logs(
    status: Optional[str] = None,
    template_code: Optional[str] = None,
    to_email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get email logs history. Admin only."""
    repo = EmailLogRepository(session)
    if not (current_user.is_admin or current_user.is_hr):
        raise HTTPException(status_code=403, detail="Admin or HR role required")
    return await repo.get_history(
        limit=limit,
        offset=offset,
        status=status,
        template_code=template_code,
        to_email=to_email,
    )


@router.get("/notifications/email-logs/stats", response_model=dict)
async def get_email_stats(
    days: int = 7,
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get email delivery statistics. Admin only."""
    repo = EmailLogRepository(session)
    if not (current_user.is_admin or current_user.is_hr):
        raise HTTPException(status_code=403, detail="Admin or HR role required")
    return await repo.get_stats(days=days)


@router.post("/notifications/email-logs/{id}/retry", response_model=EmailLogResponse)
async def retry_email(
    id: UUID,
    current_user: TokenPayload = Depends(require_permission("notifications:manage")),
    service: NotificationService = Depends(get_notification_service),
):
    """Manually retry a failed email. Admin only."""
    return await service.retry_email(id)


@router.get("/notifications/email-logs/{id}/events", response_model=list[dict])
async def get_email_events(
    id: UUID,
    permissive: bool = False,
    current_user: TokenPayload = Depends(require_permission("notifications:view")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get Brevo events for a specific email log. Admin only."""
    try:
        return await service.get_email_events(id, permissive=permissive)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(
    data: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
):
    """Create notification. Called by other services."""
    notification = await service.create_notification(data)
    if not notification:
        raise HTTPException(status_code=400, detail="Notification not created (user preferences)")
    return notification


@router.post("/notifications/mark-read", response_model=MessageResponse)
async def mark_read(
    data: MarkReadRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark notifications as read."""
    count = await service.mark_read(data.notification_ids, current_user.user_id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.post("/notifications/mark-all-read", response_model=MessageResponse)
async def mark_all_read(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    count = await service.mark_all_read(current_user.user_id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.post("/notifications/bulk", response_model=BulkNotificationResponse)
async def send_bulk(
    data: BulkNotificationRequest,
    current_user: TokenPayload = Depends(require_permission("notifications:send")),
    service: NotificationService = Depends(get_notification_service),
):
    """Send bulk notifications. Admin only."""
    return await service.send_bulk(data)


# ═══════════════════════════════════════════════════════════
# Email Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/notifications/send-email", response_model=SendEmailResponse)
async def send_email(
    data: SendEmailRequest,
    service: NotificationService = Depends(get_notification_service),
):
    """Send email directly. Called by other services."""
    return await service.send_email(data)


# ═══════════════════════════════════════════════════════════
# Template Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/notifications/templates", response_model=list[EmailTemplateResponse])
async def get_templates(
    active_only: bool = True,
    current_user: TokenPayload = Depends(require_permission("notifications:templates")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get all email templates. Admin only."""
    return await service.get_templates(active_only)


@router.get("/notifications/templates/{id}", response_model=EmailTemplateResponse)
async def get_template(
    id: UUID,
    current_user: TokenPayload = Depends(require_permission("notifications:templates")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get template by ID. Admin only."""
    try:
        return await service.get_template(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/notifications/templates", response_model=EmailTemplateResponse, status_code=201)
async def create_template(
    data: EmailTemplateCreate,
    current_user: TokenPayload = Depends(require_permission("notifications:templates")),
    service: NotificationService = Depends(get_notification_service),
):
    """Create email template. Admin only."""
    return await service.create_template(data)


@router.put("/notifications/templates/{id}", response_model=EmailTemplateResponse)
async def update_template(
    id: UUID,
    data: EmailTemplateUpdate,
    current_user: TokenPayload = Depends(require_permission("notifications:templates")),
    service: NotificationService = Depends(get_notification_service),
):
    """Update email template. Admin only."""
    try:
        return await service.update_template(id, data, user_id=current_user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/notifications/templates/{id}/sync", response_model=dict)
async def sync_template_to_brevo(
    id: UUID,
    current_user: TokenPayload = Depends(require_permission("notifications:templates")),
    service: NotificationService = Depends(get_notification_service),
):
    """Sync template to Brevo. Admin only."""
    try:
        return await service.sync_template_to_brevo(id, user_id=current_user.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Push Subscription Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/notifications/push-subscriptions", response_model=PushSubscriptionResponse, status_code=201)
async def subscribe_to_push(
    data: PushSubscriptionCreate,
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Subscribe to Web Push notifications."""
    repo = PushSubscriptionRepository(session)
    subscription = await repo.create(
        user_id=current_user.user_id,
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth,
        device_info=data.device_info,
    )
    return subscription


@router.get("/notifications/push-subscriptions", response_model=list[PushSubscriptionResponse])
async def get_my_push_subscriptions(
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's push subscriptions."""
    repo = PushSubscriptionRepository(session)
    return await repo.get_by_user(current_user.user_id)


@router.delete("/notifications/push-subscriptions/{id}", response_model=MessageResponse)
async def unsubscribe_from_push(
    id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Unsubscribe from Web Push notifications."""
    repo = PushSubscriptionRepository(session)
    success = await repo.deactivate(id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return MessageResponse(message="Unsubscribed from push notifications")


# ═══════════════════════════════════════════════════════════
# Email Provider Settings Endpoints (Admin Only)
# ═══════════════════════════════════════════════════════════

@router.get("/notifications/settings", response_model=EmailProviderSettingsResponse)
async def get_email_provider_settings(
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    session: AsyncSession = Depends(get_db),
):
    """Get active email provider settings. Admin only."""
    repo = EmailProviderSettingsRepository(session)
    settings = await repo.get_by_provider("brevo")
    if not settings:
        raise HTTPException(status_code=404, detail="Email provider not configured")
    
    # Mask API key for security
    api_key_masked = f"...{settings.api_key[-4:]}" if settings.api_key else ""
    
    return EmailProviderSettingsResponse(
        id=settings.id,
        provider=settings.provider,
        api_key_masked=api_key_masked,
        sender_email=settings.sender_email,
        sender_name=settings.sender_name,
        reply_to_email=settings.reply_to_email,
        reply_to_name=settings.reply_to_name,
        is_active=settings.is_active,
        test_mode=settings.test_mode,
        test_email=settings.test_email,
        daily_limit=settings.daily_limit,
        emails_sent_today=settings.emails_sent_today or 0,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.post("/notifications/settings", response_model=EmailProviderSettingsResponse, status_code=201)
async def create_email_provider_settings(
    data: EmailProviderSettingsCreate,
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    session: AsyncSession = Depends(get_db),
):
    """Create email provider settings. Admin only."""
    repo = EmailProviderSettingsRepository(session)
    
    # Check if settings already exist
    existing = await repo.get_active(data.provider)
    if existing:
        raise HTTPException(status_code=400, detail="Settings for this provider already exist. Use PUT to update.")
    
    settings = await repo.create(**data.model_dump())
    await session.commit()
    
    api_key_masked = f"...{settings.api_key[-4:]}" if settings.api_key else ""
    
    return EmailProviderSettingsResponse(
        id=settings.id,
        provider=settings.provider,
        api_key_masked=api_key_masked,
        sender_email=settings.sender_email,
        sender_name=settings.sender_name,
        reply_to_email=settings.reply_to_email,
        reply_to_name=settings.reply_to_name,
        is_active=settings.is_active,
        test_mode=settings.test_mode,
        test_email=settings.test_email,
        daily_limit=settings.daily_limit,
        emails_sent_today=settings.emails_sent_today or 0,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("/notifications/settings/{id}", response_model=EmailProviderSettingsResponse)
async def update_email_provider_settings(
    id: UUID,
    data: EmailProviderSettingsUpdate,
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    session: AsyncSession = Depends(get_db),
):
    """Update email provider settings. Admin only."""
    repo = EmailProviderSettingsRepository(session)
    settings = await repo.update(id, **data.model_dump(exclude_unset=True))
    
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    await session.commit()
    
    api_key_masked = f"...{settings.api_key[-4:]}" if settings.api_key else ""
    
    return EmailProviderSettingsResponse(
        id=settings.id,
        provider=settings.provider,
        api_key_masked=api_key_masked,
        sender_email=settings.sender_email,
        sender_name=settings.sender_name,
        reply_to_email=settings.reply_to_email,
        reply_to_name=settings.reply_to_name,
        is_active=settings.is_active,
        test_mode=settings.test_mode,
        test_email=settings.test_email,
        daily_limit=settings.daily_limit,
        emails_sent_today=settings.emails_sent_today or 0,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.post("/notifications/settings/test", response_model=SendEmailResponse)
async def test_email_settings(
    data: TestEmailRequest,
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    session: AsyncSession = Depends(get_db),
    service: NotificationService = Depends(get_notification_service),
):
    """Send a test email to verify settings. Admin only."""
    # Use the generic_notification template or create inline
    result = await service.send_email(SendEmailRequest(
        to_email=data.to_email,
        template_code="generic_notification",
        variables={
            "title": "Test Email from KRONOS",
            "message": "This is a test email to verify your email provider configuration.",
        }
    ))
    return result


# ═══════════════════════════════════════════════════════════
# Generic Notification Endpoint (Must be last to avoid conflicts)
# ═══════════════════════════════════════════════════════════

@router.get("/notifications/{id}", response_model=NotificationResponse)
async def get_notification(
    id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification by ID."""
    try:
        return await service.get_notification(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
