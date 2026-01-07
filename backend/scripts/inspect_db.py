
import asyncio
from sqlalchemy import text
from src.core.database import get_db_context, init_db

async def inspect_columns():
    await init_db()
    async with get_db_context() as session:
        # Check leaves schema
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'leaves' AND table_name = 'leave_requests'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result.all()]
        print(f"Columns in leaves.leave_requests: {columns}")
        
        # Check public schema
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'leave_requests'
            ORDER BY ordinal_position
        """))
        public_columns = [row[0] for row in result.all()]
        if public_columns:
            print(f"WARNING: leave_requests table ALSO exists in PUBLIC schema! Columns: {public_columns}")
        else:
            print("No leave_requests table in public schema.")

if __name__ == "__main__":
    asyncio.run(inspect_columns())
