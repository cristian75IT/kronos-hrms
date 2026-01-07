
import asyncio
from uuid import UUID
from src.core.database import get_db_context, init_db
from src.services.leaves.services import LeaveService
from src.services.leaves.schemas import AcceptConditionRequest
from sqlalchemy import select
from src.services.leaves.wallet.models import WalletTransaction

async def verify():
    await init_db()
    leave_id = UUID("3c52ca26-c2c0-462e-9413-a08bb900185e")
    user_id = UUID("b5cd12c2-b314-4ed2-9b09-21715f4c0d2b")
    
    async with get_db_context() as session:
        service = LeaveService(session)
        print(f"Accepting conditions for leave {leave_id}...")
        
        try:
            await service.accept_condition(
                id=leave_id,
                user_id=user_id,
                data=AcceptConditionRequest(accept=True)
            )
            print("Conditions accepted successfully.")
        except Exception as e:
            print(f"Acceptance failed: {e}")
            
        print("\nChecking for wallet transactions...")
        stmt = select(WalletTransaction).where(WalletTransaction.reference_id == leave_id)
        result = await session.execute(stmt)
        txs = result.scalars().all()
        
        if txs:
            print(f"Found {len(txs)} transactions:")
            for tx in txs:
                print(f"  ID: {tx.id}, Type: {tx.transaction_type}, Amount: {tx.amount}, Ref: {tx.reference_id}")
        else:
            print("No transactions found for this leave request.")

if __name__ == "__main__":
    asyncio.run(verify())
