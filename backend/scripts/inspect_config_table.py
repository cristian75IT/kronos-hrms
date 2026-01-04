import asyncio
import sys
import os
from sqlalchemy import text

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context

async def inspect():
    async with get_db_context() as session:
        # Check table columns
        res = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'config' AND table_name = 'system_config'"))
        print("Columns in config.system_config:")
        for row in res:
            print(f"  - {row[0]}: {row[1]}")
            
        # Check all values of 'key'
        res = await session.execute(text("SELECT key, length(key), value_type FROM config.system_config"))
        print("\nAll config keys:")
        for row in res:
            print(f"  - '{row[0]}' (len: {row[1]}, type: {row[2]})")

if __name__ == "__main__":
    asyncio.run(inspect())
