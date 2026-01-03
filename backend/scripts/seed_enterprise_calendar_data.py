import asyncio
import sys
import os
from uuid import uuid4
from datetime import date

# Add backend root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import get_db_context
from src.services.calendar.models import (
    WorkWeekProfile, Calendar, HolidayProfile, CalendarHoliday,
    CalendarType, LocationCalendar, LocationSubscription
)

async def seed():
    print("Starting seed...")
    async with get_db_context() as session:
        try:
            # 1. Create Work Week Profile "STANDARD_5"
            # Check if exists
            # (Skipping check for brevity, assuming clean or unique constraint handle it. 
            # But duplicate key error creates noise).
            
            ww_5 = WorkWeekProfile(
                code="STANDARD_5", 
                name="Standard 5 Days (Lun-Ven)",
                weekly_config={
                    "monday": {"is_working": True, "hours": 8.0, "start_time": "09:00", "end_time": "18:00"},
                    "tuesday": {"is_working": True, "hours": 8.0, "start_time": "09:00", "end_time": "18:00"},
                    "wednesday": {"is_working": True, "hours": 8.0, "start_time": "09:00", "end_time": "18:00"},
                    "thursday": {"is_working": True, "hours": 8.0, "start_time": "09:00", "end_time": "18:00"},
                    "friday": {"is_working": True, "hours": 8.0, "start_time": "09:00", "end_time": "18:00"},
                    "saturday": {"is_working": False, "hours": 0.0},
                    "sunday": {"is_working": False, "hours": 0.0}
                },
                total_weekly_hours=40.0,
                is_default=True
            )
            session.add(ww_5)
            
            # 2. Create System Calendar "Italian Holidays"
            sys_cal = Calendar(
                type=CalendarType.SYSTEM,
                name="Festività Italiane",
                description="Calendario nazionale festività italiane",
                color="#EF4444",
                is_system=True,
                is_active=True
            )
            session.add(sys_cal)
            await session.flush()
            
            # 3. Create Holiday Profile linked to Calendar
            hol_prof = HolidayProfile(
                calendar_id=sys_cal.id,
                code="ITA_NATIONAL",
                name="Festività Nazionali Italia",
                country_code="IT"
            )
            session.add(hol_prof)
            await session.flush()
            
            # 4. Add Holidays
            holidays = [
                {"name": "Capodanno", "date": date(2025, 1, 1), "recurrence": {"type": "yearly", "month": 1, "day": 1}},
                {"name": "Epifania", "date": date(2025, 1, 6), "recurrence": {"type": "yearly", "month": 1, "day": 6}},
                {"name": "Liberazione", "date": date(2025, 4, 25), "recurrence": {"type": "yearly", "month": 4, "day": 25}},
                {"name": "Lavoro", "date": date(2025, 5, 1), "recurrence": {"type": "yearly", "month": 5, "day": 1}},
                {"name": "Repubblica", "date": date(2025, 6, 2), "recurrence": {"type": "yearly", "month": 6, "day": 2}},
                {"name": "Ferragosto", "date": date(2025, 8, 15), "recurrence": {"type": "yearly", "month": 8, "day": 15}},
                {"name": "Ognissanti", "date": date(2025, 11, 1), "recurrence": {"type": "yearly", "month": 11, "day": 1}},
                {"name": "Immacolata", "date": date(2025, 12, 8), "recurrence": {"type": "yearly", "month": 12, "day": 8}},
                {"name": "Natale", "date": date(2025, 12, 25), "recurrence": {"type": "yearly", "month": 12, "day": 25}},
                {"name": "Santo Stefano", "date": date(2025, 12, 26), "recurrence": {"type": "yearly", "month": 12, "day": 26}},
            ]
            
            for h in holidays:
                new_h = CalendarHoliday(
                    profile_id=hol_prof.id,
                    name=h["name"],
                    date=h["date"],
                    is_recurring=True,
                    recurrence_rule=h["recurrence"],
                    is_active=True
                )
                session.add(new_h)

            await session.commit()
            print("Seed completed successfully.")
            
        except Exception as e:
            print(f"Error seeding: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed())
