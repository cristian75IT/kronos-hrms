# KRONOS Expense Management - Enterprise Architecture

## Executive Summary

This document outlines the enterprise-grade refactoring of the Expense and Trip Wallet services to eliminate redundancy, establish clear role separation, and add premium features.

---

## 🏗 Current State Analysis

### Issues Identified

| Issue | Service | Severity |
|-------|---------|----------|
| No audit trail on wallet transactions | expensive_wallet | 🔴 High |
| Budget validation not centralized | expenses | 🟠 Medium |
| Missing advance payment workflow | expenses | 🔴 High |
| No policy limit enforcement | expensive_wallet | 🔴 High |
| Missing receipt OCR integration | expenses | 🟡 Low |
| No multi-currency proper handling | both | 🟠 Medium |
| Missing expense delegation | expenses | 🟠 Medium |
| No reconciliation workflow | expensive_wallet | 🔴 High |

### Current Responsibility Split

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           CURRENT ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────┤
│  expenses-service (ExpenseService)                                        │
│  ├── Create/Update/Delete BusinessTrip                                   │
│  ├── Create/Update/Delete ExpenseReport                                  │
│  ├── Workflow: Submit → Approve/Reject → Complete → Paid                 │
│  ├── Daily Allowance generation                                          │
│  ├── Expense Item management                                             │
│  ├── Wallet client calls for transactions                                │
│  └── Attachments management                                              │
├───────────────────────────────────────────────────────────────────────────┤
│  expensive_wallet-service (TripWalletService)                            │
│  ├── Wallet CRUD (TripWallet)                                            │
│  ├── Transaction processing (budget, advance, expense, refund)           │
│  ├── Policy violation tracking                                           │
│  └── Balance calculations (via properties)                               │
├───────────────────────────────────────────────────────────────────────────┤
│  ISSUES:                                                                  │
│  ├── No pre-approval budget check                                        │
│  ├── Wallet created on trip approval - should check budget first         │
│  ├── No audit integration in wallet                                      │
│  ├── Policy violations only count, no detailed tracking                  │
│  └── Missing reconciliation and settlement workflows                     │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Target Enterprise Architecture

### Principle: Single Responsibility + Clear API Contracts

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         TARGET ARCHITECTURE                               │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      EXPENSE SERVICE                                │  │
│  │  Owns: Trip lifecycle, Reports, Approvals, Items                   │  │
│  │                                                                     │  │
│  │  ┌───────────────────┐      ┌────────────────────────┐             │  │
│  │  │ EmployeeAPI       │      │ ApproverAPI            │             │  │
│  │  ├───────────────────┤      ├────────────────────────┤             │  │
│  │  │ • create_trip     │      │ • approve_trip         │             │  │
│  │  │ • update_trip     │      │ • reject_trip          │             │  │
│  │  │ • submit_trip     │      │ • approve_report       │             │  │
│  │  │ • create_report   │      │ • reject_report        │             │  │
│  │  │ • add_item        │      │ • approve_item         │  ← NEW      │  │
│  │  │ • submit_report   │      │ • reject_item          │  ← NEW      │  │
│  │  │ • request_advance │ NEW  │ • approve_advance      │  ← NEW      │  │
│  │  │ • get_my_wallet   │      │ • process_payment      │             │  │
│  │  │ • upload_receipt  │      │ • delegate_approval    │  ← NEW      │  │
│  │  └───────────────────┘      └────────────────────────┘             │  │
│  │                                                                     │  │
│  │  ┌────────────────────────────────────────────────────┐            │  │
│  │  │ AdminAPI (Finance/HR)                              │            │  │
│  │  ├────────────────────────────────────────────────────┤            │  │
│  │  │ • reconcile_trip                                   │  ← NEW     │  │
│  │  │ • bulk_process_payments                            │  ← NEW     │  │
│  │  │ • update_policy_limits                             │            │  │
│  │  │ • export_to_accounting                             │  ← NEW     │  │
│  │  │ • void_transaction                                 │  ← NEW     │  │
│  │  │ • get_compliance_report                            │  ← NEW     │  │
│  │  └────────────────────────────────────────────────────┘            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                          ┌─────────▼─────────┐                           │
│                          │ Wallet Client     │                           │
│                          │ (HTTP/Internal)   │                           │
│                          └─────────┬─────────┘                           │
│                                    │                                      │
│  ┌─────────────────────────────────▼───────────────────────────────────┐  │
│  │                      TRIP WALLET SERVICE                            │  │
│  │  Owns: Financial data, Transactions, Policy limits, Audit          │  │
│  │                                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐  │  │
│  │  │ Internal API (consumed by Expense Service only)               │  │  │
│  │  ├───────────────────────────────────────────────────────────────┤  │  │
│  │  │ • create_wallet(trip_id, user_id, budget)                     │  │  │
│  │  │ • check_budget_available(trip_id, amount)              ← NEW  │  │  │
│  │  │ • reserve_budget(trip_id, amount, ref_id)              ← NEW  │  │  │
│  │  │ • confirm_expense(trip_id, ref_id)                     ← NEW  │  │  │
│  │  │ • cancel_expense(trip_id, ref_id)                      ← NEW  │  │  │
│  │  │ • register_advance(trip_id, amount, ref_id)                   │  │  │
│  │  │ • register_expense(trip_id, item_details)                     │  │  │
│  │  │ • register_payment(trip_id, amount, ref_id)                   │  │  │
│  │  │ • check_policy_limit(trip_id, category, amount)        ← NEW  │  │  │
│  │  │ • get_wallet_summary(trip_id)                                 │  │  │
│  │  │ • void_transaction(transaction_id, reason)             ← NEW  │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐  │  │
│  │  │ Admin/Finance API                                             │  │  │
│  │  ├───────────────────────────────────────────────────────────────┤  │  │
│  │  │ • reconcile_wallet(trip_id)                            ← NEW  │  │  │
│  │  │ • settle_wallet(trip_id)                               ← NEW  │  │  │
│  │  │ • get_all_open_wallets()                               ← NEW  │  │  │
│  │  │ • get_policy_violations(filters)                       ← NEW  │  │  │
│  │  │ • export_transactions(trip_id, format)                 ← NEW  │  │  │
│  │  │ • update_budget(trip_id, new_budget, reason)           ← NEW  │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🆕 Premium Features to Add

