# KRONOS Expensive Wallet Service

Microservice dedicated to managing finances associated with Business Trips (Trasferte). It handles budgets, transactions, reconciliation, and policy compliance.

## Architecture

This service acts as a "Financial Digital Twin" for business trips.

- **`models.py`**: `TripWallet`, `TripWalletTransaction`.
- **`routers/`**: Standardized router split.
- **`repository.py`**: Repository pattern for DB access.

## API Structure

### 1. `users.py` (`/api/v1/expensive-wallets`)
User access to their trip wallets.
- **GET /{trip_id}**: View wallet status and budget.
- **GET /{trip_id}/transactions**: View transaction history.

### 2. `admin.py` (`/api/v1/expensive-wallets/admin`)
Finance/Admin operations.
- **POST /admin/{trip_id}/reconcile**: Finance reconciliation.
- **POST /admin/{trip_id}/settle**: Final settlement/payment.
- **GET /admin/policy-violations**: Audit compliance.

### 3. `internal.py` (`/api/v1/expensive-wallets/internal`)
Internal system operations (called by Expense Service).
- **POST /internal/initialize/{trip_id}**: Create wallet upon trip approval.
- **POST /internal/{trip_id}/reserve**: Reserve budget for pending expense.
- **POST /internal/{trip_id}/confirm/{ref_id}**: Commit expense upon approval.

## Key Concepts
- **Wallet per Trip**: Every approved trip gets a dedicated wallet.
- **Double Entry Lite**: Tracks `budget`, `reserved`, `spent`, and `available`.
- **Policy Engine**: Checks for category limits (e.g., max 50€/day for meals).
