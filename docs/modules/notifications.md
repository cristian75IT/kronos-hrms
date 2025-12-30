# Modulo Notifications (Notifiche Email)

## Responsabilità

Il microservizio gestisce:
- Invio email transazionali via **Brevo** (ex Sendinblue)
- Gestione template email
- Queue asincrona per invio massivo
- Notifiche in-app
- Tracking delivery/open/click

---

## Architettura

```
┌─────────────────────────────────────────────────────────────┐
│                    OTHER MICROSERVICES                       │
│         (auth, leaves, expenses, config, audit)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Redis Queue (events)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  NOTIFICATION SERVICE                        │
│                       :8005                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Router    │    │   Service   │    │   Workers   │     │
│  │  (API)      │───▶│  (Logic)    │───▶│  (Celery)   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                               │              │
│                                               ▼              │
│                                    ┌─────────────────┐      │
│                                    │   Brevo API     │      │
│                                    │  (Email Send)   │      │
│                                    └─────────────────┘      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    DATABASE                          │   │
│  │  notifications.email_templates                       │   │
│  │  notifications.notification_queue                    │   │
│  │  notifications.notification_logs                     │   │
│  │  notifications.user_preferences                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Brevo Integration

### Configurazione

```bash
# .env
BREVO_API_KEY=xkeysib-xxxxxxxxxxxx
BREVO_SENDER_EMAIL=noreply@kronos.company.com
BREVO_SENDER_NAME=KRONOS HR
BREVO_WEBHOOK_SECRET=your-webhook-secret
```

### Template IDs in Brevo

| Template ID | Nome | Trigger |
|-------------|------|---------|
| 1 | `leave_request_pending` | Nuova richiesta assenza |
| 2 | `leave_request_approved` | Richiesta approvata |
| 3 | `leave_request_rejected` | Richiesta rifiutata |
| 4 | `leave_request_conditional` | Approvazione con condizioni |
| 5 | `leave_request_recalled` | Richiamo dalle ferie |
| 6 | `expense_submitted` | Nota spese inviata |
| 7 | `expense_approved` | Nota spese approvata |
| 8 | `expense_paid` | Nota spese pagata |
| 9 | `approval_reminder` | Reminder richieste pendenti |
| 10 | `balance_alert` | Alert saldo in scadenza |
| 11 | `password_reset` | Reset password |
| 12 | `welcome` | Benvenuto nuovo utente |

---

## Endpoints API

| Method | Endpoint | Descrizione | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/notifications/send` | Invia notifica (internal) | Service |
| `POST` | `/api/v1/notifications/send-bulk` | Invio massivo | Admin |
| `GET` | `/api/v1/notifications` | Lista notifiche utente | User |
| `PUT` | `/api/v1/notifications/{id}/read` | Marca come letta | User |
| `GET` | `/api/v1/notifications/preferences` | Preferenze utente | User |
| `PUT` | `/api/v1/notifications/preferences` | Aggiorna preferenze | User |
| `GET` | `/api/v1/notifications/templates` | Lista template | Admin |
| `PUT` | `/api/v1/notifications/templates/{id}` | Aggiorna mapping template | Admin |
| `POST` | `/api/v1/notifications/webhook/brevo` | Webhook Brevo | Public |

---

## Database Schema

