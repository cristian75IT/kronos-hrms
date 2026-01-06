# KRONOS Notification Service

Centralized notification dispatch service integrating with Email (Brevo) and Web Push.

## Architecture

The service follows the KRONOS microservice architecture with standardized router splitting:

- **`models.py`**: SQLAlchemy models for `Notification`, `EmailLog`, `EmailTemplate`, `PushSubscription`.
- **`services.py`**: Logic for dispatching emails and push notifications.
- **`routers/`**: API endpoints split by audience/function.

## API Structure

### 1. `users.py` (`/api/v1/notifications`)
User-facing endpoints.
- **GET /notifications/me**: List user's notifications.
- **POST /notifications/read**: Mark notifications as read.
- **POST /notifications/push-subscriptions**: Subscribe current device to web push.

### 2. `admin.py` (`/api/v1/notifications`)
Administrative endpoints.
- **GET /notifications/email-logs**: Audit trail of sent emails.
- **GET /notifications/templates**: Manage email templates (Brevo sync).
- **POST /notifications/settings**: Configure Email Provider (SMTP/API).

### 3. `internal.py` (`/api/v1/internal`)
Internal service-to-service communication.
- **POST /internal/notify**: Send a notification (called by other services).
- **POST /internal/email**: Send a raw email.

## Key Features
- **Multi-Channel**: Supports Email and Web Push.
- **Template Management**: Syncs templates with external providers (Brevo).
- **Resiliency**: Retry mechanism for failed emails.
