import asyncio
import sys
import os
import logging
from datetime import date, timedelta
from uuid import UUID
import json

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.calendar.services import CalendarService
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_api_response():
    async with get_db_context() as session:
        service = CalendarService(session)
        
        # 1. Get user ID
        result = await session.execute(text("SELECT id FROM auth.users LIMIT 1"))
        user_id = result.scalar()
        logger.info(f"Testing with User ID: {user_id}")
        
        # 2. Define range covering recent events
        today = date.today()
        start = today - timedelta(days=30)
        end = today + timedelta(days=30)
        
        # 3. Call get_calendar_range (main logic used by Endpoint)
        response = await service.get_calendar_range(
            user_id=user_id,
            start_date=start,
            end_date=end
        )
        
        # 4. Dump JSON to see structure
        # We need to manually serialize UUIDs and dates or use Pydantic's model_dump
        logger.info("--- START API RESPONSE SNAPSHOT ---")
        
        # Iterate days and find any day with items that are 'event' or 'meeting' etc
        found_event = False
        for day in response.days:
            event_items = [i for i in day.items if i.item_type not in ('holiday', 'closure', 'leave')]
            if event_items:
                found_event = True
                logger.info(f"Day: {day.date}")
                for item in event_items:
                    # Convert to dict to see exact field names like 'date', 'start_date' etc
                    item_dict = item.model_dump()
                    logger.info(f"  ITEM: {json.dumps(item_dict, default=str)}")
                    
                    # Explicit check for known frontend issues
                    if 'start_date' in item_dict:
                        logger.warning("  ⚠️ Found 'start_date' in item! Frontend expects 'date' or might be confused.")
                    if 'date' not in item_dict:
                        logger.error("  ❌ Missing 'date' field in item!")
                    else:
                        logger.info(f"  ✅ 'date' field present: {item_dict['date']}")
        
        if not found_event:
            logger.warning("No events found in the range. Create one first.")

if __name__ == "__main__":
    asyncio.run(debug_api_response())
