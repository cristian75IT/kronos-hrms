# Struttura Progetto

## Overview

Il progetto segue i principi della **Clean Architecture** con separazione chiara delle responsabilità.

---

## Struttura Directory Backend

```
backend/
├── docker-compose.yml          # Ambiente sviluppo completo
├── Dockerfile                  # Build container servizio
├── pyproject.toml              # Dipendenze e configurazione progetto
├── alembic.ini                 # Configurazione Alembic
│
├── alembic/                    # Migrazioni database
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       └── 002_add_leaves.py
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entrypoint FastAPI, include routers
│   ├── dependencies.py         # Dependency Injection (get_db, get_current_user)
│   │
│   ├── core/                   # Configurazione e utilities globali
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings (carica da ENV)
│   │   ├── database.py         # Engine, AsyncSession, Base
│   │   ├── security.py         # JWT encode/decode, password hashing
│   │   ├── exceptions.py       # Custom exceptions (NotFoundError, etc.)
│   │   └── logging.py          # Configurazione structlog
│   │
│   ├── modules/                # Moduli business (Domain-Driven)
│   │   │
│   │   ├── auth/               # ══════════════════════════════════
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # POST /auth/login, POST /auth/refresh
│   │   │   ├── schemas.py      # LoginRequest, TokenResponse
│   │   │   ├── service.py      # AuthService (authenticate, create_token)
│   │   │   ├── repository.py   # AuthRepository (get_user_by_email)
│   │   │   └── models.py       # (usa UserModel da users)
│   │   │
│   │   ├── users/              # ══════════════════════════════════
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # CRUD /users
│   │   │   ├── schemas.py      # UserCreate, UserResponse, UserUpdate
│   │   │   ├── service.py      # UserService
│   │   │   ├── repository.py   # UserRepository
│   │   │   └── models.py       # UserModel, AreaModel, LocationModel
│   │   │
│   │   ├── leaves/             # ══════════════════════════════════
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # CRUD /leaves, /balances
│   │   │   ├── schemas.py      # LeaveRequestCreate, LeaveResponse
│   │   │   ├── service.py      # LeaveService (create, approve, reject)
│   │   │   ├── repository.py   # LeaveRepository, BalanceRepository
│   │   │   ├── models.py       # LeaveRequestModel, LeaveBalanceModel
│   │   │   └── policy_engine.py # PolicyEngine (validate_request)
│   │   │
│   │   ├── expenses/           # ══════════════════════════════════
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # CRUD /trips, /expenses
│   │   │   ├── schemas.py      # TripCreate, ExpenseReportCreate
│   │   │   ├── service.py      # ExpenseService
│   │   │   ├── repository.py   # TripRepository, ExpenseRepository
│   │   │   └── models.py       # BusinessTripModel, ExpenseReportModel
│   │   │
│   │   ├── config/             # ══════════════════════════════════
│   │   │   ├── __init__.py
│   │   │   ├── router.py       # GET/PUT /config, /leave-types, /holidays
│   │   │   ├── schemas.py      # ConfigItem, LeaveTypeCreate
│   │   │   ├── service.py      # ConfigService (get, set, invalidate_cache)
│   │   │   ├── repository.py   # ConfigRepository
│   │   │   ├── models.py       # SystemConfigModel, LeaveTypeModel
│   │   │   └── cache.py        # Redis cache wrapper
│   │   │
│   │   ├── notifications/      # ══════════════════════════════════
│   │   │   ├── __init__.py
│   │   │   ├── service.py      # NotificationService (send_email, send_inapp)
│   │   │   ├── templates/      # Template email HTML
│   │   │   └── tasks.py        # Celery tasks per invio asincrono
│   │   │
│   │   └── reports/            # ══════════════════════════════════
│   │       ├── __init__.py
│   │       ├── router.py       # GET /reports/payroll, /reports/dashboard
│   │       ├── service.py      # ReportService
│   │       └── generators/     # PayrollExporter, DashboardBuilder
│   │
│   └── shared/                 # Codice condiviso tra moduli
│       ├── __init__.py
│       ├── base_models.py      # BaseModel con id, created_at, updated_at
│       ├── base_schemas.py     # BaseSchema, PaginatedResponse
│       ├── pagination.py       # PaginationParams, paginate()
│       ├── enums.py            # Enum condivisi (Role, LeaveStatus)
│       └── utils.py            # Helpers (calculate_working_days, etc.)
│
└── tests/
    ├── conftest.py             # Fixtures pytest (db, client, user)
    ├── unit/
    │   ├── test_policy_engine.py
    │   └── test_working_days.py
    └── integration/
        ├── test_auth_flow.py
        └── test_leave_workflow.py
```

