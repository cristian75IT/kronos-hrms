
import asyncio
from uuid import UUID
from sqlalchemy import text
from src.core.database import get_db_context, init_db

async def check():
    await init_db()
    async with get_db_context() as session:
        res = await session.execute(text("SELECT * FROM leaves.leave_balances WHERE user_id = 'b5cd12c2-b314-4ed2-9b09-21715f4c0d2b'"))
        balances = res.mappings().all()
        for b in balances:
            print(f"Balance for Year {b['year']}:")
            print(f"  Vacation: AP={b['vacation_previous_year']}, AC={b['vacation_current_year']}, Accrued={b['vacation_accrued']}, Used={b['vacation_used']}")
            print(f"  ROL: AP={b['rol_previous_year']}, AC={b['rol_current_year']}, Accrued={b['rol_accrued']}, Used={b['rol_used']}")

if __name__ == "__main__":
    asyncio.run(check())
