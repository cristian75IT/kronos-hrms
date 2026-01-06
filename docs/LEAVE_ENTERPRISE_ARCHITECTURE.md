# KRONOS Leave Management - Enterprise Architecture

## Executive Summary

This document outlines the enterprise-grade refactoring of the Leave and Wallet services to eliminate redundancy, establish clear role separation, and add premium features.

---

## 🏗 Current State Analysis

### Issues Identified

| Issue | Service | Severity |
|-------|---------|----------|
| No partial recall (single day) support | leaves | 🔴 High |
| Overlapping balance calculation logic | leaves + wallet | 🔴 High |
| User/Approver actions mixed in same methods | leaves | 🟠 Medium |
| No interruption workflow (sick during vacation) | leaves | 🔴 High |
| No delegation support | leaves | 🟠 Medium |
| No team-wide visibility controls | leaves | 🟡 Low |
| Missing audit trail on wallet transactions | wallet | 🟠 Medium |

### Current Responsibility Split

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           CURRENT ARCHITECTURE                            │
├───────────────────────────────────────────────────────────────────────────┤
│  leaves-service (LeaveService)                                            │
│  ├── Create/Update/Delete LeaveRequest                                   │
│  ├── Workflow: Submit → Approve/Reject → Complete                        │
│  ├── Recall (full leave)                                                 │
│  ├── Days calculation (via CalendarUtils)                                │
│  ├── Balance deduction orchestration (calls wallet)                      │
│  └── Reporting (calendar, attendance)                                    │
├───────────────────────────────────────────────────────────────────────────┤
│  leaves_wallet-service (WalletService)                                   │
│  ├── Wallet CRUD (EmployeeWallet)                                        │
│  ├── Transaction processing (accrual, deduction, refund)                 │
│  ├── FIFO bucket consumption                                             │
│  └── Balance snapshots                                                   │
├───────────────────────────────────────────────────────────────────────────┤
│  OVERLAP/ISSUES:                                                          │
│  ├── balance_service.py in leaves WRAPS wallet calls                     │
│  ├── Some balance logic duplicated                                       │
│  ├── No clear ApproverService vs UserService separation                  │
│  └── Recall only supports full vacancy termination                       │
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
│  │                      LEAVE REQUEST SERVICE                          │  │
│  │  Owns: LeaveRequest entity lifecycle                                │  │
│  │                                                                     │  │
│  │  ┌───────────────────┐      ┌────────────────────────┐             │  │
│  │  │ UserRequestAPI    │      │ ApproverWorkflowAPI    │             │  │
│  │  │ (Employee Portal) │      │ (Manager Portal)       │             │  │
│  │  ├───────────────────┤      ├────────────────────────┤             │  │
│  │  │ • create_draft    │      │ • approve              │             │  │
│  │  │ • update_draft    │      │ • approve_conditional  │             │  │
│  │  │ • submit          │      │ • reject               │             │  │
│  │  │ • cancel          │      │ • revoke               │             │  │
│  │  │ • accept_condition│      │ • reopen               │             │  │
│  │  │ • get_my_requests │      │ • recall_partial       │  ← NEW      │  │
│  │  │ • get_my_calendar │      │ • recall_full          │             │  │
│  │  │ • report_sick     │ NEW  │ • interrupt_for_sick   │  ← NEW      │  │
│  │  └───────────────────┘      │ • modify_approved      │  ← NEW      │  │
│  │                              │ • delegate_approval    │  ← NEW      │  │
│  │                              │ • get_team_calendar    │             │  │
│  │                              │ • get_pending_requests │             │  │
│  │                              └────────────────────────┘             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                          ┌─────────▼─────────┐                           │
│                          │ Wallet Client     │                           │
│                          │ (HTTP/Internal)   │                           │
│                          └─────────┬─────────┘                           │
│                                    │                                      │
│  ┌─────────────────────────────────▼───────────────────────────────────┐  │
│  │                      WALLET SERVICE                                 │  │
│  │  Owns: Balance data, Transactions, FIFO logic                      │  │
│  │                                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐  │  │
│  │  │ Internal API (consumed by Leave Service only)     ✅ DONE      │  │  │
│  │  ├───────────────────────────────────────────────────────────────┤  │  │
│  │  │ • process_transaction(user_id, type, amount, ref_id)          │  │  │
│  │  │ • reserve_balance(user_id, balance_type, amount, ref_id)  ✅  │  │  │
│  │  │ • confirm_reservation(ref_id)                             ✅  │  │  │
│  │  │ • cancel_reservation(ref_id)                              ✅  │  │  │
│  │  │ • get_available_balance(user_id, balance_type)            ✅  │  │  │
│  │  │ • check_balance_sufficient(user_id, balance_type, amount) ✅  │  │  │
│  │  │ • get_balance_summary(user_id, year)                      ✅  │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌───────────────────────────────────────────────────────────────┐  │  │
│  │  │ Admin API (HR Portal)                              ✅ DONE     │  │  │
│  │  ├───────────────────────────────────────────────────────────────┤  │  │
│  │  │ • process_expiration(wallet_id, balance_type, amount)     ✅  │  │  │
│  │  │ • get_wallets_for_accrual(year)                           ✅  │  │  │
│  │  │ • get_expiring_balances(date)                             ✅  │  │  │
│  │  │ • get_wallet_transactions(wallet_id, limit)               ✅  │  │  │
│  │  └───────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🆕 Premium Features to Add

