"""KRONOS Notification Service - API Router."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_token, require_admin, TokenPayload
from src.core.exceptions import NotFoundError
from src.shared.schemas import MessageResponse
from src.services.notifications.service import NotificationService
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
)


router = APIRouter()


async def get_notification_service(
    session: AsyncSession = Depends(get_db),
) -> NotificationService:
    """Dependency for NotificationService."""
    return NotificationService(session)


# ═══════════════════════════════════════════════════════════
# Notification Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/notifications", response_model=list[NotificationListItem])
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    token: TokenPayload = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notifications."""
    user_id = UUID(token.keycloak_id)
    notifications = await service.get_user_notifications(user_id, unread_only, limit)
    return [NotificationListItem.model_validate(n) for n in notifications]


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    token: TokenPayload = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
):
    """Get unread notification count."""
    user_id = UUID(token.keycloak_id)
    count = await service.count_unread(user_id)
    return UnreadCountResponse(count=count)


@router.get("/notifications/{id}", response_model=NotificationResponse)
async def get_notification(
    id: UUID,
    token: TokenPayload = Depends(get_current_token),
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
    token: TokenPayload = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark notifications as read."""
    user_id = UUID(token.keycloak_id)
    count = await service.mark_read(data.notification_ids, user_id)
    return MessageResponse(message=f"Marked {count} notifications as read")


@router.post("/notifications/mark-all-read", response_model=MessageResponse)
async def mark_all_read(
    token: TokenPayload = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    user_id = UUID(token.keycloak_id)
    count = await service.mark_all_read(user_id)
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
        return await service.update_template(id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Preferences Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/notifications/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    token: TokenPayload = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notification preferences."""
    user_id = UUID(token.keycloak_id)
    return await service.get_preferences(user_id)


@router.put("/notifications/preferences", response_model=UserPreferencesResponse)
async def update_my_preferences(
    data: UserPreferencesUpdate,
    token: TokenPayload = Depends(get_current_token),
    service: NotificationService = Depends(get_notification_service),
):
    """Update current user's notification preferences."""
    user_id = UUID(token.keycloak_id)
    return await service.update_preferences(user_id, data)
