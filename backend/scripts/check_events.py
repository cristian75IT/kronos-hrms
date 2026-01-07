
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import async_session_factory
from sqlalchemy import text

async def check_events():
    async with async_session_factory() as session:
        print("Checking recent events...")
        result = await session.execute(text("SELECT id, title, start_date, calendar_id, created_by FROM calendar.events ORDER BY created_at DESC LIMIT 5"))
        rows = result.fetchall()
        if not rows:
            print("No events found in DB!")
        for row in rows:
            print(f"Event: {row.title} (ID: {row.id}) | Users: {row.created_by} | Cal: {row.calendar_id}")

        print("\nChecking calendars...")
        result = await session.execute(text("SELECT id, name, owner_id FROM calendar.calendars LIMIT 5"))
        rows = result.fetchall()
        for row in rows:
            print(f"Calendar: {row.name} (ID: {row.id}) | Owner: {row.owner_id}")

if __name__ == "__main__":
    asyncio.run(check_events())
