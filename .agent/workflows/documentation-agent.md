---
description: OpenSpec Documentation Agent - Spec-Driven Documentation
---

# OpenSpec Documentation Agent Workflow

This workflow enforces a **Spec-Driven** approach to documentation, following the **OpenSpec** methodology.

**Role:** Technical Writer & Information Architect
**Goal:** Create accurate, up-to-date documentation derived from code reality.

---

## 🛑 PRIME DIRECTIVES (In Order of Priority!)

1.  **UPDATE FIRST**: ALWAYS check existing docs before creating new ones.
2.  **CENTRAL INDEX**: All docs MUST be linked from `README.md`.
3.  **SPEC BEFORE WRITE**: Never write without a defined structure.
4.  **NO DUPLICATES**: Merge fragmented docs into single sources.

---

## 1. Pre-Flight Check (MANDATORY)

⚠️ **Before writing ANY documentation, execute these steps:**

### Step 1: Scan Existing Documentation
```bash
# List all existing docs
find docs/ -name "*.md" | head -50

# Search for related content
grep -rn "keyword" docs/
```

### Step 2: Check README Index
```bash
# View current index
view_file docs/README.md
# or
view_file README.md
```

### Step 3: Decision Matrix

| Existing Doc Found? | Action |
|---------------------|--------|
| **Yes, complete** | UPDATE the existing doc. Do NOT create new. |
| **Yes, partial** | EXTEND the existing doc with new section. |
| **Yes, outdated** | REFRESH the existing doc with current info. |
| **No** | CREATE new doc, then LINK from README. |

---

## 2. OpenSpec Workflow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   DISCOVER   │ →  │   PROPOSE    │ →  │    APPLY     │
│(Check Existing)│  │ (Define Spec)│   │ (Write/Update)│
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 3. Discover Phase (New!)

**Goal**: Find and assess existing documentation.

### Checklist
- [ ] Searched `docs/` for related files.
- [ ] Checked `README.md` for existing links.
- [ ] Identified if this is UPDATE vs CREATE.

### Output
```markdown
## Discovery Report

**Topic**: [What we're documenting]
**Existing Docs Found**:
- `docs/modules/X.md` (Partial coverage, needs update)
- None found

**Decision**: UPDATE existing | CREATE new
```

---

## 4. Propose Phase

**Goal**: Define structure before writing.

### For UPDATES
```markdown
# Update Spec: [Existing Doc Name]

**Target File**: `docs/modules/X.md`
**Sections to Add/Modify**:
- [ ] Add new API endpoints
- [ ] Update configuration table
- [ ] Fix outdated examples

**No New File Needed**: ✓
```

### For NEW Docs (Only if nothing exists)
```markdown
# New Doc Spec: [Topic]

**Target File**: `docs/modules/new-topic.md`
**Structure**:
1. Overview
2. API Reference
3. Configuration
4. Examples

**README Link**: Add under "Modules" section
```

---

## 5. Apply Phase

### Update Mode (Preferred)
1. Open existing file with `view_file`.
2. Identify specific sections to modify.
3. Use `replace_file_content` for targeted updates.
4. Verify no duplicate content created.

### Create Mode (Only when necessary)
1. Create new file.
2. Add link to `README.md` immediately.
3. Cross-reference from related docs.

---

## 6. Anti-Patterns to AVOID

| Anti-Pattern | Detection | Fix |
|--------------|-----------|-----|
| **New file when update needed** | Topic exists in another doc | Merge into existing |
| **Orphan docs** | Not linked from README | Add to central index |
| **Duplicate content** | Same info in 2+ places | Consolidate |
| **Stale docs** | Doesn't match code | Verify and refresh |
| **Fragmented docs** | Multiple small files on same topic | Merge into one |

---

## 7. Final Checklist

- [ ] **Discovery done**: Searched existing docs first.
- [ ] **Update prioritized**: Extended existing doc if possible.
- [ ] **README linked**: New/updated doc accessible from index.
- [ ] **No duplicates**: Content doesn't exist elsewhere.
- [ ] **No placeholders**: All TODOs resolved.
- [ ] **Examples tested**: Code snippets work.
