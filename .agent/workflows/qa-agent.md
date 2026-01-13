---
description: Enterprise QA & Testing Agent
---

# Enterprise QA Agent Workflow

This workflow enforces **Code Quality**, **Static Analysis**, and **Automated Testing**.

**Role:** QA Automation Engineer
**Goal:** Catch issues before they hit production.

---

## 🛑 PRIME DIRECTIVES

1.  **Type Safety First**: No `Any` (Python) or `any` (TS).
2.  **Coverage Matters**: New code requires tests.
3.  **Security Testing**: Verify RBAC enforcement.

---

## 1. Static Analysis (The "Gatekeeper")

Run these before ANY testing.

### Backend (Python)
```bash
# Type checking
mypy src/services/{service}/ --strict

# Linting & formatting
ruff check src/services/{service}/
ruff format src/services/{service}/ --check

# Import sorting
isort src/services/{service}/ --check-only
```

### Frontend (TypeScript)
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Unused exports
npx ts-prune
```

---

## 2. Testing Strategy

### A. Unit Tests (Isolated Logic)

| Layer | Scope | Mocking |
|-------|-------|---------|
| Service | Business logic | Mock Repository |
| Repository | DB queries | Use test DB |
| Hooks (FE) | Logic hooks | Mock API |

**Command**: `pytest src/services/{service}/tests/unit/`

### B. Integration Tests (API Level)

| Scope | Description |
|-------|-------------|
| Router | HTTP → Service → DB |
| Auth | Verify 401/403 responses |
| Audit | Verify audit log entries |

**Command**: `pytest src/services/{service}/tests/integration/`

### C. Frontend Tests

| Scope | Tool |
|-------|------|
| Components | Vitest + Testing Library |
| Hooks | Vitest |
| E2E | Playwright (optional) |

**Command**: `npm run test`

---

## 3. Security Testing Checklist

- [ ] **RBAC**: Verify unauthorized users get 403.
- [ ] **Injection**: Test with SQL injection payloads.
- [ ] **XSS**: Test with script injection in inputs.
- [ ] **Secrets**: Grep for hardcoded tokens/passwords.

```bash
# Grep for secrets
grep -rn "password\|secret\|api_key" src/ --include="*.py" --include="*.ts"
```

---

## 4. Code Quality Metrics

### File Size Check
```bash
# Find oversized Python files (>300 lines)
find src/ -name "*.py" -exec wc -l {} \; | awk '$1 > 300'

# Find oversized TS/TSX files (>150 lines)
find frontend/src/ -name "*.tsx" -exec wc -l {} \; | awk '$1 > 150'
```

### Dead Code Detection
```bash
# Python unused imports
ruff check src/ --select F401

# TypeScript unused exports
npx ts-prune
```

---

## 5. Final Checklist

- [ ] `mypy` / `tsc` pass with no errors.
- [ ] `ruff` / `eslint` pass with no errors.
- [ ] New code has corresponding tests.
- [ ] Security tests pass.
- [ ] No files exceed size limits.
- [ ] No dead code detected.
