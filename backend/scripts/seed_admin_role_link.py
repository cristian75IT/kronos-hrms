import asyncio
import uuid
from sqlalchemy import text
from src.core.database import async_session_factory

async def fix_user_role():
    async with async_session_factory() as session:
        user_id = '3a5b855c-e426-42e0-a51a-210fc1ac3f61'
        role_name = 'admin'
        
        print(f"Assigning role '{role_name}' to user {user_id}...")
        
        # Check if exists
        result = await session.execute(
            text("SELECT 1 FROM auth.user_roles WHERE user_id = :uid AND role_name = :role"),
            {"uid": user_id, "role": role_name}
        )
        if result.scalar():
            print("Role already assigned.")
        else:
            new_id = uuid.uuid4()
            await session.execute(
                text("INSERT INTO auth.user_roles (id, user_id, role_name, scope) VALUES (:id, :uid, :role, 'GLOBAL')"),
                {"id": new_id, "uid": user_id, "role": role_name}
            )
            await session.commit()
            print("Role assigned successfully.")

if __name__ == "__main__":
    asyncio.run(fix_user_role())
