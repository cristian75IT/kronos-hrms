import asyncio
import sys
import os
from datetime import date
from uuid import UUID

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.calendar.service import CalendarService

async def test():
    print("Connecting to DB...")
    async with get_db_context() as session:
        service = CalendarService(session)
        
        # Test April 2025
        # April 25th is Liberation Day (Friday) -> Holiday
        # April has 30 days.
        start = date(2025, 4, 1)
        end = date(2025, 4, 30)
        
        print(f"Calculating working days for {start} to {end}...")
        try:
            res = await service.calculate_working_days(start, end, location_id=None)
            
            print("--- RESULT ---")
            print(f"Total Calendar Days: {res.total_calendar_days}")
            print(f"Working Days: {res.working_days}")
            print(f"Holidays found: {len(res.holidays)} -> {[h.strftime('%Y-%m-%d') for h in res.holidays]}")
            print(f"Weekend days: {len(res.weekend_days)}")
            
            # Validation
            assert res.total_calendar_days == 30
            # 25th April is in holidays?
            is_25_holiday = any(h.month == 4 and h.day == 25 for h in res.holidays)
            print(f"Is Apr 25 recognized as holiday? {is_25_holiday}")
            
        except Exception as e:
            print(f"Error during calculation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
