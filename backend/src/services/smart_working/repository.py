"""
KRONOS - Smart Working Repository
"""
from datetime import date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.smart_working.models import (
    SWAgreement, SWAgreementStatus,
    SWRequest, SWRequestStatus,
    SWAttendance
)

class SmartWorkingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    # -----------------------------------------------------------------------
    # Agreements
    # -----------------------------------------------------------------------

    async def get_agreement(self, id: UUID) -> Optional[SWAgreement]:
        return await self._session.get(SWAgreement, id)

    async def get_active_agreement(self, user_id: UUID, target_date: date) -> Optional[SWAgreement]:
        """Find active agreement covering target_date."""
        stmt = select(SWAgreement).where(
            SWAgreement.user_id == user_id,
            SWAgreement.status == SWAgreementStatus.ACTIVE,
            SWAgreement.start_date <= target_date,
            (SWAgreement.end_date.is_(None) | (SWAgreement.end_date >= target_date))
        )
        return await self._session.scalar(stmt)

    async def get_user_agreements(self, user_id: UUID) -> List[SWAgreement]:
        stmt = select(SWAgreement).where(SWAgreement.user_id == user_id).order_by(SWAgreement.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_agreement(self, agreement: SWAgreement) -> SWAgreement:
        self._session.add(agreement)
        await self._session.flush()
        return agreement

    async def update_agreement(self, agreement: SWAgreement) -> SWAgreement:
        await self._session.flush()
        await self._session.refresh(agreement)
        return agreement

    async def get_active_agreements_for_user(self, user_id: UUID) -> List[SWAgreement]:
        """Get all active agreements for a user (for auto-expire logic)."""
        stmt = select(SWAgreement).where(
            SWAgreement.user_id == user_id,
            SWAgreement.status == SWAgreementStatus.ACTIVE
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # Requests
    # -----------------------------------------------------------------------

    async def get_request(self, id: UUID) -> Optional[SWRequest]:
        return await self._session.get(SWRequest, id)

    async def get_request_by_date(self, user_id: UUID, target_date: date) -> Optional[SWRequest]:
        """Check for existing request on date."""
        stmt = select(SWRequest).where(
            SWRequest.user_id == user_id,
            SWRequest.date == target_date,
            SWRequest.status != SWRequestStatus.CANCELLED,
            SWRequest.status != SWRequestStatus.REJECTED
        )
        return await self._session.scalar(stmt)

    async def get_requests_in_week(self, user_id: UUID, start_date: date, end_date: date) -> int:
        """Count active requests in a week/range."""
        stmt = select(func.count(SWRequest.id)).where(
            SWRequest.user_id == user_id,
            SWRequest.date >= start_date,
            SWRequest.date <= end_date,
            SWRequest.status.in_([SWRequestStatus.PENDING, SWRequestStatus.APPROVED])
        )
        return await self._session.scalar(stmt) or 0

    async def get_user_requests(self, user_id: UUID, limit: int = 50) -> List[SWRequest]:
        stmt = (
            select(SWRequest)
            .where(SWRequest.user_id == user_id)
            .options(joinedload(SWRequest.attendance))
            .order_by(SWRequest.date.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())
    
    async def create_request(self, request: SWRequest) -> SWRequest:
        self._session.add(request)
        await self._session.flush()
        return request

    async def update_request(self, request: SWRequest) -> SWRequest:
        await self._session.flush()
        return request

    # -----------------------------------------------------------------------
    # Attendance
    # -----------------------------------------------------------------------

    async def get_attendance(self, request_id: UUID) -> Optional[SWAttendance]:
        stmt = select(SWAttendance).where(SWAttendance.request_id == request_id)
        return await self._session.scalar(stmt)

    async def create_attendance(self, attendance: SWAttendance) -> SWAttendance:
        self._session.add(attendance)
        await self._session.flush()
        return attendance

    async def update_attendance(self, attendance: SWAttendance) -> SWAttendance:
        await self._session.flush()
        return attendance
