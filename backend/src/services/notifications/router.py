"""KRONOS Notification Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, require_admin, TokenPayload
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
)
from src.services.notifications.repository import (
    PushSubscriptionRepository,
    EmailLogRepository,
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
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notifications."""
    notifications = await service.get_user_notifications(token.user_id, unread_only, limit, channel)
    return [NotificationListItem.model_validate(n) for n in notifications]


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get unread notification count."""
    count = await service.count_unread(token.user_id)
    return UnreadCountResponse(count=count)


@router.get("/notifications/history", response_model=list[NotificationResponse])
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[UUID] = None,
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    token: TokenPayload = Depends(require_admin),
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
    token: TokenPayload = Depends(require_admin),
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
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notification preferences."""
    return await service.get_preferences(token.user_id)


@router.put("/notifications/preferences", response_model=UserPreferencesResponse)
async def update_my_preferences(
    data: UserPreferencesUpdate,
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Update current user's notification preferences."""
    return await service.update_preferences(token.user_id, data)


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
    token: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get email logs history. Admin only."""
    repo = EmailLogRepository(session)
    if not (token.is_admin or token.is_hr):
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
    token: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get email delivery statistics. Admin only."""
    repo = EmailLogRepository(session)
    if not (token.is_admin or token.is_hr):
        raise HTTPException(status_code=403, detail="Admin or HR role required")
    return await repo.get_stats(days=days)


@router.post("/notifications/email-logs/{id}/retry", response_model=EmailLogResponse)
async def retry_email(
    id: UUID,
    token: TokenPayload = Depends(require_admin),
    service: NotificationService = Depends(get_notification_service),
):
    """Manually retry a failed email. Admin only."""
    return await service.retry_email(id)


@router.get("/notifications/{id}", response_model=NotificationResponse)
async def get_notification(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification by ID."""
    try:
        return await service.get_notification(id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


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
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark notifications as read."""
    count = await service.mark_read(data.notification_ids, token.user_id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.post("/notifications/mark-all-read", response_model=MessageResponse)
async def mark_all_read(
    token: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    count = await service.mark_all_read(token.user_id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.post("/notifications/bulk", response_model=BulkNotificationResponse)
async def send_bulk(
    data: BulkNotificationRequest,
    token: TokenPayload = Depends(require_admin),
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
    token: TokenPayload = Depends(require_admin),
    service: NotificationService = Depends(get_notification_service),
):
    """Get all email templates. Admin only."""
    return await service.get_templates(active_only)


@router.get("/notifications/templates/{id}", response_model=EmailTemplateResponse)
async def get_template(
    id: UUID,
    token: TokenPayload = Depends(require_admin),
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
    token: TokenPayload = Depends(require_admin),
    service: NotificationService = Depends(get_notification_service),
):
    """Create email template. Admin only."""
    return await service.create_template(data)


@router.put("/notifications/templates/{id}", response_model=EmailTemplateResponse)
async def update_template(
    id: UUID,
    data: EmailTemplateUpdate,
    token: TokenPayload = Depends(require_admin),
    service: NotificationService = Depends(get_notification_service),
):
    """Update email template. Admin only."""
    try:
        return await service.update_template(id, data, user_id=token.user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Push Subscription Endpoints
# ═══════════════════════════════════════════════════════════

@router.post("/notifications/push-subscriptions", response_model=PushSubscriptionResponse, status_code=201)
async def subscribe_to_push(
    data: PushSubscriptionCreate,
    token: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Subscribe to Web Push notifications."""
    repo = PushSubscriptionRepository(session)
    subscription = await repo.create(
        user_id=token.user_id,
        endpoint=data.endpoint,
        p256dh=data.p256dh,
        auth=data.auth,
        device_info=data.device_info,
    )
    return subscription


@router.get("/notifications/push-subscriptions", response_model=list[PushSubscriptionResponse])
async def get_my_push_subscriptions(
    token: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's push subscriptions."""
    repo = PushSubscriptionRepository(session)
    return await repo.get_by_user(token.user_id)


@router.delete("/notifications/push-subscriptions/{id}", response_model=MessageResponse)
async def unsubscribe_from_push(
    id: UUID,
    token: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Unsubscribe from Web Push notifications."""
    repo = PushSubscriptionRepository(session)
    success = await repo.deactivate(id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return MessageResponse(message="Unsubscribed from push notifications")



