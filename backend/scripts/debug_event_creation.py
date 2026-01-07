import asyncio
import sys
import os
import logging
from datetime import date, time
from uuid import uuid4

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.calendar.services import CalendarService
from src.services.calendar.schemas import EventCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from sqlalchemy import text

async def test_event_creation():
    async with get_db_context() as session:
        service = CalendarService(session)
        
        # 1. Get a user (we'll use the first one found or a specific ID if known)
        result = await session.execute(text("SELECT id FROM auth.users LIMIT 1"))
        user_id = result.scalar()
        
        if not user_id:
            logger.error("No users found in DB to test with.")
            return

        logger.info(f"Testing with User ID: {user_id}")

        # 2. Create Event Data
        event_data = EventCreate(
            title="Debug Test Event",
            description="Created via debug script",
            start_date=date.today(),
            end_date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_all_day=False,
            event_type="meeting",
            visibility="private",
            color="#FF0000",
            is_virtual=False
        )
        
        try:
            # 3. Call Service
            logger.info("Calling create_event...")
            event = await service.create_event(user_id, event_data)
            logger.info(f"Service returned event: {event.id}")
            
            # 4. Verify Persistence (Query DB directly)
            # We need a new session or check this one? 
            # The service should have committed.
            
            check_result = await session.execute(
                text(f"SELECT id, title FROM calendar.events WHERE id = '{event.id}'")
            )
            row = check_result.first()
            
            if row:
                logger.info(f"✅ SUCCESS: Event found in DB: {row}")
            else:
                logger.error("❌ FAILURE: Event NOT found in DB after creation!")
                
        except Exception as e:
            logger.error(f"❌ EXCEPTION during creation: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_event_creation())
