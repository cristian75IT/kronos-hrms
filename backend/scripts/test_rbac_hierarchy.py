"""KRONOS - Test RBAC Hierarchy and Inheritance."""
import asyncio
import uuid
from sqlalchemy import select
from src.core.database import async_session_factory
from src.services.auth.models import Role, Permission, RolePermission
from src.services.auth.repository import RoleRepository

async def test_hierarchy():
    async with async_session_factory() as session:
        repo = RoleRepository(session)
        
        # 1. Clear existing roles/perms mapping for clean test
        # await session.execute(delete(RolePermission))
        # await session.commit()
        
        # 2. Get or Create roles
        roles_data = {
            "employee": "Dipendente",
            "manager": "Responsabile",
            "hr_manager": "HR Manager",
            "admin": "Amministratore"
        }
        
        db_roles = {}
        for name, display in roles_data.items():
            role = (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
            if not role:
                role = Role(id=uuid.uuid4(), name=name, display_name=display)
                session.add(role)
            db_roles[name] = role
        
        await session.commit()
        for r in db_roles.values(): await session.refresh(r)
        
        # 3. Setup Hierarchy
        # hr_manager -> manager -> employee
        db_roles["hr_manager"].parent_id = db_roles["manager"].id
        db_roles["manager"].parent_id = db_roles["employee"].id
        
        await session.commit()
        print("Hierarchy set: hr_manager -> manager -> employee")
        
        # 4. Map Permissions
        # We need some permission codes
        perm_codes = ["leaves:read", "leaves:approve", "users:manage"]
        db_perms = {}
        for code in perm_codes:
            perm = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
            if not perm:
                res, act = code.split(":")
                perm = Permission(
                    id=uuid.uuid4(), 
                    code=code, 
                    resource=res.upper(), 
                    action=act.upper(), 
                    name=code
                )
                session.add(perm)
            db_perms[code] = perm
            
        await session.commit()
        for p in db_perms.values(): await session.refresh(p)
        
        # Assign
        # employee: leaves:read
        # manager: leaves:approve
        # hr_manager: users:manage
        
        # Assign with scopes
        # employee: leaves:read:OWN
        # manager: leaves:approve:AREA
        # hr_manager: users:manage:GLOBAL
        
        assignments = [
            (db_roles["employee"].id, db_perms["leaves:read"].id, "OWN"),
            (db_roles["manager"].id, db_perms["leaves:approve"].id, "AREA"),
            (db_roles["hr_manager"].id, db_perms["users:manage"].id, "GLOBAL"),
        ]
        
        for role_id, perm_id, scope in assignments:
            exists = (await session.execute(select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == perm_id,
                RolePermission.scope == scope
            ))).scalar_one_or_none()
            if not exists:
                session.add(RolePermission(role_id=role_id, permission_id=perm_id, scope=scope))
        
        await session.commit()
        print("Permissions assigned with scopes.")
        
        # 5. TEST RECURSIVE FETCH with scopes
        print("\n--- Testing Inheritance with Scopes ---")
        
        cases = [
            (["employee"], ["leaves:read:OWN"]),
            (["manager"], ["leaves:read:OWN", "leaves:approve:AREA"]),
            (["hr_manager"], ["leaves:read:OWN", "leaves:approve:AREA", "users:manage:GLOBAL"]),
        ]
        
        for input_roles, expected_perms in cases:
            actual_perms = await repo.get_permissions_for_roles(input_roles)
            print(f"Roles {input_roles} => {actual_perms}")
            missing = set(expected_perms) - set(actual_perms)
            if not missing:
                print(f"  ✅ SUCCESS: Found all expected permissions")
            else:
                print(f"  ❌ FAILURE: Missing {missing}")

if __name__ == "__main__":
    asyncio.run(test_hierarchy())
