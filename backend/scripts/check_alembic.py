
import asyncio
from sqlalchemy import text
from src.core.database import get_db_context, init_db

async def check_version():
    await init_db()
    async with get_db_context() as session:
        # Check in 'public' (default)
        try:
            result = await session.execute(text("SELECT version_num FROM public.alembic_version"))
            version = result.scalar()
            print(f"Current Alembic Version (public): {version}")
        except Exception:
            print("No alembic_version in public schema")
            
        # Check in 'leaves' if it exists
        try:
            result = await session.execute(text("SELECT version_num FROM leaves.alembic_version"))
            version = result.scalar()
            print(f"Current Alembic Version (leaves): {version}")
        except Exception:
            print("No alembic_version in leaves schema")

if __name__ == "__main__":
    asyncio.run(check_version())
