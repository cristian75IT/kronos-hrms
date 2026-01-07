
import asyncio
from uuid import UUID
from sqlalchemy import select, text
from src.core.database import get_db_context, init_db
from src.services.approvals.models import ApprovalRequest, ApprovalStatus

async def diagnose():
    await init_db()
    async with get_db_context() as session:
        # 1. Count all approval requests
        stmt = select(ApprovalRequest).where(ApprovalRequest.entity_type == "LEAVE")
        result = await session.execute(stmt)
        all_reqs = result.scalars().all()
        print(f"Total Approval Requests (LEAVE) in DB: {len(all_reqs)}")
        
        for req in all_reqs:
            print(f"  ID: {req.id}, Status: {req.status}, EntityID: {req.entity_id}, Requester: {req.requester_name}")

if __name__ == "__main__":
    asyncio.run(diagnose())
