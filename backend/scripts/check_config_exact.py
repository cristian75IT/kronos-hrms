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
        key = 'approval.auto_escalate'
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        res = await session.execute(stmt)
        config = res.scalar_one_or_none()
        if config:
            print(f"Found EXACT key: {config.key} (len: {len(config.key)})")
        else:
            print(f"Key NOT found: {key}")

if __name__ == "__main__":
    asyncio.run(check())
