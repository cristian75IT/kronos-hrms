import asyncio
import sys
import os

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.config.models import SystemConfig
from sqlalchemy import select

async def check():
    async with get_db_context() as session:
        stmt = select(SystemConfig).where(SystemConfig.key.like('approval.%'))
        res = await session.execute(stmt)
        configs = res.scalars().all()
        print(f"Found {len(configs)} approval configs:")
        for c in configs:
            print(f"  - {c.key}: {c.value} ({c.value_type})")

if __name__ == "__main__":
    asyncio.run(check())
