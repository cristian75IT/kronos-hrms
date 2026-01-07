# Enterprise Error Handling

This document describes the standardized error handling system used across all KRONOS microservices.

## Overview

KRONOS implements a **unified error handling architecture** that ensures:
- Consistent JSON error responses
- Automatic error propagation to UI via toast notifications
- Error deduplication to prevent multiple toasts for the same error
- Severity-based styling (warning, error, critical)

---

## Backend Error Response Format

All microservices return errors in a standardized JSON format:

```json
{
    "error": {
        "code": "NOT_FOUND",
        "message": "User with ID 'abc123' not found",
        "details": {
            "resource_type": "User",
            "resource_id": "abc123"
        },
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-01-07T05:10:00Z"
    }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Machine-readable error code (e.g., `NOT_FOUND`, `VALIDATION_ERROR`) |
| `message` | string | Human-readable error description |
| `details` | object | Additional context (optional) |
| `request_id` | string | UUID for tracking/support |
| `timestamp` | datetime | When the error occurred |

---

## Exception Hierarchy

Use exceptions from `src.shared.exceptions`:

```python
from src.shared.exceptions import (
    NotFoundError,
    ValidationError,
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    InvalidStateError,
)

# Not found
raise NotFoundError("User", user_id)

# Validation
raise ValidationError("Email format is invalid", field="email")

# Business rule
raise BusinessRuleError(
    "Cannot approve own leave request",
    rule="SELF_APPROVAL_FORBIDDEN"
)

# State violation
raise InvalidStateError(
    "Cannot cancel an approved request",
    current_state="APPROVED",
    allowed_states=["PENDING", "SUBMITTED"]
)
```

### Exception → HTTP Status Mapping

| Exception | HTTP Status |
|-----------|-------------|
| `NotFoundError` | 404 |
| `ValidationError` | 422 |
| `BusinessRuleError` | 400 |
| `ConflictError` | 409 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |
| `InvalidStateError` | 400 |
| `ServiceUnavailableError` | 503 |

---

## Frontend Error Interceptor

The API client (`frontend/src/services/api.ts`) automatically:

1. **Parses error responses** from all microservices
2. **Dispatches toast events** via `window.dispatchEvent`
3. **Deduplicates errors** (same error within 2s is shown once)
4. **Categorizes severity**:
   - `400-499`: User errors (orange/warning style)
   - `500+`: System errors (red/critical style, 8s duration)

### Manual Error Handling

If you need to handle errors in a component AND show a toast:

```typescript
try {
    await api.post('/leaves', data);
} catch (error) {
    // Toast is automatically shown by interceptor
    // You can still handle for local state updates
    setIsSubmitting(false);
}
```

If you want to suppress the automatic toast:

```typescript
try {
    await api.post('/leaves', data);
} catch (error) {
    // Interceptor still fires, but you could add a flag in config
    // to suppress if needed in the future
}
```

---

## Adding New Exception Types

1. Create exception in `src/shared/exceptions.py`:

```python
class QuotaExceededError(MicroserviceError):
    http_status = 429
    code = "QUOTA_EXCEEDED"
    
    def __init__(self, resource: str, limit: int, current: int):
        super().__init__(
            message=f"{resource} quota exceeded ({current}/{limit})",
            details={"resource": resource, "limit": limit, "current": current}
        )
```

2. It will automatically be handled by `microservice_exception_handler` in `error_handlers.py`.

---

## Debugging

### Finding Request ID

1. Check browser console for error details
2. The toast message includes `(Ref: xxxxxxxx)` for 5xx errors
3. Search backend logs for the full request ID

### Common Error Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| `NOT_FOUND` | Resource doesn't exist | Invalid ID, deleted resource |
| `VALIDATION_ERROR` | Invalid input | Missing required field, bad format |
| `BUSINESS_RULE_VIOLATION` | Domain rule failed | Insufficient balance, self-approval |
| `CONFLICT` | Duplicate/overlap | Email exists, date overlap |
| `FORBIDDEN` | Missing permission | RBAC check failed |
| `INTERNAL_SERVER_ERROR` | Unhandled exception | Bug, DB error |