### 1. Partial Recall (Richiamo Parziale)
**Use Case**: Manager needs employee for just 1 day during 10-day vacation

```python
# API: POST /api/v1/leaves/requests/{id}/recall/partial
{
    "recall_days": ["2026-01-08"],  # Specific days to work
    "reason": "Urgent client meeting"
}
```

**Result**:
- Original 10-day request stays APPROVED
- Creates new "interruption" record
- Balance refunds only for recalled days
- Employee vacation resumes after recalled day(s)

### 2. Vacation Interruption for Sickness (Malattia in Ferie)
**Use Case**: Employee gets sick during vacation (Italian law Art. 6 D.Lgs 66/2003)

```python
# API: POST /api/v1/leaves/requests/{id}/interrupt/sickness
{
    "sick_start_date": "2026-01-05",
    "sick_end_date": "2026-01-07",
    "protocol_number": "INPS12345",
    "attachment_path": "/uploads/medical_cert.pdf"
}
```

**Result**:
- Sick days are NOT counted as vacation
- Balance is automatically refunded for sick days
- Creates linked sickness request
- Original vacation request updated with interruption metadata

### 3. Approval Delegation
**Use Case**: Manager is on vacation, delegates approval to another manager

```python
# API: POST /api/v1/leaves/delegations
{
    "delegate_to": "uuid-of-backup-manager",
    "start_date": "2026-01-01",
    "end_date": "2026-01-15",
    "delegation_type": "full"  # full | readonly
}
```

### 4. Balance Reservation (Pre-approval Hold)
**Use Case**: Reserve balance when request is PENDING, confirm on APPROVE

**Workflow**:
1. `submit_request` → calls `wallet.reserve_balance()`
2. `approve_request` → calls `wallet.confirm_reservation()`
3. `reject_request` → calls `wallet.cancel_reservation()`

**Benefits**:
- Prevents double-booking of insufficient balance
- Real-time availability in UI

### 5. Modify Approved Request
**Use Case**: Change dates of approved future vacation

```python
# API: PATCH /api/v1/leaves/requests/{id}/modify
{
    "new_start_date": "2026-01-10",
    "new_end_date": "2026-01-15",
    "reason": "Travel plans changed"
}
```

**Constraints**:
- Only for future dates
- Must have sufficient balance for new period
- Creates history entry with modifications

### 6. Voluntary Work During Vacation (Lavoro Volontario)
**Use Case**: Employee wants to work specific day(s) during approved vacation

```python
# API: POST /api/v1/leaves/my/requests/{id}/request-work
{
    "work_days": ["2026-01-08"],  # Days to convert to working days
    "reason": "Important project deadline, I prefer to work this day"
}
```

**Workflow**:
1. Employee submits request with detailed reason
2. Manager receives notification
3. Manager approves/rejects the request
4. On approval: vacation days are refunded to balance

**Key Points**:
- Employee-initiated (not manager recall)
- Requires manager approval
- Vacation continues for non-requested days
- Full audit trail maintained

---

## 📁 Implementation Files

### Backend Architecture (Microservice standard)
```
backend/src/services/leaves/
├── models.py               # Enterprise models
├── repository.py           # NEW - Central data access with specialized repositories
├── schemas.py              # Pydantic models for I/O
├── services/               # MODULAR SERVICE ARCHITECTURE
│   ├── base.py             # Base class with repository injection
│   ├── enterprise.py       # Core leave logic & interruptions
│   ├── query.py            # Read-only queries & analytics
│   └── strategies/         # Leave calculation strategies
├── routers/                # HTTP Endpoints (Router Layer)
│   ├── leave.py            # Core leave requests
│   ├── delegation.py       # Approval delegation
│   └── balance.py          # Wallet integration & balances
├── accrual_service.py      # Monthly accrual logic
├── balance_service.py      # Balance calculation orchestration
└── report_service.py       # Attendance & aggregate reporting
```

---

## 🔄 Migration Steps

1. **Add new models** (LeaveInterruption, ApprovalDelegation)
2. **Create new Alembic migration**
3. **Refactor service.py** into domain-specific services
4. **Update routers** with clear separation
5. **Add reservation logic** to wallet service
6. **Create comprehensive tests**
7. **Update frontend** to use new endpoints

---

## ✅ Validation Checklist

- [ ] No balance calculation in leaves-service (only orchestration)
- [ ] Clear User vs Approver API separation
- [ ] Partial recall supports single or multiple days
- [ ] Sickness interruption follows Italian labor law
- [ ] Delegation has proper audit trail
- [ ] All transactions have reference_id for traceability
- [ ] Frontend updated for new workflows
