from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.core.security import get_current_user, require_permission, TokenPayload
from src.core.exceptions import BusinessRuleError
from src.services.notifications.exceptions import (
    TemplateNotFound,
    ProviderConfigurationError,
    NotificationNotFound,
)
from src.shared.schemas import MessageResponse, DataTableRequest, DataTableResponse
from src.services.notifications.services import NotificationService
from src.services.notifications.deps import get_notification_service

from src.services.notifications.schemas import (
    NotificationResponse,
    EmailTemplateResponse,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    BulkNotificationRequest,
    BulkNotificationResponse,
    EmailLogResponse,
    EmailProviderSettingsResponse,
    EmailProviderSettingsCreate,
    EmailProviderSettingsUpdate,
    TestEmailRequest,
    SendEmailResponse
)

router = APIRouter()

class NotificationDataTableRequest(DataTableRequest):
    """DataTable request including channel filter."""
    channel: Optional[str] = None

@router.get("/notifications/history", response_model=List[NotificationResponse])
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
    total_records = await service.count_history()
    filtered_records = await service.count_history(channel=data.channel)
    items = await service.get_sent_history(
        limit=data.length,
        offset=data.start,
        channel=data.channel
    )
    
    return DataTableResponse(
        draw=data.draw,
        recordsTotal=total_records,
        recordsFiltered=filtered_records,
        data=[NotificationResponse.model_validate(item) for item in items],
    )


@router.post("/notifications/bulk", response_model=BulkNotificationResponse)
async def send_bulk(
    data: BulkNotificationRequest,
    current_user: TokenPayload = Depends(require_permission("notifications:send")),
    service: NotificationService = Depends(get_notification_service),
):
    """Send bulk notifications. Admin only."""
    return await service.send_bulk(data)


@router.get("/notifications/templates", response_model=List[EmailTemplateResponse])
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
    return await service.get_template(id)


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
    return await service.update_template(id, data, user_id=current_user.user_id)


@router.post("/notifications/templates/{id}/sync", response_model=dict)
async def sync_template_to_brevo(
    id: UUID,
    current_user: TokenPayload = Depends(require_permission("notifications:templates")),
    service: NotificationService = Depends(get_notification_service),
):
    """Sync template to Brevo. Admin only."""
    try:
        if await service.sync_template_to_brevo(id, user_id=current_user.user_id):
            return {"status": "ok"}
        raise HTTPException(status_code=500, detail="Sync failed")
    except TemplateNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, BusinessRuleError, ProviderConfigurationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/email-logs", response_model=List[EmailLogResponse])
async def get_email_logs(
    status: Optional[str] = None,
    template_code: Optional[str] = None,
    to_email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenPayload = Depends(require_permission("notifications:view")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get email logs history. Admin only."""
    return await service.get_email_logs(
        limit=limit,
        offset=offset,
        status=status,
        template_code=template_code,
        to_email=to_email,
    )


@router.get("/notifications/email-logs/stats", response_model=dict)
async def get_email_stats(
    days: int = 7,
    current_user: TokenPayload = Depends(require_permission("notifications:view")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get email delivery statistics. Admin only."""
    return await service.get_email_stats(days=days)


@router.post("/notifications/email-logs/{id}/retry", response_model=MessageResponse)
async def retry_email(
    id: UUID,
    current_user: TokenPayload = Depends(require_permission("notifications:manage")),
    service: NotificationService = Depends(get_notification_service),
):
    """Manually retry a failed email. Admin only."""
    res = await service.retry_email(id)
    if not res:
         raise HTTPException(status_code=400, detail="Retry failed")
    return MessageResponse(message="Retry initiated successfully. Check logs for status.")


@router.get("/notifications/email-logs/{id}/events", response_model=List[dict])
async def get_email_events(
    id: UUID,
    permissive: bool = False,
    current_user: TokenPayload = Depends(require_permission("notifications:view")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get Brevo events for a specific email log. Admin only."""
    return await service.get_email_events(id, permissive=permissive)


@router.get("/notifications/settings", response_model=EmailProviderSettingsResponse)
async def get_email_provider_settings(
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    service: NotificationService = Depends(get_notification_service),
):
    """Get active email provider settings. Admin only."""
    settings = await service.get_email_provider_settings()
    if not settings:
        raise HTTPException(status_code=404, detail="Email provider not configured")
    
    return EmailProviderSettingsResponse.model_validate(settings)


@router.post("/notifications/settings", response_model=EmailProviderSettingsResponse, status_code=201)
async def create_email_provider_settings(
    data: EmailProviderSettingsCreate,
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    service: NotificationService = Depends(get_notification_service),
):
    """Create email provider settings. Admin only."""
    settings = await service.create_email_provider_settings(data)
        
    return EmailProviderSettingsResponse.model_validate(settings)


@router.put("/notifications/settings/{id}", response_model=EmailProviderSettingsResponse)
async def update_email_provider_settings(
    id: UUID,
    data: EmailProviderSettingsUpdate,
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    service: NotificationService = Depends(get_notification_service),
):
    """Update email provider settings. Admin only."""
    settings = await service.update_email_provider_settings(id, data)
        
    return EmailProviderSettingsResponse.model_validate(settings)


@router.post("/notifications/settings/test", response_model=SendEmailResponse)
async def test_email_settings(
    data: TestEmailRequest,
    current_user: TokenPayload = Depends(require_permission("notifications:settings")),
    service: NotificationService = Depends(get_notification_service),
):
    """Send a test email to verify settings. Admin only."""
    success = await service.test_email_settings(data)
    return SendEmailResponse(success=success, message="Test email sent")
