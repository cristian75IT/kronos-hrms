# Schema Database

## Overview

Il database utilizza **PostgreSQL 15+** con schema separati per modulo logico.
Tutte le tabelle usano **UUID** come primary key e includono `created_at`, `updated_at`.

---

## Schema: `auth` (Utenti e Organizzazione)

### Tabella: `users`
```sql
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(50),                    -- Matricola
    
    -- Ruolo e permessi
    role VARCHAR(20) NOT NULL DEFAULT 'employee',  -- 'admin', 'manager', 'employee'
    is_approver BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Relazioni organizzative
    line_manager_id UUID REFERENCES auth.users(id),
    location_id UUID REFERENCES auth.locations(id),
    contract_type_id UUID REFERENCES auth.contract_types(id),
    work_schedule_id UUID REFERENCES auth.work_schedules(id),
    
    -- Timestamps
    hire_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_role ON auth.users(role);
CREATE INDEX idx_users_manager ON auth.users(line_manager_id);
```

### Tabella: `areas`
```sql
CREATE TABLE auth.areas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    manager_id UUID REFERENCES auth.users(id),  -- Responsabile area
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `user_areas` (N:M)
```sql
CREATE TABLE auth.user_areas (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    area_id UUID REFERENCES auth.areas(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, area_id)
);
```

### Tabella: `locations`
```sql
CREATE TABLE auth.locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    address TEXT,
    patron_saint_date DATE,         -- Es. 7 Dicembre per Milano
    timezone VARCHAR(50) DEFAULT 'Europe/Rome',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `contract_types`
```sql
CREATE TABLE auth.contract_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,         -- Es. "Full-Time 40h", "Part-Time 50%"
    weekly_hours DECIMAL(4,1) NOT NULL, -- Es. 40.0, 20.0
    percentage DECIMAL(3,2) NOT NULL,   -- Es. 1.00, 0.50
    is_full_time BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `work_schedules`
```sql
CREATE TABLE auth.work_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,         -- Es. "Standard Lun-Ven", "Turnista"
    monday_hours DECIMAL(3,1) DEFAULT 0,
    tuesday_hours DECIMAL(3,1) DEFAULT 0,
    wednesday_hours DECIMAL(3,1) DEFAULT 0,
    thursday_hours DECIMAL(3,1) DEFAULT 0,
    friday_hours DECIMAL(3,1) DEFAULT 0,
    saturday_hours DECIMAL(3,1) DEFAULT 0,
    sunday_hours DECIMAL(3,1) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Schema: `leaves` (Assenze)

### Tabella: `leave_requests`
```sql
CREATE TABLE leaves.leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    leave_type_id UUID NOT NULL REFERENCES config.leave_types(id),
    
    -- Date e ore
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,                    -- Per permessi orari
    end_time TIME,
    hours_requested DECIMAL(5,2),       -- Ore totali richieste
    
    -- Stato workflow
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- 'draft', 'pending', 'approved', 'approved_conditional', 
    -- 'rejected', 'cancelled', 'recalled', 'completed'
    
    -- Approvazione
    approver_id UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,
    
    -- Approvazione condizionata
    approval_type VARCHAR(20) DEFAULT 'standard', -- 'standard', 'conditional'
    condition_type VARCHAR(10),         -- 'RIC', 'REP', 'PAR', 'MOD', 'ALT'
    approval_conditions TEXT,
    conditions_accepted BOOLEAN DEFAULT FALSE,
    conditions_accepted_at TIMESTAMPTZ,
    
    -- Richiamo
    is_recalled BOOLEAN DEFAULT FALSE,
    recall_date DATE,
    recall_reason TEXT,
    
    -- Malattia
    inps_protocol VARCHAR(50),
    
    -- Note e allegati
    notes TEXT,
    attachment_paths JSONB DEFAULT '[]',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leave_requests_user ON leaves.leave_requests(user_id);
CREATE INDEX idx_leave_requests_status ON leaves.leave_requests(status);
CREATE INDEX idx_leave_requests_dates ON leaves.leave_requests(start_date, end_date);
CREATE INDEX idx_leave_requests_approver ON leaves.leave_requests(approver_id) WHERE status = 'pending';
```

### Tabella: `leave_balances`
```sql
CREATE TABLE leaves.leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    year INTEGER NOT NULL,
    
    -- Ferie (in ore o giorni, configurabile)
    vacation_total DECIMAL(6,2) DEFAULT 0,      -- Monte totale
    vacation_used DECIMAL(6,2) DEFAULT 0,       -- Fruito
    vacation_pending DECIMAL(6,2) DEFAULT 0,    -- In approvazione
    vacation_previous_year DECIMAL(6,2) DEFAULT 0, -- Residuo AP
    
    -- ROL
    rol_total DECIMAL(6,2) DEFAULT 0,
    rol_used DECIMAL(6,2) DEFAULT 0,
    rol_pending DECIMAL(6,2) DEFAULT 0,
    
    -- Permessi
    permits_total DECIMAL(6,2) DEFAULT 0,
    permits_used DECIMAL(6,2) DEFAULT 0,
    permits_pending DECIMAL(6,2) DEFAULT 0,
    
    -- Banca ore (opzionale)
    overtime_balance DECIMAL(6,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, year)
);

CREATE INDEX idx_leave_balances_user_year ON leaves.leave_balances(user_id, year);
```

---

## Schema: `expenses` (Trasferte e Rimborsi)

