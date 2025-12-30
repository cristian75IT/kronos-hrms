---
description: Read KRONOS documentation before any development task
---

# KRONOS Documentation Workflow

**IMPORTANT**: This workflow MUST be executed before starting any development task on the KRONOS project.

## Step 1: Read Project Overview

Always read the main project document first:

```
view_file /Users/cristian/Desktop/app-gestione-presenze/progetto.md
```

This contains:
- 9 architectural principles (MUST follow)
- Microservices architecture
- Technology stack
- Business rules overview

## Step 2: Read Architecture (for infrastructure/networking tasks)

```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/architecture.md
```

Key topics:
- Network isolation (kronos-internal, kronos-external)
- Nginx + ModSecurity configuration
- Audit system (audit_logs, audit_trail)
- Service ports and routing

## Step 3: Read Relevant Module Documentation

Based on the task, read the specific module:

### For Authentication/Users:
```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/modules/auth.md
```

### For Leave Requests/Balances:
```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/modules/leaves.md
```

### For Expenses/Trips:
```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/modules/expenses.md
```

### For Configuration/Settings:
```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/modules/config.md
```

### For Email/Notifications:
```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/modules/notifications.md
```

## Step 4: Read Database Schema (for any DB work)

```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/database/schema.md
```

## Step 5: Read Business Rules (for leave/compliance logic)

```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/business/leave-policies.md
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/business/compliance-italy.md
```

## Step 6: Read Coding Standards (before writing code)

```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/development/coding-standards.md
```

## Step 7: Read Tech Stack (for library choices)

```
view_file /Users/cristian/Desktop/app-gestione-presenze/docs/tech-stack.md
```

Key requirements:
- DataTables.net for ALL tables (server-side pagination)
- FullCalendar for ALL calendars
- Brevo for ALL emails
- Keycloak for ALL authentication
- NEVER create custom components when standard libraries exist

---

## CRITICAL PRINCIPLES TO REMEMBER

After reading documentation, always verify:

1. **Zero Hardcoding**: All business values must come from `system_config` table
2. **Database Schema Isolation**: Each microservice uses its own PostgreSQL schema
3. **SSO Only**: Authentication through Keycloak, NEVER custom auth
4. **Server-Side DataTables**: NEVER load all data to frontend
5. **Audit Everything**: All actions must be logged to audit schema
6. **Clean Architecture**: Router → Service → Repository → Model
7. **Type Safety**: Type hints required on all public methods
8. **Async First**: Use async SQLAlchemy and FastAPI endpoints