### 1. Advance Payment Workflow (Anticipazione)
**Use Case**: Employee requests cash advance before trip

```python
# API: POST /api/v1/expenses/trips/{id}/request-advance
{
    "amount": 500.00,
    "purpose": "Hotel and transport costs",
    "preferred_date": "2026-01-10"
}
```

**Workflow**:
1. Employee submits advance request
2. Manager approves/rejects
3. Finance processes payment
4. Wallet tracks advance vs expenses
5. Final settlement calculates net reimbursement

### 2. Budget Reservation (Pre-expense Hold)
**Use Case**: Reserve budget when expense is submitted, confirm on approval

```python
# Internal: Called when ExpenseItem is created (draft)
wallet.reserve_budget(trip_id, item.amount, item.id)

# Internal: Called when item is approved
wallet.confirm_expense(trip_id, item.id)

# Internal: Called when item is rejected/deleted
wallet.cancel_expense(trip_id, item.id)
```

### 3. Policy Limit Enforcement
**Use Case**: Real-time check against company expense policies

```python
# API: POST /api/v1/wallets/internal/check-policy
{
    "trip_id": "uuid",
    "category": "FOOD",
    "amount": 75.00
}
# Response:
{
    "allowed": false,
    "limit": 50.00,
    "exceeded_by": 25.00,
    "policy_code": "FOOD_DAILY_MAX",
    "requires_approval": true
}
```

### 4. Wallet Reconciliation (Riconciliazione)
**Use Case**: Finance closes trip and settles accounts

```python
# API: POST /api/v1/wallets/{trip_id}/reconcile
{
    "final_notes": "All receipts verified",
    "adjustments": [
        {"item_id": "uuid", "new_amount": 45.00, "reason": "Partial receipt"}
    ]
}
```

**Result**:
- Status changes to RECONCILED
- Calculates final net_to_pay
- Creates settlement transaction
- Marks for payment processing

### 5. Multi-Currency Support
**Use Case**: Auto-convert foreign expenses to EUR

```python
# ExpenseItem includes:
{
    "amount": 100.00,
    "currency": "USD",
    "exchange_rate": 0.92,  # Auto-fetched or manual
    "amount_eur": 92.00     # Calculated
}
```

### 6. Expense Delegation
**Use Case**: Manager delegates expense approvals during absence

```python
# API: POST /api/v1/expenses/delegations
{
    "delegate_to": "uuid-of-backup-manager",
    "start_date": "2026-01-01",
    "end_date": "2026-01-15",
    "max_amount": 5000.00  # Optional limit
}
```

---

## 📁 Implementation Files

### Files to Modify:

```
backend/src/services/expensive_wallet/
├── service.py              # Add enterprise methods
├── routers/wallet.py       # Add internal/admin endpoints
├── schemas.py              # Add new schemas
└── models.py               # Add policy_violations detail

backend/src/services/expenses/
├── service.py              # Integrate budget checking
├── router.py               # Add advance workflow endpoints
├── schemas.py              # Add advance request schemas
└── models.py               # Add advance request model
```

---

## 🔄 Clear Responsibility Split

### EXPENSE Service Owns:
- ✅ Trip/Report/Item lifecycle (CRUD)
- ✅ Workflow state machine
- ✅ Allowance calculation
- ✅ Approval routing
- ✅ Notification sending
- ❌ NO balance calculations
- ❌ NO policy limit logic

### WALLET Service Owns:
- ✅ All financial data (budget, expenses, advances)
- ✅ Transaction ledger
- ✅ Policy limit enforcement
- ✅ Reconciliation logic
- ✅ Currency conversion storage
- ✅ Audit trail for all transactions
- ❌ NO workflow logic
- ❌ NO approval routing

---

## ✅ Validation Checklist

- [ ] No expense calculations in expense-service
- [ ] All transactions go through wallet
- [ ] Budget checked before approval
- [ ] Policy limits enforced in wallet
- [ ] Audit trail on all financial operations
- [ ] Clear Internal vs Admin API separation
- [ ] Advance workflow complete
- [ ] Reconciliation workflow complete
