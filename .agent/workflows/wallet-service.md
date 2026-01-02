---
description: Manage Wallet Service
---

# Wallet Service Management

The Wallet Service (`wallet-service`) handles employee leave balances (Vacation, ROL, Permits).

## Development
- **Source Code**: `backend/src/services/wallet/`
- **Port**: `8006`
- **Database Schema**: `wallet`

## Common Tasks

### 1. View Employee Wallet
Retrieve the current wallet status for a user.
```bash
# Get wallet for a specific user (admin required or self)
http://localhost:8006/api/v1/wallets/{user_id}
```

### 2. Add Transaction
Manually add a transaction (e.g., Adjustment).
**Endpoint**: `POST /api/v1/wallets/{user_id}/transactions`
**Body**:
```json
{
  "user_id": "uuid...",
  "transaction_type": "adjustment",
  "balance_type": "vacation" | "rol" | "permits",
  "amount": 10.0,
  "description": "Manual correction"
}
```

### 3. Run Migrations
If models change, create and apply migrations.
```bash
docker exec kronos-wallet alembic revision --autogenerate -m "message"
docker exec kronos-wallet alembic upgrade head
```

## Integration Status
- [x] Service Created & Dockerized
- [x] Database Schema & Models
- [x] Basic CRUD API
- [ ] Integration with Leave Service (Pending)
- [ ] Integration with Auth Service (Pending)
