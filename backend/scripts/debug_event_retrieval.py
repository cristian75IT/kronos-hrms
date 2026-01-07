import asyncio
import sys
import os
import logging
from datetime import date, timedelta
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.calendar.services import CalendarService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_retrieval():
    async with get_db_context() as session:
        # 1. Check how many events exist in DB
        result = await session.execute(text("SELECT COUNT(*) FROM calendar.events"))
        total = result.scalar()
        logger.info(f"Total events in DB: {total}")
        
        # 2. List recent events
        result = await session.execute(text("""
            SELECT id, title, calendar_id, start_date, event_type 
            FROM calendar.events 
            ORDER BY created_at DESC 
            LIMIT 10
        """))
        rows = result.fetchall()
        logger.info("Recent events:")
        for row in rows:
            logger.info(f"  - {row}")
        
        if not rows:
            logger.warning("No events found in database!")
            return
            
        # 3. Get a user ID
        user_result = await session.execute(text("SELECT id FROM auth.users LIMIT 1"))
        user_id = user_result.scalar()
        logger.info(f"Testing with user: {user_id}")
        
        # 4. Check what calendars the user can see
        service = CalendarService(session)
        
        # Get owned calendars
        owned = await service._calendars._repo.get_owned_calendars(user_id)
        logger.info(f"User owns {len(owned)} calendars:")
        for c in owned:
            logger.info(f"  - {c.id}: {c.name} (type={c.type})")
        
        # Get shared calendars
        shared = await service._calendars._repo.get_shared_with_user(user_id)
        logger.info(f"User has {len(shared)} shared calendars")
        
        # Get public calendars
        public = await service._calendars._repo.get_public_calendars()
        logger.info(f"There are {len(public)} public calendars")
        
        # 5. Check if event's calendar is in visible list
        if rows:
            event_calendar_id = rows[0][2]  # calendar_id
            all_visible = [c.id for c in owned] + [c.id for c in shared] + [c.id for c in public]
            logger.info(f"Event calendar_id: {event_calendar_id}")
            logger.info(f"Is event's calendar visible? {event_calendar_id in all_visible}")
            
        # 6. Try to get visible events via service
        today = date.today()
        start = today - timedelta(days=7)
        end = today + timedelta(days=7)
        
        visible_events = await service.get_visible_events(user_id, start, end)
        logger.info(f"Service returned {len(visible_events)} visible events")
        for e in visible_events[:5]:
            logger.info(f"  - {e.id}: {e.title}")

if __name__ == "__main__":
    asyncio.run(debug_retrieval())