```sql
-- Schema: notifications

-- Template mapping (Brevo template ID -> internal code)
CREATE TABLE notifications.email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,       -- 'leave_request_pending'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    brevo_template_id INTEGER NOT NULL,     -- ID template in Brevo
    subject_fallback VARCHAR(255),          -- Subject se Brevo fallisce
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Queue per invio asincrono
CREATE TABLE notifications.notification_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Destinatario
    user_id UUID,
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    
    -- Template e dati
    template_code VARCHAR(50) NOT NULL,
    template_params JSONB NOT NULL DEFAULT '{}',
    
    -- Stato
    status VARCHAR(20) DEFAULT 'pending',   -- 'pending', 'processing', 'sent', 'failed'
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    
    -- Error tracking
    last_error TEXT,
    
    -- Metadata
    priority INTEGER DEFAULT 5,             -- 1=highest, 10=lowest
    source_service VARCHAR(50),
    source_entity_type VARCHAR(50),
    source_entity_id UUID,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_queue_status ON notifications.notification_queue(status, scheduled_at);
CREATE INDEX idx_queue_user ON notifications.notification_queue(user_id);

-- Log invii (per tracking e audit)
CREATE TABLE notifications.notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID REFERENCES notifications.notification_queue(id),
    
    -- Destinatario
    recipient_email VARCHAR(255) NOT NULL,
    
    -- Template
    template_code VARCHAR(50) NOT NULL,
    brevo_template_id INTEGER,
    
    -- Brevo response
    brevo_message_id VARCHAR(255),
    
    -- Status tracking
    status VARCHAR(20) NOT NULL,            -- 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed'
    
    -- Timestamps
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    
    -- Error
    error_code VARCHAR(50),
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_logs_brevo_id ON notifications.notification_logs(brevo_message_id);
CREATE INDEX idx_logs_recipient ON notifications.notification_logs(recipient_email);

-- Preferenze utente
CREATE TABLE notifications.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,
    
    -- Canali
    email_enabled BOOLEAN DEFAULT TRUE,
    inapp_enabled BOOLEAN DEFAULT TRUE,
    
    -- Tipi notifica
    notify_leave_updates BOOLEAN DEFAULT TRUE,
    notify_expense_updates BOOLEAN DEFAULT TRUE,
    notify_approvals BOOLEAN DEFAULT TRUE,
    notify_reminders BOOLEAN DEFAULT TRUE,
    notify_compliance_alerts BOOLEAN DEFAULT TRUE,
    
    -- Digest
    daily_digest_enabled BOOLEAN DEFAULT FALSE,
    daily_digest_hour INTEGER DEFAULT 9,    -- 0-23
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notifiche in-app (non lette)
CREATE TABLE notifications.inapp_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),                      -- Link to entity
    icon VARCHAR(50),                       -- 'leave', 'expense', 'alert', etc.
    
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    
    -- Source
    source_entity_type VARCHAR(50),
    source_entity_id UUID,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ                  -- Auto-delete after
);

CREATE INDEX idx_inapp_user ON notifications.inapp_notifications(user_id, is_read);
```

---

## Schemas Pydantic

```python
# schemas.py
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr


class NotificationChannel(str, Enum):
    EMAIL = "email"
    INAPP = "inapp"
    BOTH = "both"


class NotificationPriority(int, Enum):
    CRITICAL = 1
    HIGH = 3
    NORMAL = 5
    LOW = 8


# === Requests ===

class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    user_id: Optional[UUID] = None
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    template_code: str
    params: dict[str, Any] = {}
    channel: NotificationChannel = NotificationChannel.BOTH
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    source_service: Optional[str] = None
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[UUID] = None


class SendBulkRequest(BaseModel):
    """Bulk notification request."""
    template_code: str
    recipients: list[dict]  # [{email, name, params}]
    priority: NotificationPriority = NotificationPriority.LOW


class UpdatePreferencesRequest(BaseModel):
    email_enabled: Optional[bool] = None
    inapp_enabled: Optional[bool] = None
    notify_leave_updates: Optional[bool] = None
    notify_expense_updates: Optional[bool] = None
    notify_approvals: Optional[bool] = None
    notify_reminders: Optional[bool] = None
    daily_digest_enabled: Optional[bool] = None
    daily_digest_hour: Optional[int] = None


# === Responses ===

class InAppNotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    link: Optional[str]
    icon: Optional[str]
    is_read: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserPreferencesResponse(BaseModel):
    email_enabled: bool
    inapp_enabled: bool
    notify_leave_updates: bool
    notify_expense_updates: bool
    notify_approvals: bool
    notify_reminders: bool
    daily_digest_enabled: bool
    daily_digest_hour: int
    
    model_config = {"from_attributes": True}
```

---

## Brevo Service

```python
# brevo_client.py
from typing import Any, Optional
import httpx
from pydantic import BaseModel

from src.core.config import settings


class BrevoClient:
    """Client for Brevo (Sendinblue) API."""
    
    BASE_URL = "https://api.brevo.com/v3"
    
    def __init__(self) -> None:
        self._api_key = settings.BREVO_API_KEY
        self._sender_email = settings.BREVO_SENDER_EMAIL
        self._sender_name = settings.BREVO_SENDER_NAME

    async def send_template_email(
        self,
        *,
        to_email: str,
        to_name: Optional[str],
        template_id: int,
        params: dict[str, Any],
    ) -> dict:
        """Send email using Brevo template.
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            template_id: Brevo template ID
            params: Template parameters (merged with template)
            
        Returns:
            Brevo API response with messageId
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/smtp/email",
                headers={
                    "api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {
                        "email": self._sender_email,
                        "name": self._sender_name,
                    },
                    "to": [
                        {
                            "email": to_email,
                            "name": to_name or to_email,
                        }
                    ],
                    "templateId": template_id,
                    "params": params,
                },
                timeout=30.0,
            )
            
            response.raise_for_status()
            return response.json()

    async def send_transactional_email(
        self,
        *,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: str,
    ) -> dict:
        """Send raw transactional email (fallback)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/smtp/email",
                headers={
                    "api-key": self._api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "sender": {
                        "email": self._sender_email,
                        "name": self._sender_name,
                    },
                    "to": [{"email": to_email, "name": to_name}],
                    "subject": subject,
                    "htmlContent": html_content,
                },
                timeout=30.0,
            )
            
            response.raise_for_status()
            return response.json()

    async def get_email_events(self, message_id: str) -> dict:
        """Get delivery events for a message."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/smtp/statistics/events",
                headers={"api-key": self._api_key},
                params={"messageId": message_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
```

