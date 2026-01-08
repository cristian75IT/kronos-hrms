from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

class CalendarExternalRepository:
    """Repository for accessing calendar data from notification service.
    
    NOTE: This violates strict microservice isolation but centralizes queries
    until a full API-based integration is implemented.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_upcoming_closures(self, target_date: Any) -> list:
        """Get closures starting on a specific date."""
        from src.services.calendar.models import CalendarClosure
        result = await self._session.execute(
            select(CalendarClosure).where(
                and_(
                    CalendarClosure.start_date == target_date,
                    CalendarClosure.is_active == True,
                )
            )
        )
        return list(result.scalars().all())

    async def get_upcoming_holidays(self, target_date: Any, scope: str = "national") -> list:
        """Get holidays on a specific date with given scope."""
        from src.services.calendar.models import CalendarHoliday
        result = await self._session.execute(
            select(CalendarHoliday).where(
                and_(
                    CalendarHoliday.date == target_date,
                    CalendarHoliday.is_active == True,
                    CalendarHoliday.scope == scope,
                )
            )
        )
        return list(result.scalars().all())

    async def get_upcoming_personal_events(self, target_date: Any) -> list:
        """Get personal events starting on a specific date."""
        from src.services.calendar.models import CalendarEvent
        result = await self._session.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.start_date == target_date,
                    CalendarEvent.status == "confirmed",
                    CalendarEvent.user_id.isnot(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_upcoming_shared_events(self, target_date: Any) -> list:
        """Get shared/team events starting on a specific date."""
        from src.services.calendar.models import CalendarEvent
        result = await self._session.execute(
            select(CalendarEvent).where(
                and_(
                    CalendarEvent.start_date == target_date,
                    CalendarEvent.status == "confirmed",
                    CalendarEvent.calendar_id.isnot(None),
                    CalendarEvent.visibility.in_(["team", "public"]),
                )
            )
        )
        return list(result.scalars().all())

    async def get_calendar_shares(self, calendar_id: UUID) -> list:
        """Get shares for a specific calendar."""
        from src.services.calendar.models import CalendarShare
        result = await self._session.execute(
            select(CalendarShare).where(CalendarShare.calendar_id == calendar_id)
        )
        return list(result.scalars().all())
