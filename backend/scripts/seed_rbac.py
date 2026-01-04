import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select
from src.core.database import async_session_factory
from src.services.auth.models import Role, Permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define System Roles
ROLES = [
    {"name": "admin", "display_name": "System Administrator", "description": "Full access to all resources", "is_system": True},
    {"name": "hr", "display_name": "HR Manager", "description": "Manage users, leaves, and contracts", "is_system": True},
    {"name": "manager", "display_name": "Manager", "description": "Manage team and approvals", "is_system": True},
    {"name": "approver", "display_name": "Approver", "description": "Can approve requests", "is_system": True},
    {"name": "employee", "display_name": "Employee", "description": "Standard access", "is_system": True},
]

# Define System Permissions
PERMISSIONS = [
    # Users
    {"code": "users:read", "resource": "User", "action": "READ", "name": "View Users", "description": "View user profiles list"},
    {"code": "users:create", "resource": "User", "action": "CREATE", "name": "Create User", "description": "Create new users"},
    {"code": "users:update", "resource": "User", "action": "UPDATE", "name": "Update User", "description": "Update user details"},
    {"code": "users:delete", "resource": "User", "action": "DELETE", "name": "Delete User", "description": "Deactivate/Delete users"},
    
    # Roles
    {"code": "roles:read", "resource": "Role", "action": "READ", "name": "View Roles", "description": "View roles and permissions"},
    {"code": "roles:update", "resource": "Role", "action": "UPDATE", "name": "Manage Permissions", "description": "Assign permissions to roles"},
    
    # Leaves
    {"code": "leaves:read", "resource": "Leave", "action": "READ", "name": "View Leaves", "description": "View leave requests"},
    {"code": "leaves:create", "resource": "Leave", "action": "CREATE", "name": "Request Leave", "description": "Submit leave requests"},
    {"code": "leaves:approve", "resource": "Leave", "action": "APPROVE", "name": "Approve Leaves", "description": "Approve/Reject leaves"},
    {"code": "leaves:manage", "resource": "Leave", "action": "MANAGE", "name": "Manage Leaves", "description": "Force update/cancel leaves"},
    
    # Trips
    {"code": "trips:read", "resource": "Trip", "action": "READ", "name": "View Trips", "description": "View business trips"},
    {"code": "trips:create", "resource": "Trip", "action": "CREATE", "name": "Request Trip", "description": "Submit trip requests"},
    {"code": "trips:approve", "resource": "Trip", "action": "APPROVE", "name": "Approve Trips", "description": "Approve/Reject trips"},
    
    # Expenses
    {"code": "expenses:read", "resource": "Expense", "action": "READ", "name": "View Expenses", "description": "View expense reports"},
    {"code": "expenses:create", "resource": "Expense", "action": "CREATE", "name": "Submit Expense", "description": "Submit expense reports"},
    {"code": "expenses:approve", "resource": "Expense", "action": "APPROVE", "name": "Approve Expenses", "description": "Approve/Reject expenses"},
    
    # HR Console
    {"code": "hr:access", "resource": "HR", "action": "ACCESS", "name": "Access HR Console", "description": "View HR dashboard"},
    {"code": "hr:reports", "resource": "HR", "action": "REPORT", "name": "View Reports", "description": "View attendance reports"},
    {"code": "contracts:manage", "resource": "Contract", "action": "MANAGE", "name": "Manage Contracts", "description": "Manage employee contracts"},
    
    # Calendars
    {"code": "calendar:manage", "resource": "Calendar", "action": "MANAGE", "name": "Manage Calendar", "description": "Manage system holidays/closures"},
    
    # Settings
    {"code": "settings:read", "resource": "Settings", "action": "READ", "name": "View Settings", "description": "View system configuration"},
    {"code": "settings:update", "resource": "Settings", "action": "UPDATE", "name": "Update Settings", "description": "Update system configuration"},
]

async def seed_rbac():
    """Seed Roles and Permissions."""
    async with async_session_factory() as session:
        # 1. Seed Roles
        logger.info("Seeding Roles...")
        for role_data in ROLES:
            result = await session.execute(select(Role).where(Role.name == role_data["name"]))
            role = result.scalar_one_or_none()
            
            if not role:
                logger.info(f"Creating role: {role_data['name']}")
                role = Role(
                    id=uuid4(),
                    **role_data
                )
                session.add(role)
            else:
                logger.info(f"Role exists: {role_data['name']}")
        
        await session.flush()
        
        # 2. Seed Permissions
        logger.info("Seeding Permissions...")
        for perm_data in PERMISSIONS:
            result = await session.execute(select(Permission).where(Permission.code == perm_data["code"]))
            perm = result.scalar_one_or_none()
            
            if not perm:
                logger.info(f"Creating permission: {perm_data['code']}")
                perm = Permission(
                    id=uuid4(),
                    **perm_data
                )
                session.add(perm)
            else:
                 # Update if needed (optional)
                 pass
                 
        await session.commit()
        logger.info("RBAC Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed_rbac())
