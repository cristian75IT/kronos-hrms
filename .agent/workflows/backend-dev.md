---
description: Enterprise Backend Development Workflow
---

# Enterprise Backend Agent Workflow

This workflow enforces **strict code quality** and adherence to the **Enterprise Backend Rules** defined in `.agent/RULES.md`.

**Role:** Senior Backend Architect (FastAPI/Python).

---

## 🛑 PRIME DIRECTIVES (Read First!)

Before ANY coding, internalize these non-negotiable rules:

1.  **NO HARDCODING**: All values from ENV/DB. Never hardcode URLs, credentials, or magic numbers.
2.  **CLEAN ARCHITECTURE**: `Router` → `Service` → `Repository` → `Model`. Never skip layers.
3.  **DATABASE-PER-SERVICE**: Each microservice owns its schema. NO cross-schema queries.
4.  **AUDIT TRAIL**: Every write operation MUST log to `audit.logs`.
5.  **TYPE SAFETY**: 100% Type Hints. `Any` is forbidden.

---

## 1. Context & Compliance Check
1.  **Read Rules**: `view_file .agent/RULES.md` (focus on backend sections).
2.  **Review Architecture**: Understand existing services in `docker-compose.yml`.

---

## 2. Planning Phase
1.  **Analyze Request**: Identify the target service/domain.
2.  **Microservice Check**:
    -   **New Service?** Requires new schema, Dockerfile entry, Nginx route.
    -   **Shared DB?** STOP. Create a Trade-off Analysis document first.
3.  **Output**: Update `implementation_plan.md`.

---

## 3. Implementation Checklist (Strict Layer by Layer)

### A. Data Layer (`models.py` & `repository.py`)

| Rule | Description |
|------|-------------|
| **Single Responsibility** | One Model per Entity. Max ~100 lines per file. |
| **ORM Only** | NO Raw SQL in Repository. Use SQLAlchemy ORM. |
| **Encapsulation** | If Raw SQL is absolutely needed for performance, use `text()` with bound params. |
| **No Business Logic** | Repository only handles data access. Calculations belong in Service. |

**Checklist**:
- [ ] Models defined with full type hints.
- [ ] Repositories use `async def` for all methods.
- [ ] NO `import` of `Service` classes here (no circular deps).

### B. Business Logic (`service.py`)

| Rule | Description |
|------|-------------|
| **Purity** | Service contains ONLY business rules. No HTTP, no SQLAlchemy imports. |
| **Audit Trail** | Every `create`/`update`/`delete` MUST call `audit_service.log(...)`. |
| **Error Handling** | Catch specific exceptions, raise custom `BusinessException`. |
| **Max Complexity** | Methods should be < 20 lines. Refactor long methods into private helpers. |

**Checklist**:
- [ ] Audit log inserted for every write.
- [ ] No direct DB session usage (use Repository).
- [ ] Methods are well-named and focused (SRP).

### C. Interface Layer (`router.py` & `schemas.py`)

| Rule | Description |
|------|-------------|
| **Thin Router** | Router only parses HTTP and calls Service. NO logic. |
| **Pydantic Everywhere** | All Request/Response use Pydantic schemas. |
| **Security** | EVERY endpoint uses `Depends(require_permission(...))`. |
| **OpenAPI** | Use `summary`, `description`, `response_model` for docs. |

**Checklist**:
- [ ] Schemas define strict types (no `Optional` without default).
- [ ] Router uses `APIRouter` prefix correctly.
- [ ] Responses wrapped in standard format `{"data": ..., "meta": ...}`.

### D. Configuration (`core/config.py`)

| Rule | Description |
|------|-------------|
| **Pydantic Settings** | Use `BaseSettings` for all config. |
| **No Secrets in Code** | Use `get_vault_secret()` for sensitive data. |

---

## 4. Code Quality Gates (Mandatory Before PR)

### 🧹 Cleanup Rules

| Anti-Pattern | Action |
|--------------|--------|
| **Dead Code** | Remove unused imports, functions, variables. |
| **Commented Code** | Delete it. Use Git history. |
| **Duplicated Logic** | Extract to `shared/utils.py` or base class. |
| **Monolithic Files** | Split files > 300 lines into logical modules. |
| **Scattered Classes** | Group related classes in same module or `__init__.py`. |

### 📏 File Size Limits

| File Type | Max Lines | Action if Exceeded |
|-----------|-----------|-------------------|
| `router.py` | 200 | Split into sub-routers. |
| `service.py` | 300 | Split by subdomain (e.g., `leave_service.py`, `balance_service.py`). |
| `repository.py` | 250 | Split into base + specialized repos. |
| `schemas.py` | 200 | Group by domain or use `schemas/` folder. |

### ✅ Verification Commands
```bash
# Type check
mypy src/services/{service}/

# Linting
ruff check src/services/{service}/

# Tests
pytest src/services/{service}/ -v
```

---

## 5. Final Checklist

- [ ] All layers respect their responsibility (no leaking).
- [ ] Audit Trail implemented for writes.
- [ ] File sizes under limits.
- [ ] No `Any` types.
- [ ] No hardcoded values.
- [ ] Dead code removed.
- [ ] Docs updated if architecture changed.
