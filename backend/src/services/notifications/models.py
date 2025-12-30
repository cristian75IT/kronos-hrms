"""KRONOS Notification Service - SQLAlchemy Models."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.core.database import Base


class NotificationChannel(str, enum.Enum):
    """Notification delivery channel."""
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"  # Future use
    PUSH = "push"  # Future use


class NotificationStatus(str, enum.Enum):
    """Notification status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class NotificationType(str, enum.Enum):
    """Notification type for categorization."""
    LEAVE_REQUEST_SUBMITTED = "leave_request_submitted"
    LEAVE_REQUEST_APPROVED = "leave_request_approved"
    LEAVE_REQUEST_REJECTED = "leave_request_rejected"
    LEAVE_REQUEST_CANCELLED = "leave_request_cancelled"
    LEAVE_CONDITIONAL_APPROVAL = "leave_conditional_approval"
    LEAVE_BALANCE_LOW = "leave_balance_low"
    LEAVE_UPCOMING_REMINDER = "leave_upcoming_reminder"
    
    TRIP_SUBMITTED = "trip_submitted"
    TRIP_APPROVED = "trip_approved"
    TRIP_REJECTED = "trip_rejected"
    
    EXPENSE_SUBMITTED = "expense_submitted"
    EXPENSE_APPROVED = "expense_approved"
    EXPENSE_REJECTED = "expense_rejected"
    EXPENSE_PAID = "expense_paid"
    
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    COMPLIANCE_ALERT = "compliance_alert"


class Notification(Base):
    """Notification record."""
    
    __tablename__ = "notifications"
    __table_args__ = {"schema": "notifications"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Recipient
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Content
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Channel
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel),
        default=NotificationChannel.IN_APP,
    )
    
    # Status
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus),
        default=NotificationStatus.PENDING,
    )
    
    # Tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Related entity
    entity_type: Mapped[Optional[str]] = mapped_column(String(50))  # LeaveRequest, Trip, etc.
    entity_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Action URL
    action_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Extra data
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class EmailTemplate(Base):
    """Email templates for Brevo transactional emails."""
    
    __tablename__ = "email_templates"
    __table_args__ = {"schema": "notifications"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Template identification
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Brevo template ID (for external templates)
    brevo_template_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Or inline template
    subject: Mapped[Optional[str]] = mapped_column(String(200))
    html_content: Mapped[Optional[str]] = mapped_column(Text)
    text_content: Mapped[Optional[str]] = mapped_column(Text)
    
    # Linked notification types
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType),
        nullable=False,
    )
    
    # Variables (for documentation)
    available_variables: Mapped[Optional[list]] = mapped_column(JSONB)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserNotificationPreference(Base):
    """User preferences for notifications."""
    
    __tablename__ = "user_notification_preferences"
    __table_args__ = {"schema": "notifications"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, nullable=False)
    
    # Email preferences
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    email_leave_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    email_expense_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    email_system_announcements: Mapped[bool] = mapped_column(Boolean, default=True)
    email_compliance_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # In-app preferences
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Digest settings
    digest_frequency: Mapped[str] = mapped_column(
        String(20),
        default="instant",  # instant, daily, weekly
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
