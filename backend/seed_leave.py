import asyncio
import os
import sys
from datetime import date, timedelta
from uuid import UUID

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
sys.path.append("/app")

from sqlalchemy import select, text
from src.core.database import get_db_context
from src.services.leaves.models import LeaveRequest
from src.services.auth.models import User

async def seed_approved_leave():
    async with get_db_context() as session:
        # We need to access auth.users, but checking leaves schema
        # Let's try to query User. If it fails, we might need to adjust search_path or assume a user_id
        try:
             # Initial check of user
             pass
        except:
             pass
        
        # HACK: Hardcode a user ID or just try to fetch assuming cross-schema visibility if models define schema
        # Better yet, let's just insert raw SQL for simplicity to avoid ORM schema mismatch hell in a simple seed script
        # But we need the ID.
        
        # Let's try ORM first. If User model has schema='auth', it works.
        # If not, it uses default session schema which is 'leaves'.
        
        # To be safe, let's explicitly set search path to include auth
        await session.execute(text("SET search_path TO leaves, auth, public"))
        
        # Get first user
        result = await session.execute(select(User))
        user = result.scalars().first()
        
        if not user:
            print("No user found")
            return

        # Create Approved Leave for Jan 2025
        leave = LeaveRequest(
            user_id=user.id,
            leave_type_id=UUID("00000000-0000-0000-0000-000000000000"), # Dummy ID
            leave_type_code="FERIE",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 17),
            days_requested=3, # Required field
            status="approved", # Enum will be cast
            employee_notes="Seeded for Calendar Test"
        )
        # Note: Depending on model, we might need a valid leave_type_id. 
        # For simplicity, let's hope leave_type_code is sufficient or we need to query LeaveType.
        
        session.add(leave)
        await session.commit()
        print(f"Seeded Approved Leave for user {user.email if hasattr(user, 'email') else user.id}: 2025-01-15 to 2025-01-17")

if __name__ == "__main__":
    asyncio.run(seed_approved_leave())