---

## Notification Service

```python
# service.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.notifications.repository import (
    NotificationQueueRepository,
    NotificationLogRepository,
    TemplateRepository,
    InAppRepository,
    PreferencesRepository,
)
from src.modules.notifications.brevo_client import BrevoClient
from src.modules.notifications.schemas import (
    SendNotificationRequest,
    NotificationChannel,
)


class NotificationService:
    """Service for sending notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._queue_repo = NotificationQueueRepository(session)
        self._log_repo = NotificationLogRepository(session)
        self._template_repo = TemplateRepository(session)
        self._inapp_repo = InAppRepository(session)
        self._prefs_repo = PreferencesRepository(session)
        self._brevo = BrevoClient()

    async def send(self, request: SendNotificationRequest) -> UUID:
        """Queue a notification for sending.
        
        Returns:
            Queue entry ID
        """
        # Check user preferences
        if request.user_id:
            prefs = await self._prefs_repo.get_by_user(request.user_id)
            if prefs and not self._should_send(prefs, request.template_code):
                return None  # User opted out
        
        # Add to queue
        queue_entry = await self._queue_repo.create(
            user_id=request.user_id,
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            template_code=request.template_code,
            template_params=request.params,
            priority=request.priority,
            scheduled_at=request.scheduled_at or datetime.utcnow(),
            source_service=request.source_service,
            source_entity_type=request.source_entity_type,
            source_entity_id=request.source_entity_id,
        )
        
        # Create in-app notification if enabled
        if request.channel in (NotificationChannel.INAPP, NotificationChannel.BOTH):
            if request.user_id:
                await self._create_inapp(request)
        
        return queue_entry.id

    async def process_queue(self, batch_size: int = 50) -> int:
        """Process pending notifications in queue.
        
        Called by Celery worker.
        Returns number processed.
        """
        pending = await self._queue_repo.get_pending(limit=batch_size)
        processed = 0
        
        for entry in pending:
            try:
                await self._send_email(entry)
                await self._queue_repo.mark_sent(entry.id)
                processed += 1
            except Exception as e:
                await self._queue_repo.mark_failed(entry.id, str(e))
        
        return processed

    async def _send_email(self, queue_entry) -> None:
        """Send single email via Brevo."""
        # Get template
        template = await self._template_repo.get_by_code(queue_entry.template_code)
        if not template:
            raise ValueError(f"Template not found: {queue_entry.template_code}")
        
        # Send via Brevo
        result = await self._brevo.send_template_email(
            to_email=queue_entry.recipient_email,
            to_name=queue_entry.recipient_name,
            template_id=template.brevo_template_id,
            params=queue_entry.template_params,
        )
        
        # Log
        await self._log_repo.create(
            queue_id=queue_entry.id,
            recipient_email=queue_entry.recipient_email,
            template_code=queue_entry.template_code,
            brevo_template_id=template.brevo_template_id,
            brevo_message_id=result.get("messageId"),
            status="sent",
            sent_at=datetime.utcnow(),
        )

    async def _create_inapp(self, request: SendNotificationRequest) -> None:
        """Create in-app notification."""
        # Map template to in-app content
        title, message, link, icon = self._map_template_to_inapp(
            request.template_code,
            request.params,
        )
        
        await self._inapp_repo.create(
            user_id=request.user_id,
            title=title,
            message=message,
            link=link,
            icon=icon,
            source_entity_type=request.source_entity_type,
            source_entity_id=request.source_entity_id,
        )

    def _map_template_to_inapp(
        self,
        template_code: str,
        params: dict,
    ) -> tuple[str, str, Optional[str], str]:
        """Map email template to in-app notification content."""
        mappings = {
            "leave_request_pending": (
                "Nuova richiesta di assenza",
                f"{params.get('employee_name', 'Un dipendente')} ha richiesto {params.get('leave_type', 'assenza')}",
                f"/leaves/{params.get('request_id')}",
                "calendar",
            ),
            "leave_request_approved": (
                "Richiesta approvata",
                f"La tua richiesta di {params.get('leave_type', 'assenza')} è stata approvata",
                f"/leaves/{params.get('request_id')}",
                "check",
            ),
            "leave_request_rejected": (
                "Richiesta rifiutata",
                f"La tua richiesta di {params.get('leave_type', 'assenza')} è stata rifiutata",
                f"/leaves/{params.get('request_id')}",
                "x",
            ),
            "expense_approved": (
                "Nota spese approvata",
                f"La nota spese di €{params.get('amount', '0')} è stata approvata",
                f"/expenses/{params.get('expense_id')}",
                "receipt",
            ),
            "approval_reminder": (
                "Richieste in attesa",
                f"Hai {params.get('count', 0)} richieste in attesa di approvazione",
                "/approvals",
                "bell",
            ),
        }
        
        return mappings.get(
            template_code,
            ("Notifica", "Hai una nuova notifica", None, "bell"),
        )

    def _should_send(self, prefs, template_code: str) -> bool:
        """Check if notification should be sent based on preferences."""
        if not prefs.email_enabled:
            return False
        
        category_map = {
            "leave_": "notify_leave_updates",
            "expense_": "notify_expense_updates",
            "approval_": "notify_approvals",
            "reminder_": "notify_reminders",
            "balance_": "notify_compliance_alerts",
        }
        
        for prefix, pref_field in category_map.items():
            if template_code.startswith(prefix):
                return getattr(prefs, pref_field, True)
        
        return True
```

