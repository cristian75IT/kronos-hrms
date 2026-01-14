---
description: Enterprise Frontend Development Workflow
---

# Enterprise Frontend Agent Workflow

This workflow enforces **strict code quality** and adherence to the **Enterprise Frontend Rules** defined in `.agent/RULES.md`.

**Role:** Senior Frontend Architect (React/TypeScript).

---

## 🛑 PRIME DIRECTIVES (Read First!)

Before ANY coding, internalize these non-negotiable rules:

1.  **FEATURE-SLICED DESIGN**: All code organized in `src/features/{domain}/`.
2.  **SERVER STATE ≠ CLIENT STATE**: React Query for API data. Zustand for UI only.
3.  **ZOD VALIDATION**: Every form and API response validated with Zod.
4.  **DUMB COMPONENTS**: UI components receive data via props/hooks. NO logic in JSX.
5.  **TYPE SAFETY**: Strict TypeScript. `any` is forbidden.

---

## 1. Context & Compliance Check
1.  **Read Rules**: `view_file .agent/RULES.md` (focus on frontend sections).
2.  **Review Feature**: Identify target feature in `src/features/`.

---

## 2. Planning Phase
1.  **Analyze Request**: Map to existing feature or define new one.
2.  **State Strategy**:
    -   **API Data?** → React Query hook in `api/`.
    -   **UI State?** → Zustand store in `stores/`.
3.  **Output**: Update `implementation_plan.md`.

---

## 3. Implementation Checklist (Strict Layer by Layer)

### A. API Layer (`features/{domain}/api/`)

| Rule | Description |
|------|-------------|
| **React Query** | All data fetching via `useQuery`/`useMutation`. |
| **Zod Validation** | Validate API responses. Never trust backend. |
| **No useEffect** | NEVER fetch data in `useEffect`. Use Query hooks. |
| **Optimistic Updates** | Use `useMutation` with `onMutate` for UX. |

**Checklist**:
- [ ] Custom hooks created (`useUsers`, `useCreateUser`, etc.).
- [ ] Zod schemas defined for all responses.
- [ ] Error handling with `onError` callbacks.

### B. Logic Layer (`features/{domain}/hooks/`)

| Rule | Description |
|------|-------------|
| **Encapsulation** | All complex logic in custom hooks. |
| **Return Contract** | Return `{ data, actions, status }` pattern. |
| **No Side Effects** | Hooks should be predictable and testable. |

**Checklist**:
- [ ] Form logic extracted to `useXForm()` hooks.
- [ ] Calculations/transformations in dedicated hooks.
- [ ] Hooks are well-named and focused (SRP).

### C. UI Components (`features/{domain}/components/`)

| Rule | Description |
|------|-------------|
| **Dumb Components** | Receive all data via props. |
| **No Business Logic** | No API calls, no complex conditions in JSX. |
| **Composition** | Build complex UIs from small, reusable pieces. |
| **Accessibility** | Semantic HTML, ARIA labels where needed. |

**Checklist**:
- [ ] Components are purely presentational.
- [ ] Props are typed with interfaces (not inline).
- [ ] Responsive design verified (mobile + desktop).

### D. Global State (`stores/`)

| Rule | Description |
|------|-------------|
| **Zustand Only** | For client-side state (theme, sidebar, session). |
| **No Server Data** | NEVER duplicate API data here. |
| **Minimal** | Keep stores small and focused. |

---

## 4. Code Quality Gates (Mandatory Before PR)

### 🧹 Cleanup Rules

| Anti-Pattern | Action |
|--------------|--------|
| **Dead Code** | Remove unused imports, components, hooks. |
| **Commented Code** | Delete it. Use Git history. |
| **Duplicated Components** | Extract to `src/components/` (shared). |
| **Monolithic Components** | Split components > 150 lines. |
| **Inline Styles** | Move to CSS/Tailwind classes. |

### 📏 File Size Limits

| File Type | Max Lines | Action if Exceeded |
|-----------|-----------|-------------------|
| Component (`.tsx`) | 150 | Split into sub-components. |
| Hook | 100 | Split into smaller hooks. |
| API file | 150 | Group by entity or split. |
| Store | 80 | Split by domain. |

### ✅ Verification Commands
// turbo
```bash
# Type check
npm run type-check

# Linting
npm run lint

# Tests
npm run test
```

---

## 5. Final Checklist

- [ ] Feature-Sliced Design respected.
- [ ] React Query used for all API data.
- [ ] Zod schemas validate all forms/responses.
- [ ] Components are dumb (no logic in JSX).
- [ ] File sizes under limits.
- [ ] No `any` types.
- [ ] Dead code removed.
- [ ] Responsive design verified.
