"""KRONOS Auth - Organization Legacy Repository (Area/Location)."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.auth.models import Area, Location


class AreaRepository:
    """Repository for areas."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Area]:
        """Get area by ID."""
        result = await self._session.execute(
            select(Area)
            .options(selectinload(Area.users))
            .where(Area.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Area]:
        """Get area by code."""
        result = await self._session.execute(
            select(Area).where(Area.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[Area]:
        """Get all areas."""
        query = select(Area).order_by(Area.name)
        
        if active_only:
            query = query.where(Area.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Area:
        """Create new area."""
        area = Area(**kwargs)
        self._session.add(area)
        await self._session.flush()
        return area

    async def update(self, id: UUID, **kwargs: Any) -> Optional[Area]:
        """Update area."""
        area = await self.get(id)
        if not area:
            return None
        
        for field, value in kwargs.items():
            if hasattr(area, field) and value is not None:
                setattr(area, field, value)
        
        await self._session.flush()
        return area


class LocationRepository:
    """Repository for locations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[Location]:
        """Get location by ID."""
        result = await self._session.execute(
            select(Location).where(Location.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Location]:
        """Get location by code."""
        result = await self._session.execute(
            select(Location).where(Location.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all(self, active_only: bool = True) -> list[Location]:
        """Get all locations."""
        query = select(Location).order_by(Location.name)
        
        if active_only:
            query = query.where(Location.is_active == True)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Location:
        """Create new location."""
        location = Location(**kwargs)
        self._session.add(location)
        await self._session.flush()
        return location
