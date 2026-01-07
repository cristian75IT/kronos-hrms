
import asyncio
from uuid import UUID
from sqlalchemy import select, text
from src.core.database import async_session_factory, get_db_context, init_db
from src.services.leaves.models import LeaveRequest, LeaveRequestStatus
from src.services.leaves.wallet.models import WalletTransaction

async def diagnose():
    await init_db()
    async with get_db_context() as session:
        # 1. Count all requests
        stmt = select(LeaveRequest)
        result = await session.execute(stmt)
        all_reqs = result.scalars().all()
        print(f"Total Leave Requests in DB: {len(all_reqs)}")
        
        for req in all_reqs:
            print(f"  ID: {req.id}, Status: {req.status}, User: {req.user_id}, Deducted: {req.balance_deducted}")

        # 2. Count wallet transactions
        stmt = select(WalletTransaction)
        result = await session.execute(stmt)
        txns = result.scalars().all()
        print(f"\nTotal Wallet Transactions: {len(txns)}")
        for t in txns:
            print(f"  Txn ID: {t.id}, Type: {t.transaction_type}, Amount: {t.amount}, Ref: {t.reference_id}")

if __name__ == "__main__":
    asyncio.run(diagnose())
