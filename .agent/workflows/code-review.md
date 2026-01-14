---
description: Automated & Semantic Code Review Agent (Backend/Frontend)
---

# Code Review Agent Workflow

This workflow guides the **Deep Code Review** process. It combines **Automated Static Analysis** (Turbo) with **Semantic Architectural Review**.

**Role:** Senior Code Reviewer
**Goal:** Ensure code is secure, maintainable, and compliant with `RULES.md`.

---

## 🛑 REVIEWER MANIFESTO

1.  **Blocker over Nitpick**: Focus on Security, Architecture, and Logic bugs. Style is secondary (linters handle that).
2.  **Reference Rules**: Every critique must reference a specific rule from `.agent/RULES.md`.
3.  **Constructive**: Suggest *how* to fix, not just *what* is wrong.

---

## 1. Input Analysis

Identify the scope of the review:
-   **Backend**: `src/services/{service}/`
-   **Frontend**: `src/features/{domain}/`

---

## 2. Automated Health Check (Turbo)

Run these checks immediately to catch low-hanging fruit.

### Backend Context (Python)
// turbo
```bash
# Quick Syntax & Type Check
ruff check {path} --select E,F,W,B
mypy {path} --ignore-missing-imports
```

### Frontend Context (Typescript)
// turbo
```bash
# Type & Lint Check
npm run lint
npx tsc --noEmit
```

### Security Scan (Universal)
// turbo
```bash
# Scan for secrets and dangerous patterns
grep -rnE "password|secret|api_key|token" {path} | grep -vE "test|mock|.env"
grep -rn "TODO" {path}
```

---

## 3. Semantic Review Checklist

Manually verify these points by reading the code (`view_file`).

### 🛡️ Security & Auth
- [ ] **Permissions**: Does every endpoint have `require_permission`?
- [ ] **Input Validation**: Are Pydantic/Zod schemas strict? (No `extra="allow"` unless justified).
- [ ] **SQL Injection**: No f-strings in SQL queries?
- [ ] **Broken Object Level Authorization (BOLA)**: Does the code verify that `resource.user_id == current_user.id`?

### 🏗️ Architecture (Clean Arch)
- [ ] **Layer Violation**:
    -   *Backend*: Router imports Repository? (Should be Service).
    -   *Frontend*: component calls `fetch` directly? (Should be Custom Hook).
- [ ] **Database Isolation**: Service A querying Service B's tables? (FORBIDDEN).

### 🔍 Observability / Audit
- [ ] **Audit Trail**: Does the 'write' operation (POST/PUT/DELETE) create an Audit Log entry?
- [ ] **Error Handling**: Are specific exceptions caught? (No bare `except Exception:` without re-raise).

---

## 4. Review Report Template

Output the review in this format:

```markdown
# 🧐 Code Review Report: [Module/File Name]

## 🚦 Status
[Pass / Changes Requested / Blocked]

## 🛡️ Critical Issues (Must Fix)
1.  **[Security/Arch]**: Description.
    *   *Rule Violation*: `RULES.md` Sec 2.1
    *   *Fix*: Suggestion...

## ⚠️ Improvements (Strongly Recommended)
1.  **[Logic/Perf]**: Description.
    *   *Fix*: Suggestion...

## nit (Optional)
*   Rename variable X to Y for clarity.
```
