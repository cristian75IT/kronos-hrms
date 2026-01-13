---
description: Enterprise Database & Migration Agent
---

# Enterprise Database Agent Workflow

This workflow manages the **Database-per-Service** architecture, **Alembic Migrations**, and **Data Seeding**.

**Role:** Database Administrator / Backend Lead
**Goal:** Safe, isolated, and auditable database changes.

---

## 🛑 PRIME DIRECTIVES

1.  **DATABASE-PER-SERVICE**: Each service owns its schema. NO cross-schema queries.
2.  **MIGRATION SAFETY**: Always review generated migrations before applying.
3.  **NO RAW SQL**: Except in Repository layer with `text()` binding.

---

## 1. Architecture Overview

```
kronos (database)
├── auth          # Auth service schema
├── leaves        # Leave service schema
├── expenses      # Expense service schema
├── config        # Config service schema
├── notifications # Notification service schema
├── calendar      # Calendar service schema
├── audit         # Audit service schema (READ-ONLY for other services)
└── ...
```

**Rule**: Services communicate via HTTP, NOT via DB joins.

---

## 2. Migration Workflow (Alembic)

### Step 1: Create Migration
```bash
# Set target schema
export DATABASE_SCHEMA={schema_name}

# Generate migration
alembic revision --autogenerate -m "describe change"
```

### Step 2: Review Migration

⚠️ **CRITICAL**: Always review the generated file!

| Check | Action |
|-------|--------|
| `DROP TABLE` | Verify data backup exists. |
| `ALTER COLUMN` | Verify no data loss. |
| `CREATE INDEX` | Verify it won't lock table too long. |
| FK References | Verify it's within SAME schema. |

### Step 3: Apply Migration
```bash
export DATABASE_SCHEMA={schema_name}
alembic upgrade head
```

### Step 4: Rollback (if needed)
```bash
alembic downgrade -1
```

---

## 3. Seeding Workflow

### Locate Scripts
```
backend/scripts/
├── seed_leave_types.py
├── seed_contracts.py
├── seed_trips_expenses.py
└── ...
```

### Execute Seed
```bash
python backend/scripts/{script_name}.py
```

### Best Practices

| Rule | Description |
|------|-------------|
| **Idempotent** | Seeds should be re-runnable without duplicates. |
| **Minimal** | Only seed essential data. |
| **Documented** | Each script has a docstring explaining purpose. |

---

## 4. Schema Isolation Verification

### Check for Cross-Schema References
```bash
# Grep for potential violations
grep -rn "FROM auth\." src/services/leaves/
grep -rn "FROM leaves\." src/services/expenses/
```

**Expected Result**: No matches (each service only queries its own schema).

---

## 5. Performance Considerations

| Action | Guideline |
|--------|-----------|
| **Indexes** | Add indexes on frequently filtered columns (`user_id`, `created_at`). |
| **Bulk Operations** | Use `bulk_insert_mappings` for large inserts. |
| **Pagination** | All list queries MUST use `LIMIT` + `OFFSET`. |

---

## 6. Final Checklist

- [ ] Migration reviewed and safe.
- [ ] No cross-schema references.
- [ ] Indexes added for query performance.
- [ ] Seeds are idempotent.
- [ ] Rollback tested.
