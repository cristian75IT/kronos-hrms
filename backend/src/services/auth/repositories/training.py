"""KRONOS Auth - Training Repository."""
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth.models import EmployeeTraining


class EmployeeTrainingRepository:
    """Repository for employee training records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> Optional[EmployeeTraining]:
        """Get training record by ID."""
        result = await self._session.execute(
            select(EmployeeTraining).where(EmployeeTraining.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[EmployeeTraining]:
        """Get all training records for a user."""
        result = await self._session.execute(
            select(EmployeeTraining)
            .where(EmployeeTraining.user_id == user_id)
            .order_by(EmployeeTraining.issue_date.desc())
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> EmployeeTraining:
        """Create new training record."""
        training = EmployeeTraining(**kwargs)
        self._session.add(training)
        await self._session.flush()
        return training

    async def update(self, id: UUID, **kwargs: Any) -> Optional[EmployeeTraining]:
        """Update training record."""
        training = await self.get(id)
        if not training:
            return None
        
        for field, value in kwargs.items():
            if hasattr(training, field) and value is not None:
                setattr(training, field, value)
        
        await self._session.flush()
        return training

    async def delete(self, id: UUID) -> bool:
        """Delete training record."""
        training = await self.get(id)
        if not training:
            return False
        
        await self._session.delete(training)
        await self._session.flush()
        return True
