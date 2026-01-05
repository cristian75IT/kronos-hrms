import asyncio
import os
import sys
from datetime import date, timedelta
from uuid import UUID

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
# Ensure src is in path so imports work
sys.path.append("/app")

from src.shared.clients import LeavesClient
from src.core.config import settings

async def main():
    print(f"Checking Leaves Service URL: {settings.leave_service_url}")
    
    client = LeavesClient()
    
    # Check for Jan 2025 (or current month range)
    start_date = date(2025, 1, 1)
    end_date = date(2025, 2, 1) # Jan 31st
    
    print(f"Fetching leaves from {start_date} to {end_date}...")
    
    try:
        leaves = await client.get_leaves_in_period(
            start_date=start_date,
            end_date=end_date,
            status="approved,approved_conditional"
        )
        print(f"Found {len(leaves)} approved leaves.")
        for l in leaves:
            print(f" - [{l.get('id')}] {l.get('user_name')} ({l.get('leave_type_code')}): {l.get('start_date')} to {l.get('end_date')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