---

## Celery Tasks

```python
# tasks.py
from celery import shared_task

from src.core.database import get_session_sync
from src.modules.notifications.service import NotificationService


@shared_task(name="notifications.process_queue")
def process_notification_queue():
    """Process pending notifications. Runs every minute."""
    with get_session_sync() as session:
        service = NotificationService(session)
        processed = service.process_queue_sync(batch_size=100)
        return f"Processed {processed} notifications"


@shared_task(name="notifications.send_daily_digest")
def send_daily_digest():
    """Send daily digest to users. Runs daily at configured hour."""
    with get_session_sync() as session:
        service = NotificationService(session)
        sent = service.send_daily_digests_sync()
        return f"Sent {sent} daily digests"


@shared_task(name="notifications.cleanup_old")
def cleanup_old_notifications():
    """Cleanup old notifications. Runs weekly."""
    with get_session_sync() as session:
        service = NotificationService(session)
        deleted = service.cleanup_old_sync(days=90)
        return f"Deleted {deleted} old notifications"
```

---

## Brevo Webhook Handler

```python
# router.py
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/webhook/brevo")
async def brevo_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Handle Brevo delivery webhooks."""
    # Verify signature
    signature = request.headers.get("X-Mailin-Signature")
    body = await request.body()
    
    expected = hmac.new(
        settings.BREVO_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    
    if not hmac.compare_digest(signature or "", expected):
        raise HTTPException(401, "Invalid signature")
    
    # Process events
    data = await request.json()
    event = data.get("event")
    message_id = data.get("messageId")
    
    log_repo = NotificationLogRepository(session)
    
    if event == "delivered":
        await log_repo.update_status(message_id, "delivered")
    elif event == "opened":
        await log_repo.update_status(message_id, "opened")
    elif event == "clicked":
        await log_repo.update_status(message_id, "clicked")
    elif event in ("soft_bounce", "hard_bounce", "blocked"):
        await log_repo.update_status(message_id, "bounced")
    
    return {"status": "ok"}
```

---

## Event Triggers (Altri Servizi)

```python
# leave-service/service.py
from src.modules.notifications.client import NotificationClient

class LeaveService:
    def __init__(self, session, notification_client):
        self._notifications = notification_client

    async def approve(self, request_id: UUID, approver_id: UUID):
        # ... approval logic ...
        
        # Send notification
        await self._notifications.send(
            template_code="leave_request_approved",
            user_id=request.user_id,
            recipient_email=request.user.email,
            recipient_name=request.user.full_name,
            params={
                "employee_name": request.user.full_name,
                "leave_type": request.leave_type.name,
                "start_date": request.start_date.strftime("%d/%m/%Y"),
                "end_date": request.end_date.strftime("%d/%m/%Y"),
                "approver_name": approver.full_name,
                "request_id": str(request.id),
            },
            source_service="leave-service",
            source_entity_type="leave_request",
            source_entity_id=request.id,
        )
```

---

## Template Variables

| Template | Variables |
|----------|-----------|
| `leave_request_pending` | employee_name, leave_type, start_date, end_date, days_count, notes, request_id, approval_url |
| `leave_request_approved` | employee_name, leave_type, start_date, end_date, approver_name, request_id |
| `leave_request_rejected` | employee_name, leave_type, rejection_reason, approver_name, request_id |
| `expense_submitted` | employee_name, amount, period, expense_id, approval_url |
| `expense_approved` | employee_name, amount, approved_amount, expense_id |
| `expense_paid` | employee_name, amount, payment_date, expense_id |
| `approval_reminder` | approver_name, count, pending_list, approval_url |
| `balance_alert` | employee_name, balance_type, balance_value, expiry_date |