### Tabella: `business_trips`
```sql
CREATE TABLE expenses.business_trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    
    destination VARCHAR(255) NOT NULL,
    purpose TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- 'draft', 'pending', 'approved', 'rejected', 'completed'
    
    approver_id UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    
    -- Diaria calcolata
    daily_allowance_rate DECIMAL(8,2),
    total_allowance DECIMAL(10,2),
    
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `expense_reports`
```sql
CREATE TABLE expenses.expense_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    business_trip_id UUID REFERENCES expenses.business_trips(id),
    
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    -- 'draft', 'submitted', 'approved', 'partially_approved', 'rejected', 'paid'
    
    total_amount DECIMAL(10,2) DEFAULT 0,
    approved_amount DECIMAL(10,2) DEFAULT 0,
    
    approver_id UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    payment_date DATE,
    
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `expense_items`
```sql
CREATE TABLE expenses.expense_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_report_id UUID NOT NULL REFERENCES expenses.expense_reports(id) ON DELETE CASCADE,
    expense_type_id UUID NOT NULL REFERENCES config.expense_types(id),
    
    expense_date DATE NOT NULL,
    description VARCHAR(500),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Per rimborso km
    km_traveled DECIMAL(8,2),
    
    receipt_path VARCHAR(500),
    
    is_approved BOOLEAN,
    rejection_reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Schema: `config` (Configurazione Dinamica)

### Tabella: `system_config`
```sql
CREATE TABLE config.system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    value_type VARCHAR(20) NOT NULL,    -- 'string', 'integer', 'boolean', 'float', 'json'
    category VARCHAR(50) NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_system_config_key ON config.system_config(key);
CREATE INDEX idx_system_config_category ON config.system_config(category);
```

### Tabella: `leave_types`
```sql
CREATE TABLE config.leave_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,   -- 'FER', 'ROL', 'MAL'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Comportamento
    scales_balance BOOLEAN DEFAULT TRUE,
    balance_type VARCHAR(20),           -- 'vacation', 'rol', 'permits', NULL
    requires_approval BOOLEAN DEFAULT TRUE,
    requires_attachment BOOLEAN DEFAULT FALSE,
    requires_protocol BOOLEAN DEFAULT FALSE,
    
    -- Policy
    min_notice_days INTEGER DEFAULT 0,
    max_consecutive_days INTEGER,
    max_per_month INTEGER,
    allow_past_dates BOOLEAN DEFAULT FALSE,
    allow_half_day BOOLEAN DEFAULT TRUE,
    allow_negative_balance BOOLEAN DEFAULT FALSE,
    
    -- UI
    color VARCHAR(7) DEFAULT '#3B82F6',
    icon VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `policy_rules`
```sql
CREATE TABLE config.policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,     -- 'leave_validation', 'approval_flow', 'notification'
    conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `holidays`
```sql
CREATE TABLE config.holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    name VARCHAR(100) NOT NULL,
    location_id UUID REFERENCES auth.locations(id), -- NULL = nazionale
    is_national BOOLEAN DEFAULT TRUE,
    year INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(date, location_id)
);

CREATE INDEX idx_holidays_year ON config.holidays(year);
CREATE INDEX idx_holidays_date ON config.holidays(date);
```

### Tabella: `expense_types`
```sql
CREATE TABLE config.expense_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),               -- 'transport', 'lodging', 'meals', 'other'
    max_amount DECIMAL(10,2),
    requires_receipt BOOLEAN DEFAULT TRUE,
    km_reimbursement_rate DECIMAL(4,2), -- Per tipo 'AUT'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella: `daily_allowance_rules`
```sql
CREATE TABLE config.daily_allowance_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    destination_type VARCHAR(20) NOT NULL, -- 'national', 'eu', 'extra_eu'
    full_day_amount DECIMAL(8,2) NOT NULL,
    half_day_amount DECIMAL(8,2) NOT NULL,
    threshold_hours INTEGER DEFAULT 8,
    meals_deduction DECIMAL(8,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Schema: `audit` (Tracciabilità)

### Tabella: `audit_logs`
```sql
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(50) NOT NULL,        -- 'create', 'update', 'delete', 'approve', 'reject'
    entity_type VARCHAR(50) NOT NULL,   -- 'leave_request', 'expense_report', 'user'
    entity_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit.audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit.audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit.audit_logs(created_at);
```

---

## Diagramma ERD Semplificato

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │     areas       │       │   locations     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id              │──┐    │ id              │       │ id              │
│ email           │  │    │ name            │       │ name            │
│ role            │  │    │ manager_id ─────┼───────│ patron_saint    │
│ is_approver     │  │    └─────────────────┘       └─────────────────┘
│ line_manager_id │  │              │
│ contract_type_id│  │    ┌─────────┴─────────┐
│ work_schedule_id│  │    │   user_areas      │
│ location_id     │  │    ├───────────────────┤
└─────────────────┘  └────│ user_id           │
                          │ area_id           │
                          └───────────────────┘

┌─────────────────┐       ┌─────────────────┐
│ leave_requests  │       │ leave_balances  │
├─────────────────┤       ├─────────────────┤
│ id              │       │ id              │
│ user_id    ─────┼───────│ user_id         │
│ leave_type_id   │       │ year            │
│ start_date      │       │ vacation_*      │
│ end_date        │       │ rol_*           │
│ status          │       │ permits_*       │
│ approver_id     │       └─────────────────┘
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ business_trips  │───────│ expense_reports │───────│ expense_items   │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id              │       │ id              │       │ id              │
│ user_id         │       │ user_id         │       │ expense_report_id
│ destination     │       │ trip_id         │       │ expense_type_id │
│ start_date      │       │ status          │       │ amount          │
│ status          │       │ total_amount    │       │ receipt_path    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```
