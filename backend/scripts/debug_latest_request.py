
import asyncio
import sys
import os
from sqlalchemy import select, text
from uuid import UUID

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.database import get_db_context
from src.core.config import settings

async def main():
    async with get_db_context() as session:
        print("--- Latest Leave Request (Checking 'leaves' schema) ---")
        
        result = await session.execute(
            text("SELECT id, status, user_id, leave_type_code, days_requested, created_at FROM leave_requests ORDER BY created_at DESC LIMIT 1")
        )
        row = result.first()
        if not row:
            print("No leave requests found.")
            return

        req_id, status, user_id, lt_code, days, created_at = row
        print(f"ID: {req_id}")
        print(f"Status: {status}")
        print(f"User: {user_id}")
        print(f"Type: {lt_code}")
        print(f"Days: {days}")
        print(f"Created: {created_at}")

        print("\n--- Decisions for this Request ---")
        decisions = await session.execute(
            text("SELECT approver_id, decision, approval_level FROM approval_decisions WHERE approval_request_id = :req_id"),
            {"req_id": req_id}
        )
        for d in decisions:
            print(f"Approver: {d.approver_id} | Level: {d.approval_level} | Decision: {d.decision}")

        print("\n--- User Info ---")
        user = await session.execute(
            text("SELECT id, email, first_name, last_name, is_admin FROM auth.users WHERE id = :uid"),
            {"uid": requester_id}
        )
        u_row = user.first()
        if u_row:
             print(f"User: {u_row.first_name} {u_row.last_name} ({u_row.email}) | Admin: {u_row.is_admin}")

if __name__ == "__main__":
    asyncio.run(main())
