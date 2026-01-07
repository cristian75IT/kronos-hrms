# Changelog: Approvals Service & Workflow Logic Fixes

**Date:** 2026-01-07
**Components:** `kronos-approvals`, `Database`

## 🐛 Bug Fixes

### 1. Workflow Selection Priority
- **Issue:** The "Approvazione Ferie Manager" workflow was being selected for all leave requests because it had a higher priority (90) than "Standard" (100) and no conditions, acting as a catch-all before the actual default.
- **Fix:** Increased "Approvazione Ferie Manager" priority to 110 (lower precedence) and added a condition `target_roles: ["manager"]` to restrict its scope.

### 2. Missing Approver Assignment
- **Issue:** Approval requests were created with status `PENDING` but no approvers were assigned (empty `approval_decisions` table).
- **Root Cause:**
    - Workflow configurations in the database had empty `approver_role_ids`.
    - The `create_approval_request` logic called `assign_approvers` directly without first resolving the User IDs from the configured Role IDs via the Auth Service.
- **Fix:**
    - Updated database `workflow_configs` to include correct `approver_role_ids`.
    - Updated `src/services/approvals/services/requests.py` to fetching users from `AuthClient` using the configured role before calling `assign_approvers`.

### 3. Missing User Roles
- **Issue:** The single user in the database did not have `manager`, `hr`, or `admin` roles, preventing any approver resolution.
- **Fix:** Manually inserted role assignments for the default user in `auth.user_roles`.

## 🛠️ Technical Details

### Code Changes
- **`backend/src/services/approvals/services/requests.py`**:
    - Added logic in `create_approval_request` to iterate over `config.approver_role_ids`.
    - Implemented calls to `self._auth_client.get_users_by_role(id)` to resolve actual users.
    - Added filtering to prevent self-approval (unless configured) and duplicates.

### SQL Migration (Manual)
```sql
-- Update Workflow Configs with correct roles
UPDATE approvals.workflow_configs SET approver_role_ids = '["05d822c3-8bde-44e6-87d4-2d8b0ca24bfd"]' WHERE name = 'Approvazione Ferie Standard';
-- (Repeated for other workflows...)

-- Fix Priority and Conditions
UPDATE approvals.workflow_configs SET priority = 110, conditions = '{"target_roles": ["manager"]}' WHERE name = 'Approvazione Ferie Manager';

-- Assign Roles to User (Dev Environment)
INSERT INTO auth.user_roles ... VALUES ... ('admin', 'manager', 'hr', 'approver');
```

## ✅ Verification
- Successfully created a Leave Request via `curl` simulation.
- Confirmed `approval_decisions` record creation linked to the user.
- Verified `PENDING` status and correct workflow selection.
