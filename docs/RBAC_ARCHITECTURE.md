# Dynamic Scoped RBAC Architecture

KRONOS implements a robust, enterprise-grade Role-Based Access Control (RBAC) system that supports role inheritance and contextual (scoped) permissions.

## Core Concepts

### 1. Permissions
A permission defines a specific action that can be performed on a resource.
- **Permission Code**: A unique identifier like `leaves:approve`, `users:manage`, `audit:view`.

### 2. Scopes
Every permission in the system is associated with a scope. This allows for fine-grained access control based on the context of the resource.
- **GLOBAL**: Full access to all resources of that type across the entire system.
- **AREA**: Access to resources within the user's assigned area (or sub-areas).
- **OWN**: Access only to resources owned by or assigned to the specific user.

Permissions are represented as `code:scope` strings (e.g., `leaves:view:AREA`).

### 3. Roles and Inheritance
Roles are collections of permissions. KRONOS supports role hierarchy where a child role inherits all permissions from its parent.
- **Higher-level roles** (like `admin`) inherit from **lower-level roles** (like `manager`).
- This simplifies management and ensures consistency.

### 4. Key Components

#### Backend Service-Level Security
The system uses a shared `require_permission` decorator in `backend/src/core/security.py`.
```python
@router.post("/approve", dependencies=[Depends(require_permission("leaves:approve", scope="AREA"))])
async def approve_leave(...):
    ...
```

#### Frontend Identity Resolution
The `AuthContext` provides a `hasPermission` helper that takes inheritance and scopes into account.
```typescript
const { hasPermission } = useAuth();

if (hasPermission('leaves:approve', 'AREA')) {
  return <Button>Approve</Button>;
}
```

## Developer Guide

### How to Add a New Permission
1. Define the permission in the `auth` database:
   ```sql
   INSERT INTO auth.permissions (code, name, description) VALUES ('custom:action', 'Custom Action', 'Allows custom action');
   ```
2. Assign it to a role with a specific scope in `auth.role_permissions`.

### How to Define Role Hierarchies
Use the `parent_id` column in the `auth.roles` table to link a child role to its parent.

### Checking Permissions
- **Backend**: Use the `TokenPayload.has_permission(code, scope)` method.
- **Frontend**: Use the `useAuth().hasPermission(code, scope)` hook.

---
*Last Updated: January 2026*
