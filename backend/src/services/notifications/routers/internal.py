from fastapi import APIRouter, Depends, HTTPException

from src.services.notifications.services import NotificationService
from src.services.notifications.deps import get_notification_service
from src.services.notifications.schemas import (
    NotificationResponse,
    NotificationCreate,
    SendEmailRequest,
    SendEmailResponse
)

router = APIRouter()

@router.post("/notifications/send-email", response_model=SendEmailResponse)
async def send_email(
    data: SendEmailRequest,
    service: NotificationService = Depends(get_notification_service),
):
    """Send email directly. Called by other services."""
    return await service.send_email(data)

@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(
    data: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
):
    """Create notification. Called by other services."""
    notification = await service.create_notification(data)
    if not notification:
        raise HTTPException(status_code=400, detail="Notification not created")
    return notification
