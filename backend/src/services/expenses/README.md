# KRONOS Expense Service

Handles business trip management, expense reporting, dailly allowances, and reimbursement workflows.

## Architecture

The service follows the KRONOS microservice architecture with standardized router splitting:

- **`models.py`**: SQLAlchemy ORM models (`BusinessTrip`, `ExpenseReport`, `ExpenseItem`, `DailyAllowance`).
- **`schemas.py`**: Pydantic models for request/response validation.
- **`services.py`**: Business logic layer.
- **`repository.py`**: Data access layer.
- **`deps.py`**: Dependency injection.
- **`routers/`**: API endpoints split by domain.

## API Structure

The API is organized into the following routers:

### 1. `trips.py` (`/api/v1/trips`)
Manages business trips (Trasferte).
- **GET /trips**: List user's trips.
- **POST /trips**: Create a new trip request.
- **GET /trips/{id}/allowances**: View calculated daily allowances.
- **POST /trips/{id}/approve|reject**: Approval workflow.

### 2. `reports.py` (`/api/v1/expenses`)
Manages expense reports (Note Spese).
- **GET /expenses**: List expense reports.
- **POST /expenses**: Create a new report ( standalone or linked to trip).
- **POST /expenses/{id}/submit**: Submit for approval.

### 3. `items.py` (`/api/v1/expenses/items`)
Manages individual expense items (receipts).
- **POST /expenses/items**: Add a receipt/expense item.
- **PUT /expenses/items/{id}**: Update details.

### 4. `internal.py` (`/api/v1/internal`)
Internal service-to-service communication.
- Used by other services to validate trip status or budget.

## Key Features
- **Automatic Allowance Calculation**: Based on trip duration and destination.
- **Workflow Engine Support**: Integrated with standard approval flows.
- **Budget Control**: Checks against `expensive_wallet` limits.
