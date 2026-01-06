# Enterprise Microservices Refactor Plan

## Objectives
- **Optimization**: Implement robust connection pooling for inter-service communication.
- **Responsibility**: Decompose the monolithic `clients.py` into single-responsibility modules.
- **Error Management**: Replace generic error swallowing with a standardized enterprise exception hierarchy.
- **Maintainability & Agnosticism**: Centralize configuration and ensure clients don't leak implementation details.
- **Configuration**: Eliminate hardcoded URLs and introduce `FRONTEND_URL` for correct absolute link generation.

## 1. Foundation Layer

### 1.1 Enterprise Exceptions
Create `backend/src/shared/exceptions.py` to define a standard hierarchy:
- `MicroserviceError` (Base)
- `ServiceUnavailableError` (Network/Timeout)
- `ServiceResponseError` (5xx, 4xx from upstream)
- `UnauthorizedServiceError` (Auth failures)

### 1.2 Configuration Update
Update `backend/src/core/config.py`:
- Add `FRONTEND_URL` (e.g., `http://localhost:3000` default, configurable via env).
- Add `AUTH_CALLBACK_URL` if distinct.

### 1.3 Base Client
Create `backend/src/shared/clients/base.py` defining `BaseClient`:
- **Singleton HTTP Session**: Use a persistent `httpx.AsyncClient` to enable connection pooling (Keep-Alive).
- **Circuit Breaker Pattern** (Optional but recommended): Simple failure counting.
- **Standardized Request Wrapper**: Method `_make_request` dealing with timeouts, retries (using `tenacity` or custom loop), and error mapping.

## 2. Refactoring Clients
Split `backend/src/shared/clients.py` into modular files within `backend/src/shared/clients/`:

- `__init__.py` (Exports components for backward compatibility imports)
- `auth.py` (`AuthClient`)
- `config.py` (`ConfigClient`)
- `notification.py` (`NotificationClient`)
- `leaves_wallet.py` (`LeavesWalletClient`)
- `expensive_wallet.py` (`ExpensiveWalletClient`)
- `audit.py` (`AuditClient` - note: `audit_client.py` currently exists separately, consolidate if needed)

**Optimization**: Each client will inherit from `BaseClient` and reuse the connection pool.

## 3. Interaction & Agnosticism
- **URL Handling**:
    - Usage of `action_url` (e.g. `/approvals/{id}`) is currently agnostic of the domain, which is good.
    - **Fix**: The `NotificationService` (or the Client) must resolve this to an absolute URL using `FRONTEND_URL` before sending emails.
    - Implementation: Update `NotificationService._render_template` or `_send_email_notification` to prepend `settings.FRONTEND_URL` if `action_url` starts with `/`.

## 4. Verification & Testing
- **Verify**: One service (e.g., `ApprovalsService`) explicitly to ensure it handles the new client exceptions or that the client wraps them gracefully (if we choose soft-failure for now).
- **Safe Rollout**: The refactored clients will maintain the same public API methods (`get_user`, `send_notification`) to avoid breaking all consumers.

## 5. Implementation Steps

1.  Create `src/shared/exceptions.py`.
2.  Update `src/core/config.py`.
3.  Create `src/shared/clients/` directory and `base.py`.
4.  Migrate `AuthClient` to `src/shared/clients/auth.py`.
5.  Migrate `NotificationClient` to `src/shared/clients/notification.py`.
6.  Migrate `LeavesWalletClient` to `src/shared/clients/leaves_wallet.py`.
7.  Migrate other clients.
8.  Update `src/shared/clients/__init__.py` to re-export.
9.  Modify `NotificationService` to prepend `FRONTEND_URL`.
10. Remove old `clients.py`.

## 6. Callback URL Fix
- The user specifically requested removing hardcoded callback URLs.
- Investigation found relative paths like `/approvals/{id}` in `ApprovalsService`.
- **Solution**: These will be standardized by the `FRONTEND_URL` configuration in `NotificationService`, ensuring strictly one source of truth for the domain.

