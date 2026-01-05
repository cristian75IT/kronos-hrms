
import asyncio
import sys
import os
from sqlalchemy import text
from uuid import UUID

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.database import get_db_context

async def main():
    req_id = "6f755b95-6d14-422f-9bf6-cc1b04720f11"
    async with get_db_context() as session:
        print(f"Reverting request {req_id} to DRAFT...")
        await session.execute(
            text("UPDATE leave_requests SET status = 'DRAFT' WHERE id = :id"),
            {"id": req_id}
        )
        await session.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
