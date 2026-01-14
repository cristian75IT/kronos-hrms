from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.core.security import get_current_user, TokenPayload
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

from fastapi import Request, Query
from starlette.responses import StreamingResponse
from src.services.notifications.broadcaster import NotificationBroadcaster

@router.get("/notifications/sse-test")
async def stream_notifications_test(request: Request):
    """
    Server-Sent Events (SSE) stream for real-time notifications.
    Client must connect with ?token=<access_token>.
    """
    print(f"DEBUG: SSE-TEST endpoint ENTERED", flush=True)
    
    # helper for manual auth
    try:
        from src.core.security import resolve_user
        print(f"DEBUG: Extracting token...", flush=True)
        token = request.query_params.get("token")
        if not token:
            print("DEBUG: Missing token", flush=True)
            raise HTTPException(401, "Token required")
            
        print(f"DEBUG: Resolving user from token with length {len(token)}...", flush=True)
        # Use full resolution logic (DB sync, Cache)
        payload = await resolve_user(token)
        print(f"DEBUG: Auth Success: {payload.sub} -> Internal: {payload.internal_user_id}", flush=True)
        user_id = payload.user_id
        
    except Exception as e:
        print(f"DEBUG: Auth FAILED: {str(e)}", flush=True)
        # Use a simpler error response for SSE
        raise HTTPException(401, f"Auth failed: {str(e)}")

    print(f"DEBUG: Connecting broadcaster...", flush=True)
    broadcaster = NotificationBroadcaster.get_instance()
    
    return StreamingResponse(
        broadcaster.connect(user_id),
        media_type="text/event-stream"
    )

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

@router.get("/notifications/stream")
async def stream_notifications(request: Request):
    """
    Server-Sent Events (SSE) stream for real-time notifications.
    Client must connect with ?token=<access_token>.
    """
    print(f"DEBUG: Manual Stream endpoint ENTERED", flush=True)
    
    # helper for manual auth
    try:
        from src.core.security import resolve_user
        token = request.query_params.get("token")
        print(f"DEBUG: Manual Stream token: {str(token)[:10]}...", flush=True)
        if not token:
            print("DEBUG: Missing token", flush=True)
            raise HTTPException(401, "Token required")
            
        payload = await resolve_user(token)
        print(f"DEBUG: Manual Stream Auth Success: {payload.sub} -> Internal: {payload.internal_user_id}", flush=True)
        # Use internal_user_id if available (it should be after resolve_user), otherwise fallback to sub if that's what broadcaster expects
        # But usually broadcaster expects the internal UUID or the user ID used in the system.
        # Let's assume resolve_user sets the correct user_id in payload.
        user_id = payload.user_id 
        
    except Exception as e:
        print(f"DEBUG: Manual Stream Auth FAILED: {str(e)}", flush=True)
        # Use a simpler error response for SSE
        raise HTTPException(401, f"Auth failed: {str(e)}")

    print(f"DEBUG: Connecting broadcaster for user {user_id}", flush=True)
    broadcaster = NotificationBroadcaster.get_instance()
    
    return StreamingResponse(
        broadcaster.connect(user_id),
        media_type="text/event-stream"
    )


@router.get("/notifications/{id}", response_model=NotificationResponse)
async def get_notification(
    id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get notification by ID."""
    return await service.get_notification(id)
