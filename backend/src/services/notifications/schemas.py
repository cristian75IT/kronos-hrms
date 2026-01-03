"""KRONOS Notification Service - Pydantic Schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.shared.schemas import BaseSchema, IDMixin, DataTableResponse
from src.services.notifications.models import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


# ═══════════════════════════════════════════════════════════
# Notification Schemas
# ═══════════════════════════════════════════════════════════

class NotificationCreate(BaseModel):
    """Schema for creating notification."""
    
    user_id: UUID
    user_email: str = Field(..., max_length=255)
    notification_type: NotificationType
    title: str = Field(..., max_length=200)
    message: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action_url: Optional[str] = None
    payload: Optional[dict] = None


class NotificationResponse(IDMixin, BaseSchema):
    """Response schema for notification."""
    
    user_id: UUID
    notification_type: NotificationType
    title: str
    message: str
    channel: NotificationChannel
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    recipient_name: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action_url: Optional[str] = None
    created_at: datetime


class NotificationListItem(BaseModel):
    """Simplified notification for lists."""
    
    id: UUID
    recipient_name: Optional[str] = None
    notification_type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class NotificationDataTableResponse(DataTableResponse[NotificationListItem]):
    """DataTable response for notifications."""
    pass


class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""
    
    notification_ids: list[UUID]


class UnreadCountResponse(BaseModel):
    """Response with unread count."""
    
    count: int


# ═══════════════════════════════════════════════════════════
# Email Template Schemas
# ═══════════════════════════════════════════════════════════

class EmailTemplateBase(BaseModel):
    """Base email template schema."""
    
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    notification_type: NotificationType
    brevo_template_id: Optional[int] = None
    subject: Optional[str] = Field(None, max_length=200)
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    available_variables: Optional[list[str]] = None


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating email template."""
    pass


class EmailTemplateUpdate(BaseModel):
    """Schema for updating email template."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    brevo_template_id: Optional[int] = None
    subject: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    available_variables: Optional[list[str]] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(EmailTemplateBase, IDMixin, BaseSchema):
    """Response schema for email template."""
    
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
# User Preferences Schemas
# ═══════════════════════════════════════════════════════════

class UserPreferencesBase(BaseModel):
    """Base user preferences schema."""
    
    email_enabled: bool = True
    in_app_enabled: bool = True
    push_enabled: bool = True
    preferences_matrix: dict[str, dict[str, bool]] = Field(default_factory=dict)
    digest_frequency: str = Field(default="instant", pattern="^(instant|daily|weekly)$")


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""
    
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    preferences_matrix: Optional[dict[str, dict[str, bool]]] = None
    digest_frequency: Optional[str] = None


class UserPreferencesResponse(UserPreferencesBase, IDMixin, BaseSchema):
    """Response schema for user preferences."""
    
    user_id: UUID


# ═══════════════════════════════════════════════════════════
# Email Sending Schemas
# ═══════════════════════════════════════════════════════════

class SendEmailRequest(BaseModel):
    """Request to send email directly."""
    
    to_email: str
    to_name: Optional[str] = None
    template_code: str
    variables: dict = {}
    
    # Optional: override recipient from notification
    notification_id: Optional[UUID] = None


class SendEmailResponse(BaseModel):
    """Response from email send."""
    
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class BulkNotificationRequest(BaseModel):
    """Request to send bulk notifications."""
    
    notification_type: NotificationType
    title: str = Field(..., max_length=200)
    message: str
    user_ids: list[UUID]
    channels: list[NotificationChannel] = [NotificationChannel.IN_APP]
    action_url: Optional[str] = None
    payload: Optional[dict] = None


class BulkNotificationResponse(BaseModel):
    """Response from bulk notification."""
    
    total: int
    sent: int
    failed: int
    errors: list[str] = []


# ═══════════════════════════════════════════════════════════
# Push Subscription Schemas
# ═══════════════════════════════════════════════════════════

class PushSubscriptionCreate(BaseModel):
    """Schema for creating push subscription."""
    
    endpoint: str
    p256dh: str
    auth: str
    device_info: Optional[dict] = None


class PushSubscriptionResponse(IDMixin, BaseSchema):
    """Response schema for push subscription."""
    
    user_id: UUID
    endpoint: str
    p256dh: str
    auth: str
    device_info: Optional[dict] = None
    is_active: bool
    created_at: datetime


class EmailLogResponse(IDMixin, BaseSchema):
    """Response schema for email log."""
    
    to_email: str
    to_name: Optional[str] = None
    user_id: Optional[UUID] = None
    template_code: str
    subject: Optional[str] = None
    variables: Optional[dict] = None
    
    status: str
    message_id: Optional[str] = None
    notification_id: Optional[UUID] = None
    
    error_message: Optional[str] = None
    retry_count: int
    next_retry_at: Optional[datetime] = None
    
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
# Email Provider Settings Schemas
# ═══════════════════════════════════════════════════════════

class EmailProviderSettingsBase(BaseModel):
    """Base email provider settings schema."""
    
    provider: str = Field(default="brevo", max_length=20)
    api_key: str = Field(..., min_length=1)
    sender_email: str = Field(..., max_length=255)
    sender_name: str = Field(default="KRONOS HR", max_length=100)
    reply_to_email: Optional[str] = Field(None, max_length=255)
    reply_to_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    test_mode: bool = False
    test_email: Optional[str] = Field(None, max_length=255)
    daily_limit: Optional[int] = None


class EmailProviderSettingsCreate(EmailProviderSettingsBase):
    """Schema for creating provider settings."""
    pass


class EmailProviderSettingsUpdate(BaseModel):
    """Schema for updating provider settings."""
    
    api_key: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    reply_to_email: Optional[str] = None
    reply_to_name: Optional[str] = None
    is_active: Optional[bool] = None
    test_mode: Optional[bool] = None
    test_email: Optional[str] = None
    daily_limit: Optional[int] = None


class EmailProviderSettingsResponse(IDMixin, BaseSchema):
    """Response schema for provider settings (API key masked)."""
    
    provider: str
    api_key_masked: str  # Show only last 4 chars
    sender_email: str
    sender_name: str
    reply_to_email: Optional[str] = None
    reply_to_name: Optional[str] = None
    is_active: bool
    test_mode: bool
    test_email: Optional[str] = None
    daily_limit: Optional[int] = None
    emails_sent_today: int
    created_at: datetime
    updated_at: datetime


class TestEmailRequest(BaseModel):
    """Request to send a test email."""
    
    to_email: str = Field(..., max_length=255)