---

## Struttura Directory Frontend

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
│
├── public/
│   └── favicon.ico
│
└── src/
    ├── main.tsx                # Entrypoint React
    ├── App.tsx                 # Router principale
    │
    ├── api/                    # Client HTTP
    │   ├── client.ts           # Axios instance con interceptor
    │   ├── auth.ts             # login(), refresh()
    │   ├── leaves.ts           # getLeaves(), createLeave()
    │   └── users.ts            # getUsers(), updateUser()
    │
    ├── components/             # Componenti riutilizzabili
    │   ├── ui/                 # Shadcn components
    │   │   ├── button.tsx
    │   │   ├── input.tsx
    │   │   └── dialog.tsx
    │   ├── layout/
    │   │   ├── Sidebar.tsx
    │   │   ├── Header.tsx
    │   │   └── DashboardLayout.tsx
    │   └── forms/
    │       ├── LeaveRequestForm.tsx
    │       └── ExpenseForm.tsx
    │
    ├── pages/                  # Route pages
    │   ├── auth/
    │   │   └── LoginPage.tsx
    │   ├── dashboard/
    │   │   └── DashboardPage.tsx
    │   ├── leaves/
    │   │   ├── LeaveListPage.tsx
    │   │   ├── LeaveDetailPage.tsx
    │   │   └── LeaveCalendarPage.tsx
    │   ├── approvals/
    │   │   └── ApprovalListPage.tsx
    │   └── admin/
    │       ├── UsersPage.tsx
    │       └── ConfigPage.tsx
    │
    ├── hooks/                  # Custom hooks
    │   ├── useAuth.ts
    │   ├── useLeaves.ts
    │   └── useConfig.ts
    │
    ├── stores/                 # Global state (se necessario)
    │   └── authStore.ts
    │
    ├── types/                  # TypeScript interfaces
    │   ├── user.ts
    │   ├── leave.ts
    │   └── api.ts
    │
    └── lib/                    # Utilities
        ├── utils.ts            # cn(), formatDate()
        └── constants.ts
```

---

## Pattern di Responsabilità

| Layer | File | Responsabilità |
|-------|------|----------------|
| **Router** | `router.py` | Definizione endpoint, HTTP status, response model |
| **Schema** | `schemas.py` | Validazione request, serializzazione response |
| **Service** | `service.py` | Business logic, orchestrazione, validazioni dominio |
| **Repository** | `repository.py` | Query database, CRUD, nessuna logica di business |
| **Model** | `models.py` | Definizione tabelle SQLAlchemy, relazioni |
| **Policy** | `policy_engine.py` | Validazione regole configurabili da DB |

---

## Flusso Request

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       v
┌─────────────┐
│   Router    │ → Parsing, Auth check (Depends)
└──────┬──────┘
       │ Schema validated
       v
┌─────────────┐
│   Service   │ → Business logic, Policy validation
└──────┬──────┘
       │ Domain objects
       v
┌─────────────┐
│ Repository  │ → Database queries
└──────┬──────┘
       │ SQLAlchemy models
       v
┌─────────────┐
│  Database   │
└─────────────┘
```
