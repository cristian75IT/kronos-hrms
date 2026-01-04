import asyncio
import json
from uuid import UUID
from sqlalchemy import select
from src.core.database import async_session_factory
from src.services.auth.models import Role, Permission, User

async def check_data():
    async with async_session_factory() as session:
        # Check Users
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        print(f"Users found: {len(users)}")
        for u in users:
            print(f"User: {u.email} (ID: {u.id})")
            print(f"     is_admin: {u.is_admin}")
            print(f"     is_manager: {u.is_manager}, is_hr: {u.is_hr}")
            print(f"     is_employee: {u.is_employee}")

        # Check Roles
        roles_result = await session.execute(select(Role))
        roles = roles_result.scalars().all()
        print(f"Roles found: {len(roles)}")
        for r in roles:
            print(f" - {r.name} ({r.display_name})")

        # Check Permissions
        perms_result = await session.execute(select(Permission))
        perms = perms_result.scalars().all()
        print(f"Permissions found: {len(perms)}")
        # for p in perms[:5]:
        #    print(f" - {p.code}")

if __name__ == "__main__":
    asyncio.run(check_data())
