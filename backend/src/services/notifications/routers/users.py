from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.core.security import get_current_user, TokenPayload
from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.notifications.services import NotificationService
from src.services.notifications.deps import get_notification_service

from src.shared.schemas import MessageResponse

from src.services.notifications.schemas import (
    NotificationResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    MarkReadRequest
)

router = APIRouter()

@router.get("/notifications/me", response_model=list[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    channel: Optional[str] = None,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notifications."""
    return await service.get_user_notifications(
        current_user.user_id,
        unread_only=unread_only,
        limit=limit,
        channel=channel,
    )


@router.get("/notifications/unread-count", response_model=dict)
async def get_unread_count(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get unread notification count."""
    count = await service.count_unread(current_user.user_id)
    return {"count": count}


@router.get("/notifications/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's notification preferences."""
    return await service.get_my_preferences(current_user.user_id)


@router.put("/notifications/preferences", response_model=UserPreferencesResponse)
async def update_my_preferences(
    data: UserPreferencesUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Update current user's notification preferences."""
    return await service.update_my_preferences(current_user.user_id, data)


@router.post("/notifications/read", response_model=MessageResponse)
async def mark_read(
    data: MarkReadRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark notifications as read."""
    await service.mark_read(data.notification_ids, current_user.user_id)
    return MessageResponse(message="Notifications marked as read")


@router.post("/notifications/read/all", response_model=MessageResponse)
async def mark_all_read(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    await service.mark_all_read(current_user.user_id)
    return MessageResponse(message="Marked all notifications as read")


@router.post("/notifications/push-subscriptions", response_model=PushSubscriptionResponse, status_code=201)
async def subscribe_to_push(
    data: PushSubscriptionCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Subscribe to Web Push notifications."""
    return await service.subscribe_to_push(current_user.user_id, data)


@router.get("/notifications/push-subscriptions", response_model=list[PushSubscriptionResponse])
async def get_my_push_subscriptions(
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get current user's push subscriptions."""
    return await service.get_my_push_subscriptions(current_user.user_id)


@router.delete("/notifications/push-subscriptions/{id}", response_model=MessageResponse)
async def unsubscribe_from_push(
    id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Unsubscribe from Web Push notifications."""
    await service.unsubscribe_from_push(id, current_user.user_id)
    return MessageResponse(message="Unsubscribed from push notifications")

@router.get("/notifications/{id}", response_model=NotificationResponse)
async def get_notification(
    id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification by ID."""
    return await service.get_notification(id)
